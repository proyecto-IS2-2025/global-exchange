.PHONY: dev-up dev-down prod-up prod-down docker-loaddata-dev docker-loaddata-prod docker-exec-dev docker-exec-prod docker-migrate-dev docker-migrate-prod docs test-medios-pago test-divisas test-simulador local-loaddata local-migrate help
#Variables de los nombres de proyecto para mantener los entornos separados
#Cada miembro del equipo usará el mismo nombre de proyecto, eliminando conflictos.

DEV_PROJECT_NAME = global-exchange-local-dev
PROD_PROJECT_NAME = global-exchange-local-prod

#------------------ Operaciones del Entorno de Desarrollo (Docker) ------------------#

dev-up:
	@echo "Levantando el entorno de desarrollo..."
	docker compose -p $(DEV_PROJECT_NAME) up --build
	@echo "Entorno de desarrollo levantado. Accede en http://localhost:8000"

dev-down:
	@echo "Deteniendo y limpiando el entorno de desarrollo..."
	docker compose -p $(DEV_PROJECT_NAME) down -v --remove-orphans
	@echo "Entorno de desarrollo detenido y limpiado."

docker-exec-dev:
	@echo "Ejecutando un comando en el contenedor web de desarrollo..."
	docker compose -p $(DEV_PROJECT_NAME) exec web sh

docker-migrate-dev:
	@echo "Aplicando migraciones en el entorno de desarrollo..."
	docker compose -p $(DEV_PROJECT_NAME) exec web python manage.py migrate
	@echo "Migraciones aplicadas."

loaddata-dev:
	@echo "Cargando datos iniciales en el entorno de desarrollo..."
	docker compose -p $(DEV_PROJECT_NAME) exec web python manage.py loaddata roles_data.json
	docker compose -p $(DEV_PROJECT_NAME) exec web python manage.py loaddata users_data.json
	docker compose -p $(DEV_PROJECT_NAME) exec web python manage.py loaddata clientes_data.json
	docker compose -p $(DEV_PROJECT_NAME) exec web python manage.py loaddata divisas_initial_data.json
	@echo "Datos iniciales cargados en desarrollo."

init-db: docker-migrate-dev docker-loaddata-dev
	@echo "Base de datos de desarrollo inicializada y con datos de ejemplo."

#------------------ Operaciones del Entorno de Producción (Docker) ------------------#

prod-up:
	@echo "Levantando el entorno de producción..."
	docker compose -p $(PROD_PROJECT_NAME) -f docker-compose.prod.yml up --build -d
	@echo "Entorno de producción levantado. Accede en http://localhost"

prod-down:
	@echo "Deteniendo y limpiando el entorno de producción..."
	docker compose -p $(PROD_PROJECT_NAME) -f docker-compose.prod.yml down -v --remove-orphans
	@echo "Entorno de producción detenido y limpiado."

docker-exec-prod:
	@echo "Ejecutando un comando en el contenedor web de producción..."
	docker compose -p $(PROD_PROJECT_NAME) -f docker-compose.prod.yml exec web sh

docker-migrate-prod:
	@echo "Aplicando migraciones en el entorno de producción..."
	docker compose -p $(PROD_PROJECT_NAME) -f docker-compose.prod.yml exec web python manage.py migrate
	@echo "Migraciones aplicadas."

loaddata-prod:
	@echo "Cargando datos iniciales en el entorno de producción..."
	docker compose -p $(PROD_PROJECT_NAME) -f docker-compose.prod.yml exec web python manage.py loaddata roles_data.json
	docker compose -p $(PROD_PROJECT_NAME) -f docker-compose.prod.yml exec web python manage.py loaddata users_data.json
	docker compose -p $(PROD_PROJECT_NAME) -f docker-compose.prod.yml exec web python manage.py loaddata clientes_data.json
	docker compose -p $(PROD_PROJECT_NAME) -f docker-compose.prod.yml exec web python manage.py loaddata divisas_initial_data.json
	@echo "Datos iniciales cargados en producción."

#------------------ Comandos DJANGO (Sin Docker) ------------------#

runserver:
	@echo "Iniciando el servidor de desarrollo Django (local)..."
	poetry run python manage.py runserver

migrations:
	@echo "Creando migraciones..."
	poetry run python manage.py makemigrations

migrate:
	@echo "Migrando la base de datos (local)..."
	poetry run python manage.py migrate

loaddata:
	@echo "Cargando datos iniciales (local)..."
	poetry run python manage.py loaddata roles_data.json
	poetry run python manage.py loaddata users_data.json
	poetry run python manage.py loaddata clientes_data.json
	poetry run python manage.py loaddata divisas_initial_data.json
	@echo "Datos iniciales cargados (local)."

docs:
	@echo "Generando documentación con Sphinx..."
	poetry run sphinx-build -b html docs/source docs/build
	@echo "Documentación generada en docs/build"

#------------------ Pruebas (Sin Docker) ------------------#

test-medios-pago:
	@echo "Probando migraciones..."
	python manage.py test medios_pago.tests.MedioDePagoModelTest medios_pago.tests.CampoMedioDePagoModelTest medios_pago.tests.EdgeCasesTest -v 2
	@echo "Pruebas de migraciones completadas."

test-divisas:
	@echo "Probando migraciones..."
	python manage.py test divisas
	@echo "Pruebas de migraciones completadas."

test-simulador:
	@echo "Probando simulador de pagos..."
	python manage.py test simulador
	@echo "Pruebas de simulador completadas."

delete-migrations:
	@echo "Eliminando archivos de migraciones..."
	find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
	find . -path "*/migrations/*.pyc" -delete
	@echo "Archivos de migraciones eliminados."

#------------------ Ayuda ------------------#

help:
	@echo ""
	@echo "Comandos disponibles:"
	@echo "--------------------"
	@echo "dev-up                   Levanta el entorno de desarrollo (Docker)."
	@echo "dev-down                 Detiene y elimina el entorno de desarrollo."
	@echo "docker-exec-dev          Abre una shell en el contenedor web de desarrollo."
	@echo "docker-migrate-dev       Aplica migraciones en el entorno de desarrollo."
	@echo "docker-loaddata-dev      Carga los datos iniciales en el entorno de desarrollo."
	@echo ""
	@echo "prod-up                  Levanta el entorno de producción (Docker)."
	@echo "prod-down                Detiene y elimina el entorno de producción."
	@echo "docker-exec-prod         Abre una shell en el contenedor web de producción."
	@echo "docker-migrate-prod      Aplica migraciones en el entorno de producción."
	@echo "docker-loaddata-prod     Carga los datos iniciales en el entorno de producción."
	@echo ""
	@echo "runserver                Inicia el servidor de desarrollo local de Django (sin Docker)."
	@echo "migrations               Crea migraciones de Django (local)."
	@echo "migrate                  Aplica migraciones de Django (local)."
	@echo "loaddata                 Carga datos iniciales (local)."
	@echo "docs                     Genera la documentación con Sphinx."
	@echo "tests                    Ejecuta los tests de la app."
	@echo ""
#Fin del archivo make
