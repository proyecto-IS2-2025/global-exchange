from django.urls import path
from .views import (
    MedioDePagoListView, MedioDePagoCreateView, MedioDePagoUpdateView,
    MedioDePagoToggleActivoView, ChequeFormView, MedioDePagoCreateAdminView
)

app_name = 'medios_pago'

urlpatterns = [
    path('', MedioDePagoListView.as_view(), name='lista'),
    path('nuevo/', MedioDePagoCreateView.as_view(), name='crear'),
    path('<int:pk>/editar/', MedioDePagoUpdateView.as_view(), name='editar'),
    path('<int:pk>/toggle/', MedioDePagoToggleActivoView.as_view(), name='toggle'),
    path('nuevo/cheque/', ChequeFormView.as_view(), name='crear_cheque'),
    path('admin/nuevo/', MedioDePagoCreateAdminView.as_view(), name='crear_admin'),
]