#divisas
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, View, FormView, TemplateView
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import Divisa, TasaCambio, CotizacionSegmento,  Denominacion, DesgloseDenominacion
from clientes.models import Cliente, AsignacionCliente, Descuento, Segmento, ClienteMedioDePago
from .forms import DivisaForm, TasaCambioForm
from django.db.models import Max
from django.db.models import OuterRef, Subquery
from django.contrib.auth.decorators import login_required
#Visualización tasas inicio
from divisas.services import ultimas_por_segmento
from divisas.models import Divisa
from simulador.views import calcular_simulacion_api
from django.http import JsonResponse
import json
from django.test import RequestFactory
from clientes.views import get_medio_acreditacion_seleccionado, get_medio_pago_seleccionado
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import logging
from django.contrib import messages
from .forms import DenominacionForm, DenominacionFormSet, DenominacionQuickForm
from django.forms import inlineformset_factory, formset_factory

from transacciones.models import Transaccion
from divisas.models import DesgloseDenominacion
from divisas.forms import DesgloseDenominacionForm
from .forms import DenominacionForm, DenominacionFormSet, DenominacionBaseFormSet, DenominacionQuickForm    


"""
Vistas para la gestión de divisas y tasas de cambio.

Este módulo define vistas basadas en clases (CBV) y funciones
que permiten listar, crear, actualizar y visualizar divisas
y sus tasas de cambio, incluyendo un visualizador para clientes
y otro para administradores.
"""
class DivisaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'divisas.view_divisa'
    model = Divisa
    template_name = 'divisas/lista.html'
    context_object_name = 'divisas'
    paginate_by = 20
    
    def get_queryset(self):
        # PYG siempre primero
        return Divisa.objects.all().order_by('-es_moneda_base', 'code')


class DivisaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Vista para crear una nueva divisa.

    Requiere que el usuario esté autenticado y tenga el permiso `divisas.add_divisa`.
    Asigna `is_active` a `False` por defecto al guardar la nueva divisa.
    """
    permission_required = 'divisas.add_divisa'
    model = Divisa
    form_class = DivisaForm
    template_name = 'divisas/form.html'
    success_url = reverse_lazy('divisas:lista')

    def form_valid(self, form):
        """
        Maneja el guardado del formulario válido.

        Establece `is_active` a `False` antes de guardar el objeto.
        
        :param form: El formulario de la divisa.
        :type form: :class:`~divisas.forms.DivisaForm`
        :return: Un objeto de respuesta HTTP.
        :rtype: django.http.HttpResponse
        """
        obj = form.save(commit=False)
        obj.is_active = False  # TODA nueva divisa nace deshabilitada
        obj.save()
        return redirect(self.success_url)


class DivisaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'divisas.change_divisa'
    model = Divisa
    form_class = DivisaForm
    template_name = 'divisas/form.html'
    success_url = reverse_lazy('divisas:lista')
    
    def dispatch(self, request, *args, **kwargs):
        divisa = self.get_object()
        if divisa.es_moneda_base:
            messages.error(request, "No se puede editar la moneda base del sistema.")
            return redirect('divisas:lista')
        return super().dispatch(request, *args, **kwargs)


# Agregar protección a DivisaToggleActivaView
class DivisaToggleActivaView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'divisas.change_divisa'

    def post(self, request, pk):
        divisa = get_object_or_404(Divisa, pk=pk)
        
        if divisa.es_moneda_base:
            messages.error(request, "No se puede deshabilitar la moneda base del sistema.")
            return redirect('divisas:lista')
        
        divisa.is_active = not divisa.is_active
        divisa.save()
        
        estado = "habilitada" if divisa.is_active else "deshabilitada"
        messages.success(request, f"Divisa {divisa.code} {estado} correctamente.")
        
        return redirect('divisas:lista')


def redondear(valor, decimales=2):
    try:
        return Decimal(valor).quantize(
            Decimal("1") if decimales == 0 else Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )
    except Exception:
        return valor

# ----------------------------
# TASAS DE CAMBIO
# ----------------------------
class TasaCambioListView(LoginRequiredMixin, ListView):
    """
    Vista de lista para las tasas de cambio de una divisa específica.

    Requiere que el usuario esté autenticado y tenga el permiso `divisas.view_tasacambio`.
    Muestra una tabla con las tasas de cambio históricas de una divisa.

    :param divisa_id: ID de la divisa. Se pasa a través de la URL.
    :type divisa_id: int
    """
    model = TasaCambio
    template_name = 'divisas/tasa_list.html'
    context_object_name = 'tasas'
    paginate_by = 20

    def get_queryset(self):
        """
        Filtra el queryset para mostrar solo las tasas de la divisa especificada.

        :return: El queryset filtrado de tasas de cambio.
        :rtype: django.db.models.query.QuerySet
        """
        divisa_id = self.kwargs['divisa_id']
        qs = TasaCambio.objects.filter(divisa_id=divisa_id).order_by('-fecha')

        ini = self.request.GET.get('inicio')
        fin = self.request.GET.get('fin')
        if ini:
            qs = qs.filter(fecha__gte=ini)
        if fin:
            qs = qs.filter(fecha__lte=fin)
        return qs

    def get_context_data(self, **kwargs):
        """
        Agrega la divisa al contexto de la plantilla.
        """
        ctx = super().get_context_data(**kwargs)
        ctx['divisa'] = get_object_or_404(Divisa, pk=self.kwargs['divisa_id'])
        return ctx


class TasaCambioCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Permite registrar una nueva tasa de cambio para una divisa.

    Requiere autenticación y el permiso `divisas.add_tasacambio`.
    Prellena valores con la última tasa registrada.
    """
    permission_required = 'divisas.add_tasacambio'
    model = TasaCambio
    form_class = TasaCambioForm
    template_name = 'divisas/tasa_form.html'

    def dispatch(self, request, *args, **kwargs):
        """Bloquea la creación de tasas para la moneda base (PYG)"""
        divisa = get_object_or_404(Divisa, pk=self.kwargs['divisa_id'])
        if divisa.es_moneda_base:
            messages.error(request, "No se pueden registrar tasas de cambio para la moneda base del sistema.")
            return redirect('divisas:lista')
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        divisa = get_object_or_404(Divisa, pk=self.kwargs['divisa_id'])
        ultima = TasaCambio.objects.filter(divisa=divisa).order_by('-fecha').first()
        if ultima:
            initial.update({
                'precio_base': ultima.precio_base,
                'comision_compra': ultima.comision_compra,
                'comision_venta': ultima.comision_venta,
            })
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['divisa'] = get_object_or_404(Divisa, pk=self.kwargs['divisa_id'])
        return kwargs

    def form_valid(self, form):
        tasa = form.save(commit=False)
        tasa.divisa = form.divisa
        tasa.creado_por = self.request.user
        tasa.save()
        return redirect(self.get_success_url())

    def get_success_url(self):
        # redirige al listado de tasas de la misma divisa
        return reverse('divisas:tasas', kwargs={'divisa_id': self.kwargs['divisa_id']})


class TasaCambioAllListView(LoginRequiredMixin, ListView):
    """
    Vista para ver todas las tasas de cambio de todas las divisas.

    Permite filtrar por divisa y rango de fechas.
    """
    model = TasaCambio
    template_name = 'tasa_list_global.html'
    context_object_name = 'tasas'
    paginate_by = 20

    def get_queryset(self):
        """
        Filtra el queryset de tasas de cambio basado en los parámetros de la URL.

        Los filtros disponibles son:
        * `divisa`: ID o código de la divisa.
        * `inicio`: Fecha de inicio del rango (formato YYYY-MM-DD).
        * `fin`: Fecha de fin del rango (formato YYYY-MM-DD).

        :return: El queryset filtrado de tasas de cambio.
        :rtype: django.db.models.query.QuerySet
        """
        qs = TasaCambio.objects.select_related('divisa').order_by('fecha')

        divisa_param = self.request.GET.get('divisa')
        ini = self.request.GET.get('inicio')
        fin = self.request.GET.get('fin')

        if divisa_param:
            if divisa_param.isdigit():
                qs = qs.filter(divisa_id=int(divisa_param))
            else:
                qs = qs.filter(divisa__code__iexact=divisa_param)

        if ini:
            qs = qs.filter(fecha__gte=ini)
        if fin:
            qs = qs.filter(fecha__lte=fin)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['divisas'] = Divisa.objects.order_by('code')
        # Mantener valores del filtro en el form
        ctx['f_divisa'] = self.request.GET.get('divisa', '')
        ctx['f_inicio'] = self.request.GET.get('inicio', '')
        ctx['f_fin'] = self.request.GET.get('fin', '')
        return ctx





def visualizador_tasas(request):
    """
    Muestra las tasas de cambio actuales filtradas por el cliente activo en la sesión.
    Si no hay cliente activo, usa el segmento 'general'.
    Solo muestra divisas que tienen cotizaciones para el segmento activo.
    """
    from clientes.models import Cliente, Segmento
    from .services import ultimas_por_segmento

    segmento_activo = None

    # 1. Detectar cliente activo en la sesión
    cliente_id = request.session.get("cliente_id")

    if cliente_id:
        try:
            cliente = Cliente.objects.get(id=cliente_id, esta_activo=True)
            segmento_activo = cliente.segmento
        except Cliente.DoesNotExist:
            pass

    # 2. Si no hay cliente activo, usar segmento "general"
    if not segmento_activo:
        segmento_activo, _ = Segmento.objects.get_or_create(name="general")

    # 3. Obtener divisas activas
    divisas_activas = Divisa.objects.filter(is_active=True).order_by("code")
    divisas_data = []

    for divisa in divisas_activas:
        # Obtener las últimas cotizaciones
        ultimas_cotizaciones = ultimas_por_segmento(divisa)

        # Filtrar SOLO el segmento activo
        cotizaciones_segmento = [
            cot for cot in ultimas_cotizaciones
            if cot.segmento == segmento_activo
        ]

        # 🔹 SOLO agregar si hay cotizaciones para este segmento
        if cotizaciones_segmento:
            divisas_data.append({
                "divisa": divisa,
                "cotizaciones": cotizaciones_segmento
            })

    return render(request, "visualizador.html", {
        "divisas_data": divisas_data,
        "segmento_activo": segmento_activo
    })

#Para administradores
from django.contrib.auth.decorators import user_passes_test

def is_admin_or_staff(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@user_passes_test(is_admin_or_staff)
def visualizador_tasas_admin(request):
    """
    Vista administrativa que muestra todas las cotizaciones de todos los segmentos.
    Solo accesible para staff y superusuarios.
    """
    from .services import ultimas_por_segmento
    
    divisas_activas = Divisa.objects.filter(is_active=True).order_by('code')
    divisas_data = []
    
    for divisa in divisas_activas:
        # Obtener las últimas cotizaciones para esta divisa (todos los segmentos)
        ultimas_cotizaciones = ultimas_por_segmento(divisa)
        
        divisas_data.append({
            'divisa': divisa,
            'cotizaciones': list(ultimas_cotizaciones)
        })
    
    return render(request, 'visualizador_admin.html', {
        'divisas_data': divisas_data,
        'is_admin_view': True
    })
 
# ==================== CRUD DE DENOMINACIONES ====================

class DenominacionQuickCreateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Vista para crear denominaciones rápidamente desde una lista de valores"""
    permission_required = 'divisas.add_denominacion'
    template_name = 'denominacion_quick_create.html'

    def get(self, request):
        divisa_id = request.GET.get('divisa')
        initial_data = {}
        divisa_preseleccionada = None
        
        if divisa_id:
            try:
                divisa_preseleccionada = Divisa.objects.get(id=divisa_id, is_active=True)
                initial_data['divisa'] = divisa_preseleccionada
            except Divisa.DoesNotExist:
                pass
        
        form = DenominacionQuickForm(initial=initial_data)
        
        context = {
            'form': form,
            'titulo': 'Creación Rápida de Denominaciones',
            'divisa_preseleccionada': divisa_preseleccionada,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        form = DenominacionQuickForm(request.POST)
        
        divisa_preseleccionada = None
        if 'divisa' in request.POST:
            try:
                divisa_preseleccionada = Divisa.objects.get(id=request.POST['divisa'])
            except (Divisa.DoesNotExist, ValueError):
                pass
        
        if form.is_valid():
            divisa = form.cleaned_data['divisa']
            valores = form.cleaned_data['valores']
            is_active = form.cleaned_data['is_active']
            
            count = 0
            errores = []
            
            for valor in valores:
                try:
                    # Verificar si ya existe (sin tipo)
                    existe = Denominacion.objects.filter(
                        divisa=divisa,
                        valor=valor
                    ).exists()
                    
                    if existe:
                        errores.append(f'{divisa.code} {valor} ya existe')
                        continue
                    
                    # Calcular orden
                    BASE = 100000000
                    valor_float = float(valor)
                    
                    if valor_float > 0:
                        orden_calculado = max(1, BASE - int(valor_float * 100))
                    else:
                        orden_calculado = BASE
                    
                    # Crear denominación (sin color ni tipo)
                    Denominacion.objects.create(
                        divisa=divisa,
                        valor=valor,
                        is_active=is_active,
                        orden=orden_calculado
                    )
                    count += 1
                    
                except Exception as e:
                    errores.append(f'Error al crear {valor}: {str(e)}')
            
            if count > 0:
                messages.success(
                    request, 
                    f'✅ {count} denominación(es) de {divisa.code} creada(s) exitosamente.'
                )
            
            if errores:
                for error in errores:
                    messages.warning(request, f'⚠️ {error}')
            
            if count > 0:
                return redirect('divisas:denominaciones_divisa', divisa_id=divisa.id)
            else:
                messages.error(request, '❌ No se pudo crear ninguna denominación.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
        
        context = {
            'form': form,
            'titulo': 'Creación Rápida de Denominaciones',
            'divisa_preseleccionada': divisa_preseleccionada,
        }
        return render(request, self.template_name, context)


class DenominacionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Lista todas las denominaciones con filtros"""
    model = Denominacion
    template_name = 'denominacion_list.html'
    context_object_name = 'denominaciones'
    permission_required = 'divisas.view_denominacion'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Denominacion.objects.select_related('divisa').all()
        
        # Filtro por divisa
        divisa_id = self.kwargs.get('divisa_id') or self.request.GET.get('divisa')
        if divisa_id:
            queryset = queryset.filter(divisa_id=divisa_id)
        
        # Filtro por estado
        estado = self.request.GET.get('estado')
        if estado == 'activas':
            queryset = queryset.filter(is_active=True)
        elif estado == 'inactivas':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-valor')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['divisas'] = Divisa.objects.filter(is_active=True).order_by('code')
        
        divisa_id = self.kwargs.get('divisa_id') or self.request.GET.get('divisa')
        if divisa_id:
            try:
                context['divisa_seleccionada'] = Divisa.objects.get(id=divisa_id)
            except Divisa.DoesNotExist:
                context['divisa_seleccionada'] = None
        
        denominaciones_qs = self.get_queryset()
        context['total_denominaciones'] = denominaciones_qs.count()
        context['denominaciones_activas'] = denominaciones_qs.filter(is_active=True).count()
        
        if divisa_id:
            context['estadisticas_divisa'] = {
                'total': denominaciones_qs.count(),
                'activas': denominaciones_qs.filter(is_active=True).count(),
                'inactivas': denominaciones_qs.filter(is_active=False).count(),
            }
        
        return context


class DenominacionesDivisaView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Vista para mostrar denominaciones de una divisa específica"""
    model = Denominacion
    template_name = 'denominaciones_divisa.html'
    context_object_name = 'denominaciones'
    permission_required = 'divisas.view_denominacion'
    paginate_by = 50
    
    def get_queryset(self):
        self.divisa = get_object_or_404(Divisa, id=self.kwargs['divisa_id'])
        queryset = Denominacion.objects.filter(divisa=self.divisa)
        
        # Filtro por estado
        estado = self.request.GET.get('estado')
        if estado == 'activas':
            queryset = queryset.filter(is_active=True)
        elif estado == 'inactivas':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-valor')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['divisa'] = self.divisa
        
        denoms = self.get_queryset()
        context['estadisticas'] = {
            'total': denoms.count(),
            'activas': denoms.filter(is_active=True).count(),
            'inactivas': denoms.filter(is_active=False).count(),
        }
        
        return context
    
class DenominacionCreateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Crea múltiples denominaciones a la vez"""
    permission_required = 'divisas.add_denominacion'
    template_name = 'denominacion_create_multiple.html'
    
    def get(self, request):
        # Crear formset vacío
        formset = DenominacionBaseFormSet()
        
        context = {
            'formset': formset,
            'titulo': 'Crear Denominaciones',
            'boton_texto': 'Guardar Denominaciones',
            'divisas': Divisa.objects.filter(is_active=True).order_by('code'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        formset = DenominacionBaseFormSet(request.POST, request.FILES)
        # Almacenar la divisa para redirección posterior
        divisa_redireccion = None

        if formset.is_valid():
            count = 0
            errores = []
            
            for form in formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    try:
                        denominacion = form.save(commit=False)
                        
                        # Calcular orden si no está definido o es 0
                        if not denominacion.orden or denominacion.orden == 0:
                            BASE = 100000000
                            valor_float = float(denominacion.valor) if denominacion.valor else 0
                            
                            if valor_float > 0:
                                denominacion.orden = max(1, BASE - int(valor_float * 100))
                            else:
                                denominacion.orden = BASE
                        
                        denominacion.save()
                        count += 1
                    except Exception as e:
                        errores.append(f'Error al guardar denominación: {str(e)}')
            
            if count > 0:
                messages.success(request, f'{count} denominación(es) creada(s) exitosamente.')
            
            if errores:
                for error in errores:
                    messages.error(request, error)
            
            if count > 0:
                # Redirigir a la vista de denominaciones de la divisa
                return redirect('divisas:denominaciones_divisa', divisa_id=divisa_redireccion.id)
            elif count > 0:
                # Si no hay divisa específica, ir a lista general
                return redirect('divisas:denominacion_list')
            else:
                messages.warning(request, '⚠️ No se creó ninguna denominación.')
        
        context = {
            'formset': formset,
            'titulo': 'Crear Denominaciones',
            'boton_texto': 'Guardar Denominaciones',
            'divisas': Divisa.objects.filter(is_active=True).order_by('code'),
        }
        return render(request, self.template_name, context)
    
class DenominacionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Actualiza una denominación existente"""
    model = Denominacion
    form_class = DenominacionForm
    template_name = 'denominacion_form.html'
    success_url = reverse_lazy('divisas:denominacion_list')
    permission_required = 'divisas.change_denominacion'

    def get_success_url(self):
        # Redirigir a la vista de denominaciones de la divisa
        return reverse('divisas:denominaciones_divisa', kwargs={'divisa_id': self.object.divisa.id})
    
    def form_valid(self, form):
        messages.success(self.request, f'Denominación actualizada exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Denominación: {self.object}'
        context['boton_texto'] = 'Guardar Cambios'
        return context


class DenominacionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Desactiva/activa una denominación"""
    permission_required = 'divisas.delete_denominacion'
    
    def post(self, request, pk):
        denominacion = get_object_or_404(Denominacion, pk=pk)
        divisa_id = denominacion.divisa.id  # Guardar ID de divisa antes del toggle
        denominacion.is_active = not denominacion.is_active
        denominacion.save()
        
        estado = "activada" if denominacion.is_active else "desactivada"
        messages.success(
            request, 
            f'✅ Denominación {denominacion} {estado} exitosamente.'
        )
        messages.success(request, f'Denominación {estado} correctamente.')

        return redirect('divisas:denominaciones_divisa', divisa_id=divisa_id)


@login_required
@user_passes_test(lambda u: u.has_perm('divisas.view_denominacion'))
def denominaciones_disponibles_json(request, divisa_id):
    """API para obtener denominaciones disponibles de una divisa (JSON)"""
    denominaciones = Denominacion.objects.filter(
        divisa_id=divisa_id,
        is_active=True
    ).order_by('-valor').values(
        'id', 'valor', 'valor_formateado'
    )
    
    return JsonResponse({
        'denominaciones': list(denominaciones)
    })


# ==================== CALCULADORA DE DENOMINACIONES ====================

class CalculadoraDenominacionesView(LoginRequiredMixin, TemplateView):
    """Vista para calcular el desglose óptimo de denominaciones"""
    template_name = 'divisas/calculadora_denominaciones.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['divisas'] = Divisa.objects.filter(is_active=True).order_by('code')
        return context
    
    def post(self, request, *args, **kwargs):
        divisa_id = request.POST.get('divisa_id')
        monto_str = request.POST.get('monto', '0')
        
        try:
            monto = Decimal(monto_str)
            divisa = get_object_or_404(Divisa, pk=divisa_id, is_active=True)
            
            # Obtener denominaciones activas ordenadas de mayor a menor
            denominaciones = Denominacion.objects.filter(
                divisa=divisa,
                is_active=True
            ).order_by('-valor')
            
            # Calcular desglose óptimo (algoritmo greedy)
            desglose = []
            restante = monto
            
            for denom in denominaciones:
                if restante <= 0:
                    break
                
                cantidad = int(restante / denom.valor)
                if cantidad > 0:
                    desglose.append({
                        'denominacion': denom,
                        'cantidad': cantidad,
                        'subtotal': denom.valor * cantidad
                    })
                    restante -= denom.valor * cantidad
            
            # Si hay restante, significa que no se puede dar cambio exacto
            cambio_exacto = (restante == 0)
            
            context = self.get_context_data()
            context.update({
                'divisa_seleccionada': divisa,
                'monto_solicitado': monto,
                'desglose': desglose,
                'total_entregado': sum(d['subtotal'] for d in desglose),
                'restante': restante,
                'cambio_exacto': cambio_exacto,
            })
            
            if not cambio_exacto:
                messages.warning(
                    request,
                    f'No se puede dar cambio exacto. Faltante: {divisa.simbolo}{restante:,.2f}'
                )
            
            return render(request, self.template_name, context)
            
        except (ValueError, InvalidOperation):
            messages.error(request, 'Monto inválido.')
            return redirect('divisas:calculadora_denominaciones')
        
class TransaccionDesgloseDenominacionesView(LoginRequiredMixin, View):
    """Vista para agregar desglose de denominaciones a una transacción"""
    
    def get(self, request, numero_transaccion):
        transaccion = get_object_or_404(Transaccion, numero_transaccion=numero_transaccion)
        
        # Crear formset dinámicamente
        DesgloseDenominacionFormSet = inlineformset_factory(
            Transaccion,
            DesgloseDenominacion,
            form=DesgloseDenominacionForm,
            extra=3,
            can_delete=True,
            fields=['denominacion', 'cantidad']
        )
        
        formset = DesgloseDenominacionFormSet(
            instance=transaccion,
            form_kwargs={'divisa': transaccion.divisa_destino}
        )
        
        context = {
            'transaccion': transaccion,
            'formset': formset,
        }
        
        return render(request, 'transacciones/desglose_denominaciones.html', context)
    
    def post(self, request, numero_transaccion):
        transaccion = get_object_or_404(Transaccion, numero_transaccion=numero_transaccion)
        
        DesgloseDenominacionFormSet = inlineformset_factory(
            Transaccion,
            DesgloseDenominacion,
            form=DesgloseDenominacionForm,
            extra=3,
            can_delete=True,
            fields=['denominacion', 'cantidad']
        )
        
        formset = DesgloseDenominacionFormSet(
            request.POST,
            instance=transaccion,
            form_kwargs={'divisa': transaccion.divisa_destino}
        )
        
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Desglose de denominaciones guardado correctamente.')
            return redirect('transacciones:detalle', numero_transaccion=numero_transaccion)
        
        context = {
            'transaccion': transaccion,
            'formset': formset,
        }
        
        return render(request, 'transacciones/desglose_denominaciones.html', context)
