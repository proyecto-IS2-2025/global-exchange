import os
import django
import psycopg2
from django.conf import settings

# 1. Configura la variable de entorno
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "casa_de_cambios.settings")

# 2. Llama a django.setup()
django.setup()

# 3. Obtén la configuración de la base de datos por su clave 'default'
db_config = settings.DATABASES['default']

try:
    conn = psycopg2.connect(
        dbname=db_config['NAME'],
        user=db_config['USER'],
        password=db_config['PASSWORD'],
        host=db_config['HOST'],
        port=db_config['PORT']
    )
    print("¡Conexión a la base de datos exitosa!")
    conn.close()
except psycopg2.OperationalError as e:
    print(f"Error al conectar a la base de datos: {e}")