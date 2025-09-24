# billetera/views.py - FUNCIÓN CORREGIDA CON MEJOR MANEJO DE ERRORES
from django.shortcuts import render, redirect
from django.contrib import messages
from decimal import Decimal
import requests
import json
from .models import BilleteraUser, Billetera, TransferenciaBilleteraABanco
from banco.models import Cuenta, EntidadBancaria, BancoUser
from .forms import BilleteraTransferenciaForm, BilleteraABancoForm, RecargaForm

# --------- FUNCIÓN DE USUARIO AUTENTICADO ---------
def get_logged_user(request):
    user_id = request.session.get("billetera_user_id")
    if user_id:
        try:
            return BilleteraUser.objects.get(id=user_id)
        except BilleteraUser.DoesNotExist:
            return None
    return None

# --------- LOGIN --------
def login_view(request):
    if request.method == "POST":
        numero_telefono = request.POST.get("numero_telefono")
        password = request.POST.get("password")

        try:
            user = BilleteraUser.objects.get(numero_telefono=numero_telefono)
            if user.password == password:
                request.session["billetera_user_id"] = user.id
                return redirect("billetera:billetera")
            else:
                error = "Contraseña incorrecta"
        except BilleteraUser.DoesNotExist:
            error = "Usuario no encontrado"

        return render(request, "billetera/login.html", {"error": error})
    return render(request, "billetera/login.html")

# --------- LOGOUT ---------
def logout_view(request):
    request.session.flush()
    return redirect("billetera:login")

# --------- VISTA PRINCIPAL BILLETERA (CORREGIDA CON MEJOR MANEJO DE ERRORES) --------
def billetera_view(request):
    user = get_logged_user(request)
    if not user:
        return redirect("billetera:login")

    billetera = user.billetera
    error = None

    try:
        banco_user = BancoUser.objects.get(id=user.id) 
    except BancoUser.DoesNotExist:
        banco_user = None
    
    form_recarga = RecargaForm()
    if banco_user:
        form_recarga.fields['cuenta_origen'].queryset = banco_user.cuentas.all()

    if request.method == "POST":
        if 'recargar_form' in request.POST:
            form_recarga = RecargaForm(request.POST)
            if banco_user:
                form_recarga.fields['cuenta_origen'].queryset = banco_user.cuentas.all()

            if form_recarga.is_valid():
                cuenta_origen = form_recarga.cleaned_data['cuenta_origen']
                monto = form_recarga.cleaned_data['monto']

                try:
                    # Llamada a la API del banco con mejor manejo de errores
                    api_url = "http://127.0.0.1:8000/banco/api/recargar/"
                    payload = {
                        'cuenta_id': cuenta_origen.id,
                        'monto': str(monto),
                        'billetera_user_id': user.id
                    }
                    
                    print(f"DEBUG: Enviando payload a API: {payload}")  # Para debugging
                    
                    response = requests.post(
                        api_url, 
                        json=payload, 
                        timeout=30,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    print(f"DEBUG: Status code: {response.status_code}")  # Para debugging
                    print(f"DEBUG: Response text: {response.text}")  # Para debugging
                    
                    # Verificar si la respuesta está vacía
                    if not response.text.strip():
                        messages.error(request, "El servidor del banco devolvió una respuesta vacía.")
                        return render(request, "billetera/billetera.html", {"billetera": billetera, "form_recarga": form_recarga})
                    
                    # Intentar parsear JSON
                    try:
                        response_data = response.json()
                    except json.JSONDecodeError as e:
                        messages.error(request, f"Respuesta inválida del banco. Error: {str(e)}")
                        return render(request, "billetera/billetera.html", {"billetera": billetera, "form_recarga": form_recarga})
                    
                    if response.status_code == 200:
                        # Actualizar saldo de billetera localmente
                        billetera.saldo += Decimal(str(monto))
                        billetera.save()
                        messages.success(request, response_data.get('message', "Recarga exitosa."))
                        return redirect("billetera:billetera")
                    else:
                        error_message = response_data.get("error", f"Error del banco (código {response.status_code})")
                        messages.error(request, error_message)

                except requests.exceptions.ConnectionError:
                    messages.error(request, "No se puede conectar con el servidor del banco. Verifique que esté funcionando.")
                except requests.exceptions.Timeout:
                    messages.error(request, "Tiempo de espera agotado al conectar con el banco.")
                except requests.exceptions.RequestException as e:
                    messages.error(request, f"Error de conexión con el banco: {str(e)}")
                except Exception as e:
                    messages.error(request, f"Error inesperado: {str(e)}")
    
    return render(
        request,
        "billetera/billetera.html",
        {"billetera": billetera, "form_recarga": form_recarga}
    )

# --------- VISTA DE TRANSFERENCIA A OTRA BILLETERA --------
def transferir_billetera_view(request):
    user = get_logged_user(request)
    if not user:
        return redirect("billetera:login")
        
    billetera_origen = user.billetera
    error = None
    
    if request.method == "POST":
        form = BilleteraTransferenciaForm(request.POST)
        if form.is_valid():
            destinatario_telefono = form.cleaned_data['destinatario_telefono']
            monto = form.cleaned_data['monto']
            
            try:
                billetera_destino = Billetera.objects.get(usuario__numero_telefono=destinatario_telefono)
                monto_decimal = Decimal(str(monto))
                
                if billetera_origen.saldo >= monto_decimal:
                    billetera_origen.saldo -= monto_decimal
                    billetera_destino.saldo += monto_decimal
                    billetera_origen.save()
                    billetera_destino.save()
                    messages.success(request, f"Se han transferido ₲ {monto} a {destinatario_telefono}.")
                    return redirect("billetera:billetera")
                else:
                    error = "Saldo insuficiente en tu billetera."
            except Billetera.DoesNotExist:
                error = "Usuario no encontrado."
    else:
        form = BilleteraTransferenciaForm()
    
    return render(
        request,
        "billetera/transferir_billetera.html",
        {"billetera": billetera_origen, "form": form, "error": error}
    )

# --------- VISTA DE TRANSFERENCIA A CUENTA BANCARIA --------
def transferir_a_banco_view(request):
    user = get_logged_user(request)
    if not user:
        return redirect("billetera:login")
        
    billetera_origen = user.billetera
    error = None
    
    if request.method == "POST":
        form = BilleteraABancoForm(request.POST)
        if form.is_valid():
            entidad_destino = form.cleaned_data['entidad_destino']
            numero_cuenta_destino = form.cleaned_data['numero_cuenta_destino']
            monto = form.cleaned_data['monto']
            
            try:
                cuenta_destino = Cuenta.objects.get(
                    numero_cuenta=numero_cuenta_destino,
                    entidad=entidad_destino
                )
                monto_decimal = Decimal(str(monto))
                
                if billetera_origen.saldo >= monto_decimal:
                    billetera_origen.saldo -= monto_decimal
                    cuenta_destino.saldo += monto_decimal
                    billetera_origen.save()
                    cuenta_destino.save()
                    
                    TransferenciaBilleteraABanco.objects.create(
                        billetera_origen=billetera_origen,
                        cuenta_destino=cuenta_destino,
                        monto=monto_decimal
                    )
                    
                    messages.success(request, f"Se han transferido ₲ {monto} a la cuenta bancaria {numero_cuenta_destino}.")
                    return redirect("billetera:billetera")
                else:
                    error = "Saldo insuficiente en tu billetera."
            except Cuenta.DoesNotExist:
                error = "La cuenta de destino no existe en la entidad seleccionada."
    else:
        form = BilleteraABancoForm()
    
    return render(
        request,
        "billetera/transferir_a_banco.html",
        {"billetera": billetera_origen, "form": form, "error": error}
    )