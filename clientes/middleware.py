# clientes/middleware.py
from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch
from django.conf import settings

from .models import Cliente, AsignacionCliente


class ClienteActivoMiddleware:
    """
    Asegura que al usuario autenticado se le asigne un 'cliente_id' en sesión
    cuando corresponda. Si tiene >1 cliente asignado y no hay selección, redirige
    a la vista de selección. Evita bucles asegurándose de no redirigir cuando ya
    estamos en la ruta de selección o login/logout/static.
    """
    def __init__(self, get_response):
        self.get_response = get_response

        # Intentar resolver los nombres de URL más comunes; si fallan, usar fallback.
        try:
            self.selector_path = reverse('clientes:seleccionar')
        except NoReverseMatch:
            try:
                self.selector_path = reverse('clientes:seleccionar_cliente')
            except NoReverseMatch:
                self.selector_path = '/clientes/seleccionar/'

        # Login url (puede venir de settings)
        self.login_path = settings.LOGIN_URL or '/login/'

        # Rutas que no queremos que redirijan
        self.exempt_paths = {
            self.selector_path,
            self.login_path,
            '/logout/',
        }

    def __call__(self, request):
        # No autenticados → nada que hacer
        if not request.user.is_authenticated:
            return self.get_response(request)

        path = request.path

        # Evitar tocar archivos estáticos / media
        if path.startswith('/static/') or path.startswith('/media/'):
            return self.get_response(request)

        # Excluir rutas de TAUSER y Banco (sistemas independientes)
        if path.startswith('/tauser/') or path.startswith('/banco/'):
            return self.get_response(request)

        # Si estamos ya en la página de selección o login, no redirigir
        if path in self.exempt_paths:
            return self.get_response(request)

        # Obtener cliente_id de la sesión
        cliente_id = request.session.get('cliente_id')
        
        # Migración: Si existe el viejo 'cliente_activo_id', migrar a 'cliente_id'
        if not cliente_id:
            cliente_activo_id_viejo = request.session.get('cliente_activo_id')
            if cliente_activo_id_viejo:
                request.session['cliente_id'] = cliente_activo_id_viejo
                request.session.pop('cliente_activo_id', None)
                cliente_id = cliente_activo_id_viejo
        
        if cliente_id:
            # Revisa si el cliente es válido (activo y asignado al usuario)
            exists = Cliente.objects.filter(
                id=cliente_id,
                esta_activo=True,
                asignacioncliente__usuario=request.user
            ).exists()
            
            if exists:
                return self.get_response(request)
            
            # Cliente inválido -> limpiar sesión
            request.session.pop('cliente_id', None)

        # Buscar asignaciones activas del usuario
        asign_qs = AsignacionCliente.objects.filter(
            usuario=request.user, 
            cliente__esta_activo=True
        )

        total = asign_qs.count()

        if total == 0:
            return self.get_response(request)

        if total == 1:
            # Si tiene exactamente 1, auto-asignar
            cliente = asign_qs.first().cliente
            request.session['cliente_id'] = cliente.id
            
            # Opcional: persistir en user.ultimo_cliente_id si existe ese campo
            try:
                request.user.ultimo_cliente_id = cliente.id
                request.user.save(update_fields=['ultimo_cliente_id'])
            except (AttributeError, Exception):
                pass
            
            return self.get_response(request)

        # Tiene más de 1 -> redirigir al selector (con next)
        next_url = request.get_full_path()
        return redirect(f"{self.selector_path}?next={next_url}")