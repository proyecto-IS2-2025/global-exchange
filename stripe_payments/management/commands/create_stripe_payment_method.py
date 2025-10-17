"""
Comando para crear el medio de pago Stripe automáticamente
"""
from django.core.management.base import BaseCommand
from medios_pago.models import MedioDePago, CampoMedioDePago


class Command(BaseCommand):
    help = 'Crea el medio de pago Stripe con todos sus campos configurados'

    def handle(self, *args, **options):
        # Verificar si ya existe
        if MedioDePago.objects.filter(nombre__icontains='stripe').exists():
            self.stdout.write(
                self.style.WARNING('Ya existe un medio de pago con "Stripe" en el nombre')
            )
            respuesta = input('¿Desea crear uno nuevo de todas formas? (s/n): ')
            if respuesta.lower() != 's':
                self.stdout.write(self.style.SUCCESS('Operación cancelada'))
                return

        # Crear el medio de pago
        medio = MedioDePago.objects.create(
            nombre='Stripe - Tarjeta de Crédito/Débito',
            tipo_medio='stripe',
            comision_porcentaje=2.9,
            es_activo=True
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Medio de pago creado: {medio.nombre} (ID: {medio.id})')
        )

        # Crear campos del medio
        campos = [
            {
                'nombre_campo': 'Entidad',
                'campo_api': 'bank_name',
                'es_requerido': True,
                'tipo_campo': 'text',
                'orden': 1,
                'texto_ayuda': 'Debe ser "Stripe" para procesar con Stripe',
            },
            {
                'nombre_campo': 'Número de Tarjeta',
                'campo_api': 'card_number',
                'es_requerido': True,
                'tipo_campo': 'text',
                'orden': 2,
                'texto_ayuda': 'Ingrese el número de tarjeta sin espacios (16 dígitos)',
            },
            {
                'nombre_campo': 'Mes de Expiración',
                'campo_api': 'exp_month',
                'es_requerido': True,
                'tipo_campo': 'number',
                'orden': 3,
                'texto_ayuda': 'Mes de expiración (MM)',
            },
            {
                'nombre_campo': 'Año de Expiración',
                'campo_api': 'exp_year',
                'es_requerido': True,
                'tipo_campo': 'number',
                'orden': 4,
                'texto_ayuda': 'Año de expiración (YYYY)',
            },
            {
                'nombre_campo': 'Código de Seguridad (CVC)',
                'campo_api': 'cvc',
                'es_requerido': True,
                'tipo_campo': 'text',
                'orden': 5,
                'texto_ayuda': '3 o 4 dígitos en el reverso de la tarjeta',
            },
            {
                'nombre_campo': 'Nombre del Titular',
                'campo_api': 'cardholder_name',
                'es_requerido': True,
                'tipo_campo': 'text',
                'orden': 6,
                'texto_ayuda': 'Nombre como aparece en la tarjeta',
            },
        ]

        for campo_data in campos:
            campo = CampoMedioDePago.objects.create(
                medio_de_pago=medio,
                **campo_data
            )
            self.stdout.write(
                self.style.SUCCESS(f'  ✓ Campo creado: {campo.nombre_campo}')
            )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('✓ Medio de pago Stripe creado exitosamente'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')
        self.stdout.write('Próximos pasos:')
        self.stdout.write('1. Ir al admin de Django: /admin/')
        self.stdout.write('2. Ir a "Cliente medio de pagos"')
        self.stdout.write('3. Crear un nuevo registro asignando el medio Stripe a un cliente')
        self.stdout.write('4. En el campo "Entidad" poner: Stripe')
        self.stdout.write('5. Usar tarjeta de prueba: 4242424242424242')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('IMPORTANTE: Asegúrate de que el campo "Entidad" contenga "Stripe"'))
        self.stdout.write('')
