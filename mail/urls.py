from django.urls import path
from . import views

app_name = 'mail'

urlpatterns = [
    # Основные страницы
    path('', views.inbox_view, name='inbox'),
    path('sent/', views.sent_view, name='sent'),
    path('trash/', views.trash_view, name='trash'),
    path('archive/', views.archive_view, name='archive'),
    
    # Работа с письмами
    path('compose/', views.compose_email, name='compose'),
    path('email/<int:email_id>/', views.view_email, name='view_email'),
    
    # Действия с письмами
    path('move/', views.move_emails, name='move_emails'),
    path('delete/', views.delete_emails, name='delete_emails'),
    path('permanent-delete/', views.permanent_delete, name='permanent_delete'),
]