# global-exchange/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("interfaz.urls")),
    path('usuarios/', include('users.urls')),  # URLs de la app users
    path('', lambda request: redirect('seleccionar_cliente')),  # raíz redirige a seleccionar cliente
    path('nueva_ruta/', include('nueva_app.urls')),  # Incluye las URLs de la nueva app
    path('', lambda request: redirect('nueva_ruta/')),  # Redirige a la nueva app
]