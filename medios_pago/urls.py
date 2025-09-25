# urls.py - Versión con templates dinámicos
from django.urls import path
from .views import (
    MedioDePagoListView, MedioDePagoUpdateView,
    MedioDePagoToggleActivoView, MedioDePagoCreateAdminView,
    MedioDePagoDeleteView, TemplateDataView, DeleteTemplateView,
    TemplateListView
)

app_name = 'medios_pago'

urlpatterns = [
    # Vista principal con filtros
    path('', MedioDePagoListView.as_view(), name='lista'),
    
    # CRUD básico
    path('admin/nuevo/', MedioDePagoCreateAdminView.as_view(), name='crear_admin'),
    path('<int:pk>/editar/', MedioDePagoUpdateView.as_view(), name='editar'),
    path('<int:pk>/toggle/', MedioDePagoToggleActivoView.as_view(), name='toggle'),
    path('<int:pk>/delete/', MedioDePagoDeleteView.as_view(), name='delete'),
    
    # APIs para templates dinámicos
    path('template-data/<str:template_key>/', TemplateDataView.as_view(), name='template_data'),
    path('delete-template/<str:template_key>/', DeleteTemplateView.as_view(), name='delete_template'),
    path('templates/list/', TemplateListView.as_view(), name='template_list'),
]