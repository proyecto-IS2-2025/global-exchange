from django.utils import timezone
from django.db.models import Sum
from clientes.models import LimiteDiario, LimiteMensual

def verificar_limites(cliente, monto):
    hoy = timezone.localdate()

    # --- Límite diario ---
    limite_diario = LimiteDiario.objects.filter(fecha=hoy).first()
    if limite_diario:
        total_hoy = cliente.transacciones.filter(
            fecha_creacion__gte=limite_diario.inicio_vigencia
        ).aggregate(total=Sum("monto_destino"))["total"] or 0
        print(">>> [Límite diario]")
        print(f"    Limite: {limite_diario.monto}")
        print(f"    Monto previo: {total_hoy}")
        print(f"    Monto nuevo: {monto}")
        print(f"    Total si apruebo: {total_hoy + monto}")

        if total_hoy + monto > limite_diario.monto:
            return False, f"Supera el límite diario de {limite_diario.monto}"

    # --- Límite mensual ---
    limite_mensual = LimiteMensual.objects.filter(
        mes__year=hoy.year,
        mes__month=hoy.month
    ).first()

    if limite_mensual:
        total_mes = cliente.transacciones.filter(
            fecha_creacion__gte=limite_mensual.inicio_vigencia  # usar inicio real
        ).aggregate(total=Sum("monto_destino"))["total"] or 0
        print(">>> [Límite mensual]")
        print(f"    Limite: {limite_mensual.monto}")
        print(f"    Monto previo: {total_mes}")
        print(f"    Monto nuevo: {monto}")
        print(f"    Total si apruebo: {total_mes + monto}")

        if total_mes + monto > limite_mensual.monto:
            return False, f"Supera el límite mensual de {limite_mensual.monto}"

    return True, "Dentro de los límites"
