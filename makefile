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

#-------------- Configuración del proyecto ----------------#
app-setup:
	@echo "Configurando el proyecto Django..."
	make db-clean
	make db-up
	sleep 5
	make migrate
	@echo "Proyecto configurado correctamente"

help:
	@echo "Comandos disponibles:"
	@echo "  db-up        - Levanta PostgreSQL en Docker"
	@echo "  db-clean     - Limpia base de datos y volúmenes"
	@echo "  runserver    - Inicia Django localmente"
	@echo "  migrations   - Crea migraciones"
	@echo "  migrate      - Aplica migraciones"
	@echo "  db-check     - Verifica conexión a la base de datos"
	@echo "  dbshell      - Abre shell de PostgreSQL"
	@echo "  app-setup    - Configuración inicial completa"

fresh-setup:
	@echo "Configurando el proyecto Django desde cero..."
	make db-clean
	make db-up
	sleep 5
	poetry run python reset_migrations.py
	make migrate
	@echo "Proyecto configurado correctamente"