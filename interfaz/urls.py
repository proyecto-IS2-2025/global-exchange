from django.urls import path
from .views import menu_principal
from . import views
from django.contrib.auth.views import LogoutView
from .views import CustomLoginView


urlpatterns = [
    path("", views.inicio, name="inicio"),
    #path("login/", views.login_view, name="login"),
    #path("registro/", views.registro_view, name="registro"),
    path("registro/", views.registro_usuario, name="registro"),
    path("contacto/", views.contacto, name="contacto"),
    path('verificar/<str:token>/', views.verificar_correo, name='verificar_correo'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', LogoutView.as_view(next_page='inicio'), name='logout'),

]

