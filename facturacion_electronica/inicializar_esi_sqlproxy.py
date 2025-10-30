#!/usr/bin/env python
"""
Script para inicializar el ESI en SQL Proxy con los datos correctos del XML del docente
IMPORTANTE: Ejecutar SOLO UNA VEZ después de levantar PostgreSQL
"""
import psycopg2
import sys

# Configuración SQL Proxy
SQL_PROXY_CONFIG = {
    'host': 'localhost',
    'port': 45432,
    'database': 'fs_proxy_bd',
    'user': 'fs_proxy_user',
    'password': 'p123456'
}

# Datos del ESI (del XML del docente)
ESI_DATA = {
    'email': 'glex.globalexchange@gmail.com',
    'password': 'Globalexchange#2000',
    'token': 'IjU4ZjAwMzAwMzRiMGMzNGNiMTdhODI4OTY2OWZiNTM2ZTMzZTg1NTMi.aPA24g.CZiHTVen8x7RZgEXIfr7f0Y4dO4',
    'ambiente': 'test',  # 'test' o 'prod'
    
    # Datos del Emisor (del XML)
    'ruc': '2595733',
    'dv': '3',
    'nombre': 'DE generado en ambiente de prueba - sin valor comercial ni fiscal',
    'direccion': 'YVAPOVO C/ TOBATI',
    'numero_casa': '1543',
    'departamento': '1',
    'ciudad': '1',
    'telefono': '(0961)988439',
    'email_emisor': 'ggonzar@gmail.com',
    'tipo_contribuyente': 1,
    
    # Actividades Económicas
    'actividades': [
        {'codigo': '62010', 'descripcion': 'Actividades de programación informática'},
        {'codigo': '74909', 'descripcion': 'Otras actividades profesionales, científicas y técnicas n.c.p.'}
    ]
}

def main():
    print("=" * 70)
    print("INICIALIZACIÓN DEL ESI EN SQL PROXY")
    print("=" * 70)
    
    try:
        # Conectar
        conn = psycopg2.connect(**SQL_PROXY_CONFIG)
        cur = conn.cursor()
        print("✓ Conectado a SQL Proxy")
        
        # Verificar si ya existe
        cur.execute("SELECT COUNT(*) FROM public.esi")
        count = cur.fetchone()[0]
        
        if count > 0:
            print(f"\n⚠️  Ya existe {count} configuración(es) ESI")
            respuesta = input("¿Deseas reemplazarla? (s/n): ").strip().lower()
            if respuesta != 's':
                print("❌ Operación cancelada")
                return
            
            # Eliminar configuración anterior
            cur.execute("DELETE FROM public.esi")
            print("✓ Configuración anterior eliminada")
        
        # Insertar ESI
        print(f"\n📝 Insertando configuración ESI...")
        esi_url = 'https://apitest.facturasegura.com.py' if ESI_DATA['ambiente'] == 'test' else 'https://api.facturasegura.com.py'
        
        cur.execute("""
            INSERT INTO public.esi (
                ruc, ruc_dv, nombre, descripcion, estado,
                esi_email, esi_passwd, esi_token, esi_url
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
        """, (
            ESI_DATA['ruc'], ESI_DATA['dv'], ESI_DATA['nombre'], 
            'Configuración ESI para ambiente TEST', 'activo',
            ESI_DATA['email'], ESI_DATA['password'], ESI_DATA['token'], esi_url
        ))
        
        conn.commit()
        
        print("\n" + "=" * 70)
        print("✅ ESI CONFIGURADO EXITOSAMENTE")
        print("=" * 70)
        print(f"\n📋 Datos configurados:")
        print(f"  Email: {ESI_DATA['email']}")
        print(f"  Ambiente: {ESI_DATA['ambiente'].upper()}")
        print(f"  RUC: {ESI_DATA['ruc']}-{ESI_DATA['dv']}")
        print(f"  Nombre: {ESI_DATA['nombre']}")
        print(f"  Actividades:")
        for act in ESI_DATA['actividades']:
            print(f"    - {act['codigo']}: {act['descripcion']}")
        
        print("\n🚀 Ahora puedes generar facturas y SQL Proxy las procesará correctamente")
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
