Requisitos Previos
Antes de empezar, asegúrate de tener instalado:

Docker: Para crear y correr contenedores. Descárgalo de docker.com e instálalo. Verifica con docker --version.
Docker Compose: Viene incluido con Docker Desktop. Verifica con docker-compose --version.
Make: Herramienta para ejecutar el Makefile.

En Linux/Mac: Suele estar instalado; verifica con make --version. Si no, instálalo con sudo apt install make (Ubuntu) o brew install make (Mac con Homebrew).
En Windows: Usa WSL (Windows Subsystem for Linux) o instala Make vía Chocolatey (choco install make).


Git: Para clonar el repositorio si no lo tienes.
Python y Django conocimientos básicos: No obligatorios para usar el Makefile, pero útiles para entender qué pasa.

Clona el repositorio si no lo has hecho:
    git clone <URL_DEL_REPOSITORIO>
    cd <NOMBRE_DEL_PROYECTO>

Cómo Ejecutar Comandos del Makefile
Abre una terminal en la carpeta del proyecto (donde está el Makefile). Ejecuta comandos con make <nombre_del_comando>. Por ejemplo:
    make help

Esto muestra una lista de todos los comandos disponibles con descripciones. ¡Úsalo siempre que dudes!
Los comandos están organizados en secciones para que sea fácil encontrar lo que necesitas. Muchos usan colores en la terminal (verde para éxito, amarillo para advertencias) si estás en Linux/Mac.



Secciones y Comandos Principales
1. Ayuda y Comandos Básicos

make help: Muestra esta misma lista de comandos con descripciones. Empieza aquí si estás perdido.

2. Configuración Inicial (Para la Primera Vez)
Estos comandos preparan todo desde cero.

make build: Construye las imágenes Docker (como "paquetes" para tu app y base de datos).
make setup: Configuración completa: construye imágenes, espera a la base de datos, ejecuta migraciones y te pregunta si quieres crear un superusuario. Ejecuta esto la primera vez que configures el proyecto.

3. Desarrollo Diario (Lo que Usarás Más)
Comandos para trabajar todos los días.

make dev: Ejecuta migraciones y inicia el servidor en modo desarrollo. Accede a http://localhost:8000 en tu navegador.
make up: Inicia todos los servicios (app y DB) en primer plano (ves los logs en tiempo real).
make up-d: Inicia servicios en segundo plano (no bloquea la terminal).
make down: Detiene todos los servicios.
make restart: Detiene y reinicia los servicios en segundo plano.

4. Base de Datos
Comandos para manejar la DB (PostgreSQL).

make migrate: Crea y aplica migraciones (actualiza la estructura de la DB según tus modelos Django).
make makemigrations: Solo crea nuevas migraciones (sin aplicarlas).
make db-reset: ¡Cuidado! Resetea la DB completamente (borra todos los datos). Te pide confirmación. Úsalo solo si quieres empezar de cero.
make db-wait: Espera a que la DB esté lista (útil si hay delays).

5. Comandos de Django
Herramientas específicas de Django.

make shell: Abre un shell interactivo de Python con Django cargado (para probar código).
make shell-plus: Shell avanzado (si tienes django-extensions instalado).
make createsuperuser: Crea un usuario administrador.
make createsuperuser-optional: Te pregunta si quieres crear un superusuario (opcional).
make collectstatic: Recopila archivos estáticos (CSS, JS) para producción.

6. Testing y Calidad de Código
Para verificar que todo funcione bien.

make test: Ejecuta las pruebas unitarias de Django.
make test-coverage: Ejecuta pruebas y muestra cobertura de código (qué partes están probadas).
make test-verbose: Pruebas con más detalles en la salida.
make lint: Revisa el código por errores de estilo (requiere flake8 en requirements.txt).

7. Logs y Debugging (Para Diagnosticar Problemas)

make logs: Muestra logs de todos los servicios en tiempo real.
make logs-web: Solo logs de la app web.
make logs-db: Solo logs de la base de datos.
make bash: Entra al contenedor web con bash (para explorar archivos o ejecutar comandos manuales).
make bash-run: Ejecuta un nuevo contenedor web con bash.

8. Limpieza
Para mantener limpio tu sistema.

make clean: Elimina contenedores e imágenes no usadas.
make clean-all: Limpieza completa, incluyendo volúmenes (borra datos de DB). ¡Cuidado!

9. Estado e Información

make status o make ps: Muestra el estado de los contenedores (corriendo, detenidos, etc.).
make top: Muestra procesos dentro de los contenedores.

10. Producción (Para Deploy en Servidor Real)
Estos usan un archivo extra docker-compose.prod.yml para modo producción.

make build-prod: Construye imágenes para producción.
make prod: Inicia en modo producción (con Nginx para manejo de tráfico).
make prod-logs: Ve logs de producción.
make prod-down: Detiene producción.
make prod-restart: Reinicia producción.
make nginx-reload: Recarga config de Nginx sin detener.
make nginx-test: Prueba config de Nginx.

11. Utilidades

make requirements: Genera un requirements.txt actualizado desde el contenedor.
make backup-db: Crea un backup de la DB (guarda en un archivo SQL con fecha).
make restore-db: Restaura DB desde un archivo (usa make restore-db FILE=backup.sql).
make django-cmd: Ejecuta un comando Django personalizado (ej: make django-cmd CMD="check").
make pip-install: Instala un paquete Python (ej: make pip-install PKG="requests"), actualiza requirements y rebuild.

12. Atajos Rápidos (Shortcuts)
Para ahorrar tiempo:

make u: Igual a up.
make d: Igual a down.
make b: Igual a build.
make m: Igual a migrate.
make s: Igual a shell.
make l: Igual a logs.
make t: Igual a test.

Consejos Útiles

Problemas comunes:

Si la DB no conecta: Ejecuta make db-wait o verifica logs con make logs-db.
Errores de permisos: Asegúrate de que Docker corra sin sudo (configura en instalación).
En Windows: Usa WSL para mejor compatibilidad.


Variables de Entorno: Edita .env para cambiar DB, secrets, etc. No lo subas a Git.
Extender el Makefile: Si necesitas más comandos, agrégalos al final del archivo.
Seguridad: En producción, usa contraseñas fuertes y DEBUG=False en .env.
Aprende más: Lee la docs de Docker, Django o ejecuta make help para refrescar.