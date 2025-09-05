# casa_de_cambios/urls.py
from django.contrib import admin
from django.urls import path, include
urlpatterns = [
    path("", include("interfaz.urls")),
    path('admin/', admin.site.urls),
    path('clientes/', include('clientes.urls')),
    path('divisas/', include('divisas.urls', namespace='divisas')),
    path('', include('roles.urls')),
    path('medios_pago/', include('medios_pago.urls')),
]