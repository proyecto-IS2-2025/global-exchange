from django.urls import path
from . import views

app_name = "banco"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("transferir/", views.transferir, name="transferir"),
    path("historial/", views.historial, name="historial"),
]
