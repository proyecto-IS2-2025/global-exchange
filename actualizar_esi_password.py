#!/usr/bin/env python3
"""
Script para ACTUALIZAR el ESI con la contraseña correcta.
Esto permitirá que el SQL Proxy obtenga un token válido automáticamente.
"""
import psycopg2

# Configuración de conexión
DB_CONFIG = {
    'user': 'fs_proxy_user',
    'password': 'p123456',
    'host': 'localhost',
    'port': '45432',
    'database': 'fs_proxy_bd'
}

print("=" * 80)
print("ACTUALIZAR ESI CON CONTRASEÑA")
print("=" * 80)
print("\n⚠️  IMPORTANTE:")
print("El SQL Proxy necesita EMAIL + CONTRASEÑA del ESI para obtener un token válido.")
print("El token se renueva automáticamente cuando tiene contraseña configurada.")
print("\n" + "=" * 80)

# Solicitar contraseña
print("\n📧 Email actual del ESI: glex.globalexchange@gmail.com")
print("🔑 Necesitamos la CONTRASEÑA del ESI que el profesor configuró.")
print("\nPregunta al profesor:")
print('   "¿Cuál es la contraseña del ESI para glex.globalexchange@gmail.com?"')
print("\nSi no la tienes, presiona ENTER para ver las opciones...")

password = input("\nIngresa la contraseña del ESI (o ENTER para opciones): ").strip()

if not password:
    print("\n" + "=" * 80)
    print("OPCIONES SIN CONTRASEÑA:")
    print("=" * 80)
    print("\n1. SOLICITAR AL PROFESOR:")
    print("   Email al profesor: soporte@facturasegura.com.py")
    print("   Asunto: Contraseña ESI para glex.globalexchange@gmail.com")
    print("   Mensaje:")
    print("   ---")
    print("   Estimado profesor,")
    print("   ")
    print("   Necesitamos la contraseña del ESI configurado para:")
    print("   - Email: glex.globalexchange@gmail.com")
    print("   - RUC: 2595733-3")
    print("   - Rango documentos: 51-100")
    print("   ")
    print("   El SQL Proxy requiere email + contraseña para obtener")
    print("   el token de autenticación automáticamente.")
    print("   ")
    print("   Gracias!")
    print("   ---")
    print("\n2. USAR CLIENT APP.PY DEL PROFESOR:")
    print("   El script ./client/app.py permite configurar un nuevo ESI")
    print("   con email + contraseña que tú elijas.")
    print("\n" + "=" * 80)
    exit(0)

# Conectar y actualizar
try:
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    print("\n✅ Conectado a PostgreSQL")
    
    # Actualizar contraseña
    update_query = """
    UPDATE public.esi 
    SET esi_passwd = %s,
        esi_token = ''
    WHERE esi_email = 'glex.globalexchange@gmail.com';
    """
    
    cursor.execute(update_query, (password,))
    connection.commit()
    
    print("\n✅ CONTRASEÑA ACTUALIZADA")
    print("\n" + "=" * 80)
    print("PRÓXIMOS PASOS:")
    print("=" * 80)
    print("\n1. El scheduler obtendrá un token válido automáticamente")
    print("2. Espera 20-40 segundos")
    print("3. Genera una nueva factura")
    print("4. Verifica el estado:")
    print("   docker exec sql-proxy01-db-1 psql -U fs_proxy_user -d fs_proxy_bd -c")
    print("   \"SELECT dnumdoc, estado, estado_sifen FROM public.de ORDER BY id DESC LIMIT 1;\"")
    print("\n🎯 Si la contraseña es correcta, la factura debería ser APROBADA")
    print("   y tendrás el PDF disponible en http://localhost:40080/kude/")
    print("\n" + "=" * 80)
    
    # Verificar
    cursor.execute("SELECT ruc, esi_email, LENGTH(esi_passwd) as pwd_len FROM public.esi WHERE esi_email = 'glex.globalexchange@gmail.com';")
    result = cursor.fetchone()
    if result:
        print(f"\n📋 ESI ACTUALIZADO:")
        print(f"   RUC: {result[0]}")
        print(f"   Email: {result[1]}")
        print(f"   Contraseña: {'*' * result[2]} ({result[2]} caracteres)")
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    if connection:
        cursor.close()
        connection.close()
        print("\n✅ Conexión cerrada")
