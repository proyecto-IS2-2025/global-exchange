# global-exchange/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("interfaz.urls")),
    path("asociar_clientes_usuarios/", include("asociar_clientes_usuarios.urls")),
    path('users/', include('users.urls')),
]   