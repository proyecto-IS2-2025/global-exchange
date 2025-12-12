"""
Configuración para la integración con SQL Proxy de Factura Segura
Datos proporcionados por el profesor para el Equipo 7
"""

# Configuración del SQL Proxy
SQL_PROXY_CONFIG = {
    'host': 'host.docker.internal',  # Usar host.docker.internal para acceder desde Docker
    'port': 45432,
    'database': 'fs_proxy_bd',
    'user': 'fs_proxy_user',
    'password': 'p123456',
    'kude_url': 'http://host.docker.internal:40080/kude'  # URL para acceder a los PDFs y XMLs generados
}

# Configuración del ESI (Equipo 7)
ESI_CONFIG = {
    'email': 'glex.globalexchange@gmail.com',
    'password': 'Globalexchange#2000',  # Completar con la contraseña del ESI
    'token': 'IjU4ZjAwMzAwMzRiMGMzNGNiMTdhODI4OTY2OWZiNTM2ZTMzZTg1NTMi.aPA24g.CZiHTVen8x7RZgEXIfr7f0Y4dO4',
    'url_test': 'https://apitest.facturasegura.com.py',
    'url_prod': 'https://api.facturasegura.com.py',
    'ambiente': 'TEST'  # Cambiar a 'PROD' cuando se pase a producción
}

# Configuración del Emisor (Datos del profesor)
EMISOR_CONFIG = {
    'ruc': '2595733',
    'dv': '3',
    'nombre': 'DE generado en ambiente de prueba - sin valor comercial ni fiscal',
    'direccion': 'YVAPOVO C/ TOBATI',
    'numero_casa': '1543',
    'departamento': '1',  # CAPITAL
    'departamento_desc': 'CAPITAL',
    'ciudad': '1',  # ASUNCION (DISTRITO)
    'ciudad_desc': 'ASUNCION (DISTRITO)',
    'telefono': '(0961)988439',
    'email': 'ggonzar@gmail.com',
    'tipo_contribuyente': '1'  # 1 = Persona Física
}

# Configuración de Timbrado
TIMBRADO_CONFIG = {
    'numero': '02595733',
    'fecha_inicio': '2025-03-27',
    'establecimiento': '001',
    'punto_expedicion': '003'
}

# Rango de numeración asignado al equipo 7
# DICIEMBRE 2025 - Nuevo rango: 701-750
FACTURACION_CONFIG = {
    'numero_inicial': 701,  # DICIEMBRE 2025: Nuevo rango 701-750
    'numero_final': 750,
    'numero_actual': 701,  # Primera factura del nuevo rango
    'formato_numero': '0000701'  # Formato de 7 dígitos con ceros a la izquierda
}

# Actividades Económicas (según XML del profesor)
ACTIVIDADES_ECONOMICAS = [
    {
        'codigo': '62010',
        'descripcion': 'Actividades de programación informática'
    },
    {
        'codigo': '74909',
        'descripcion': 'Otras actividades profesionales, científicas y técnicas n.c.p.'
    }
]

# URL para acceder a los KuDE (PDF y XML)
KUDE_CONFIG = {
    'url': 'http://host.docker.internal:40080/kude/',
    'username': 'sqlproxy',
    'password': 'kude1234'
}
