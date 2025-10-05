"""
URLs para la gestión de roles y permisos.
"""
from django.urls import path
from .views import (
    GroupListView,
    GroupDetailView,
    GroupCreateView,
    GroupUpdateView,
    GroupDeleteView,
    GroupDetailPermissionsView,
    GroupDetailUsersView,
    SearchPermissionsView,
    PermissionMatrixView,
    GroupToggleStatusView,
)

urlpatterns = [
    # ═══════════════════════════════════════════════════════════════
    # GESTIÓN DE GRUPOS/ROLES
    # ═══════════════════════════════════════════════════════════════
    path('groups/', GroupListView.as_view(), name='group_list'),
    path('groups/create/', GroupCreateView.as_view(), name='group_create'),
    path('groups/<int:pk>/', GroupDetailView.as_view(), name='group_detail'),
    path('groups/<int:pk>/edit/', GroupUpdateView.as_view(), name='group_update'),
    path('groups/<int:pk>/delete/', GroupDeleteView.as_view(), name='group_delete'),
    
    # ═══════════════════════════════════════════════════════════════
    # GESTIÓN DE PERMISOS
    # ═══════════════════════════════════════════════════════════════
    path('groups/<int:pk>/permissions/', 
         GroupDetailPermissionsView.as_view(), 
         name='group_detail_permissions'),
    
    # ═══════════════════════════════════════════════════════════════
    # GESTIÓN DE USUARIOS
    # ═══════════════════════════════════════════════════════════════
    path('groups/<int:pk>/users/', 
         GroupDetailUsersView.as_view(), 
         name='group_detail_users'),
    
    # ═══════════════════════════════════════════════════════════════
    # API DE BÚSQUEDA
    # ═══════════════════════════════════════════════════════════════
    path('api/permissions/search/', 
         SearchPermissionsView.as_view(), 
         name='search_permissions'),
    
    # ═══════════════════════════════════════════════════════════════
    # MATRIZ DE PERMISOS
    # ═══════════════════════════════════════════════════════════════
    path('permissions/matrix/', 
         PermissionMatrixView.as_view(), 
         name='permission_matrix'),
    path('groups/<int:pk>/toggle-status/', GroupToggleStatusView.as_view(), name='group_toggle_status'),
]