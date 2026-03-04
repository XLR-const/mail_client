from django import forms
from django.contrib.auth.models import User
from .models import Email

class EmailForm(forms.ModelForm):
    """Форма для создания и отправки письма"""
    
    recipient_username = forms.CharField(
        max_length=150,
        label='Получатель',
        help_text='Введите имя пользователя получателя'
    )
    
    class Meta:
        model = Email
        fields = ['subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Тема письма'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Текст письма...'}),
        }
    
    def clean_recipient_username(self):
        """Проверяем существование получателя"""
        username = self.cleaned_data['recipient_username']
        try:
            user = User.objects.get(username=username)
            return user
        except User.DoesNotExist:
            raise forms.ValidationError('Пользователь с таким именем не найден')
    
    def save(self, sender, commit=True):
        """Сохраняем письмо с отправителем"""
        email = super().save(commit=False)
        email.sender = sender
        email.recipient = self.cleaned_data['recipient_username']
        
        if commit:
            email.save()
        return email


class EmailMoveForm(forms.Form):
    """Форма для перемещения писем между папками"""
    
    folder = forms.ChoiceField(
        choices=Email.FOLDER_CHOICES,
        label='Переместить в папку'
    )
    
    email_ids = forms.ModelMultipleChoiceField(
        queryset=Email.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='Выберите письма'
    )