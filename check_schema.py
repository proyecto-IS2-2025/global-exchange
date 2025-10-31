import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute("""
    SELECT column_name, data_type, character_maximum_length 
    FROM information_schema.columns 
    WHERE table_name='transacciones_transaccion' 
    AND column_name='estado'
""")
result = cursor.fetchall()
print("Columna 'estado' en transacciones_transaccion:")
for row in result:
    print(f"  Nombre: {row[0]}, Tipo: {row[1]}, Max Length: {row[2]}")

cursor.execute("""
    SELECT column_name, data_type, character_maximum_length 
    FROM information_schema.columns 
    WHERE table_name='transacciones_historialtransaccion' 
    AND column_name IN ('estado_anterior', 'estado_nuevo')
""")
result = cursor.fetchall()
print("\nColumnas 'estado' en transacciones_historialtransaccion:")
for row in result:
    print(f"  Nombre: {row[0]}, Tipo: {row[1]}, Max Length: {row[2]}")
