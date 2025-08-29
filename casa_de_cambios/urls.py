# casa_de_cambios/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("", include("interfaz.urls")),
    path("asociar_clientes_usuarios/", include("asociar_clientes_usuarios.urls")),
    path('admin/', admin.site.urls),
    #path("adminpanel/", include("admin_app.urls")),
    path('', include('roles.urls')),
]