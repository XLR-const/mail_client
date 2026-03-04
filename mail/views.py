from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Email
from .forms import EmailForm, EmailMoveForm

@login_required
def inbox_view(request):
    """Просмотр входящих писем"""
    # Получаем все входящие письма для текущего пользователя
    emails = Email.objects.filter(
        recipient=request.user,
        folder='inbox',
        is_deleted=False
    ).select_related('sender', 'recipient')
    
    # Поиск по письмам
    query = request.GET.get('q')
    if query:
        emails = emails.filter(
            Q(subject__icontains=query) | 
            Q(body__icontains=query) |
            Q(sender__username__icontains=query)
        )
    
    # Фильтр по прочитанным/непрочитанным
    filter_type = request.GET.get('filter')
    if filter_type == 'unread':
        emails = emails.filter(is_read=False)
    elif filter_type == 'read':
        emails = emails.filter(is_read=True)
    
    # Пагинация
    paginator = Paginator(emails, 20)  # 20 писем на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Статистика
    unread_count = emails.filter(is_read=False).count()
    
    context = {
        'page_obj': page_obj,
        'unread_count': unread_count,
        'current_folder': 'inbox'
    }
    return render(request, 'mail/inbox.html', context)


@login_required
def sent_view(request):
    """Просмотр отправленных писем"""
    emails = Email.objects.filter(
        sender=request.user,
        folder='sent',
        is_deleted=False
    ).select_related('sender', 'recipient')
    
    paginator = Paginator(emails, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_folder': 'sent'
    }
    return render(request, 'mail/sent.html', context)


@login_required
def compose_email(request):
    """Отправка нового письма (создание записи в БД)"""
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            try:
                # Создаем письмо для получателя (во входящих)
                email = form.save(sender=request.user, commit=False)
                email.folder = 'inbox'
                email.save()
                
                # Создаем копию для отправителя (в отправленных)
                sent_email = Email.objects.create(
                    sender=request.user,
                    recipient=email.recipient,
                    subject=email.subject,
                    body=email.body,
                    folder='sent',
                    is_read=True  # Для отправителя письмо считается прочитанным
                )
                
                messages.success(request, 'Письмо успешно отправлено!')
                return redirect('mail:sent')
                
            except Exception as e:
                messages.error(request, f'Ошибка при отправке: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    else:
        form = EmailForm()
    
    return render(request, 'mail/compose.html', {'form': form})


@login_required
def view_email(request, email_id):
    """Просмотр содержимого конкретного письма с отметкой о прочтении"""
    # Получаем письмо, проверяем права доступа
    email = get_object_or_404(
        Email, 
        id=email_id,
        is_deleted=False
    )
    
    # Проверяем, что пользователь имеет доступ к письму
    if email.recipient != request.user and email.sender != request.user:
        messages.error(request, 'У вас нет доступа к этому письму')
        return redirect('mail:inbox')
    
    # Если это входящее письмо и оно не прочитано - отмечаем как прочитанное
    if email.recipient == request.user and not email.is_read:
        email.mark_as_read()
    
    # Получаем следующее и предыдущее письма для навигации
    next_email = Email.objects.filter(
        recipient=request.user,
        folder=email.folder,
        created_at__gt=email.created_at,
        is_deleted=False
    ).first()
    
    prev_email = Email.objects.filter(
        recipient=request.user,
        folder=email.folder,
        created_at__lt=email.created_at,
        is_deleted=False
    ).last()
    
    context = {
        'email': email,
        'next_email': next_email,
        'prev_email': prev_email
    }
    return render(request, 'mail/view_email.html', context)


@login_required
def move_emails(request):
    """Перемещение писем между папками (POST запрос)"""
    if request.method == 'POST':
        folder = request.POST.get('folder')
        email_ids = request.POST.getlist('email_ids')
        
        if not email_ids:
            messages.warning(request, 'Не выбрано ни одного письма')
            return redirect(request.META.get('HTTP_REFERER', 'mail:inbox'))
        
        # Перемещаем каждое выбранное письмо
        moved_count = 0
        for email_id in email_ids:
            try:
                email = Email.objects.get(id=email_id)
                # Проверяем права доступа
                if email.recipient == request.user or email.sender == request.user:
                    if email.move_to_folder(folder):
                        moved_count += 1
            except Email.DoesNotExist:
                continue
        
        messages.success(
            request, 
            f'Успешно перемещено {moved_count} писем в папку "{dict(Email.FOLDER_CHOICES)[folder]}"'
        )
        
        return redirect(request.POST.get('next', 'mail:inbox'))
    
    return redirect('mail:inbox')


@login_required
def delete_emails(request):
    """Удаление писем (перемещение в корзину)"""
    if request.method == 'POST':
        email_ids = request.POST.getlist('email_ids')
        
        if not email_ids:
            messages.warning(request, 'Не выбрано ни одного письма')
            return redirect(request.META.get('HTTP_REFERER', 'mail:inbox'))
        
        # Перемещаем письма в корзину
        deleted_count = 0
        for email_id in email_ids:
            try:
                email = Email.objects.get(id=email_id)
                if email.recipient == request.user or email.sender == request.user:
                    if email.delete_email():
                        deleted_count += 1
            except Email.DoesNotExist:
                continue
        
        messages.success(request, f'{deleted_count} писем перемещено в корзину')
        
        return redirect(request.POST.get('next', 'mail:inbox'))
    
    return redirect('mail:inbox')


@login_required
def trash_view(request):
    """Просмотр корзины"""
    emails = Email.objects.filter(
        Q(recipient=request.user) | Q(sender=request.user),
        folder='trash',
        is_deleted=True
    ).select_related('sender', 'recipient')
    
    paginator = Paginator(emails, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_folder': 'trash'
    }
    return render(request, 'mail/trash.html', context)


@login_required
def archive_view(request):
    """Просмотр архива"""
    emails = Email.objects.filter(
        Q(recipient=request.user) | Q(sender=request.user),
        folder='archive',
        is_deleted=False
    ).select_related('sender', 'recipient')
    
    paginator = Paginator(emails, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_folder': 'archive'
    }
    return render(request, 'mail/archive.html', context)


@login_required
def permanent_delete(request):
    """Полное удаление писем из корзины"""
    if request.method == 'POST':
        email_ids = request.POST.getlist('email_ids')
        
        if not email_ids:
            messages.warning(request, 'Не выбрано ни одного письма')
            return redirect('mail:trash')
        
        # Удаляем письма полностью
        deleted_count = 0
        for email_id in email_ids:
            try:
                email = Email.objects.get(
                    id=email_id,
                    folder='trash'
                )
                if email.recipient == request.user or email.sender == request.user:
                    email.delete()
                    deleted_count += 1
            except Email.DoesNotExist:
                continue
        
        messages.success(request, f'{deleted_count} писем удалено навсегда')
        
        return redirect('mail:trash')
    
    return redirect('mail:trash')