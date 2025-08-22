# global-exchange/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("interfaz.urls")),
    path("nueva_app/", include("nueva_app.urls")),
    path('users/', include('users.urls')),
]