from django.contrib.auth.models import Permission

# Ver todos los permisos personalizados
perms = Permission.objects.filter(
    content_type__app_label__in=['clientes', 'divisas', 'transacciones', 'medios_pago', 'users']
).order_by('content_type__app_label', 'codename')

for p in perms:
    print(f"{p.content_type.app_label:20} | {p.codename:40} | {p.name}")