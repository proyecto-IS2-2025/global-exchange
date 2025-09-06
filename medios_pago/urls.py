# urls.py - Versión simplificada sin AJAX
from django.urls import path
from .views import (
    MedioDePagoListView, MedioDePagoUpdateView,
    MedioDePagoToggleActivoView, MedioDePagoCreateAdminView,
    MedioDePagoSoftDeleteView,
    MedioDePagoDeletedListView, MedioDePagoRestoreView, MedioDePagoHardDeleteView
)

app_name = 'medios_pago'

urlpatterns = [
    path('', MedioDePagoListView.as_view(), name='lista'),
    path('<int:pk>/editar/', MedioDePagoUpdateView.as_view(), name='editar'),
    path('<int:pk>/toggle/', MedioDePagoToggleActivoView.as_view(), name='toggle'),
    path('<int:pk>/delete/', MedioDePagoSoftDeleteView.as_view(), name='delete'),
    path('admin/nuevo/', MedioDePagoCreateAdminView.as_view(), name='crear_admin'),
    # Gestión de papelera
    path('papelera/', MedioDePagoDeletedListView.as_view(), name='papelera'),
    path('<int:pk>/restore/', MedioDePagoRestoreView.as_view(), name='restore'),
    path('<int:pk>/hard-delete/', MedioDePagoHardDeleteView.as_view(), name='hard_delete'),
    # ⚠️ ELIMINAR esta URL - Ya no se necesita la eliminación AJAX de campos
    # path('<int:medio_pk>/campo/<int:campo_pk>/delete/', CampoSoftDeleteView.as_view(), name='delete_campo'),
]