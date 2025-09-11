# clientes/middleware.py
from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch
from django.conf import settings

from .models import AsignacionCliente, Cliente

class ClienteActivoMiddleware:
    """
    Asegura que al usuario autenticado se le asigne un 'cliente_activo_id' en sesión
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

        # Si estamos ya en la página de selección o login, no redirigir
        if path in self.exempt_paths:
            return self.get_response(request)

        # Chequear si ya hay cliente en sesión (puede venir de versiones previas)
        cliente_id = request.session.get('cliente_activo_id') or request.session.get('cliente_id')
        if cliente_id:
            # Validar que el cliente exista, esté activo y pertenezca al usuario
            exists = Cliente.objects.filter(
                id=cliente_id,
                esta_activo=True,
                asignacioncliente__usuario=request.user
            ).exists()
            if exists:
                # todo OK, continuar
                return self.get_response(request)
            # cliente inválido -> limpiar
            request.session.pop('cliente_activo_id', None)
            request.session.pop('cliente_id', None)

        # Buscar asignaciones activas del usuario
        asign_qs = AsignacionCliente.objects.filter(usuario=request.user, cliente__esta_activo=True)

        total = asign_qs.count()
        if total == 0:
            # no tiene clientes asignados -> no hacemos nada
            return self.get_response(request)

        if total == 1:
            # Si tiene exactamente 1, auto-asignar
            cliente = asign_qs.first().cliente
            request.session['cliente_activo_id'] = cliente.id
            # opcional: persistir en user.ultimo_cliente_id si existe ese campo
            try:
                request.user.ultimo_cliente_id = cliente.id
                request.user.save(update_fields=['ultimo_cliente_id'])
            except Exception:
                pass
            return self.get_response(request)

        # Tiene más de 1 -> redirigir al selector (con next)
        # Evitamos redirigir si ya estamos en selector (ya se cubre arriba)
        next_url = request.get_full_path()
        return redirect(f"{self.selector_path}?next={next_url}")
