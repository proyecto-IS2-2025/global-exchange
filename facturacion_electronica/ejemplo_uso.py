"""
Script de ejemplo para probar la integración con SQL Proxy
"""
import os
import sys

# Agregar el directorio padre al path para poder importar los módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar Django si es necesario
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')

try:
    import django
    django.setup()
except:
    pass  # Si Django no está disponible, continuar sin él

from facturacion_electronica.services import SQLProxyService


def ejemplo_uso():
    """
    Ejemplo de cómo usar el servicio de facturación electrónica
    """
    
    # Crear instancia del servicio
    servicio = SQLProxyService()
    
    # Conectar al SQL Proxy
    if not servicio.conectar():
        print("No se pudo conectar al SQL Proxy")
        return
    
    try:
        # 1. Inicializar ESI (solo la primera vez)
        print("\n1. Inicializando ESI...")
        if not servicio.verificar_esi_existe():
            servicio.inicializar_esi()
        else:
            print("✓ ESI ya está configurado")
        
        # 2. Crear una factura de ejemplo
        print("\n2. Creando factura de ejemplo...")
        datos_factura = {
            'cliente_ruc': '80026216',
            'cliente_dv': '6',
            'cliente_nombre': 'JUAN PEREZ',
            'cliente_email': 'cliente@example.com',
            'items': [
                {
                    'descripcion': 'CAMBIO DE DOLARES A GUARANIES',
                    'cantidad': '1',
                    'precio_unitario': '500000',
                    'descuento': '0',
                    'afectacion_iva': '1',  # 1=Gravado, 2=Exonerado, 3=Exento
                    'proporcion_iva': '100',
                    'tasa_iva': '10'  # 10% IVA
                }
            ]
        }
        
        resultado = servicio.crear_factura(datos_factura)
        print(f"\n✓ {resultado['mensaje']}")
        print(f"  ID interno: {resultado['de_id']}")
        
        # 3. Consultar estado de la factura
        print("\n3. Consultando estado de la factura...")
        import time
        time.sleep(2)  # Esperar un poco para que se procese
        
        estado = servicio.consultar_estado_factura(resultado['numero_factura'])
        if estado:
            print(f"\n  Número: {estado['dnumdoc']}")
            print(f"  Estado: {estado['estado']}")
            print(f"  Estado SIFEN: {estado['estado_sifen']}")
            if estado['desc_sifen']:
                print(f"  Descripción SIFEN: {estado['desc_sifen']}")
            if estado['error_sifen']:
                print(f"  Error SIFEN: {estado['error_sifen']}")
            if estado['cdc']:
                print(f"  CDC: {estado['cdc']}")
        
        print("\n✓ Proceso completado exitosamente")
        print("\nPuedes acceder a los KuDE (PDF y XML) en:")
        print("http://localhost:40080/kude/")
        print("Usuario: sqlproxy")
        print("Contraseña: kude1234")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
    
    finally:
        # Desconectar
        servicio.desconectar()


if __name__ == "__main__":
    ejemplo_uso()
