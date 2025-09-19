from django.urls import path
from . import views

urlpatterns = [
    path('groups/', views.group_list, name='group_list'),
    path('groups/add/', views.group_create, name='group_create'),
    path('groups/<int:pk>/edit/', views.group_update, name='group_update'),
    path('groups/<int:pk>/delete/', views.group_delete, name='group_delete'),
    path('groups/<int:pk>/permissions/', views.group_detail_permissions, name='group_detail_permissions'),
    path('groups/<int:pk>/users/', views.group_detail_users, name='group_detail_users'), # Nueva URL
    path('api/search_permissions/', views.search_permissions, name='search_permissions'),
    path('api/search_users/', views.search_users, name='search_users'), # Nueva URL
    path('permissions/create/', views.permission_create, name='permission_create'),
    path('roles/<int:pk>/toggle_status/', views.group_toggle_status, name='group_toggle_status'),
]