from django.urls import path
from .views import (
    CustomUserCreateView,
    CustomUserListView,
    CustomUserUpdateView,
    CustomUserDeleteView
)

urlpatterns = [
    path('users/', CustomUserListView.as_view(), name='user_list'),
    path('users/add/', CustomUserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', CustomUserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/delete/', CustomUserDeleteView.as_view(), name='user_delete'),
]