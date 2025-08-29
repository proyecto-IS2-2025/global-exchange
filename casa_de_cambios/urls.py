# casa_de_cambios/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("", include("interfaz.urls")),
    path('admin/', admin.site.urls),
    path('clientes/', include('clientes.urls')),
    #path("adminpanel/", include("admin_app.urls")),
    path('', include('roles.urls')),
]