# interfaz/urls.py

from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from autenticacion.views import registro_usuario
from autenticacion.views import verificar_correo
from autenticacion.views import login_view
#from interfaz.views import redireccion_por_grupo


# interfaz/urls.py
urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("registro/", registro_usuario, name="registro"),
    path("contacto/", views.contacto, name="contacto"),
    path("verificar/<str:token>/", verificar_correo, name="verificar_correo"),
    path("login/", login_view, name="login"),
    path("logout/", LogoutView.as_view(next_page='inicio'), name="logout"),

    # Opciones admin
    # Redirección automática según grupo
    #path("redirect-dashboard/", views.redireccion_por_grupo, name="redirect_dashboard"),
]
