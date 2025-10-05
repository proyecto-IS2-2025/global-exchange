"""
Decoradores para proteger vistas con permisos personalizados.
CENTRALIZADOS PARA TODO EL SISTEMA.

Este módulo contiene decoradores reutilizables para Function-Based Views (FBV)
y Class-Based Views (CBV) que permiten verificar permisos personalizados
y validar acceso a clientes específicos.
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


def require_permission(permission_codename, check_client_assignment=True):
    """
    Decorador principal para proteger vistas con permisos personalizados.
    
    Este decorador verifica:
    1. Que el usuario esté autenticado (vía @login_required)
    2. Que el usuario tenga el permiso especificado
    3. (Opcional) Que el usuario tenga acceso al cliente activo en sesión
    
    Args:
        permission_codename (str): Permiso requerido en formato 'app.codename'
                                   Ejemplos:
                                   - 'clientes.view_all_clientes'
                                   - 'divisas.manage_divisas'
                                   - 'transacciones.view_transacciones_globales'
        
        check_client_assignment (bool): Si True, valida que el usuario tenga acceso
                                       al cliente activo en sesión. Usar False para
                                       vistas administrativas que no requieren cliente.
                                       Default: True
    
    Returns:
        function: Vista decorada con validaciones de permisos
    
    Raises:
        PermissionDenied: Si el usuario no tiene el permiso o no tiene acceso al cliente
    
    Ejemplos de uso:
        
        # FBV (Function-Based View):
        @require_permission('clientes.view_all_clientes', check_client_assignment=False)
        def lista_clientes(request):
            clientes = Cliente.objects.all()
            return render(request, 'clientes/lista.html', {'clientes': clientes})
        
        # FBV que requiere cliente activo:
        @require_permission('clientes.view_medios_pago', check_client_assignment=True)
        def medios_pago_cliente(request):
            cliente_id = request.session.get('cliente_activo_id')
            # ... lógica de la vista
        
        # CBV (Class-Based View):
        from django.utils.decorators import method_decorator
        
        @method_decorator(
            require_permission('clientes.view_all_clientes', check_client_assignment=False),
            name='dispatch'
        )
        class ClienteListView(ListView):
            model = Cliente
            template_name = 'clientes/lista.html'
    
    Notas:
        - El decorador automáticamente agrega @login_required
        - Los superusuarios tienen acceso a todos los clientes
        - Los usuarios con 'view_all_clientes' tienen acceso a todos los clientes
        - Otros usuarios solo acceden a clientes asignados específicamente
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required  # ✅ Requiere autenticación automáticamente
        def _wrapped_view(request, *args, **kwargs):
            # ═══════════════════════════════════════════════════════════
            # PASO 1: Verificar que el usuario tenga el permiso
            # ═══════════════════════════════════════════════════════════
            if not request.user.has_perm(permission_codename):
                raise PermissionDenied(
                    f"Se requiere el permiso '{permission_codename}' para acceder a esta vista."
                )
            
            # ═══════════════════════════════════════════════════════════
            # PASO 2: Si se requiere, validar acceso al cliente activo
            # ═══════════════════════════════════════════════════════════
            if check_client_assignment:
                cliente = _get_cliente_activo(request)
                
                # Si no hay cliente en sesión, denegar acceso
                if not cliente:
                    raise PermissionDenied(
                        "No hay un cliente activo seleccionado. "
                        "Por favor, selecciona un cliente antes de continuar."
                    )
                
                # Verificar que el usuario tenga acceso a este cliente
                if not _tiene_acceso_a_cliente(request.user, cliente):
                    raise PermissionDenied(
                        f"No tienes acceso al cliente '{cliente.razon_social}'. "
                        "Solo puedes acceder a los clientes que te han sido asignados."
                    )
            
            # ═══════════════════════════════════════════════════════════
            # PASO 3: Todas las validaciones pasaron, ejecutar vista
            # ═══════════════════════════════════════════════════════════
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    return decorator


def _get_cliente_activo(request):
    """
    Obtiene el cliente activo desde la sesión del usuario.
    
    Esta es una función helper interna que busca el ID del cliente
    almacenado en la sesión y retorna la instancia del modelo.
    
    Args:
        request: HttpRequest de Django
    
    Returns:
        Cliente | None: Instancia del cliente activo, o None si no hay seleccionado
                       o si el ID no corresponde a un cliente existente.
    
    Ejemplo de uso interno:
        cliente = _get_cliente_activo(request)
        if cliente:
            print(f"Cliente activo: {cliente.razon_social}")
    """
    # Import local para evitar importación circular
    from clientes.models import Cliente
    
    # Obtener ID de la sesión
    cliente_id = request.session.get("cliente_activo_id")
    if not cliente_id:
        return None
    
    # Buscar el cliente en la BD
    try:
        return Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        # El ID en sesión no corresponde a un cliente válido
        return None


def _tiene_acceso_a_cliente(user, cliente):
    """
    Verifica si un usuario tiene acceso a un cliente específico.
    
    Lógica de acceso:
    1. Superusuarios: Acceso total a todos los clientes
    2. Usuarios con permiso 'clientes.view_all_clientes': Acceso total
    3. Otros usuarios: Solo acceso a clientes explícitamente asignados
    
    Args:
        user: Instancia de Usuario (CustomUser o User de Django)
        cliente: Instancia del modelo Cliente
    
    Returns:
        bool: True si el usuario tiene acceso, False en caso contrario
    
    Ejemplos:
        # Superusuario
        admin = User.objects.get(username='admin')
        tiene_acceso = _tiene_acceso_a_cliente(admin, cliente)  # True
        
        # Usuario con permiso global
        gerente = User.objects.get(username='gerente')
        tiene_acceso = _tiene_acceso_a_cliente(gerente, cliente)  # True (si tiene el permiso)
        
        # Usuario con asignación específica
        operador = User.objects.get(username='operador')
        tiene_acceso = _tiene_acceso_a_cliente(operador, cliente)  # True solo si está asignado
    """
    # Import local para evitar importación circular
    from clientes.models import AsignacionCliente
    
    # Validar que el cliente exista
    if not cliente:
        return False
    
    # ═══════════════════════════════════════════════════════════
    # CASO 1: Superusuario - Acceso total
    # ═══════════════════════════════════════════════════════════
    if user.is_superuser:
        return True
    
    # ═══════════════════════════════════════════════════════════
    # CASO 2: Usuario con permiso global - Acceso total
    # ═══════════════════════════════════════════════════════════
    if user.has_perm("clientes.view_all_clientes"):
        return True
    
    # ═══════════════════════════════════════════════════════════
    # CASO 3: Usuario normal - Solo clientes asignados
    # ═══════════════════════════════════════════════════════════
    return AsignacionCliente.objects.filter(
        usuario=user,
        cliente=cliente
    ).exists()


# ═════════════════════════════════════════════════════════════════════════
# DECORADORES ADICIONALES (OPCIONALES - Para casos avanzados)
# ═════════════════════════════════════════════════════════════════════════

def any_permission_required(*perms, raise_exception=True, redirect_url='inicio'):
    """
    Decorador que requiere AL MENOS UNO de los permisos especificados.
    
    Útil cuando una vista puede ser accedida por usuarios con diferentes permisos.
    
    Args:
        *perms: Lista variable de permisos (al menos uno debe cumplirse)
        raise_exception (bool): Si True, lanza PermissionDenied. Si False, redirige.
        redirect_url (str): URL a donde redirigir si no tiene permisos (cuando raise_exception=False)
    
    Returns:
        function: Vista decorada
    
    Ejemplo:
        @any_permission_required(
            'clientes.view_cliente',
            'clientes.add_cliente',
            'clientes.change_cliente'
        )
        def panel_clientes(request):
            # Accesible si tiene view, add O change
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Superusuarios siempre pasan
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Verificar si tiene AL MENOS UN permiso
            if any(request.user.has_perm(perm) for perm in perms):
                return view_func(request, *args, **kwargs)
            
            # Sin permisos
            messages.error(
                request,
                'No tienes permisos suficientes para acceder a esta sección.'
            )
            
            if raise_exception:
                raise PermissionDenied
            
            return redirect(redirect_url)
        
        return wrapper
    return decorator


def all_permissions_required(*perms, raise_exception=True, redirect_url='inicio'):
    """
    Decorador que requiere TODOS los permisos especificados.
    
    Útil para vistas que requieren múltiples permisos simultáneamente.
    
    Args:
        *perms: Lista variable de permisos (todos deben cumplirse)
        raise_exception (bool): Si True, lanza PermissionDenied. Si False, redirige.
        redirect_url (str): URL a donde redirigir si no tiene permisos
    
    Returns:
        function: Vista decorada
    
    Ejemplo:
        @all_permissions_required(
            'clientes.view_cliente',
            'clientes.change_cliente',
            'transacciones.view_transaccion'
        )
        def editar_cliente_avanzado(request, pk):
            # Requiere view_cliente Y change_cliente Y view_transaccion
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Superusuarios siempre pasan
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Verificar si tiene TODOS los permisos
            if request.user.has_perms(perms):
                return view_func(request, *args, **kwargs)
            
            # Sin permisos
            messages.error(
                request,
                'No tienes todos los permisos necesarios para acceder a esta sección.'
            )
            
            if raise_exception:
                raise PermissionDenied
            
            return redirect(redirect_url)
        
        return wrapper
    return decorator