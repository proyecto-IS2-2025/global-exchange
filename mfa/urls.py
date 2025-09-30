# mfa/urls.py

from django.urls import path
from . import views

app_name = 'mfa'

urlpatterns = [
    path('verify/', views.mfa_verify_view, name='mfa_verify'),
    path('resend/', views.mfa_resend_view, name='mfa_resend'),
]