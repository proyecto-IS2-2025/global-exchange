# users/urls.py
app_name = 'users'
from django.urls import path
from .views import *

urlpatterns = [
    # URLs para la gestión de usuarios
    path('perfil/', perfil_usuario_view, name='perfil_usuario'),
    path('users/', CustomUserListView.as_view(), name='user_list'),
    path('users/add/', CustomUserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', CustomUserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/delete/', CustomUserDeleteView.as_view(), name='user_delete'),
    #Vista de perfil
    #path('perfil/', perfil_usuario, name='perfil_usuario'),
]