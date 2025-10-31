import os
from pathlib import Path
from dotenv import load_dotenv

# La misma lógica que en settings.py para encontrar el archivo .env
env_path = os.path.join(Path(__file__).resolve().parent, '.env')
print(f"Intentando cargar variables desde: {env_path}")

# Cargar las variables de entorno
load_dotenv(env_path)

# Verificar si las variables se cargaron correctamente
print("\nVariables de entorno cargadas:")
print(f"SECRET_KEY: {os.environ.get('SECRET_KEY', 'No se cargó')}")
print(f"DEBUG: {os.environ.get('DEBUG', 'No se cargó')}")
print(f"DB_HOST: {os.environ.get('DB_HOST', 'No se cargó')}")

if os.environ.get('SECRET_KEY'):
    print("\n¡Éxito! Las variables de entorno se cargaron correctamente.")
else:
    print("\n¡Error! Las variables de entorno no se cargaron. Revisa la ruta del archivo .env y si el paquete python-dotenv está instalado.")