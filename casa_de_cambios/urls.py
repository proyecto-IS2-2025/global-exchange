from django.contrib import admin
from django.urls import path, include
from users import views as user_views
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("interfaz.urls")),
    path('usuarios/', include('users.urls')),  # URLs de la app users
    path('', lambda request: redirect('seleccionar_cliente')),  # raíz redirige a seleccionar cliente
]
