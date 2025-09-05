from django.urls import path
from .views import (
    MedioDePagoListView, MedioDePagoUpdateView,
    MedioDePagoToggleActivoView, MedioDePagoCreateAdminView
)

app_name = 'medios_pago'

urlpatterns = [
    path('', MedioDePagoListView.as_view(), name='lista'),
    path('<int:pk>/editar/', MedioDePagoUpdateView.as_view(), name='editar'),
    path('<int:pk>/toggle/', MedioDePagoToggleActivoView.as_view(), name='toggle'),
    path('admin/nuevo/', MedioDePagoCreateAdminView.as_view(), name='crear_admin'),
]