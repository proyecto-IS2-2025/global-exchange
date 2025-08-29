from django.urls import path
from . import views

urlpatterns = [
    path('groups/', views.group_list, name='group_list'),
    path('groups/create/', views.group_create, name='group_create'),
    path('groups/<int:pk>/edit/', views.group_update, name='group_update'),
    path('groups/<int:pk>/delete/', views.group_delete, name='group_delete'),
    path('groups/<int:pk>/', views.group_detail, name='group_detail'),
]