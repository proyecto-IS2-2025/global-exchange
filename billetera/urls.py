from django.urls import path
from . import views

app_name = "billetera"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.billetera_view, name="billetera"),
    path("transferir/billetera/", views.transferir_billetera_view, name="transferir_billetera"),
    path("transferir/banco/", views.transferir_a_banco_view, name="transferir_a_banco"),
]