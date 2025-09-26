.PHONY: db-up db-clean runserver migrations migrate db-check dbshell app-setup help

#-------------- Operaciones de base de datos ----------------#
db-up:
	@echo "Levantando la base de datos PostgreSQL..."
	docker compose -f docker-compose-dev.yml up -d casa-cambios-db
	@echo "Base de datos levantada correctamente"

db-clean:
	@echo "Limpiando la base de datos y volúmenes..."
	docker compose -f docker-compose-dev.yml down -v --remove-orphans
	@echo "Base de datos y volúmenes limpiados"

#-------------- Comandos DJANGO ----------------#
runserver:
	@echo "Iniciando el servidor de desarrollo Django..."
	python manage.py runserver

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
	@echo "Migrando la base de datos..."
	poetry run python manage.py migrate

db-check:
	@echo "Chequeando conexión a la base de datos..."
	poetry run python db_check.py

dbshell:
	@echo "Abriendo shell de la base de datos..."
	poetry run python manage.py dbshell

shell:
	@echo "Abriendo shell de Django..."
	poetry run python manage.py shell

docs:
	@echo "Generando documentación con Sphinx..."
	poetry run sphinx-build -b html docs/source docs/build
	@echo "Documentación generada en docs/build"

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

docker-loaddata:
	@echo "Cargando datos iniciales..."
	docker exec glx-web python manage.py loaddata roles_data.json
	docker exec glx-web python manage.py loaddata roles_data.json
	docker exec glx-web python manage.py loaddata users_data.json
	docker exec glx-web python manage.py loaddata clientes_data.json
	docker exec glx-web python manage.py loaddata divisas_initial_data.json
#	python manage.py loaddata medios_pago_initial_data.json omitir de momento
	@echo "Datos iniciales cargados."

loaddata:
	@echo "Cargando datos iniciales..."
	poetry run python manage.py loaddata roles_data.json
	poetry run python manage.py loaddata users_data.json
	poetry run python manage.py loaddata clientes_data.json
	poetry run python manage.py loaddata divisas_initial_data.json
#poetry run python manage.py loaddata medios_pago_initial_data.json
	@echo "Datos iniciales cargados."

docker-setup:
	@echo "Configurando la aplicación..."
	docker compose up -d --build
	docker compose -f docker-compose.yml run --rm --no-deps web poetry run python manage.py makemigrations
	docker compose -f docker-compose.yml run --rm --no-deps web poetry run python manage.py migrate

run: 
	@echo "Iniciando la aplicación..."
	poetry run python manage.py runserver
	@echo "Aplicación iniciada."

prod-loaddata:
	@echo "Cargando datos iniciales en producción..."
	docker exec glx-web-prod python manage.py loaddata roles_data.json
	docker exec glx-web-prod python manage.py loaddata users_data.json
	docker exec glx-web-prod python manage.py loaddata clientes_data.json
	docker exec glx-web-prod python manage.py loaddata divisas_initial_data.json
#	python manage.py loaddata medios_pago_initial_data.json omitir de momento
	@echo "Datos iniciales cargados en producción."	

db-init:
	@echo "Inicializando la base de datos..."
	poetry run python manage.py makemigrations
	poetry run python manage.py migrate
	poetry run python manage.py loaddata roles_data.json
	poetry run python manage.py loaddata users_data.json
	poetry run python manage.py loaddata clientes_data.json
	poetry run python manage.py loaddata divisas_initial_data.json
	@echo "Datos cargados."