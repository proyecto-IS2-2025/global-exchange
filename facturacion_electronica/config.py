"""
Configuración para la integración con SQL Proxy de Factura Segura
Datos proporcionados por el profesor para el Equipo 7
"""
import os

# Configuración del SQL Proxy
SQL_PROXY_CONFIG = {
    'host': os.getenv('SQL_PROXY_DB_HOST', 'localhost'),
    'port': int(os.getenv('SQL_PROXY_DB_PORT', '45432')),
    'database': os.getenv('SQL_PROXY_DB_NAME', 'fs_proxy_bd'),
    'user': os.getenv('SQL_PROXY_DB_USER', 'fs_proxy_user'),
    'password': os.getenv('SQL_PROXY_DB_PASSWORD', 'p123456'),
    'kude_url': os.getenv('SQL_PROXY_KUDE_URL', f"http://{os.getenv('SQL_PROXY_HOST', 'localhost')}:{os.getenv('SQL_PROXY_PORT', '40080')}/kude")
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
FACTURACION_CONFIG = {
    'numero_inicial': 51,
    'numero_final': 100,
    'numero_actual': 51,  # Se irá incrementando con cada factura
    'formato_numero': '0000051'  # Formato de 7 dígitos con ceros a la izquierda
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
    # Leer configuración de KuDE (PDF/XML) desde variables de entorno para
    # que cada máquina pueda apuntar al mismo servicio sin cambiar el código.
    'url': os.getenv('SQL_PROXY_KUDE_URL', f"http://{os.getenv('SQL_PROXY_HOST','localhost')}:{os.getenv('SQL_PROXY_PORT','40080')}/kude/"),
    'username': os.getenv('KUDE_USERNAME', 'sqlproxy'),
    'password': os.getenv('KUDE_PASSWORD', 'kude1234')
}
