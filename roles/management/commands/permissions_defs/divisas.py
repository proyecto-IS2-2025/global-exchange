# roles/management/commands/permissions_defs/divisas.py

PERMISOS_DIVISAS = [
    {
        'app_label': 'divisas',
        'model': 'cotizacionsegmento',
        'codename': 'view_cotizaciones_segmento',
        'name': 'Puede ver cotizaciones del segmento',
        'modulo': 'divisas',  # ← AGREGADO
        'descripcion': 'Permite consultar las cotizaciones disponibles para los segmentos asignados.',  # ← RENOMBRADO
        'ejemplo': 'Revisar la tasa preferencial del segmento corporativo antes de una operación.',  # ← RENOMBRADO
        'nivel_riesgo': 'bajo',  # ← AGREGADO
        'orden': 10,
    },
    {
        'app_label': 'divisas',
        'model': 'cotizacionsegmento',
        'codename': 'manage_cotizaciones_segmento',
        'name': 'Puede configurar cotizaciones por segmento',
        'modulo': 'divisas',
        'descripcion': 'Autoriza la creación y actualización de cotizaciones para los distintos segmentos.',
        'ejemplo': 'Actualizar el spread para operaciones de clientes premium.',
        'nivel_riesgo': 'alto',
        'orden': 20,
    },
    {
        'app_label': 'divisas',
        'model': 'divisa',
        'codename': 'approve_operaciones_divisas',
        'name': 'Puede aprobar operaciones de divisas',
        'modulo': 'divisas',
        'descripcion': 'Habilita la aprobación de operaciones superiores al límite estándar.',
        'ejemplo': 'Aprobar la compra de USD 50.000 para el cliente ACME.',
        'nivel_riesgo': 'critico',
        'orden': 30,
    },
    {
        'app_label': 'divisas',
        'model': 'divisa',
        'codename': 'view_reportes_divisas',
        'name': 'Puede ver reportes consolidados de divisas',
        'modulo': 'divisas',
        'descripcion': 'Permite acceder a tableros y reportes de operaciones y posiciones.',
        'ejemplo': 'Descargar el reporte semanal de operaciones de divisas.',
        'nivel_riesgo': 'medio',
        'orden': 40,
    },
    {
        'app_label': 'divisas',
        'model': 'divisa',
        'codename': 'realizar_operacion',
        'name': 'Puede realizar operaciones de compra/venta',
        'modulo': 'divisas',
        'descripcion': 'Permite ejecutar transacciones de cambio de divisas',
        'ejemplo': 'Cliente compra USD 100 con PYG',
        'nivel_riesgo': 'alto',
        'orden': 50,
    },
    {
        'app_label': 'divisas',
        'model': 'divisa',
        'codename': 'ver_tasas_admin',
        'name': 'Puede ver visualizador de tasas administrativo',
        'modulo': 'divisas',
        'descripcion': 'Acceso al panel de gestión de tasas de cambio',
        'ejemplo': 'Modificar tasa de compra del dólar',
        'nivel_riesgo': 'critico',
        'orden': 60,
    },
]