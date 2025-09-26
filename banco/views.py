# views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import BancoUser, Cuenta, Transferencia, PagoTarjeta, TarjetaDebito, TarjetaCredito
from billetera.models import TransferenciaBilleteraABanco
from .forms import TransferenciaForm
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
import json
import logging
from django.db.models import Q

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

    cuenta = user.cuentas.first()
    tarjeta_debito = user.tarjetas_debito.first()
    tarjeta_credito = user.tarjetas_credito.first()

    context = {
        "user": user,
        "cuenta": cuenta,
        "tarjeta_debito": tarjeta_debito,
        "tarjeta_credito": tarjeta_credito,
        "entidad": user.entidad,
    }
    return render(request, "banco/dashboard.html", context)

# --------- TRANSFERENCIAS Y PAGOS ---------
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

                        cuenta_origen = user.cuentas.first()
                        cuenta_destino = Cuenta.objects.get(
                            entidad=entidad_destino, numero_cuenta=numero_cuenta_destino
                        )

                        if cuenta_origen.saldo < monto:
                            error = "Saldo insuficiente en la cuenta."
                        else:
                            cuenta_origen.saldo -= monto
                            cuenta_destino.saldo += monto
                            cuenta_origen.save()
                            cuenta_destino.save()
                            Transferencia.objects.create(
                                cuenta_origen=cuenta_origen,
                                cuenta_destino=cuenta_destino,
                                monto=monto
                            )
                            messages.success(request, f"Transferencia de ₲{monto} realizada con éxito.")
                            return redirect("banco:dashboard")

                    elif tipo_pago == 'PAGO_DEBITO':
                        tarjeta_debito = user.tarjetas_debito.first()
                        if not tarjeta_debito:
                            error = "No tenés tarjeta de débito."
                        else:
                            PagoTarjeta.objects.create(tarjeta_debito=tarjeta_debito, monto=monto)
                            messages.success(request, f"Pago con débito de ₲{monto} realizado con éxito.")
                            return redirect("banco:dashboard")

                    elif tipo_pago == 'PAGO_CREDITO':
                        tarjeta_credito = user.tarjetas_credito.first()
                        if not tarjeta_credito:
                            error = "No tenés tarjeta de crédito."
                        else:
                            PagoTarjeta.objects.create(tarjeta_credito=tarjeta_credito, monto=monto)
                            messages.success(request, f"Pago con crédito de ₲{monto} realizado con éxito.")
                            return redirect("banco:dashboard")

            except Cuenta.DoesNotExist:
                error = "La cuenta de destino no existe."
            except Exception as e:
                error = f"Ocurrió un error: {e}"
        else:
            error = "El formulario no es válido. Verifica los datos."

    context = {
        "entidad": user.entidad,
        "user": user,
        "form": form,
        "error": error,
    }
    return render(request, "banco/transferir.html", context)

# --------- HISTORIAL ---------
# views.py
def historial(request):
    user = get_logged_user(request)
    if not user:
        return redirect("banco:login")

    cuentas_usuario = user.cuentas.all()

    # Transferencias
    transferencias = Transferencia.objects.filter(
        Q(cuenta_origen__in=cuentas_usuario) |
        Q(cuenta_destino__in=cuentas_usuario)
    )

    # Pagos con tarjetas del usuario
    pagos = PagoTarjeta.objects.filter(
        Q(tarjeta_debito__usuario=user) |
        Q(tarjeta_credito__usuario=user)
    )

    # Unificar
    movimientos = sorted(
        list(transferencias) + list(pagos),
        key=lambda x: x.fecha,
        reverse=True
    )

    return render(request, "banco/historial.html", {
        "movimientos": movimientos,
        "user": user,
        "entidad": user.entidad,
    })

# --------- API DE RECARGA ---------
@csrf_exempt
@require_http_methods(["POST"])
def api_recargar(request):
    from billetera.models import BilleteraUser, Billetera

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

            if cuenta.saldo < monto:
                return JsonResponse({"error": "Saldo insuficiente en la cuenta."}, status=400)

            cuenta.saldo -= monto
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

# views.py
def pagar(request):
    user = get_logged_user(request)
    if not user:
        return redirect("banco:login")

    error = None
    if request.method == "POST":
        tipo = request.POST.get("tipo")  # "DEBITO" o "CREDITO"
        monto = Decimal(request.POST.get("monto", "0"))

        try:
            with transaction.atomic():
                if tipo == "DEBITO":
                    tarjeta_debito = user.tarjetas_debito.first()
                    if not tarjeta_debito:
                        error = "No tenés tarjeta de débito."
                    else:
                        PagoTarjeta.objects.create(tarjeta_debito=tarjeta_debito, monto=monto)
                        messages.success(request, f"Pago de ₲{monto} realizado con Débito.")
                        return redirect("banco:dashboard")

                elif tipo == "CREDITO":
                    tarjeta_credito = user.tarjetas_credito.first()
                    if not tarjeta_credito:
                        error = "No tenés tarjeta de crédito."
                    else:
                        PagoTarjeta.objects.create(tarjeta_credito=tarjeta_credito, monto=monto)
                        messages.success(request, f"Pago de ₲{monto} realizado con Crédito.")
                        return redirect("banco:dashboard")
        except Exception as e:
            error = f"Ocurrió un error: {e}"

    return render(request, "banco/pagar.html", {
        "user": user,
        "entidad": user.entidad,
        "error": error
    })
