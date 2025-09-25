from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import BancoUser, Cuenta, Transferencia, PagoTarjeta
from billetera.models import TransferenciaBilleteraABanco  # ✅ Importación necesaria
from .forms import TransferenciaForm
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
import json
import logging
import requests  # ✅ Asegúrate de tener esta importación para las llamadas a la API

logger = logging.getLogger(__name__)

# --------- FUNCIÓN DE USUARIO AUTENTICADO ---------
def get_logged_user(request):
    user_id = request.session.get("user_id")
    if user_id:
        try:
            return BancoUser.objects.get(id=user_id)
        except BancoUser.DoesNotExist:
            return None
    return None

# --------- LOGIN ---------
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user = BancoUser.objects.get(email=email)
            if user.password == password:
                request.session["user_id"] = user.id
                return redirect("banco:dashboard")
            else:
                error = "Contraseña incorrecta"
        except BancoUser.DoesNotExist:
            error = "Usuario no encontrado"

        return render(request, "banco/login.html", {"error": error})
    return render(request, "banco/login.html")

# --------- LOGOUT ---------
def logout_view(request):
    request.session.flush()
    return redirect("banco:login")

# --------- DASHBOARD ---------
def dashboard(request):
    user = get_logged_user(request)
    if not user:
        return redirect("banco:login")
    
    cuenta_debito = user.cuentas.filter(tipo_cuenta="DEBITO").first()
    cuenta_credito = user.cuentas.filter(tipo_cuenta="CREDITO").first()
    
    context = {
        "user": user,
        "cuenta_debito": cuenta_debito,
        "cuenta_credito": cuenta_credito,
        "entidad": user.entidad,
    }
    
    return render(request, "banco/dashboard.html", context)


# --------- VISTA PARA TRANSFERENCIAS Y PAGOS (CORREGIDA) ---------
def transferir(request):
    user = get_logged_user(request)
    if not user:
        return redirect("banco:login")

    form = TransferenciaForm(request.POST or None)
    error = None

    if request.method == "POST":
        if form.is_valid():
            tipo_pago = form.cleaned_data['tipo_pago']
            monto = form.cleaned_data['monto']

            try:
                with transaction.atomic():
                    if tipo_pago == 'TRANSFERENCIA':
                        entidad_destino = form.cleaned_data['entidad_destino']
                        numero_cuenta_destino = form.cleaned_data['numero_cuenta_destino']

                        cuenta_origen = user.cuentas.get(tipo_cuenta='DEBITO')
                        cuenta_destino = Cuenta.objects.get(entidad=entidad_destino, numero_cuenta=numero_cuenta_destino)
                        
                        if cuenta_origen.saldo < monto:
                            error = "Saldo insuficiente en la cuenta de débito."
                        else:
                            cuenta_origen.saldo -= monto
                            cuenta_destino.saldo += monto
                            cuenta_origen.save()
                            cuenta_destino.save()
                            Transferencia.objects.create(cuenta_origen=cuenta_origen, cuenta_destino=cuenta_destino, monto=monto)
                            messages.success(request, f"Transferencia de ₲{monto} realizada con éxito.")
                            return redirect("banco:dashboard")

                    elif tipo_pago in ['PAGO_DEBITO', 'PAGO_CREDITO']:
                        # --- LÓGICA AGREGADA PARA PAGOS CON TARJETA ---
                        if tipo_pago == 'PAGO_DEBITO':
                            cuenta = user.cuentas.get(tipo_cuenta='DEBITO')
                            if cuenta.saldo < monto:
                                error = "Saldo insuficiente en la cuenta de débito."
                            else:
                                cuenta.saldo -= monto
                                cuenta.save()
                                PagoTarjeta.objects.create(cuenta=cuenta, tipo='DEBITO', monto=monto)
                                messages.success(request, f"Pago con tarjeta de débito de ₲{monto} realizado con éxito.")
                                return redirect("banco:dashboard")
                        
                        elif tipo_pago == 'PAGO_CREDITO':
                            cuenta = user.cuentas.get(tipo_cuenta='CREDITO')
                            # Lógica para manejar el límite de crédito
                            limite_credito = Decimal('2000000') # Ejemplo: 2,000,000
                            nuevo_saldo = cuenta.saldo - monto
                            if nuevo_saldo < -limite_credito:
                                error = "Límite de crédito excedido."
                            else:
                                cuenta.saldo = nuevo_saldo
                                cuenta.save()
                                PagoTarjeta.objects.create(cuenta=cuenta, tipo='CREDITO', monto=monto)
                                messages.success(request, f"Pago con tarjeta de crédito de ₲{monto} realizado con éxito.")
                                return redirect("banco:dashboard")
                        # ---------------------------------------------
            except Cuenta.DoesNotExist:
                error = "La cuenta de destino no existe."
            except Exception as e:
                error = f"Ocurrió un error: {e}"

    context = {
        'entidad': user.entidad,
        'user': user,
        'form': form,
        'error': error,
    }
    return render(request, "banco/transferir.html", context)



# --------- HISTORIAL DE MOVIMIENTOS (CORREGIDO) ---------
def historial(request):
    user = get_logged_user(request)
    if not user:
        return redirect("banco:login")

    cuentas_usuario = user.cuentas.all()

    transferencias_enviadas = Transferencia.objects.filter(cuenta_origen__in=cuentas_usuario)
    transferencias_recibidas = Transferencia.objects.filter(cuenta_destino__in=cuentas_usuario)
    pagos_tarjeta = PagoTarjeta.objects.filter(cuenta__in=cuentas_usuario)
    transferencias_billetera_recibidas = TransferenciaBilleteraABanco.objects.filter(cuenta_destino__in=cuentas_usuario)

    todos_movimientos = sorted(
        list(transferencias_enviadas) + list(transferencias_recibidas) + list(pagos_tarjeta) + list(transferencias_billetera_recibidas),
        key=lambda x: x.fecha,
        reverse=True
    )
    
    context = {
        "movimientos": todos_movimientos,
        "user": user,
    }
    return render(request, "banco/historial.html", context)


# --------- VISTA API DE RECARGA DE BILLETERA (MEJORADA) ---------
@csrf_exempt
@require_http_methods(["POST"])
def api_recargar(request):
    from billetera.models import BilleteraUser, Billetera # Importación local
    
    try:
        data = json.loads(request.body)
        cuenta_id = data.get("cuenta_id")
        monto = Decimal(data.get("monto", "0"))
        billetera_user_id = data.get("billetera_user_id")

        if not all([cuenta_id, monto, billetera_user_id]):
            return JsonResponse({"error": "Parámetros incompletos."}, status=400)
        
        if monto <= 0:
            return JsonResponse({"error": "El monto debe ser mayor a cero."}, status=400)

        with transaction.atomic():
            cuenta = Cuenta.objects.select_for_update().get(id=cuenta_id)
            billetera_user = BilleteraUser.objects.select_for_update().get(id=billetera_user_id)
            billetera = billetera_user.billetera
            
            if cuenta.tipo_cuenta == 'DEBITO':
                if cuenta.saldo < monto:
                    return JsonResponse({"error": "Saldo insuficiente en la cuenta de débito."}, status=400)
                cuenta.saldo -= monto
            else: # CREDITO
                limite_credito = Decimal('200000')
                saldo_usado = abs(cuenta.saldo) + monto
                if saldo_usado > limite_credito:
                    return JsonResponse({"error": "Límite de crédito excedido."}, status=400)
                cuenta.saldo -= monto # Usamos -= para que el saldo se vuelva más negativo
            
            billetera.saldo += monto
            cuenta.save()
            billetera.save()
            
            return JsonResponse({
                "status": "ok", 
                "message": f"Recarga de ₲{monto} exitosa.",
                "nuevo_saldo_billetera": str(billetera.saldo)
            }, status=200)

    except Cuenta.DoesNotExist:
        return JsonResponse({"error": "La cuenta de origen no existe."}, status=404)
    except BilleteraUser.DoesNotExist:
        return JsonResponse({"error": "El usuario de billetera no existe."}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Formato JSON inválido."}, status=400)
    except Exception as e:
        logger.error(f"Error inesperado en api_recargar: {e}")
        return JsonResponse({"error": f"Error inesperado: {str(e)}"}, status=500)