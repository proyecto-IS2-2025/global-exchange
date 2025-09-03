from django.urls import path
from . import views
from .views import DivisaListView, DivisaCreateView, DivisaToggleActivaView, DivisaUpdateView

app_name = 'divisas'
urlpatterns = [
    path('', DivisaListView.as_view(), name='lista'),
    path('nueva/', DivisaCreateView.as_view(), name='crear'),
    path('<int:pk>/editar/', DivisaUpdateView.as_view(), name='editar'),
    path('<int:pk>/toggle/', DivisaToggleActivaView.as_view(), name='toggle'),
    path("func/", views.lista_divisas, name="lista_func"),  # usa otro name distinto
    path("func/nueva/", views.crear_divisa, name="crear_func"),
]
