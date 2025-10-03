# divisas/migrations/0004_crear_moneda_base_pyg.py
from django.db import migrations

def crear_pyg(apps, schema_editor):
    """
    Crea o actualiza la moneda base PYG.
    """
    Divisa = apps.get_model('divisas', 'Divisa')
    
    try:
        pyg = Divisa.objects.get(code='PYG')
        pyg.nombre = 'Guaraní'
        pyg.simbolo = '₲'
        pyg.is_active = True
        pyg.decimales = 0
        pyg.es_moneda_base = True
        pyg.save()
    except Divisa.DoesNotExist:
        Divisa.objects.create(
            code='PYG',
            nombre='Guaraní',
            simbolo='₲',
            is_active=True,
            decimales=0,
            es_moneda_base=True,
        )

def revertir_pyg(apps, schema_editor):
    """Eliminar PYG (solo para desarrollo)"""
    Divisa = apps.get_model('divisas', 'Divisa')
    Divisa.objects.filter(code='PYG').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('divisas', '0003_divisa_es_moneda_base_and_more'),  # ⭐ Cambiar aquí
    ]

    operations = [
        migrations.RunPython(crear_pyg, revertir_pyg),
    ]