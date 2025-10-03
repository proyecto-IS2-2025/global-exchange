"""
Vistas para gestión de medios de pago de clientes.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from decimal import Decimal
import logging
import csv
import re

from medios_pago.models import MedioDePago
from clientes.models import Cliente, ClienteMedioDePago, HistorialClienteMedioDePago, AsignacionCliente
from clientes.forms import ClienteMedioDePagoCompleteForm, SelectMedioDePagoForm
from .helpers import get_cliente_activo

logger = logging.getLogger(__name__)


class ClienteMedioDePagoListView(LoginRequiredMixin, ListView):
    """
    Vista mejorada para listar los medios de pago asociados al cliente activo
    """
    model = ClienteMedioDePago
    template_name = 'clientes/medios_pago/lista_medios_pago.html'
    context_object_name = 'medios_pago'
    paginate_by = 12

    def dispatch(self, request, *args, **kwargs):
        """Verificar que hay un cliente activo antes de proceder"""
        self.cliente = get_cliente_activo(request)
        if not self.cliente:
            messages.warning(
                request,
                'Debe seleccionar un cliente para gestionar medios de pago.'
            )
            return redirect('clientes:seleccionar_cliente')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """Filtrar medios de pago por cliente activo con optimizaciones"""
        queryset = ClienteMedioDePago.objects.filter(
            cliente=self.cliente
        ).select_related('medio_de_pago', 'creado_por').prefetch_related(
            'medio_de_pago__campos'
        )

        # Filtros opcionales
        estado = self.request.GET.get('estado')
        if estado == 'activos':
            queryset = queryset.filter(es_activo=True)
        elif estado == 'inactivos':
            queryset = queryset.filter(es_activo=False)

        tipo_medio = self.request.GET.get('tipo_medio')
        if tipo_medio:
            queryset = queryset.filter(medio_de_pago_id=tipo_medio)

        return queryset.order_by('-es_principal', '-fecha_actualizacion')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cliente'] = self.cliente

        # Estadísticas
        total_medios = self.get_queryset().count()
        medios_activos = self.get_queryset().filter(es_activo=True).count()
        medio_principal = self.get_queryset().filter(es_principal=True).first()

        context['stats'] = {
            'total': total_medios,
            'activos': medios_activos,
            'inactivos': total_medios - medios_activos,
            'principal': medio_principal
        }

        # Información adicional para filtros
        context['medios_disponibles'] = MedioDePago.objects.filter(
            is_active=True
        ).values('id', 'nombre')

        context['filtro_actual'] = {
            'estado': self.request.GET.get('estado', 'todos'),
            'tipo_medio': self.request.GET.get('tipo_medio', '')
        }

        return context


@login_required
def select_medio_pago_view(request):
    """
    Vista mejorada para seleccionar el tipo de medio de pago antes de agregar
    FILTRO APLICADO: Solo muestra medios con campos configurados
    """
    cliente = get_cliente_activo(request)
    if not cliente:
        messages.warning(request, 'Debe seleccionar un cliente primero.')
        return redirect('clientes:seleccionar_cliente')

    if request.method == 'POST':
        form = SelectMedioDePagoForm(cliente=cliente, data=request.POST)
        if form.is_valid():
            medio_de_pago = form.cleaned_data['medio_de_pago']
            return redirect('clientes:agregar_medio_pago', medio_id=medio_de_pago.id)
        else:
            messages.error(request, 'Por favor, seleccione un medio de pago válido.')
    else:
        form = SelectMedioDePagoForm(cliente=cliente)

    # CALCULAR campos activos dinámicamente y filtrar
    medios_con_campos = form.fields['medio_de_pago'].queryset.annotate(
        total_campos=Count('campos', distinct=True)
    ).filter(
        total_campos__gt=0  # Solo medios con al menos 1 campo
    ).order_by('nombre')

    # Actualizar el queryset del formulario
    form.fields['medio_de_pago'].queryset = medios_con_campos

    # Verificar si quedan medios disponibles después del filtro
    if not medios_con_campos.exists():
        messages.warning(
            request,
            'No hay medios de pago con campos configurados disponibles. '
            'Contacte al administrador para configurar los campos necesarios.'
        )
        return redirect('clientes:medios_pago_cliente')

    return render(request, 'clientes/medios_pago/seleccionar_medio.html', {
        'form': form,
        'cliente': cliente,
        'medios_disponibles': medios_con_campos,
        'total_medios_configurados': medios_con_campos.count()
    })


class ClienteMedioDePagoCreateView(LoginRequiredMixin, CreateView):
    """
    Vista mejorada para crear un nuevo medio de pago para el cliente
    """
    model = ClienteMedioDePago
    form_class = ClienteMedioDePagoCompleteForm
    template_name = 'clientes/medios_pago/form_medio_pago.html'

    def dispatch(self, request, *args, **kwargs):
        """Verificar cliente y medio de pago antes de proceder"""
        self.cliente = get_cliente_activo(request)
        if not self.cliente:
            messages.warning(request, 'Debe seleccionar un cliente primero.')
            return redirect('clientes:seleccionar_cliente')

        # Obtener y validar medio de pago
        medio_id = self.kwargs.get('medio_id')
        try:
            self.medio_de_pago = MedioDePago.objects.get(id=medio_id, is_active=True)
        except MedioDePago.DoesNotExist:
            messages.error(request, 'Medio de pago no encontrado o inactivo.')
            return redirect('clientes:seleccionar_medio_pago_crear')

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['cliente'] = self.cliente
        kwargs['medio_de_pago'] = self.medio_de_pago

        logger.debug(f"get_form_kwargs: cliente={self.cliente}, medio_de_pago={self.medio_de_pago}")

        return kwargs

    def form_valid(self, form):
        """Procesar formulario válido con debug detallado"""
        logger.debug("=== FORM_VALID ===")
        logger.debug(f"POST data RAW: {dict(self.request.POST)}")
        logger.debug(f"Form cleaned_data: {form.cleaned_data}")

        try:
            with transaction.atomic():
                form.instance.creado_por = self.request.user

                # Si es el primer medio de pago, marcarlo como principal automáticamente
                if not ClienteMedioDePago.objects.filter(cliente=self.cliente).exists():
                    form.instance.es_principal = True

                # 🔥 LÓGICA CRÍTICA RESTAURADA: Si se marca como principal, desmarcar los demás
                if form.instance.es_principal:
                    ClienteMedioDePago.objects.filter(
                        cliente=self.cliente,
                        es_principal=True
                    ).update(es_principal=False)
                    
                    logger.debug(f"Desmarcados medios principales previos para cliente {self.cliente.id}")

                logger.debug(f"Antes de guardar - datos_campos: {getattr(form.instance, 'datos_campos', 'No definido')}")

                response = super().form_valid(form)

                logger.debug(f"Después de guardar - datos_campos: {self.object.datos_campos}")

                # Crear registro de historial
                HistorialClienteMedioDePago.objects.create(
                    cliente_medio_pago=self.object,
                    accion='CREADO',
                    datos_nuevos=self.object.datos_campos,  # ✅ AGREGAR
                    modificado_por=self.request.user,
                    observaciones=f'Medio de pago "{self.medio_de_pago.nombre}" creado exitosamente'
                )

                messages.success(
                    self.request,
                    f'¡Perfecto! El medio de pago "{self.medio_de_pago.nombre}" fue agregado exitosamente.'
                )

                logger.info(
                    f'Usuario {self.request.user.username} agregó medio de pago '
                    f'{self.medio_de_pago.nombre} al cliente {self.cliente.nombre_completo}'
                )

                return response

        except ValidationError as e:
            logger.error(f"ValidationError: {e}")
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    for error in errors:
                        messages.error(self.request, f"{field}: {error}")
            else:
                messages.error(self.request, str(e))
            return self.form_invalid(form)

        except Exception as e:
            logger.error(f"Exception: {str(e)}", exc_info=True)
            messages.error(self.request, f'Error inesperado al guardar: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Manejar formulario inválido con debug detallado"""
        logger.debug("=== FORM_INVALID ===")
        logger.debug(f"Form errors: {form.errors}")

        # Debug detallado de cada campo con error
        for field_name, errors in form.errors.items():
            field = form.fields.get(field_name)
            if field and hasattr(field, 'label'):
                field_label = field.label or field_name
            else:
                field_label = field_name

            logger.debug(f"Campo '{field_label}' ({field_name}): {errors}")
            for error in errors:
                messages.error(self.request, f"{field_label}: {error}")

        # Errores generales del formulario
        for error in form.non_field_errors():
            logger.debug(f"Error general: {error}")
            messages.error(self.request, f"Error: {error}")

        if not form.errors:
            messages.error(
                self.request,
                'Por favor, revise los campos marcados en rojo y corrija los errores.'
            )

        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'cliente': self.cliente,
            'medio_de_pago': self.medio_de_pago,
            'action': 'Agregar',
            'campos': self.medio_de_pago.campos.all().order_by('orden', 'id'),
            'breadcrumb': [
                {'name': 'Medios de Pago', 'url': 'clientes:medios_pago_cliente'},
                {'name': 'Seleccionar Medio', 'url': 'clientes:seleccionar_medio_pago_crear'},
                {'name': f'Agregar {self.medio_de_pago.nombre}', 'active': True}
            ]
        })
        return context

    def get_success_url(self):
        return reverse('clientes:medios_pago_cliente')


class ClienteMedioDePagoUpdateView(LoginRequiredMixin, UpdateView):
    """
    Vista mejorada para editar un medio de pago del cliente
    """
    model = ClienteMedioDePago
    form_class = ClienteMedioDePagoCompleteForm
    template_name = 'clientes/medios_pago/form_medio_pago.html'

    def dispatch(self, request, *args, **kwargs):
        """Verificar permisos antes de proceder"""
        self.cliente = get_cliente_activo(request)
        if not self.cliente:
            messages.warning(request, 'Debe seleccionar un cliente primero.')
            return redirect('clientes:seleccionar_cliente')

        # Obtener el objeto y verificar permisos
        self.object = self.get_object()
        if self.object.cliente != self.cliente:
            messages.error(request, 'No tiene permisos para editar este medio de pago.')
            return redirect('clientes:medios_pago_cliente')

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['cliente'] = self.cliente
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
    
    
        context.update({
            'cliente': self.cliente,
            'medio_de_pago': self.object.medio_de_pago,
            'action': 'Editar',
            'campos': self.object.medio_de_pago.campos.all().order_by('orden', 'id'),
            'breadcrumb': [
                {'name': 'Medios de Pago', 'url': 'clientes:medios_pago_cliente'},
                {'name': f'Editar {self.object.medio_de_pago.nombre}', 'active': True}
            ]
        })
        return context

    def form_valid(self, form):
        """Procesar edición con historial"""
        try:
            with transaction.atomic():
                # Guardar datos anteriores para historial
                datos_anteriores = {
                    campo.nombre_campo: self.object.get_dato_campo(campo.nombre_campo)
                    for campo in self.object.medio_de_pago.campos.all()
                }

                # 🔥 LÓGICA CRÍTICA RESTAURADA: Si se marca como principal, desmarcar los demás
                if form.cleaned_data.get('es_principal'):
                    ClienteMedioDePago.objects.filter(
                        cliente=self.cliente,
                        es_principal=True
                    ).exclude(pk=self.object.pk).update(es_principal=False)
                    
                    logger.debug(f"Desmarcados medios principales previos para cliente {self.cliente.id}")

                response = super().form_valid(form)

                # Registrar en historial
                cambios = []
                for campo in self.object.medio_de_pago.campos.all():
                    valor_nuevo = self.object.get_dato_campo(campo.nombre_campo)
                    valor_anterior = datos_anteriores.get(campo.nombre_campo)
                    if valor_nuevo != valor_anterior:
                        cambios.append(f"{campo.nombre_campo}: '{valor_anterior}' → '{valor_nuevo}'")

                if cambios:
                    HistorialClienteMedioDePago.objects.create(
                        cliente_medio_pago=self.object,
                        accion='MODIFICADO',
                        modificado_por=self.request.user,
                        observaciones=f'Cambios: {"; ".join(cambios)}'
                    )

                messages.success(
                    self.request,
                    f'El medio de pago "{self.object.medio_de_pago.nombre}" fue actualizado exitosamente.'
                )

                logger.info(
                    f'Usuario {self.request.user.username} actualizó medio de pago '
                    f'{self.object.medio_de_pago.nombre} del cliente {self.cliente.nombre_completo}'
                )

                return response

        except Exception as e:
            messages.error(self.request, f'Error al actualizar: {str(e)}')
            logger.error(f'Error al actualizar medio de pago: {str(e)}', exc_info=True)
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('clientes:medios_pago_cliente')


class ClienteMedioDePagoToggleView(LoginRequiredMixin, View):
    """
    Vista mejorada para activar/desactivar un medio de pago del cliente
    """
    def post(self, request, pk):
        cliente = get_cliente_activo(request)
        if not cliente:
            messages.warning(request, 'Debe seleccionar un cliente primero.')
            return redirect('clientes:seleccionar_cliente')

        medio_pago = get_object_or_404(ClienteMedioDePago, pk=pk, cliente=cliente)

        # Verificar que no sea el único medio activo si se va a desactivar
        if medio_pago.es_activo:
            medios_activos = ClienteMedioDePago.objects.filter(
                cliente=cliente,
                es_activo=True
            ).count()

            if medios_activos <= 1:
                messages.error(
                    request,
                    'No puede desactivar el único medio de pago activo. '
                    'Debe tener al menos un medio activo.'
                )
                return redirect('clientes:medios_pago_cliente')

        # Cambiar estado
        medio_pago.es_activo = not medio_pago.es_activo

        # Si se desactiva un medio principal, asignar otro como principal
        if not medio_pago.es_activo and medio_pago.es_principal:
            otro_medio_activo = ClienteMedioDePago.objects.filter(
                cliente=cliente,
                es_activo=True
            ).exclude(pk=medio_pago.pk).first()

            if otro_medio_activo:
                otro_medio_activo.es_principal = True
                otro_medio_activo.save()
                medio_pago.es_principal = False

        medio_pago.save()

        # Registrar en historial
        accion = 'ACTIVADO' if medio_pago.es_activo else 'DESACTIVADO'
        HistorialClienteMedioDePago.objects.create(
            cliente_medio_pago=medio_pago,
            accion=accion,
            modificado_por=request.user,
            observaciones=f'Medio de pago {accion.lower()} por el usuario'
        )

        estado_actual = 'activado' if medio_pago.es_activo else 'desactivado'
        messages.success(
            request,
            f'Medio de pago "{medio_pago.medio_de_pago.nombre}" {estado_actual} exitosamente.'
        )

        return redirect('clientes:medios_pago_cliente')


@login_required
def medio_pago_detail_ajax(request, pk):
    """
    Vista AJAX mejorada para obtener detalles de un medio de pago
    """
    cliente = get_cliente_activo(request)
    if not cliente:
        return JsonResponse({'error': 'No hay cliente seleccionado'}, status=400)

    try:
        medio_pago = ClienteMedioDePago.objects.select_related(
            'medio_de_pago'
        ).prefetch_related(
            'medio_de_pago__campos'
        ).get(pk=pk, cliente=cliente)

        # Preparar datos de los campos
        campos_data = []
        for campo in medio_pago.medio_de_pago.campos.all().order_by('orden', 'id'):
            valor = medio_pago.get_dato_campo(campo.nombre_campo)
            campos_data.append({
                'id': campo.id,  # ✅ RESTAURAR: Necesario para el frontend
                'nombre': campo.nombre_campo,
                'etiqueta': campo.etiqueta or campo.nombre_campo.title(),
                'tipo': campo.get_tipo_dato_display(),  # ✅ RESTAURAR: Formato legible
                'tipo_codigo': campo.tipo_dato,  # ✅ AGREGAR: Para lógica JS
                'requerido': campo.is_required,  # ✅ RESTAURAR
                'valor': valor,
                'valor_enmascarado': campo.enmascarar_valor(valor) if valor else '',
                'tiene_valor': bool(valor and str(valor).strip())
            })

        # Historial reciente (últimos 5 cambios)
        historial_reciente = list(
            medio_pago.historial.select_related('modificado_por')
            .values(
                'accion', 'fecha', 'modificado_por__username', 'observaciones'
            )[:5]
        )

        data = {
            'id': medio_pago.id,
            'medio_pago_id': medio_pago.medio_de_pago.id,
            'medio_pago_nombre': medio_pago.medio_de_pago.nombre,
            'comision': float(medio_pago.medio_de_pago.comision_porcentaje),
            'es_activo': medio_pago.es_activo,
            'es_principal': medio_pago.es_principal,
            'fecha_creacion': medio_pago.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            'fecha_actualizacion': medio_pago.fecha_actualizacion.strftime('%d/%m/%Y %H:%M'),
            'creado_por': medio_pago.creado_por.username if medio_pago.creado_por else 'Sistema',
            'campos': campos_data,
            'campos_completos': medio_pago.campos_completos,
            'total_campos': len(campos_data),
            'campos_con_datos': len([c for c in campos_data if c['tiene_valor']]),
            'historial_reciente': historial_reciente
        }

        return JsonResponse(data)

    except ClienteMedioDePago.DoesNotExist:
        return JsonResponse({'error': 'Medio de pago no encontrado'}, status=404)
    except Exception as e:
        logger.error(f'Error en AJAX detail view: {str(e)}', exc_info=True)
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)


class ClienteMedioDePagoDeleteView(LoginRequiredMixin, View):
    """
    Vista mejorada para eliminar un medio de pago del cliente
    """
    def post(self, request, pk):
        cliente = get_cliente_activo(request)
        if not cliente:
            messages.warning(request, 'Debe seleccionar un cliente primero.')
            return redirect('clientes:seleccionar_cliente')

        medio_pago = get_object_or_404(ClienteMedioDePago, pk=pk, cliente=cliente)

        # Verificaciones de seguridad antes de eliminar
        total_medios = ClienteMedioDePago.objects.filter(cliente=cliente).count()

        if total_medios <= 1:
            messages.error(
                request,
                'No puede eliminar el único medio de pago del cliente. '
                'Debe tener al menos un medio de pago configurado.'
            )
            return redirect('clientes:medios_pago_cliente')

        # Guardar información antes de eliminar
        nombre_medio = medio_pago.medio_de_pago.nombre
        era_principal = medio_pago.es_principal

        try:
            with transaction.atomic():
                # Registrar eliminación en historial antes de borrar
                HistorialClienteMedioDePago.objects.create(
                    cliente_medio_pago=medio_pago,
                    accion='ELIMINADO',
                    datos_anteriores=medio_pago.datos_campos,  # ✅ AGREGAR
                    modificado_por=request.user,
                    observaciones=f'Medio de pago "{nombre_medio}" eliminado'
                )

                # Si era principal, asignar otro como principal
                if era_principal:
                    nuevo_principal = ClienteMedioDePago.objects.filter(
                        cliente=cliente,
                        es_activo=True
                    ).exclude(pk=pk).first()

                    if nuevo_principal:
                        nuevo_principal.es_principal = True
                        nuevo_principal.save()

                # Eliminar el medio de pago
                medio_pago.delete()

                messages.success(
                    request,
                    f'El medio de pago "{nombre_medio}" fue eliminado exitosamente.'
                )
                logger.info(
                    f'Usuario {request.user.username} eliminó medio de pago '
                    f'{nombre_medio} del cliente {cliente.nombre_completo}'
                )

        except Exception as e:
            messages.error(request, f'Error al eliminar el medio de pago: {str(e)}')
            logger.error(f'Error al eliminar medio de pago: {str(e)}', exc_info=True)

        return redirect('clientes:medios_pago_cliente')


@login_required
def dashboard_medios_pago(request):
    """
    Vista dashboard con estadísticas generales de medios de pago
    """
    cliente = get_cliente_activo(request)
    if not cliente:
        return redirect('clientes:seleccionar_cliente')

    # Estadísticas generales
    medios = ClienteMedioDePago.objects.filter(cliente=cliente)
    total_medios = medios.count()
    medios_activos = medios.filter(es_activo=True).count()
    medio_principal = medios.filter(es_principal=True).first()

    # Medios por tipo
    medios_por_tipo = medios.values(
        'medio_de_pago__nombre'
    ).annotate(
        cantidad=Count('id')
    ).order_by('-cantidad')

    # Actividad reciente
    historial_reciente = HistorialClienteMedioDePago.objects.filter(
        cliente_medio_pago__cliente=cliente
    ).select_related(
        'cliente_medio_pago__medio_de_pago',
        'modificado_por'
    ).order_by('-fecha')[:10]

    context = {
        'cliente': cliente,
        'stats': {
            'total': total_medios,
            'activos': medios_activos,
            'inactivos': total_medios - medios_activos,
            'principal': medio_principal
        },
        'medios_por_tipo': medios_por_tipo,
        'historial_reciente': historial_reciente,
        'puede_agregar_medios': MedioDePago.objects.filter(
            is_active=True
        ).exclude(
            id__in=medios.values_list('medio_de_pago_id', flat=True)
        ).exists()
    }

    return render(request, 'clientes/medios_pago/dashboard.html', context)


@login_required
def exportar_medios_pago(request):
    """
    Vista para exportar medios de pago del cliente (CSV)
    """
    from datetime import datetime
    
    cliente = get_cliente_activo(request)
    if not cliente:
        return redirect('clientes:seleccionar_cliente')

    # Crear respuesta CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="medios_pago_{cliente.cedula}_{datetime.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)

    # Encabezados
    headers = [
        'Tipo de Medio',
        'Estado',
        'Principal',
        'Fecha Creación',
        'Creado Por'
    ]

    # Agregar campos dinámicos como columnas
    campos_unicos = set()
    medios = ClienteMedioDePago.objects.filter(cliente=cliente).prefetch_related('medio_de_pago__campos')

    for medio in medios:
        for campo in medio.medio_de_pago.campos.all():
            campos_unicos.add(campo.nombre_campo)

    headers.extend(sorted(campos_unicos))
    writer.writerow(headers)

    # Datos
    for medio in medios:
        row = [
            medio.medio_de_pago.nombre,
            'Activo' if medio.es_activo else 'Inactivo',
            'Sí' if medio.es_principal else 'No',
            medio.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            medio.creado_por.username if medio.creado_por else 'Sistema'
        ]

        # Agregar valores de campos dinámicos
        for campo_nombre in sorted(campos_unicos):
            valor = medio.get_dato_campo(campo_nombre)
            row.append(valor or '')

        writer.writerow(row)

    return response


@login_required
def verificar_duplicados_ajax(request):
    """Vista AJAX para verificar posibles duplicados de medios de pago"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    cliente = get_cliente_activo(request)
    if not cliente:
        return JsonResponse({'error': 'Cliente no seleccionado'}, status=400)

    try:
        medio_id = request.POST.get('medio_id')
        campos_data = {}

        # Recopilar datos de campos
        for key, value in request.POST.items():
            if key.startswith('campo_') and value.strip():
                campos_data[key] = value.strip()

        if not medio_id or not campos_data:
            return JsonResponse({'duplicados': []})

        medio_de_pago = get_object_or_404(MedioDePago, id=medio_id, is_active=True)

        # Buscar posibles duplicados
        duplicados = []
        existing_medios = ClienteMedioDePago.objects.filter(
            cliente=cliente,
            medio_de_pago=medio_de_pago
        ).prefetch_related('medio_de_pago__campos')

        for existing in existing_medios:
            similitud = calcular_similitud_medio(campos_data, existing, medio_de_pago)

            if similitud['score'] > 0.7:  # 70% de similitud
                duplicados.append({
                    'id': existing.id,
                    'tipo': existing.medio_de_pago.nombre,
                    'score': similitud['score'],
                    'campos_similares': similitud['campos'],
                    'fecha_creacion': existing.fecha_creacion.strftime('%d/%m/%Y'),
                    'es_activo': existing.es_activo,
                    'es_principal': existing.es_principal
                })

        return JsonResponse({
            'duplicados': duplicados,
            'total': len(duplicados)
        })

    except Exception as e:
        logger.error(f'Error en verificación de duplicados: {str(e)}', exc_info=True)
        return JsonResponse({'error': 'Error interno'}, status=500)


def calcular_similitud_medio(campos_form, existing_medio, medio_de_pago):
    """Calcular similitud entre campos del formulario y un medio existente"""
    campos_similares = []
    total_peso = 0
    peso_similitud = 0

    # Pesos para diferentes tipos de campos
    pesos_campos = {
        'numero': 1.0,
        'cuenta': 1.0,
        'tarjeta': 1.0,
        'cbu': 1.0,
        'email': 0.9,
        'telefono': 0.7,
        'nombre': 0.3
    }

    # Mapear campos del formulario con campos del medio de pago
    campos_medio = {f'campo_{campo.id}': campo for campo in medio_de_pago.campos.all()}

    for campo_form, valor_form in campos_form.items():
        if campo_form in campos_medio:
            campo_obj = campos_medio[campo_form]
            nombre_campo = campo_obj.nombre_campo.lower()

            # Obtener valor existente
            valor_existente = existing_medio.get_dato_campo(campo_obj.nombre_campo)

            if valor_existente:
                # Determinar peso del campo
                peso = next((v for k, v in pesos_campos.items() if k in nombre_campo), 0.5)
                total_peso += peso

                # Normalizar valores para comparación
                valor_form_norm = normalizar_valor(valor_form, campo_obj.tipo_dato)
                valor_exist_norm = normalizar_valor(valor_existente, campo_obj.tipo_dato)

                # Comparación exacta
                if valor_form_norm == valor_exist_norm:
                    peso_similitud += peso
                    campos_similares.append({
                        'campo': campo_obj.nombre_campo,
                        'valor_actual': valor_form,
                        'valor_existente': str(valor_existente),
                        'similitud': 100
                    })
                elif campo_obj.tipo_dato == 'NUMERO' and len(valor_form_norm) > 4 and len(valor_exist_norm) > 4:
                    # Para números largos, verificar últimos dígitos
                    if valor_form_norm[-4:] == valor_exist_norm[-4:]:
                        peso_parcial = peso * 0.6
                        peso_similitud += peso_parcial
                        campos_similares.append({
                            'campo': campo_obj.nombre_campo,
                            'valor_actual': f"****{valor_form[-4:]}",
                            'valor_existente': f"****{str(valor_existente)[-4:]}",
                            'similitud': 60
                        })

    score = peso_similitud / total_peso if total_peso > 0 else 0

    return {
        'score': round(score, 2),
        'campos': campos_similares
    }


def normalizar_valor(valor, tipo_dato):
    """Normalizar valor para comparación"""
    if not valor:
        return ''

    valor_str = str(valor).strip().lower()

    if tipo_dato in ['NUMERO', 'TELEFONO']:
        # Remover espacios, guiones, paréntesis
        return re.sub(r'[\s\-\(\)]', '', valor_str)
    elif tipo_dato == 'EMAIL':
        return valor_str
    else:
        return valor_str


def to_serializable(value):
    """
    Convierte valores no serializables (como Decimal) a string antes de guardarlos en sesión
    """
    if isinstance(value, dict):
        return {k: to_serializable(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [to_serializable(v) for v in value]
    elif isinstance(value, Decimal):
        return str(value)
    return value


class SeleccionarMedioAcreditacionView(LoginRequiredMixin, View):
    """Vista para seleccionar medio de acreditación para operaciones de venta"""
    template_name = 'operaciones/venta/seleccionar_medio_acreditacion.html'

    def get(self, request):
        cliente = get_cliente_activo(request)
        if not cliente:
            messages.warning(request, 'Debe seleccionar un cliente primero.')
            return redirect('clientes:seleccionar_cliente')

        medios_activos = ClienteMedioDePago.objects.filter(
            cliente=cliente,
            es_activo=True
        ).select_related('medio_de_pago').prefetch_related(
            'medio_de_pago__campos'
        ).order_by('-es_principal', '-fecha_actualizacion')

        context = {
            'cliente': cliente,
            'medios_activos': medios_activos,
            'medio_seleccionado': request.session.get('medio_seleccionado'),
            'total_medios': medios_activos.count()
        }
        return render(request, self.template_name, context)

    def post(self, request):
        cliente = get_cliente_activo(request)
        if not cliente:
            return JsonResponse({'error': 'Cliente no seleccionado'}, status=400)

        medio_id = request.POST.get('medio_id')
        accion = request.POST.get('accion')

        if accion == 'seleccionar' and medio_id:
            try:
                medio = ClienteMedioDePago.objects.select_related("medio_de_pago").get(
                    id=medio_id,
                    cliente=cliente,
                    es_activo=True
                )
                request.session['medio_seleccionado'] = {
                    "id": medio.id,
                    "nombre": medio.medio_de_pago.nombre,
                    "comision": str(medio.medio_de_pago.comision_porcentaje),
                }
                request.session.modified = True

                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('operacion_divisas:venta_sumario'),
                })

            except ClienteMedioDePago.DoesNotExist:
                return JsonResponse({'error': 'Medio de pago no encontrado'}, status=404)

        elif accion == 'cancelar':
            request.session.pop('medio_seleccionado', None)
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('operacion_divisas:venta_medios'),
            })

        return JsonResponse({'error': 'Acción no válida'}, status=400)


class SeleccionarMedioPagoView(LoginRequiredMixin, View):
    """Vista para seleccionar medio de pago para operaciones de compra"""
    template_name = 'operaciones/compra/seleccionar_medio_pago.html'

    def get(self, request):
        cliente = get_cliente_activo(request)
        if not cliente:
            messages.warning(request, 'Debe seleccionar un cliente primero.')
            return redirect('clientes:seleccionar_cliente')

        medios_activos = ClienteMedioDePago.objects.filter(
            cliente=cliente,
            es_activo=True
        ).select_related('medio_de_pago').prefetch_related(
            'medio_de_pago__campos'
        ).order_by('-es_principal', '-fecha_actualizacion')

        context = {
            'cliente': cliente,
            'medios_activos': medios_activos,
            'medio_seleccionado': request.session.get('medio_pago_seleccionado'),
            'total_medios': medios_activos.count()
        }
        return render(request, self.template_name, context)

    def post(self, request):
        cliente = get_cliente_activo(request)
        if not cliente:
            return JsonResponse({'error': 'Cliente no seleccionado'}, status=400)

        medio_id = request.POST.get('medio_id')
        accion = request.POST.get('accion')

        if accion == 'seleccionar' and medio_id:
            try:
                medio = ClienteMedioDePago.objects.select_related("medio_de_pago").get(
                    id=medio_id,
                    cliente=cliente,
                    es_activo=True
                )
                request.session['medio_pago_seleccionado'] = {
                    "id": medio.id,
                    "nombre": medio.medio_de_pago.nombre,
                    "comision": str(medio.medio_de_pago.comision_porcentaje),
                }
                request.session.modified = True

                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('operacion_divisas:compra_sumario'),
                })

            except ClienteMedioDePago.DoesNotExist:
                return JsonResponse({'error': 'Medio no encontrado'}, status=404)

        elif accion == 'limpiar':
            request.session.pop('medio_pago_seleccionado', None)
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('clientes:seleccionar_medio_pago'),
            })

        return JsonResponse({'error': 'Acción no válida'}, status=400)


def get_medio_pago_seleccionado(request):
    """
    Obtener el medio de pago seleccionado para la operación de compra actual
    """
    return request.session.get("medio_pago_seleccionado")