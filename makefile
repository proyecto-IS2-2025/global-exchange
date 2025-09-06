runserver:
	@echo "Iniciando el servidor de desarrollo Django..."
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
	@echo "Migrando la base de datos..."
	poetry run python manage.py migrate

db-check:
	@echo "Chequeando conexión a la base de datos..."
	poetry run python db_check.py

dbshell:
	@echo "Abriendo shell de la base de datos..."
	poetry run python manage.py dbshell

tests:
	@echo "Ejecutando tests..."
	poetry run python manage.py test medios_pago.tests.MedioDePagoModelTest medios_pago.tests.CampoMedioDePagoModelTest medios_pago.tests.EdgeCasesTest -v 2
	@echo "Tests completados."