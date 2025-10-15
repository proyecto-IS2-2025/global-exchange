# transacciones/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, View
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db import transaction
from django.contrib import messages
from django.utils.decorators import method_decorator
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import logging

from roles.decorators import require_permission  # ← IMPORT PRINCIPAL
from .models import Transaccion, HistorialTransaccion
from clientes.models import Cliente
from divisas.models import Divisa
from clientes.views import get_medio_acreditacion_seleccionado, get_medio_pago_seleccionado
from clientes.services import verificar_limites

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES (SIN CAMBIOS)
# ═══════════════════════════════════════════════════════════════════

def get_cliente_from_session(request):
    """
    Obtiene el cliente activo desde la sesión.
    Retorna None si no hay cliente activo o no existe.
    """
    cliente_id = request.session.get('cliente_id')
    if not cliente_id:
        return None
    try:
        return Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return None


def calcular_monto_final(monto_base, es_compra=True):
    """
    Calcula el monto final aplicando las tasas correspondientes.
    """
    # ...existing code...
    pass


def generar_numero_transaccion():
    """
    Genera un número único de transacción basado en timestamp.
    """
    # ...existing code...
    pass


def determinar_decimales_divisa(codigo_divisa):
    """
    Determina cuántos decimales usar según la divisa.
    PYG = 0, resto = 2
    """
    return 0 if codigo_divisa.upper() == 'PYG' else 2

import re  # NUEVO: para enmascarar valores
import unicodedata  # NUEVO: normalización de texto
from django.utils import timezone  # NUEVO: para timestamps seguros
# NUEVO: modelos del banco
try:
    from banco.models import EntidadBancaria, Cuenta, BancoUser, Transferencia  # <- usar Transferencia
except Exception:
    EntidadBancaria = Cuenta = BancoUser = Transferencia = None

# === NUEVO: constantes de la cuenta de la empresa ===
EMPRESA_BANCO_NOMBRE = "Banco Py"
EMPRESA_BANCO_CODIGO = "BPY"
EMPRESA_NUMERO_CUENTA = "000111222"

def redondear(valor, decimales=2):
    """
    Redondea un valor decimal con la cantidad de decimales especificada.
    """
    try:
        return Decimal(valor).quantize(
            Decimal("1") if decimales == 0 else Decimal("0." + "0" * decimales),
            rounding=ROUND_HALF_UP
        )
    except Exception:
        return Decimal("0.00")

def determinar_decimales_divisa(codigo_divisa):
    """
    Determina la cantidad de decimales según el código de divisa.
    PYG: 0 decimales, otras: 2 decimales.
    """
    return 0 if codigo_divisa.upper() == 'PYG' else 2


# ==== RESTAURAR: helpers de presentación de medio de pago/acreditación ===#
def _humanize_etiqueta(nombre):
    """
    Convierte claves como 'numero_cuenta' -> 'Numero Cuenta'
    """
    try:
        s = str(nombre or '').strip()
        if not s:
            return 'Campo'
        return s.replace('_', ' ').replace('.', ' ').strip().title()
    except Exception:
        return 'Campo'

def _mask_generic(valor):
    """
    Enmascara emails y números largos (últimos 4). Fallback genérico.
    """
    if not valor:
        return ''
    s = str(valor).strip()
    # Email
    if '@' in s and '.' in s:
        local, _, domain = s.partition('@')
        return (local[:1] + '***@' + domain) if local else '***@' + domain
    # Numéricos largos: últimos 4
    digits = re.sub(r'\D', '', s)
    if len(digits) >= 6:
        return '****' + digits[-4:]
    # Genérico
    if len(s) > 6:
        return s[:2] + '****' + s[-2:]
    return '****'

def _build_medio_display(medio_datos):
    """
    Construye un objeto 'medio' listo para plantilla:
    { nombre, comision, tipo, campos: [ { etiqueta, valor, valor_enmascarado } ] }
    """
    if not isinstance(medio_datos, dict):
        return {}
    nombre = medio_datos.get('nombre') or ''
    comision = medio_datos.get('comision') or ''
    tipo = medio_datos.get('tipo') or ''
    campos_list = medio_datos.get('campos')

    # Si no hay lista de campos, construirla a partir de datos_campos
    if not campos_list:
        campos_list = []
        datos_campos = medio_datos.get('datos_campos') or {}
        if isinstance(datos_campos, dict):
            for key, value in datos_campos.items():
                campos_list.append({
                    'etiqueta': _humanize_etiqueta(key),
                    'valor': '' if value is None else str(value),
                    'valor_enmascarado': _mask_generic(value) if value else '',
                })
    return {
        'nombre': nombre,
        'comision': comision,
        'tipo': tipo,
        'campos': campos_list,
    }

# === NUEVO: helpers de normalización ===
def _normalize_account_number(value):
    """Deja solo dígitos en el número de cuenta, preservando ceros a la izquierda."""
    if value is None:
        return ''
    return re.sub(r'\D', '', str(value))

def _normalize_text(s):
    """
    Normaliza texto: quita acentos y caracteres no ASCII, minúsculas, compacta espacios.
    Ej: 'Guaraní' -> 'guarani', 'GuaranÝ' -> 'guarany'
    """
    if not s:
        return ''
    s = str(s).strip()
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    s = re.sub(r'\s+', ' ', s)
    return s.lower()

# ==== NUEVO: helpers de transferencia bancaria ===#
def _get_entidad(entidad_hint):
    """
    Devuelve instancia de EntidadBancaria a partir de hint (id, código o nombre),
    con matching aproximado (ignora acentos y errores típicos de codificación).
    """
    if not EntidadBancaria:
        return None
    if entidad_hint is None:
        return None
    try:
        hint = str(entidad_hint).strip()
        # ID exacto
        if hint.isdigit():
            obj = EntidadBancaria.objects.filter(pk=int(hint)).first()
            if obj:
                return obj
        # Código exacto
        obj = EntidadBancaria.objects.filter(codigo__iexact=hint).first()
        if obj:
            return obj
        # Nombre exacto
        obj = EntidadBancaria.objects.filter(nombre__iexact=hint).first()
        if obj:
            return obj

        # Matching aproximado por nombre/código normalizados
        n_hint = _normalize_text(hint)
        # Heurística: algunos fallos convierten 'í' en 'y' -> intentamos variante
        n_hint_variant = n_hint.replace('y', 'i')
        candidatos = list(EntidadBancaria.objects.all())
        for e in candidatos:
            n_nombre = _normalize_text(e.nombre)
            n_codigo = _normalize_text(e.codigo)
            if n_hint in (n_nombre, n_codigo) or n_hint_variant in (n_nombre, n_codigo):
                return e
            # Coincidencia por contains
            if n_hint and (n_hint in n_nombre or n_hint in n_codigo):
                return e
            if n_hint_variant and (n_hint_variant in n_nombre or n_hint_variant in n_codigo):
                return e
    except Exception:
        return None
    return None

def _extraer_cuenta_desde_medio(medio_datos):
    """
    Busca en medio_datos la entidad y el número de cuenta del cliente.
    Normaliza el número de cuenta (solo dígitos) y acepta etiquetas/keys flexibles.
    Retorna (entidad_hint, numero_cuenta).
    """
    if not isinstance(medio_datos, dict):
        return (None, None)

    entidad_hint = None
    numero_cuenta = None

    # 1) Intentar datos_campos raw
    datos = medio_datos.get('datos_campos') or {}
    if isinstance(datos, dict):
        for k, v in datos.items():
            key = (k or '').lower()
            if numero_cuenta is None and ('cuenta' in key or 'account' in key or key in ('numero', 'nro', 'nro_cuenta', 'numero_cuenta')):
                if v:
                    numero_cuenta = _normalize_account_number(v)
            if entidad_hint is None and any(t in key for t in ('entidad', 'banco', 'bank', 'entidad_id', 'entidad_codigo')):
                if v:
                    entidad_hint = str(v).strip()

    # 2) Intentar campos serializados (con etiqueta legible)
    if (entidad_hint is None or not numero_cuenta) and isinstance(medio_datos.get('campos'), list):
        for c in medio_datos['campos']:
            etiqueta = (c.get('etiqueta') or '').lower()
            valor = c.get('valor') or c.get('valor_enmascarado') or ''
            if not valor:
                continue
            if not numero_cuenta and ('cuenta' in etiqueta or 'account' in etiqueta or 'número' in etiqueta or etiqueta in ('numero', 'nro', 'nro cuenta', 'numero de cuenta')):
                numero_cuenta = _normalize_account_number(valor)
            if entidad_hint is None and any(t in etiqueta for t in ('entidad', 'banco', 'bank', 'código banco')):
                entidad_hint = str(valor).strip()

    return (entidad_hint, numero_cuenta or None)

def _get_cuenta_empresa():
    """
    Retorna (entidad_empresa, numero_cuenta_empresa) según datos fijos:
    - Entidad: 'Banco Py' (código 'BPY')
    - Número de cuenta: '000111222'
    Intenta resolver la entidad por código/nombre. Mantiene fallback por BancoUser si no está la entidad.
    """
    entidad = _get_entidad(EMPRESA_BANCO_CODIGO) or _get_entidad(EMPRESA_BANCO_NOMBRE)

    if not entidad and BancoUser and Cuenta:
        # Fallback: intentar por usuario conocido y su primera cuenta
        try:
            bu = BancoUser.objects.filter(email__iexact='GlobalExchange@bancopy.com').first()
            if bu:
                cta = Cuenta.objects.filter(usuario=bu).order_by('id').first()
                if cta:
                    return (cta.entidad, cta.numero_cuenta)
        except Exception:
            pass

    # Si no se encontró la entidad, devolver None y el número esperado para logging aguas arriba
    return (entidad, EMPRESA_NUMERO_CUENTA)

def realizar_transferencia_bancaria(entidad_src, numero_cuenta_src, entidad_dst, numero_cuenta_dst, monto, referencia=None):
    """
    Ejecuta transferencia entre dos cuentas. Hace fallback por número de cuenta único si la entidad no coincide.
    Retorna dict: {'ok': bool, 'code': '00', 'message': '...', 'comprobante': '...'}
    """
    if not Cuenta or not EntidadBancaria:
        return {'ok': False, 'code': '96', 'message': 'Módulo banco no disponible'}

    def _pick_by_hint(qs, hint):
        # Intenta elegir una cuenta del queryset cuyo banco coincida con el "hint" aproximado
        try:
            if not hint:
                return None
            n_hint = _normalize_text(str(hint))
            n_hint_variant = n_hint.replace('y', 'i')
            for c in qs.select_related('entidad'):
                n_nombre = _normalize_text(getattr(c.entidad, 'nombre', ''))
                n_codigo = _normalize_text(getattr(c.entidad, 'codigo', ''))
                if n_hint in (n_nombre, n_codigo) or n_hint_variant in (n_nombre, n_codigo):
                    return c
                if n_hint and (n_hint in n_nombre or n_hint in n_codigo):
                    return c
                if n_hint_variant and (n_hint_variant in n_nombre or n_hint_variant in n_codigo):
                    return c
        except Exception:
            return None
        return None

    try:
        # Validar y normalizar
        num_src = _normalize_account_number(numero_cuenta_src)
        num_dst = _normalize_account_number(numero_cuenta_dst)

        logger.info(f"[TRANSFER] Solicitud transferencia monto={monto} src_entidad={entidad_src} src_cuenta_raw={numero_cuenta_src} -> dst_entidad={entidad_dst} dst_cuenta_raw={numero_cuenta_dst}")
        logger.debug(f"[TRANSFER] Normalizado: src_cuenta={num_src}, dst_cuenta={num_dst}")

        if not (num_src and num_dst and monto is not None):
            return {'ok': False, 'code': '12', 'message': 'Datos de transferencia incompletos'}

        ent_src = entidad_src if isinstance(entidad_src, EntidadBancaria) else _get_entidad(entidad_src)
        ent_dst = entidad_dst if isinstance(entidad_dst, EntidadBancaria) else _get_entidad(entidad_dst)

        with transaction.atomic():
            # Origen
            cuenta_src = None
            if ent_src:
                cuenta_src = Cuenta.objects.select_for_update().filter(entidad=ent_src, numero_cuenta=num_src).first()
            if not cuenta_src:
                qs_src = Cuenta.objects.select_for_update().filter(numero_cuenta=num_src)
                if qs_src.count() == 1:
                    cuenta_src = qs_src.first()
                    ent_src = cuenta_src.entidad
                elif qs_src.count() > 1:
                    elegida = _pick_by_hint(qs_src, entidad_src)
                    if elegida:
                        cuenta_src = elegida
                        ent_src = cuenta_src.entidad
                    else:
                        logger.warning(f"[TRANSFER] Múltiples cuentas origen con el mismo número ({num_src}) y no se pudo desambiguar por entidad='{entidad_src}'")
                        return {'ok': False, 'code': '14', 'message': 'Cuenta origen no encontrada'}
                else:
                    return {'ok': False, 'code': '14', 'message': 'Cuenta origen no encontrada'}

            # Destino
            cuenta_dst = None
            if ent_dst:
                cuenta_dst = Cuenta.objects.select_for_update().filter(entidad=ent_dst, numero_cuenta=num_dst).first()
            if not cuenta_dst:
                qs_dst = Cuenta.objects.select_for_update().filter(numero_cuenta=num_dst)
                if qs_dst.count() == 1:
                    cuenta_dst = qs_dst.first()
                    ent_dst = cuenta_dst.entidad
                elif qs_dst.count() > 1:
                    elegida = _pick_by_hint(qs_dst, entidad_dst)
                    if elegida:
                        cuenta_dst = elegida
                        ent_dst = cuenta_dst.entidad
                    else:
                        logger.warning(f"[TRANSFER] Múltiples cuentas destino con el mismo número ({num_dst}) y no se pudo desambiguar por entidad='{entidad_dst}'")
                        return {'ok': False, 'code': '14', 'message': 'Cuenta destino no encontrada'}
                else:
                    return {'ok': False, 'code': '14', 'message': 'Cuenta destino no encontrada'}

            monto_dec = Decimal(str(monto))
            if monto_dec <= 0:
                return {'ok': False, 'code': '12', 'message': 'Monto inválido'}

            logger.info(f"[TRANSFER] Ejecutando: ORIGEN(entidad={getattr(ent_src,'codigo',None)}/{getattr(ent_src,'nombre',None)}, cuenta={cuenta_src.numero_cuenta}) "
                        f"-> DESTINO(entidad={getattr(ent_dst,'codigo',None)}/{getattr(ent_dst,'nombre',None)}, cuenta={cuenta_dst.numero_cuenta}) por Gs. {monto_dec}")

            if cuenta_src.saldo < monto_dec:
                return {'ok': False, 'code': '51', 'message': 'Fondos insuficientes en la cuenta de origen'}

            # Debitar y acreditar
            cuenta_src.saldo = cuenta_src.saldo - monto_dec
            cuenta_dst.saldo = cuenta_dst.saldo + monto_dec
            cuenta_src.save(update_fields=['saldo'])
            cuenta_dst.save(update_fields=['saldo'])

            # Registrar en banco.Transferencia para que aparezca en historial
            comprobante_val = None
            if Transferencia:
                try:
                    t = Transferencia.objects.create(
                        cuenta_origen=cuenta_src,
                        cuenta_destino=cuenta_dst,
                        monto=monto_dec
                    )
                    comprobante_val = str(getattr(t, 'comprobante', ''))
                    logger.info(f"[TRANSFER][TRX] Transferencia registrada comprobante={comprobante_val}")
                except Exception as e_trx:
                    logger.warning(f"[TRANSFER] No se pudo registrar Transferencia: {e_trx}")
            else:
                logger.warning("[TRANSFER] Modelo Transferencia no disponible")

        logger.info("[TRANSFER] Transferencia exitosa")
        # Fallback de comprobante si no se pudo crear Transferencia
        if not comprobante_val:
            comprobante_val = str(referencia or f"TR-{datetime.now().strftime('%Y%m%d%H%M%S%f')[-12:]}")
        return {'ok': True, 'code': '00', 'message': 'Transferencia realizada con éxito', 'comprobante': comprobante_val}
    except Exception as e:
        logger.error(f'Error en transferencia bancaria: {e}', exc_info=True)
        return {'ok': False, 'code': '96', 'message': 'Error interno del sistema'}

@login_required
def crear_transaccion_desde_venta(request):
    """
    Vista para crear una transacción desde el sumario de venta
    """
    if request.method != 'POST':
        messages.error(request, "Método no permitido.")
        return redirect('operacion_divisas:venta_sumario')

    try:
        operacion = request.session.get("operacion")
        medio_inst = get_medio_pago_seleccionado(request)
        
        if not operacion:
            messages.error(request, "No se encontró información de la operación.")
            return redirect("operacion_divisas:venta")

        if not medio_inst:
            messages.error(request, "No se encontró el medio de acreditación seleccionado.")
            return redirect("clientes:seleccionar_medio_acreditacion")

        # Obtener cliente activo
        cliente_id = request.session.get('cliente_id')
        if not cliente_id:
            messages.error(request, "No se encontró cliente activo.")
            return redirect('clientes:seleccionar_cliente')

        cliente = get_object_or_404(Cliente, id=cliente_id, esta_activo=True)
        
        codigo_divisa = operacion.get('divisa', '').strip().upper()
        logger.debug(f"Código de divisa desde operación: '{codigo_divisa}'")
        
        if not codigo_divisa:
            messages.error(request, "No se encontró el código de divisa en la operación.")
            return redirect('operacion_divisas:venta_sumario')
        
        try:
            divisa_origen = Divisa.objects.get(code__iexact=codigo_divisa)
            logger.debug(f"Divisa origen encontrada: {divisa_origen}")
        except Divisa.DoesNotExist:
            logger.error(f"No se encontró divisa con código: {codigo_divisa}")
            messages.error(request, f"No se encontró la divisa con código: {codigo_divisa}")
            return redirect('operacion_divisas:venta_sumario')
        
        try:
            divisa_destino = Divisa.objects.get(code__iexact='PYG')
            logger.debug(f"Divisa destino encontrada: {divisa_destino}")
        except Divisa.DoesNotExist:
            logger.error("No se encontró la divisa PYG (Guaraní)")
            messages.error(request, "Error: No se encontró la divisa Guaraní (PYG) en el sistema.")
            return redirect('operacion_divisas:venta_sumario')

        try:
            monto_origen = Decimal(str(operacion.get('monto_divisa', '0')))
            monto_destino = Decimal(str(operacion.get('monto_guaranies', '0')))
            tasa_cambio = Decimal(str(operacion.get('tasa_cambio', '0')))
        except (ValueError, TypeError) as e:
            logger.error(f"Error al convertir montos a Decimal: {e}")
            messages.error(request, "Error en los datos de la operación.")
            return redirect('operacion_divisas:venta_sumario')

        decimales_origen = determinar_decimales_divisa(divisa_origen.code)
        decimales_destino = determinar_decimales_divisa(divisa_destino.code)
        
        monto_origen = redondear(monto_origen, decimales_origen)
        monto_destino = redondear(monto_destino, decimales_destino)
        tasa_cambio = redondear(tasa_cambio, 2)

        ok, msg = verificar_limites(cliente, monto_destino)
        if not ok:
            messages.error(request, msg)
            return redirect('operacion_divisas:venta_sumario')

        medio_datos = preparar_datos_medio(medio_inst)

        with transaction.atomic():
            transaccion = Transaccion.objects.create(
                tipo_operacion='venta',
                cliente=cliente,
                divisa_origen=divisa_origen,
                divisa_destino=divisa_destino,
                monto_origen=monto_origen,
                monto_destino=monto_destino,
                tasa_de_cambio_aplicada=tasa_cambio,
                estado='pendiente',
                medio_pago_datos=medio_datos,
                procesado_por=request.user,
                observaciones=f"Transacción creada desde venta de {divisa_origen.code} por {monto_origen} {divisa_origen.code}"
            )

            HistorialTransaccion.objects.create(
                transaccion=transaccion,
                estado_anterior='',
                estado_nuevo='pendiente',
                observaciones='Transacción creada',
                modificado_por=request.user
            )

        limpiar_sesion_operacion(request)

        # NUEVO: realizar transferencia de la EMPRESA -> CLIENTE por monto_destino (PYG)
        try:
            medio_datos = transaccion.get_medio_pago_info() or {}
            ent_cli_hint, cta_cli = _extraer_cuenta_desde_medio(medio_datos)
            ent_emp, cta_emp = _get_cuenta_empresa()

            logger.debug(f"[VENTA] Extract medio -> entidad_cliente='{ent_cli_hint}', cuenta_cliente_raw='{cta_cli}' | empresa_entidad='{getattr(ent_emp,'codigo',ent_emp)}', empresa_cuenta='{cta_emp}'")

            if ent_cli_hint and cta_cli and ent_emp and cta_emp:
                resultado = realizar_transferencia_bancaria(
                    entidad_src=ent_emp,
                    numero_cuenta_src=cta_emp,
                    entidad_dst=ent_cli_hint,
                    numero_cuenta_dst=cta_cli,
                    monto=transaccion.monto_destino,
                    referencia=transaccion.numero_transaccion  # NUEVO: referencia para historial
                )
                if resultado.get('ok'):
                    transaccion.cambiar_estado('completado', observacion='Acreditación automática realizada', usuario=request.user)
                    messages.success(request, 'Transferencia realizada: operación completada.')
                else:
                    logger.warning(f"[VENTA] Transferencia fallida: {resultado}")
                    messages.warning(request, f"No se pudo realizar la transferencia: {resultado.get('message')} (código {resultado.get('code')})")
            else:
                logger.warning("[VENTA] Datos bancarios insuficientes para transferencia (empresa->cliente)")
                messages.warning(request, "No se encontraron datos bancarios suficientes para la transferencia al cliente.")
        except Exception as e:
            logger.error(f"[VENTA] Error post-transferencia: {e}", exc_info=True)
            messages.warning(request, "Ocurrió un error al procesar la transferencia al cliente.")

        # <-- RESTAURADO: siempre retornar una respuesta HTTP
        messages.success(request, f'Transacción {transaccion.numero_transaccion} creada exitosamente.')
        return redirect('transacciones:confirmacion_operacion', numero_transaccion=transaccion.numero_transaccion)

    except Exception as e:
        logger.error(f"Error al crear transacción de venta: {e}")
        messages.error(request, f"Error al procesar la transacción: {str(e)}")
        return redirect('operacion_divisas:venta_sumario')


@login_required
def crear_transaccion_desde_compra(request):
    """
    Vista para crear una transacción desde el sumario de compra
    """
    if request.method != 'POST':
        messages.error(request, "Método no permitido.")
        return redirect('operacion_divisas:compra_sumario')
    
    try:
        # Obtener datos de la sesión
        operacion = request.session.get("operacion")
        medio_inst = get_medio_pago_seleccionado(request)
        
        if not operacion:
            messages.error(request, "No se encontró información de la operación.")
            return redirect("operacion_divisas:compra")
        
        if not medio_inst:
            messages.error(request, "No se encontró el medio de pago seleccionado.")
            return redirect("clientes:seleccionar_medio_pago")

        # Obtener cliente desde la sesión
        cliente_id = request.session.get('cliente_id')
        if not cliente_id:
            messages.error(request, "No se encontró cliente activo.")
            return redirect('clientes:seleccionar_cliente')
        
        cliente = get_object_or_404(Cliente, id=cliente_id, esta_activo=True)
        
        # Obtener código de divisa desde operación
        codigo_divisa = operacion.get('divisa', '').strip().upper()
        logger.debug(f"Código de divisa desde operación: '{codigo_divisa}'")
        
        if not codigo_divisa:
            messages.error(request, "No se encontró el código de divisa en la operación.")
            return redirect('operacion_divisas:compra_sumario')
                
        # Obtener divisas - Para compra: origen=PYG, destino=divisa comprada
        try:
            divisa_origen = Divisa.objects.get(code__iexact='PYG')  # Guaraníes
            logger.debug(f"Divisa origen (PYG) encontrada: {divisa_origen}")
        except Divisa.DoesNotExist:
            logger.error("No se encontró la divisa PYG (Guaraní)")
            messages.error(request, "Error: No se encontró la divisa Guaraní (PYG) en el sistema.")
            return redirect('operacion_divisas:compra_sumario')
            
        try:
            divisa_destino = Divisa.objects.get(code__iexact=codigo_divisa)
            logger.debug(f"Divisa destino encontrada: {divisa_destino}")
        except Divisa.DoesNotExist:
            logger.error(f"No se encontró divisa con código: {codigo_divisa}")
            messages.error(request, f"No se encontró la divisa con código: {codigo_divisa}")
            return redirect('operacion_divisas:compra_sumario')

        # Convertir montos a Decimal de forma segura
        try:
            monto_origen = Decimal(str(operacion.get('monto_guaranies', '0')))  # guaraníes
            monto_destino = Decimal(str(operacion.get('monto_divisa', '0')))    # divisa extranjera
            tasa_cambio = Decimal(str(operacion.get('tasa_cambio', '0')))
        except (ValueError, TypeError) as e:
            logger.error(f"Error al convertir montos a Decimal: {e}")
            messages.error(request, "Error en los datos de la operación.")
            return redirect('operacion_divisas:compra_sumario')

        ok, msg = verificar_limites(cliente, monto_destino)
        if not ok:
            messages.error(request, msg)
            return redirect('operacion_divisas:compra_sumario')
        # Preparar datos del medio de pago
        medio_datos = {}
        if isinstance(medio_inst, dict) and medio_inst.get("id"):
            try:
                from clientes.models import ClienteMedioDePago
                medio_real = ClienteMedioDePago.objects.select_related('medio_de_pago').get(
                    id=medio_inst.get("id")
                )
                
                # Determinar el tipo del medio
                medio_model = medio_real.medio_de_pago
                tipo_label = "No definido"
                
                if medio_model.tipo_medio:
                    from medios_pago.models import TIPO_MEDIO_CHOICES
                    tipo_dict = dict(TIPO_MEDIO_CHOICES)
                    tipo_label = tipo_dict.get(medio_model.tipo_medio, "No definido")
                else:
                    api_info = medio_model.get_api_info()
                    tipo_label = api_info.get("nombre_usuario", "No definido")
                
                medio_datos = {
                    'id': medio_inst.get("id"),
                    'nombre': medio_model.nombre,
                    'tipo': tipo_label,
                    'comision': f"{medio_model.comision_porcentaje:.2f}%",
                    'datos_campos': medio_real.datos_campos or {},
                    'es_principal': medio_real.es_principal,
                }
                
            except Exception as e:
                logger.error(f"Error al obtener datos del medio: {e}")
                medio_datos = {
                    'id': medio_inst.get("id"),
                    'nombre': medio_inst.get("nombre", "Medio desconocido"),
                    'tipo': "No definido",
                    'comision': "0%",
                }
        
        # 🔹 Aplicar redondeo según regla - MEJORA ESPECÍFICA
        decimales_origen = determinar_decimales_divisa(divisa_origen.code)
        decimales_destino = determinar_decimales_divisa(divisa_destino.code)
        
        monto_origen = redondear(monto_origen, decimales_origen)  # según divisa origen
        monto_destino = redondear(monto_destino, decimales_destino)  # según divisa destino
        tasa_cambio = redondear(tasa_cambio, 2)  # tasa siempre con 2 decimales

        # Preparar datos del medio
        medio_datos = preparar_datos_medio(medio_inst)
        
        # Crear la transacción
        with transaction.atomic():
            transaccion = Transaccion.objects.create(
                tipo_operacion='compra',
                cliente=cliente,
                divisa_origen=divisa_origen,
                divisa_destino=divisa_destino,
                monto_origen=monto_origen,
                monto_destino=monto_destino,
                tasa_de_cambio_aplicada=tasa_cambio,
                estado='pendiente',
                medio_pago_datos=medio_datos,
                procesado_por=request.user,
                observaciones=f"Transacción creada desde compra de {divisa_destino.code} por {monto_origen} Gs."
            )
            
            # Crear historial inicial
            HistorialTransaccion.objects.create(
                transaccion=transaccion,
                estado_anterior='',
                estado_nuevo='pendiente',
                observaciones='Transacción creada',
                modificado_por=request.user
            )
        
        # Limpiar datos de sesión
        limpiar_sesion_operacion(request, ['operacion', 'compra_resultado', 'medio_pago_seleccionado'])

        # NUEVO: realizar transferencia del CLIENTE -> EMPRESA por monto_origen (PYG)
        try:
            medio_datos = transaccion.get_medio_pago_info() or {}
            ent_cli_hint, cta_cli = _extraer_cuenta_desde_medio(medio_datos)
            ent_emp, cta_emp = _get_cuenta_empresa()

            logger.debug(f"[COMPRA] Extract medio -> entidad_cliente='{ent_cli_hint}', cuenta_cliente_raw='{cta_cli}' | empresa_entidad='{getattr(ent_emp,'codigo',ent_emp)}', empresa_cuenta='{cta_emp}'")

            if ent_cli_hint and cta_cli and ent_emp and cta_emp:
                resultado = realizar_transferencia_bancaria(
                    entidad_src=ent_cli_hint,
                    numero_cuenta_src=cta_cli,
                    entidad_dst=ent_emp,
                    numero_cuenta_dst=cta_emp,
                    monto=transaccion.monto_origen,
                    referencia=transaccion.numero_transaccion  # NUEVO: referencia para historial
                )
                if resultado.get('ok'):
                    transaccion.cambiar_estado('pagada', observacion='Pago automático recibido', usuario=request.user)
                    messages.success(request, 'Transferencia recibida: operación pagada.')
                else:
                    logger.warning(f"[COMPRA] Transferencia fallida: {resultado}")
                    messages.warning(request, f"No se pudo recibir la transferencia: {resultado.get('message')} (código {resultado.get('code')})")
            else:
                logger.warning("[COMPRA] Datos bancarios insuficientes para transferencia (cliente->empresa)")
                messages.warning(request, "No se encontraron datos bancarios suficientes para la transferencia desde el cliente.")
        except Exception as e:
            logger.error(f"[COMPRA] Error post-transferencia: {e}", exc_info=True)
            messages.warning(request, "Ocurrió un error al procesar la transferencia desde el cliente.")

        # <-- RESTAURADO: siempre retornar una respuesta HTTP
        messages.success(request, f'Transacción {transaccion.numero_transaccion} creada exitosamente.')
        return redirect('transacciones:confirmacion_operacion', numero_transaccion=transaccion.numero_transaccion)

    except Exception as e:
        logger.error(f"Error al crear transacción de compra: {e}")
        messages.error(request, f"Error al procesar la transacción: {str(e)}")
        return redirect('operacion_divisas:compra_sumario')


def preparar_datos_medio(medio_inst):
    """
    Función auxiliar para preparar los datos del medio de pago/acreditación
    """
    medio_datos = {}
    
    if isinstance(medio_inst, dict) and medio_inst.get("id"):
        try:
            from clientes.models import ClienteMedioDePago
            medio_real = ClienteMedioDePago.objects.select_related('medio_de_pago').get(
                id=medio_inst.get("id")
            )
            medio_model = medio_real.medio_de_pago
            
            # Determinar el tipo
            tipo_label = "No definido"
            if getattr(medio_model, 'tipo_medio', None):
                from medios_pago.models import TIPO_MEDIO_CHOICES
                tipo_dict = dict(TIPO_MEDIO_CHOICES)
                tipo_label = tipo_dict.get(medio_model.tipo_medio, "No definido")
            else:
                api_info = medio_model.get_api_info()
                tipo_label = api_info.get("nombre_usuario", "No definido")

            datos_campos = medio_real.datos_campos or {}

            # NUEVO: construir lista de campos con etiqueta y valor enmascarado
            campos = []
            if isinstance(datos_campos, dict):
                for key, value in datos_campos.items():
                    campos.append({
                        'etiqueta': _humanize_etiqueta(key),
                        'valor': '' if value is None else str(value),
                        'valor_enmascarado': _mask_generic(value) if value else '',
                    })

            medio_datos = {
                'id': medio_inst.get("id"),
                'nombre': medio_model.nombre,
                'tipo': tipo_label,
                'comision': f"{medio_model.comision_porcentaje:.2f}%",
                'datos_campos': datos_campos,
                'campos': campos,  # NUEVO: listo para mostrar en plantillas
                'es_principal': medio_real.es_principal,
            }
            
        except Exception as e:
            logger.error(f"Error al obtener datos del medio: {e}")
            medio_datos = {
                'id': medio_inst.get("id"),
                'nombre': medio_inst.get("nombre", "Medio desconocido"),
                'tipo': "No definido",
                'comision': "0%",
                'datos_campos': {},
                'campos': [],
            }
    
    return medio_datos


def limpiar_sesion_operacion(request, keys_adicionales=None):
    """
    Función auxiliar para limpiar datos de operación de la sesión
    """
    keys_default = ['operacion', 'venta_resultado', 'medio']
    if keys_adicionales:
        keys_default.extend(keys_adicionales)
    
    for key in keys_default:
        request.session.pop(key, None)
    
    request.session.modified = True


@login_required
@require_permission("transacciones.view_transacciones_asignadas")  # ✅ SIN check_client_assignment
def confirmacion_operacion(request, numero_transaccion):
    """
    🔐 PROTEGIDA: transacciones.view_transacciones_asignadas
    Vista de confirmación de operación exitosa.
    """
    transaccion = get_object_or_404(
        Transaccion, 
        numero_transaccion=numero_transaccion
    )
    
    # Verificar que el usuario tenga acceso a esta transacción
    cliente_id = request.session.get('cliente_id')
    if not request.user.is_staff and str(transaccion.cliente.id) != str(cliente_id):
        messages.error(request, "No tiene permisos para ver esta transacción.")
        return redirect('inicio')
    
    # NUEVO: construir medio para la plantilla desde la transacción y adjuntar alias en el objeto
    medio_raw = transaccion.get_medio_pago_info()
    medio = _build_medio_display(medio_raw)

    # Adjuntar propiedades derivadas para plantillas que lean desde transaccion.*
    transaccion.medio_display = medio
    transaccion.medio_campos = medio.get('campos', [])
    transaccion.medio_nombre = medio.get('nombre') or ''
    transaccion.medio_comision = medio.get('comision') or ''
    transaccion.medio_tipo = medio.get('tipo') or ''
    transaccion.tiene_datos_medio = bool(transaccion.medio_campos)

    return render(request, 'confirmacion_operacion.html', {
        'transaccion': transaccion,
        # Alias adicionales en contexto por compatibilidad
        'medio': medio,                   # Objeto listo para plantilla
        'medio_pago': medio,              # Alias opcional
        'medio_campos': transaccion.medio_campos,
        'tiene_datos_medio': transaccion.tiene_datos_medio,
        'medio_datos': medio_raw,         # RAW por si la plantilla lo usa
    })


class HistorialTransaccionesClienteView(LoginRequiredMixin, ListView):
    """
    🔐 PROTEGIDA: transacciones.view_transacciones_asignadas
    Vista del historial de transacciones del cliente activo.
    """
    model = Transaccion
    template_name = 'historial_cliente.html'
    context_object_name = 'transacciones'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        # ✅ Validar cliente activo AQUÍ
        cliente_id = request.session.get('cliente_id')
        if not cliente_id:
            messages.info(request, "Selecciona un cliente para ver el historial de transacciones")
            return redirect('clientes:seleccionar_cliente')
        
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # Obtener cliente activo de la sesión
        cliente_id = self.request.session.get('cliente_id')
        if not cliente_id:
            return Transaccion.objects.none()
        
        try:
            cliente = Cliente.objects.get(id=cliente_id, esta_activo=True)
        except Cliente.DoesNotExist:
            return Transaccion.objects.none()
        
        # Filtros base
        queryset = Transaccion.objects.filter(
            cliente=cliente
        ).select_related(
            'divisa_origen', 'divisa_destino', 'cliente'
        ).order_by('-fecha_creacion')
        
        # Aplicar filtros adicionales
        tipo_filtro = self.request.GET.get('tipo', 'todos')
        if tipo_filtro in ['compra', 'venta']:
            queryset = queryset.filter(tipo_operacion=tipo_filtro)
        
        estado_filtro = self.request.GET.get('estado')
        if estado_filtro:
            queryset = queryset.filter(estado=estado_filtro)
        
        # Filtros de fecha
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        
        if fecha_desde:
            try:
                fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
                queryset = queryset.filter(fecha_creacion__gte=fecha_desde_dt)
            except ValueError:
                pass
        
        if fecha_hasta:
            try:
                fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d') + timedelta(days=1)
                queryset = queryset.filter(fecha_creacion__lt=fecha_hasta_dt)
            except ValueError:
                pass
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        cliente_id = self.request.session.get('cliente_id')
        if cliente_id:
            try:
                context['cliente_activo'] = Cliente.objects.get(id=cliente_id, esta_activo=True)
            except Cliente.DoesNotExist:
                context['cliente_activo'] = None
        
        # Estadísticas del cliente
        if context.get('cliente_activo'):
            cliente = context['cliente_activo']
            context['estadisticas'] = {
                'total_transacciones': Transaccion.objects.filter(cliente=cliente).count(),
                'total_compras': Transaccion.objects.filter(cliente=cliente, tipo_operacion='compra').count(),
                'total_ventas': Transaccion.objects.filter(cliente=cliente, tipo_operacion='venta').count(),
                'pendientes': Transaccion.objects.filter(cliente=cliente, estado='pendiente').count(),
            }
        
        # Mantener valores de filtros en el contexto
        context['filtros'] = {
            'tipo': self.request.GET.get('tipo', 'todos'),
            'estado': self.request.GET.get('estado', ''),
            'fecha_desde': self.request.GET.get('fecha_desde', ''),
            'fecha_hasta': self.request.GET.get('fecha_hasta', ''),
        }
        
        # Opciones para filtros
        context['estados_disponibles'] = Transaccion.ESTADO_CHOICES
        
        return context


@login_required
@require_permission("transacciones.view_transacciones_globales")  
def historial_admin(request):
    """
    🔐 PROTEGIDA: transacciones.view_transacciones_globales
    Vista administrativa para ver TODAS las transacciones del sistema.
    Solo accesible para usuarios con permiso de visualización global.
    """
    # Filtros base
    transacciones = Transaccion.objects.select_related(
        'cliente', 'divisa_origen', 'divisa_destino', 'procesado_por'
    ).order_by('-fecha_creacion')
    
    # Aplicar filtros
    cliente_id = request.GET.get('cliente')
    if cliente_id:
        transacciones = transacciones.filter(cliente_id=cliente_id)
    
    tipo_filtro = request.GET.get('tipo')
    if tipo_filtro in ['compra', 'venta']:
        transacciones = transacciones.filter(tipo_operacion=tipo_filtro)
    
    estado_filtro = request.GET.get('estado')
    if estado_filtro:
        transacciones = transacciones.filter(estado=estado_filtro)
    
    # Filtros de fecha
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            transacciones = transacciones.filter(fecha_creacion__gte=fecha_desde_dt)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d') + timedelta(days=1)
            transacciones = transacciones.filter(fecha_creacion__lt=fecha_hasta_dt)
        except ValueError:
            pass
    
    # Búsqueda por número de transacción o nombre de cliente
    busqueda = request.GET.get('busqueda')
    if busqueda:
        transacciones = transacciones.filter(
            Q(numero_transaccion__icontains=busqueda) |
            Q(cliente__nombre_completo__icontains=busqueda) |
            Q(cliente__cedula__icontains=busqueda)
        )
    
    # Paginación
    paginator = Paginator(transacciones, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas generales
    total_transacciones = Transaccion.objects.count()
    estadisticas = {
        'total': total_transacciones,
        'compras': Transaccion.objects.filter(tipo_operacion='compra').count(),
        'ventas': Transaccion.objects.filter(tipo_operacion='venta').count(),
        'pendientes': Transaccion.objects.filter(estado='pendiente').count(),
        'pagadas': Transaccion.objects.filter(estado='pagada').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'transacciones': page_obj,
        'clientes': Cliente.objects.filter(esta_activo=True).order_by('nombre_completo'),
        'estadisticas': estadisticas,
        'filtros': {
            'cliente': cliente_id or '',
            'tipo': tipo_filtro or '',
            'estado': estado_filtro or '',
            'fecha_desde': fecha_desde or '',
            'fecha_hasta': fecha_hasta or '',
            'busqueda': busqueda or '',
        },
        'estados_disponibles': Transaccion.ESTADO_CHOICES,
    }
    
    return render(request, 'historial_admin.html', context)


@method_decorator(require_permission("transacciones.view_transacciones_asignadas"), name="dispatch")  # ✅ SIN check_client_assignment
class DetalleTransaccionView(LoginRequiredMixin, DetailView):
    """
    🔐 PROTEGIDA: transacciones.view_transacciones_asignadas
    Vista detallada de una transacción.
    """
    model = Transaccion
    template_name = 'detalle_transaccion.html'
    context_object_name = 'transaccion'
    slug_field = 'numero_transaccion'
    slug_url_kwarg = 'numero_transaccion'

    def get_object(self, queryset=None):
        transaccion = super().get_object(queryset)
        
        # ✅ Validación adicional según rol
        if not self.request.user.is_staff:
            # Clientes solo ven sus propias transacciones
            cliente_id = self.request.session.get('cliente_id')
            if not cliente_id or str(transaccion.cliente.id) != str(cliente_id):
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("No tiene permisos para ver esta transacción.")
        elif not self.request.user.has_perm('transacciones.view_transacciones_globales'):
            # Operadores solo ven transacciones de clientes asignados
            from clientes.models import AsignacionCliente
            if not AsignacionCliente.objects.filter(
                operador=self.request.user,
                cliente=transaccion.cliente,
                activa=True
            ).exists():
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("No tiene permisos para ver esta transacción.")
        
        return transaccion

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Agregar historial
        context['historial'] = self.object.historial.select_related('modificado_por').order_by('-fecha_cambio')
        
        # Información adicional
        context['puede_cancelar'] = self.object.puede_cancelarse
        context['puede_anular'] = self.object.puede_anularse
        context['es_admin'] = self.request.user.is_staff

        # NUEVO: medio listo para renderizado y alias/flags de ayuda
        medio_raw = self.object.get_medio_pago_info()
        medio = _build_medio_display(medio_raw)

        # Adjuntar propiedades derivadas para plantillas que lean desde transaccion.*
        self.object.medio_display = medio
        self.object.medio_campos = medio.get('campos', [])
        self.object.medio_nombre = medio.get('nombre') or ''
        self.object.medio_comision = medio.get('comision') or ''
        self.object.medio_tipo = medio.get('tipo') or ''
        self.object.tiene_datos_medio = bool(self.object.medio_campos)

        # Además incluir en el contexto por compatibilidad
        context['medio'] = medio
        context['medio_pago'] = medio
        context['medio_campos'] = self.object.medio_campos
        context['tiene_datos_medio'] = self.object.tiene_datos_medio
        context['medio_datos'] = medio_raw

        return context


# ═══════════════════════════════════════════════════════════════════
# VISTAS DE EXPORTACIÓN
# ═══════════════════════════════════════════════════════════════════

@method_decorator(require_permission("transacciones.view_transacciones_asignadas"), name="dispatch")  # ✅ SIN check_client_assignment
class ExportarTransaccionesView(LoginRequiredMixin, View):
    """
    🔐 PROTEGIDA: transacciones.view_transacciones_asignadas
    Exportar transacciones del cliente activo a CSV.
    """
    
    def dispatch(self, request, *args, **kwargs):
        # ✅ Validar cliente activo AQUÍ
        cliente_id = request.session.get('cliente_id')
        if not cliente_id:
            messages.warning(request, "Selecciona un cliente para exportar transacciones")
            return redirect('clientes:seleccionar_cliente')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        import csv
        from django.http import HttpResponse
        
        cliente_id = request.session.get('cliente_id')
        cliente = get_object_or_404(Cliente, id=cliente_id, esta_activo=True)
        
        # Crear respuesta CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="transacciones_{cliente.nombre_completo}_{datetime.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Número Transacción',
            'Fecha',
            'Tipo',
            'Divisa Origen',
            'Monto Origen',
            'Divisa Destino',
            'Monto Destino',
            'Tasa Cambio',
            'Estado'
        ])
        
        transacciones = Transaccion.objects.filter(
            cliente=cliente
        ).select_related('divisa_origen', 'divisa_destino').order_by('-fecha_creacion')
        
        for t in transacciones:
            writer.writerow([
                t.numero_transaccion,
                t.fecha_creacion.strftime('%Y-%m-%d %H:%M'),
                t.get_tipo_operacion_display(),
                t.divisa_origen.code,
                t.monto_origen,
                t.divisa_destino.code,
                t.monto_destino,
                t.tasa_de_cambio_aplicada,
                t.get_estado_display()
            ])
        
        return response


# ═══════════════════════════════════════════════════════════════════
# VISTAS DE GESTIÓN (CAMBIO DE ESTADO, CANCELACIÓN)
# ═══════════════════════════════════════════════════════════════════

@login_required
@require_permission("transacciones.manage_estados_transacciones")  # ✅ SIN check_client_assignment (correcto para admin)
def cambiar_estado_transaccion(request, numero_transaccion):
    """
    🔐 PROTEGIDA: transacciones.manage_estados_transacciones
    Vista para cambiar el estado de una transacción.
    Solo accesible para usuarios con permiso de gestión de estados (admin/operador).
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    transaccion = get_object_or_404(Transaccion, numero_transaccion=numero_transaccion)
    nuevo_estado = request.POST.get('nuevo_estado')
    observaciones = request.POST.get('observaciones', '')
    
    if nuevo_estado not in dict(Transaccion.ESTADO_CHOICES):
        return JsonResponse({'success': False, 'error': 'Estado no válido'})
    
    try:
        transaccion.cambiar_estado(
            nuevo_estado=nuevo_estado,
            observacion=observaciones,
            usuario=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Estado cambiado a {transaccion.get_estado_display()}',
            'nuevo_estado': nuevo_estado,
            'nuevo_estado_display': transaccion.get_estado_display()
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_permission("transacciones.cancel_propias_transacciones")  # ✅ SIN check_client_assignment
def cancelar_transaccion(request, numero_transaccion):
    """
    🔐 PROTEGIDA: transacciones.cancel_propias_transacciones
    Vista para que el cliente cancele su transacción pendiente.
    """
    # ✅ Validar cliente activo AQUÍ
    cliente_id = request.session.get('cliente_id')
    if not cliente_id:
        messages.error(request, "Debes tener un cliente seleccionado para cancelar transacciones")
        return redirect('clientes:seleccionar_cliente')
    
    transaccion = get_object_or_404(Transaccion, numero_transaccion=numero_transaccion)
    
    # ✅ Validación adicional: el cliente solo cancela sus propias transacciones
    if not request.user.is_staff:
        if str(transaccion.cliente.id) != str(cliente_id):
            messages.error(request, "No tiene permisos para modificar esta transacción.")
            return redirect('transacciones:historial_cliente')
    
    if not transaccion.puede_cancelarse:
        messages.error(request, "Esta transacción no puede cancelarse.")
        return redirect('transacciones:detalle', numero_transaccion=numero_transaccion)
    
    if request.method == 'POST':
        try:
            # Obtener razón de cancelación si se proporcionó
            razon_cancelacion = request.POST.get('razon_cancelacion', '').strip()
            
            # Construir observación
            observacion_base = 'Transacción cancelada por el cliente'
            if razon_cancelacion:
                observacion_completa = f'{observacion_base}. Razón: {razon_cancelacion}'
            else:
                observacion_completa = observacion_base
            
            transaccion.cambiar_estado(
                nuevo_estado='cancelada',
                observacion=observacion_completa,
                usuario=request.user
            )
            messages.success(
                request, 
                f'Transacción {numero_transaccion} cancelada exitosamente.'
            )
            
            return redirect('transacciones:historial_cliente')
            
        except Exception as e:
            logger.error(f'Error al cancelar transacción {numero_transaccion}: {e}')
            messages.error(request, f'Error al cancelar la transacción: {str(e)}')
            return redirect('transacciones:detalle', numero_transaccion=numero_transaccion)
    
    # GET request - mostrar página de confirmación
    return render(request, 'confirmar_cancelacion.html', {
        'transaccion': transaccion
    })