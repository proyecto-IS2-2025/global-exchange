# casa_de_cambios/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# ✅ Importar handlers personalizados
from roles.views import (
    permission_denied_view,
    page_not_found_view,
    server_error_view,
    bad_request_view,
)

urlpatterns = [
    path("", include("interfaz.urls")),
    path('admin/', admin.site.urls),
    path('clientes/', include('clientes.urls')),
    path('divisas/', include('divisas.urls', namespace='divisas')),
    path('users/', include ('users.urls')),
    path('', include('roles.urls')),
    path('medios_pago/', include('medios_pago.urls')),
    path('simulador/', include('simulador.urls', namespace='simulador')),
    path('transacciones/', include('transacciones.urls', namespace='transacciones')),
    path("banco/", include("banco.urls")),
    path("billetera/", include("billetera.urls", namespace="billetera")),
    path('mfa/', include('mfa.urls')),
    path('divisas/operacion/', include('operacion_divisas.urls', namespace='operacion_divisas')),
]

# Handler personalizado para error 403
handler403 = 'roles.views.permission_denied_view'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ✅ Registrar handlers de errores (SIEMPRE al final)
handler400 = 'roles.views.bad_request_view'
handler403 = 'roles.views.permission_denied_view'
handler404 = 'roles.views.page_not_found_view'
handler500 = 'roles.views.server_error_view'