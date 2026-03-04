from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('mail/', include('mail.urls')),
    path('accounts/', include('django.contrib.auth.urls')),  # для входа/выхода
    path('', lambda request: redirect('mail:inbox')),
]