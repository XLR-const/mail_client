# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Email(models.Model):
    """Модель электронного письма"""
    
    # Статусы папок
    FOLDER_CHOICES = [
        ('inbox', 'Входящие'),
        ('sent', 'Отправленные'),
        ('drafts', 'Черновики'),
        ('archive', 'Архив'),
        ('trash', 'Корзина'),
    ]
    
    # Отправитель и получатели
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_emails',
        verbose_name='Отправитель'
    )
    recipient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='received_emails',
        verbose_name='Получатель'
    )
    
    # Содержимое письма
    subject = models.CharField('Тема', max_length=255)
    body = models.TextField('Текст письма')
    
    # Метаданные
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    # Статусы
    folder = models.CharField('Папка', max_length=20, choices=FOLDER_CHOICES, default='inbox')
    is_read = models.BooleanField('Прочитано', default=False)
    is_starred = models.BooleanField('Важное', default=False)
    is_deleted = models.BooleanField('Удалено', default=False)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Письмо'
        verbose_name_plural = 'Письма'
    
    def __str__(self):
        return f'{self.subject} - {self.sender} -> {self.recipient}'
    
    def mark_as_read(self):
        """Отметить письмо как прочитанное"""
        self.is_read = True
        self.save()
    
    def move_to_folder(self, folder_name):
        """Переместить письмо в указанную папку"""
        if folder_name in dict(self.FOLDER_CHOICES).keys():
            self.folder = folder_name
            self.save()
            return True
        return False
    
    def delete_email(self):
        """Переместить письмо в корзину"""
        if self.folder != 'trash':
            self.folder = 'trash'
            self.is_deleted = True
            self.save()
            return True
        return False