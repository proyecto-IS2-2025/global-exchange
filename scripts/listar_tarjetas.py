import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from banco.models import TarjetaDebito, Cuenta

print("\n=== TARJETAS DE DÉBITO ===\n")

tarjetas = TarjetaDebito.objects.filter(cuenta__isnull=False).select_related('cuenta', 'entidad', 'usuario')

for td in tarjetas:
    print(f"ID {td.id}")
    print(f"  Número: ****{td.numero[-4:]}")
    print(f"  Cuenta: {td.cuenta.numero_cuenta}")
    print(f"  Saldo cuenta: ₲{td.cuenta.saldo:,.0f}")
    print(f"  Usuario: {td.usuario.email if td.usuario else 'N/A'}")
    print(f"  Entidad: {td.entidad.nombre}")
    print()

# Verificar cuenta empresa
print("\n=== CUENTA EMPRESA ===")
cuenta_emp = Cuenta.objects.get(numero_cuenta='000111222')
print(f"Número: {cuenta_emp.numero_cuenta}")
print(f"Saldo: ₲{cuenta_emp.saldo:,.0f}")
print()
