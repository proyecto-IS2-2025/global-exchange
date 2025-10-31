"""
Definiciones de permisos personalizados para la app 'tauser' (terminales y configuración de TAUSER).

Nota: estos permisos cubren la configuración y operación de terminales, inventarios y denominaciones.
Se han evitado permisos que otorguen acceso directo a datos del modelo `clientes` o a acciones explícitas
de gestión de clientes, tal como solicitó el equipo: el admin del menú de configuración de `tauser`
obtendrá todos los permisos de TAUSER excepto los relacionados al cliente.
"""

PERMISOS_TAUSER = [
    # ═══════════════════════════════════════════════════════════════════
    # TERMINALES
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'tauser',
        'model': 'terminal',
        'codename': 'manage_terminales',
        'name': 'Puede gestionar terminales',
        'modulo': 'tauser',
        'descripcion': 'Permite crear, editar y eliminar terminales de autoservicio.',
        'ejemplo': 'Un administrador registra una nueva terminal y configura su ubicación y responsable.',
        'nivel_riesgo': 'alto',
        'orden': 10,
        'categoria': 'gestion_terminales',
        'requiere_auditoria': True,
    },
    {
        'app_label': 'tauser',
        'model': 'terminal',
        'codename': 'view_terminales',
        'name': 'Puede ver terminales',
        'modulo': 'tauser',
        'descripcion': 'Permite listar y consultar información de terminales.',
        'ejemplo': 'Un operador revisa la lista de terminales y su estado.',
        'nivel_riesgo': 'bajo',
        'orden': 20,
        'categoria': 'consulta_terminales',
        'requiere_auditoria': False,
    },

    # ═══════════════════════════════════════════════════════════════════
    # INVENTARIO DE DIVISAS EN TERMINAL
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'tauser',
        'model': 'inventariodivisaterminal',
        'codename': 'manage_inventario_divisa',
        'name': 'Puede gestionar inventario de divisas en terminales',
        'modulo': 'tauser',
        'descripcion': 'Permite ajustar cantidades y parámetros del inventario de divisas por terminal.',
        'ejemplo': 'Un administrador repone o descuenta cantidades de USD en la terminal T-01.',
        'nivel_riesgo': 'critico',
        'orden': 30,
        'categoria': 'gestion_inventario',
        'requiere_auditoria': True,
    },
    {
        'app_label': 'tauser',
        'model': 'inventariodivisaterminal',
        'codename': 'view_inventario_divisa',
        'name': 'Puede ver inventario de divisas en terminales',
        'modulo': 'tauser',
        'descripcion': 'Permite consultar los niveles de inventario sin modificarlos.',
        'ejemplo': 'Un supervisor consulta si hay USD suficientes para realizar ventas.',
        'nivel_riesgo': 'medio',
        'orden': 40,
        'categoria': 'consulta_inventario',
        'requiere_auditoria': False,
    },

    # ═══════════════════════════════════════════════════════════════════
    # DENOMINACIONES EN TERMINAL
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'tauser',
        'model': 'inventariodenominacionterminal',
        'codename': 'manage_denominaciones_inventario',
        'name': 'Puede gestionar denominaciones en terminal',
        'modulo': 'tauser',
        'descripcion': 'Permite agregar o ajustar cantidades de billetes por denominación en la terminal.',
        'ejemplo': 'Un operador carga 100 billetes de 50 USD en la terminal T-01.',
        'nivel_riesgo': 'alto',
        'orden': 50,
        'categoria': 'gestion_denominaciones',
        'requiere_auditoria': True,
    },
    {
        'app_label': 'tauser',
        'model': 'inventariodenominacionterminal',
        'codename': 'view_denominaciones_inventario',
        'name': 'Puede ver denominaciones en terminal',
        'modulo': 'tauser',
        'descripcion': 'Permite consultar cantidades de billetes disponibles por denominación.',
        'ejemplo': 'Un supervisor verifica cuántos billetes de 20 quedan en la terminal.',
        'nivel_riesgo': 'bajo',
        'orden': 60,
        'categoria': 'consulta_denominaciones',
        'requiere_auditoria': False,
    },

    # ═══════════════════════════════════════════════════════════════════
    # PINS Y SEGURIDAD DE ACCESO A TERMINAL
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'tauser',
        'model': 'pinterminalcliente',
        'codename': 'manage_pins_terminal',
        'name': 'Puede gestionar PINs temporales de terminal',
        'modulo': 'tauser',
        'descripcion': 'Permite generar y revocar PINs temporales que clientes usan para acceder a terminales.',
        'ejemplo': 'Un operador genera un PIN temporal para que un cliente realice una operación.',
        'nivel_riesgo': 'alto',
        'orden': 70,
        'categoria': 'gestion_pins',
        'requiere_auditoria': True,
    },
    {
        'app_label': 'tauser',
        'model': 'pinterminalcliente',
        'codename': 'view_pins_terminal',
        'name': 'Puede ver PINs de terminal',
        'modulo': 'tauser',
        'descripcion': 'Permite consultar PINs temporales y su estado (usado/pendiente). No otorga acceso a datos privados completos de clientes.',
        'ejemplo': 'Un supervisor consulta si un PIN ya fue usado.',
        'nivel_riesgo': 'medio',
        'orden': 80,
        'categoria': 'consulta_pins',
        'requiere_auditoria': False,
    },

    # ═══════════════════════════════════════════════════════════════════
    # REGISTROS DE OPERACIONES EN TERMINAL
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'tauser',
        'model': 'registrotransaccionterminal',
        'codename': 'view_registros_terminal',
        'name': 'Puede ver registros de operaciones en terminal',
        'modulo': 'tauser',
        'descripcion': 'Permite consultar el historial de operaciones realizadas en terminales. NOTA: este permiso no incluye gestión de clientes; los datos sensibles de clientes deberán protegerse mediante permisos del app `clientes`.',
        'ejemplo': 'Un auditor revisa operaciones de la terminal T-01 durante el día.',
        'nivel_riesgo': 'medio',
        'orden': 90,
        'categoria': 'consulta_registros',
        'requiere_auditoria': True,
    },
    {
        'app_label': 'tauser',
        'model': 'registrotransaccionterminal',
        'codename': 'export_registros_terminal',
        'name': 'Puede exportar registros de operaciones en terminal',
        'modulo': 'tauser',
        'descripcion': 'Permite exportar listados de operaciones en formato CSV/Excel para análisis. No incluye permisos de administración sobre clientes.',
        'ejemplo': 'Un administrador exporta el reporte de operaciones de la semana para conciliación.',
        'nivel_riesgo': 'alto',
        'orden': 100,
        'categoria': 'reportes',
        'requiere_auditoria': True,
    },
]
