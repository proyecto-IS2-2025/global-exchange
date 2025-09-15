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

cargar-datos:
	@echo "Cargando datos iniciales..."
	python manage.py loaddata roles_data.json
	python manage.py loaddata users_data.json
	python manage.py loaddata clientes_data.json
	python manage.py loaddata divisas_initial_data.json
	python manage.py loaddata medios_pago_initial_data.json
	@echo "Datos iniciales cargados."
