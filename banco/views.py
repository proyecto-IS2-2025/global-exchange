from django.shortcuts import render, redirect
from .models import BancoUser, Cuenta, Transferencia
from .forms import TransferenciaForm

# --------- FUNCIÓN DE USUARIO AUTENTICADO ---------
def get_logged_user(request):
    user_id = request.session.get("user_id")
    return BancoUser.objects.get(id=user_id) if user_id else None

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
    cuenta = user.cuenta
    return render(request, "banco/dashboard.html", {"cuenta": cuenta})


# --------- TRANSFERIR ---------
def transferir(request):
    user = get_logged_user(request)
    if not user:
        return redirect("banco:login")
    cuenta_emisor = user.cuenta
    error = None

    if request.method == "POST":
        form = TransferenciaForm(request.POST)
        if form.is_valid():
            numero = form.cleaned_data["numero_cuenta_destino"]
            monto = form.cleaned_data["monto"]

            try:
                cuenta_destino = Cuenta.objects.get(numero_cuenta=numero)
                if cuenta_destino == cuenta_emisor:
                    error = "No puedes transferirte a tu propia cuenta."
                elif cuenta_emisor.saldo >= monto:
                    transferencia = Transferencia.objects.create(
                        cuenta_origen=cuenta_emisor,
                        cuenta_destino=cuenta_destino,
                        monto=monto
                    )
                    cuenta_emisor.saldo -= monto
                    cuenta_destino.saldo += monto
                    cuenta_emisor.save()
                    cuenta_destino.save()
                    return redirect("banco:dashboard")
                else:
                    error = "Saldo insuficiente"
            except Cuenta.DoesNotExist:
                error = "La cuenta destino no existe."
    else:
        form = TransferenciaForm()

    return render(request, "banco/transferir.html", {"form": form, "error": error})



# --------- HISTORIAL ---------
def historial(request):
    user = get_logged_user(request)
    if not user:
        return redirect("banco:login")
    cuenta = user.cuenta
    enviadas = cuenta.transferencias_enviadas.all()
    recibidas = cuenta.transferencias_recibidas.all()
    return render(request, "banco/historial.html", {
        "enviadas": enviadas,
        "recibidas": recibidas
    })
