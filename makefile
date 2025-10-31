.PHONY: dev-up dev-down prod-up prod-down docker-loaddata-dev docker-load-prod docker-exec-dev docker-exec-prod docker-migrate-dev docker-migrate-prod docs test-medios-pago test-divisas test-simulador local-loaddata local-migrate help
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

# Variable para acortar los comandos de Docker en producción
PROD_EXEC = docker compose -p $(PROD_PROJECT_NAME) -f docker-compose.prod.yml exec web

# --- Target de Producción ---

load-prod:
	@echo "Cargando datos iniciales en el entorno de producción..."
	# Carga de fixtures (datos)
	$(PROD_EXEC) python manage.py loaddata roles_data.json
	$(PROD_EXEC) python manage.py loaddata users_data.json
	$(PROD_EXEC) python manage.py loaddata clientes_data.json
	$(PROD_EXEC) python manage.py loaddata divisas_data.json
	$(PROD_EXEC) python manage.py loaddata bancos_data.json
	# Fixtures faltantes añadidas:
	$(PROD_EXEC) python manage.py loaddata denominaciones_data.json
	$(PROD_EXEC) python manage.py loaddata billetera_data.json
	
	@echo "Sincronizando permisos y roles de producción..."
	# Configuración de permisos añadida:
	$(PROD_EXEC) python manage.py sync_permissions
	$(PROD_EXEC) python manage.py setup_test_roles --verbose
	$(PROD_EXEC) python manage.py sync_role_status
	
	@echo "Creando usuario administrador de producción..."
	$(PROD_EXEC) python manage.py create_dev_user

	@echo "Datos iniciales cargados en producción."

#------------------ Comandos DJANGO (Sin Docker) ------------------#

runserver:
	@echo "Iniciando el servidor de desarrollo Django (local)..."
	poetry run python manage.py runserver

migrations:
	@echo "Aplicando migraciones a la base de datos..."
	@ARGS="$(filter-out $@,$(MAKECMDGOALS))"; \
	FLAGS=""; APPS=""; \
	for a in $$ARGS; do \
		case $$a in \
			-*) FLAGS="$$FLAGS $$a" ;; \
			*) APPS="$$APPS $$a" ;; \
		esac; \
	done; \
	if [ -z "$$APPS" ]; then \
		poetry run python manage.py makemigrations $$FLAGS; \
	else \
		poetry run python manage.py makemigrations $$FLAGS $$APPS; \
	fi
	@echo "Migraciones creadas correctamente"

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

cargar-datos:
	@echo "Cargando datos iniciales..."
	python manage.py loaddata roles_data.json
	python manage.py loaddata users_data.json
	python manage.py loaddata clientes_data.json
	python manage.py loaddata divisas_data.json
	python manage.py loaddata medios_data.json
	@echo "Datos iniciales cargados."

run:
	@echo "Ejecutando el servidor de desarrollo con recarga automática..."
	poetry run python manage.py runserver 
	@echo "Servidor detenido."

db-init:
	@echo "Inicializando la base de datos..."
	poetry run python manage.py makemigrations
	poetry run python manage.py migrate
	poetry run python manage.py loaddata roles_data.json
	poetry run python manage.py loaddata users_data.json
	poetry run python manage.py loaddata clientes_data.json
	poetry run python manage.py loaddata divisas_data.json
	
	@echo "Datos cargados."

test-medios-acreditacion:
	@echo "Ejecutando pruebas de medios de acreditación..."
	poetry run python manage.py test clientes.tests_medios_acreditacion
	@echo "Pruebas completadas."

delete-migrations:
	@echo "Eliminando archivos de migraciones..."
	find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
	find . -path "*/migrations/*.pyc" -delete
	@echo "Archivos de migraciones eliminados."

reset-db:
	@echo "Reiniciando la base de datos..."
	
	dropdb --username=django_user  --if-exists global_exchange --host=localhost
	createdb --username=django_user --host=localhost global_exchange 
	
	@echo "Cargando datos de prueba..."
	poetry run python scripts/delete_migrations.py
	poetry run python manage.py makemigrations	
	poetry run python manage.py migrate
	poetry run python manage.py loaddata roles_data.json
	poetry run python manage.py loaddata users_data.json
	poetry run python manage.py loaddata clientes_data.json
	poetry run python manage.py loaddata divisas_data.json
	poetry run python manage.py loaddata bancos_data.json
	poetry run python manage.py loaddata denominaciones_data.json
	poetry run python manage.py loaddata billetera_data.json

	@echo "Configurando roles de prueba..."
	poetry run python manage.py sync_permissions
	poetry run python manage.py setup_test_roles --verbose
	poetry run python manage.py sync_role_status
	poetry run python manage.py create_dev_user
	
	@echo "Base de datos reiniciada y datos cargados."

migraWin:
	@echo "Realizando migraciones en Windows..."
	poetry run python manage.py makemigrations
	poetry run python manage.py migrate
	@echo "Migraciones realizadas en Windows."

sync:
	@echo "Sincronizando repositorio local con el remoto..."
	 poetry run python manage.py sync_permissions
	@echo "Repositorio sincronizado."

check:
	@echo "Verificando el estado del proyecto..."
	poetry run python manage.py check
	@echo "Verificación completada."


roles:
	@echo "Sincronizando roles y permisos..."
	python manage.py sync_permissions
	python manage.py setup_test_roles --verbose
	python manage.py sync_role_status
	python manage.py create_dev_user
	@echo "Roles y permisos sincronizados."

test-fact:
	@echo "Ejecutando pruebas de facturación electrónica..."
	poetry run python manage.py test facturacion_electronica.tests
	@echo "Pruebas de facturación electrónica completadas."


