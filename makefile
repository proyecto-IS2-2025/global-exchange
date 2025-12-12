loaddata.PHONY: dev-up dev-down prod-up prod-up-foreground prod-logs prod-down docker-loaddata-dev docker-load-prod docker-exec-dev docker-exec-prod docker-migrate-dev docker-migrate-prod docs test-medios-pago test-divisas test-simulador local-loaddata local-migrate help
#Variables de los nombres de proyecto para mantener los entornos separados
#Cada miembro del equipo usará el mismo nombre de proyecto, eliminando conflictos.

DEV_PROJECT_NAME = global-exchange-local-dev
PROD_PROJECT_NAME = global-exchange-local-prod


#------------------ Operaciones del Entorno de Producción (Docker) ------------------#

prod-up:
	@echo "Levantando el entorno de producción..."
	docker compose -p $(PROD_PROJECT_NAME) -f docker-compose.prod.yml up --build -d
	@echo "Entorno de producción levantado. Accede en http://localhost"

prod-up-foreground:
	@echo "Levantando el entorno de producción en primer plano (ver logs en terminal)..."
	@echo "Presiona Ctrl+C para detener los contenedores."
	docker compose -p $(PROD_PROJECT_NAME) -f docker-compose.prod.yml up --build

prod-logs:
	@echo "Siguiendo logs del entorno de producción..."
	docker compose -p $(PROD_PROJECT_NAME) -f docker-compose.prod.yml logs -f --tail=200

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
	$(PROD_EXEC) python scripts/setup_system.py

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

	@echo "Migrando la base de datos (local)..."
	poetry run python manage.py migrate
	@echo "Migraciones aplicadas."
	

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

run:
	@echo "Ejecutando el servidor de desarrollo con recarga automática..."
	poetry run python manage.py runserver 
	@echo "Servidor detenido."

test-medios-acreditacion:
	@echo "Ejecutando pruebas de medios de acreditación..."
	poetry run python manage.py test clientes.tests_medios_acreditacion
	@echo "Pruebas completadas."

delete-migrations:
	@echo "Eliminando archivos de migraciones..."
	poetry run python scripts/delete_migrations.py
	@echo "Archivos de migraciones eliminados."

reset-db:
	@echo "Reiniciando la base de datos..."
	
	dropdb --username=django_user  --if-exists global_exchange --host=localhost
	createdb --username=django_user --host=localhost global_exchange 
	
	@echo "Cargando datos de prueba..."
	poetry run python scripts/delete_migrations.py
	poetry run python manage.py makemigrations	
	poetry run python manage.py migrate
	poetry run python scripts/setup_system.py

	@echo "Configurando roles de prueba..."
	poetry run python manage.py sync_permissions
	poetry run python manage.py setup_test_roles --verbose
	poetry run python manage.py sync_role_status
	poetry run python manage.py create_dev_user
	
	@echo "Base de datos reiniciada y datos cargados."

check:
	@echo "Verificando el estado del proyecto..."
	poetry run python manage.py check
	@echo "Verificación completada."

test-fact:
	@echo "Ejecutando pruebas de facturación electrónica..."
	poetry run python manage.py test facturacion_electronica.tests
	@echo "Pruebas de facturación electrónica completadas. "
