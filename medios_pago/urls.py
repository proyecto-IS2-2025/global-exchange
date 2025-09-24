# urls.py - VersiÃ³n simplificada sin soft delete
from django.urls import path
from .views import (
    MedioDePagoListView, MedioDePagoUpdateView,
    MedioDePagoToggleActivoView, MedioDePagoCreateAdminView,
    MedioDePagoDeleteView
)

app_name = 'medios_pago'

urlpatterns = [
    # Vista principal con filtros
    path('', MedioDePagoListView.as_view(), name='lista'),
    
    # CRUD bÃ¡sico
    path('admin/nuevo/', MedioDePagoCreateAdminView.as_view(), name='crear_admin'),
    path('<int:pk>/editar/', MedioDePagoUpdateView.as_view(), name='editar'),
    path('<int:pk>/toggle/', MedioDePagoToggleActivoView.as_view(), name='toggle'),
    path('<int:pk>/delete/', MedioDePagoDeleteView.as_view(), name='delete'),
]