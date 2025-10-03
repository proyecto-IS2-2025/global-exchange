from django.urls import path
from .views import (
    group_list,
    group_create,
    group_update,
    group_delete,
    group_detail_permissions,
    group_detail_users,
    group_toggle_status,
    permission_create,
    search_permissions,
    search_users,
    permission_matrix,
)

urlpatterns = [
    path('groups/', group_list, name='group_list'),
    path('groups/add/', group_create, name='group_create'),
    path('groups/<int:pk>/edit/', group_update, name='group_update'),
    path('groups/<int:pk>/delete/', group_delete, name='group_delete'),
    path('groups/<int:pk>/permissions/', group_detail_permissions, name='group_detail_permissions'),
    path('groups/<int:pk>/users/', group_detail_users, name='group_detail_users'), # Nueva URL
    path('api/search_permissions/', search_permissions, name='search_permissions'),
    path('api/search_users/', search_users, name='search_users'), # Nueva URL
    path('permissions/create/', permission_create, name='permission_create'),
    path('roles/<int:pk>/toggle_status/', group_toggle_status, name='group_toggle_status'),
    path("permisos/matriz/", permission_matrix, name="permission_matrix"),
]