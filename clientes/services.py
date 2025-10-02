# clientes/services.py

from django.utils import timezone
from django.db.models import Sum
from clientes.models import LimiteDiario, LimiteMensual
from datetime import datetime, time # <<-- IMPORTAR datetime y time

def verificar_limites(cliente, monto, transaccion_a_excluir=None):
    hoy = timezone.localdate()

    # Base para el filtro de transacciones
    base_qs = cliente.transacciones.all()
    
    # 1. Excluir la transacción que se está editando, si existe
    if transaccion_a_excluir:
        base_qs = base_qs.exclude(pk=transaccion_a_excluir.pk)
    
    # --- Límite diario ---
    # Nota: Tu modelo LimiteDiario tiene un campo `fecha` (DateField)
    limite_diario = LimiteDiario.objects.filter(fecha=hoy).first()
    if limite_diario:
        
        # --------------------------------------------------------------------------
        # CAMBIO CLAVE DIARIO: Filtrar desde el inicio del día del registro `fecha`.
        # Esto ignora el `inicio_vigencia` y el momento de la edición.
        # --------------------------------------------------------------------------
        # Combina la fecha (date) con la hora mínima (time.min) y hazlo aware (zona horaria)
        inicio_del_dia = timezone.make_aware(datetime.combine(limite_diario.fecha, time.min)) 
        
        total_hoy = base_qs.filter(
            fecha_creacion__gte=inicio_del_dia
        ).aggregate(total=Sum("monto_destino"))["total"] or 0
        
        print(">>> [Límite diario]")
        print(f"    Limite: {limite_diario.monto}")
        print(f"    Monto previo (sin la excl.): {total_hoy}")
        print(f"    Monto nuevo: {monto}")
        print(f"    Total si apruebo: {total_hoy + monto}")

        if total_hoy + monto > limite_diario.monto:
            return False, f"Supera el límite diario de {limite_diario.monto}"

    # --- Límite mensual ---\r\n
    # Nota: Tu modelo LimiteMensual tiene un campo `mes` (DateField) con el primer día del mes.
    limite_mensual = LimiteMensual.objects.filter(
        mes__year=hoy.year,
        mes__month=hoy.month
    ).first()

    if limite_mensual:
        
        # --------------------------------------------------------------------------
        # CAMBIO CLAVE MENSUAL: Filtrar desde el inicio del mes del registro `mes`.
        # Esto ignora el `inicio_vigencia` y el momento de la edición.
        # --------------------------------------------------------------------------
        # Combina la fecha (date) con la hora mínima (time.min) y hazlo aware (zona horaria)
        inicio_del_mes = timezone.make_aware(datetime.combine(limite_mensual.mes, time.min))
        
        total_mes = base_qs.filter(
            fecha_creacion__gte=inicio_del_mes
        ).aggregate(total=Sum("monto_destino"))["total"] or 0
        
        print(">>> [Límite mensual]")
        print(f"    Limite: {limite_mensual.monto}")
        print(f"    Monto previo (sin la excl.): {total_mes}")
        print(f"    Monto nuevo: {monto}")
        print(f"    Total si apruebo: {total_mes + monto}")

        if total_mes + monto > limite_mensual.monto:
            return False, f"Supera el límite mensual de {limite_mensual.monto}"
    
    # ... (rest of the code)

    return True, None # Si todo pasa