# billetera/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import (
    UsuarioBilletera, Billetera, RecargaBilletera, 
    TransferenciaBilletera, MovimientoBilletera
)
from .forms import (
    RegistroUsuarioForm, CrearBilleteraForm, LoginForm,
    RecargaBilleteraForm, TransferirFondosForm
)
from banco.models import EntidadBancaria


def registro(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            messages.success(request, 'Usuario registrado exitosamente.')
            return redirect('billetera:login')
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'billetera/registro.html', {'form': form})


def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            numero_celular = form.cleaned_data['numero_celular']
            password = form.cleaned_data['password']
            
            try:
                usuario = UsuarioBilletera.objects.get(
                    numero_celular=numero_celular,
                    password=password
                )
                request.session['usuario_billetera_id'] = usuario.id
                return redirect('billetera:dashboard')
            except UsuarioBilletera.DoesNotExist:
                messages.error(request, 'Credenciales inválidas.')
    else:
        form = LoginForm()
    
    return render(request, 'billetera/login.html', {'form': form})


def logout(request):
    request.session.pop('usuario_billetera_id', None)
    messages.info(request, 'Sesión cerrada exitosamente.')
    return redirect('billetera:login')


def dashboard(request):
    usuario_id = request.session.get('usuario_billetera_id')
    if not usuario_id:
        return redirect('billetera:login')
    
    usuario = get_object_or_404(UsuarioBilletera, id=usuario_id)
    
    try:
        billetera = usuario.billetera
        movimientos = billetera.movimientos.all()[:10]  # Últimos 10 movimientos
    except Billetera.DoesNotExist:
        billetera = None
        movimientos = []
    
    context = {
        'usuario': usuario,
        'billetera': billetera,
        'movimientos': movimientos,
        'entidades': EntidadBancaria.objects.all()
    }
    
    return render(request, 'billetera/dashboard.html', context)


def crear_billetera(request):
    usuario_id = request.session.get('usuario_billetera_id')
    if not usuario_id:
        return redirect('billetera:login')
    
    usuario = get_object_or_404(UsuarioBilletera, id=usuario_id)
    
    # Verificar si ya tiene billetera
    if hasattr(usuario, 'billetera'):
        messages.warning(request, 'Ya tienes una billetera creada.')
        return redirect('billetera:dashboard')
    
    if request.method == 'POST':
        form = CrearBilleteraForm(request.POST)
        if form.is_valid():
            billetera = form.save(commit=False)
            billetera.usuario = usuario
            billetera.save()
            messages.success(request, 'Billetera creada exitosamente.')
            return redirect('billetera:dashboard')
    else:
        form = CrearBilleteraForm()
    
    return render(request, 'billetera/crear_billetera.html', {'form': form})


def recargar(request):
    usuario_id = request.session.get('usuario_billetera_id')
    if not usuario_id:
        return redirect('billetera:login')
    
    usuario = get_object_or_404(UsuarioBilletera, id=usuario_id)
    
    try:
        billetera = usuario.billetera
    except Billetera.DoesNotExist:
        messages.error(request, 'Debes crear una billetera primero.')
        return redirect('billetera:crear_billetera')
    
    if request.method == 'POST':
        form = RecargaBilleteraForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    recarga = RecargaBilletera.objects.create(
                        billetera=billetera,
                        tarjeta_debito=form.cleaned_data['tarjeta_debito'],
                        monto=form.cleaned_data['monto']
                    )
                    messages.success(request, f'Recarga exitosa. Comprobante: {recarga.comprobante}')
                    return redirect('billetera:dashboard')
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = RecargaBilleteraForm()
    
    return render(request, 'billetera/recargar.html', {'form': form, 'billetera': billetera})


def transferir(request):
    usuario_id = request.session.get('usuario_billetera_id')
    if not usuario_id:
        return redirect('billetera:login')
    
    usuario = get_object_or_404(UsuarioBilletera, id=usuario_id)
    
    try:
        billetera = usuario.billetera
    except Billetera.DoesNotExist:
        messages.error(request, 'Debes crear una billetera primero.')
        return redirect('billetera:crear_billetera')
    
    if request.method == 'POST':
        form = TransferirFondosForm(request.POST, billetera_origen=billetera)
        if form.is_valid():
            try:
                with transaction.atomic():
                    transferencia = TransferenciaBilletera.objects.create(
                        billetera_origen=billetera,
                        billetera_destino=form.cleaned_data['billetera_destino'],
                        monto=form.cleaned_data['monto']
                    )
                    messages.success(request, f'Transferencia exitosa. Comprobante: {transferencia.comprobante}')
                    return redirect('billetera:dashboard')
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = TransferirFondosForm(billetera_origen=billetera)
    
    return render(request, 'billetera/transferir.html', {'form': form, 'billetera': billetera})


def historial(request):
    usuario_id = request.session.get('usuario_billetera_id')
    if not usuario_id:
        return redirect('billetera:login')
    
    usuario = get_object_or_404(UsuarioBilletera, id=usuario_id)
    
    try:
        billetera = usuario.billetera
        movimientos = billetera.movimientos.all()
    except Billetera.DoesNotExist:
        billetera = None
        movimientos = []
    
    context = {
        'usuario': usuario,
        'billetera': billetera,
        'movimientos': movimientos
    }
    
    return render(request, 'billetera/historial.html', context)


def comprobante_ajax(request):
    """Vista AJAX para obtener detalles de un comprobante"""
    comprobante_uuid = request.GET.get('comprobante')
    
    try:
        # Buscar en movimientos
        movimiento = MovimientoBilletera.objects.get(comprobante=comprobante_uuid)
        data = {
            'tipo': movimiento.get_tipo_display(),
            'monto': str(movimiento.monto),
            'fecha': movimiento.fecha.strftime('%d/%m/%Y %H:%M'),
            'descripcion': movimiento.descripcion,
            'comprobante': str(movimiento.comprobante)
        }
        return JsonResponse(data)
    except MovimientoBilletera.DoesNotExist:
        return JsonResponse({'error': 'Comprobante no encontrado'}, status=404)