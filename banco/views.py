# banco/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import BancoUser, Cuenta, Transferencia, PagoTarjeta
from billetera.models import TransferenciaBilleteraABanco  # ✅ Importación del modelo de la otra app
from .forms import TransferenciaForm
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
import json
import logging

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


# --------- VISTA PARA TRANSFERENCIAS Y PAGOS (MEJORADA) ---------
def transferir(request):
    user = get_logged_user(request)
    if not user:
        return redirect("banco:login")
        
    error = None
    
    if request.method == "POST":
        form = TransferenciaForm(request.POST)
        if form.is_valid():
            tipo_pago = form.cleaned_data['tipo_pago']
            entidad_destino = form.cleaned_data['entidad_destino']
            numero_cuenta_destino = form.cleaned_data['numero_cuenta_destino']
            monto = form.cleaned_data['monto']
            
            try:
                with transaction.atomic():
                    # Lógica para PAGO CON DÉBITO O CRÉDITO
                    if tipo_pago in ['PAGO_DEBITO', 'PAGO_CREDITO']:
                        cuenta_origen = user.cuentas.get(tipo_cuenta='DEBITO' if tipo_pago == 'PAGO_DEBITO' else 'CREDITO')
                        
                        if tipo_pago == 'PAGO_DEBITO':
                            if cuenta_origen.saldo < monto:
                                error = "Saldo insuficiente en la cuenta de débito."
                                raise ValueError("Saldo insuficiente")

                        # Se genera el PagoTarjeta
                        PagoTarjeta.objects.create(
                            cuenta=cuenta_origen,
                            monto=monto,
                            tipo=tipo_pago.replace('PAGO_', ''), # 'DEBITO' o 'CREDITO'
                            entidad_destino=entidad_destino.nombre,
                            numero_cuenta_destino=numero_cuenta_destino
                        )
                        
                        # Actualizar saldo
                        if tipo_pago == 'PAGO_DEBITO':
                            cuenta_origen.saldo -= monto
                        elif tipo_pago == 'PAGO_CREDITO':
                            # En el caso de crédito, el saldo es un valor negativo
                            cuenta_origen.saldo -= monto
                            
                        cuenta_origen.save()
                        messages.success(request, f"Pago con {tipo_pago.replace('PAGO_', '').lower()} de ₲ {monto} exitoso.")
                    
                    # Lógica para TRANSFERENCIA BANCARIA
                    elif tipo_pago == 'TRANSFERENCIA':
                        cuenta_origen = user.cuentas.get(tipo_cuenta='DEBITO')
                        if cuenta_origen.saldo < monto:
                            error = "Saldo insuficiente en la cuenta de débito para la transferencia."
                            raise ValueError("Saldo insuficiente")

                        # Buscar cuenta de destino
                        try:
                            cuenta_destino = Cuenta.objects.get(
                                numero_cuenta=numero_cuenta_destino,
                                entidad=entidad_destino
                            )
                        except Cuenta.DoesNotExist:
                            error = "La cuenta de destino no existe en la entidad seleccionada."
                            raise ValueError("Cuenta destino no encontrada")
                        
                        # Actualizar saldos
                        cuenta_origen.saldo -= monto
                        cuenta_destino.saldo += monto
                        
                        # Guardar cambios
                        cuenta_origen.save()
                        cuenta_destino.save()
                        
                        # Registrar transferencia
                        Transferencia.objects.create(
                            cuenta_origen=cuenta_origen,
                            cuenta_destino=cuenta_destino,
                            monto=monto
                        )
                        messages.success(request, f"Transferencia de ₲ {monto} a {numero_cuenta_destino} exitosa.")

                    return redirect("banco:dashboard")
            
            except (Cuenta.DoesNotExist, ValueError) as e:
                # El error ya está en la variable 'error'
                pass
            except Exception as e:
                error = "Ocurrió un error inesperado al procesar la solicitud."
                logger.error(f"Error inesperado en transferir: {e}")
                
    else:
        form = TransferenciaForm()
        
    # Obtener el saldo de la cuenta de débito para mostrarlo en el formulario
    try:
        cuenta_debito = user.cuentas.get(tipo_cuenta="DEBITO")
        saldo_debito = cuenta_debito.saldo
    except (BancoUser.DoesNotExist, Cuenta.DoesNotExist):
        saldo_debito = None

    return render(
        request,
        "banco/transferir.html",
        {"form": form, "error": error, "saldo_debito": saldo_debito}
    )

# --------- HISTORIAL DE MOVIMIENTOS (CORREGIDO) ---------
def historial(request):
    user = get_logged_user(request)
    if not user:
        return redirect("banco:login")

    cuentas_usuario = user.cuentas.all()

    # Obtener todas las transferencias enviadas y recibidas
    transferencias_enviadas = Transferencia.objects.filter(cuenta_origen__in=cuentas_usuario)
    transferencias_recibidas = Transferencia.objects.filter(cuenta_destino__in=cuentas_usuario)
    
    # Obtener pagos con tarjeta
    pagos_tarjeta = PagoTarjeta.objects.filter(cuenta__in=cuentas_usuario)
    
    # Obtener transferencias recibidas desde Billetera
    transferencias_billetera_recibidas = TransferenciaBilleteraABanco.objects.filter(cuenta_destino__in=cuentas_usuario)

    # Combinar todos los movimientos y ordenarlos por fecha
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
                cuenta.saldo += monto
            
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