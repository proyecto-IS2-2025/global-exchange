"""
Script para inicializar el ESI en el SQL Proxy
EJECUTAR SOLO UNA VEZ después de levantar el SQL Proxy
"""
import sys
import os

# Agregar el directorio padre al path para importar el módulo
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from facturacion_electronica.services import SQLProxyService


def inicializar_esi():
    """
    Inicializa la configuración ESI en el SQL Proxy
    """
    print("="*60)
    print("INICIALIZACIÓN DE ESI - EQUIPO 7")
    print("="*60)
    print("\nEste script configurará el ESI en el SQL Proxy con los datos:")
    print("  - Email: glex.globalexchange@gmail.com")
    print("  - RUC Emisor: 2595733-3")
    print("  - Rango: 51-100")
    print("  - Establecimiento: 001, Punto Expedición: 003")
    print("\n⚠ IMPORTANTE: Solo ejecutar UNA VEZ después de levantar el SQL Proxy")
    
    confirmacion = input("\n¿Desea continuar? (s/n): ").strip().lower()
    if confirmacion != 's':
        print("Operación cancelada")
        return
    
    # Crear servicio
    servicio = SQLProxyService()
    
    # Conectar
    print("\nConectando al SQL Proxy...")
    if not servicio.conectar():
        print("✗ No se pudo conectar al SQL Proxy")
        print("\nAsegúrate de que:")
        print("  1. Docker esté ejecutándose")
        print("  2. Los contenedores del SQL Proxy estén levantados")
        print("  3. El puerto 45432 esté disponible")
        return
    
    try:
        # Verificar si ya existe
        if servicio.verificar_esi_existe():
            print("\n⚠ Ya existe configuración ESI")
            sobrescribir = input("¿Desea eliminar y reinicializar? (s/n): ").strip().lower()
            
            if sobrescribir == 's':
                # Eliminar registros existentes
                servicio.cursor.execute("DELETE FROM public.esi;")
                servicio.connection.commit()
                print("✓ Registros ESI anteriores eliminados")
            else:
                print("Operación cancelada")
                return
        
        # Inicializar
        print("\nInicializando ESI...")
        if servicio.inicializar_esi():
            print("\n" + "="*60)
            print("✓ ESI INICIALIZADO CORRECTAMENTE")
            print("="*60)
            print("\nYa puedes empezar a generar facturas electrónicas")
            print("\nPróximos pasos:")
            print("  1. Ejecutar ejemplo_uso.py para probar")
            print("  2. Integrar con tu sistema Django")
        else:
            print("\n✗ Error al inicializar ESI")
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
    
    finally:
        servicio.desconectar()


if __name__ == "__main__":
    inicializar_esi()
