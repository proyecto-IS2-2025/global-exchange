from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404
from roles.views import (
    permission_denied_view,
    page_not_found_view,
    server_error_view,
    bad_request_view,
)


class CustomErrorHandlerMiddleware:
    """
    Middleware que fuerza el uso de handlers personalizados incluso en DEBUG=True.
    Solo para desarrollo/testing.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        return self.get_response(request)
    
    def process_exception(self, request, exception):
        """
        Captura excepciones y renderiza páginas personalizadas.
        """
        # Solo en desarrollo (DEBUG=True)
        if not settings.DEBUG:
            return None
        
        # ✅ Error 403 (Permission Denied)
        if isinstance(exception, PermissionDenied):
            return permission_denied_view(request, exception)
        
        # ✅ Error 404 (Not Found)
        if isinstance(exception, Http404):
            return page_not_found_view(request, exception)
        
        # ✅ Error 500 (cualquier otra excepción no capturada)
        # Descomentar para capturar TODOS los errores:
        # return server_error_view(request)
        
        # Dejar que Django maneje otros errores normalmente
        return None