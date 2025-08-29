.PHONY: db-up db-clean app-run app-migrate check-admin-group app-setup user user-fast app-reset help docs-html docs-clean docs-live app-test

#-------------- Operaciones de base de datos ----------------#
db-up:
	@echo "Levantando la base de datos PostgreSQL..."
	docker compose -f docker-compose-dev.yml up -d glx-db
	@echo "Base de datos levantada correctamente"

db-clean:
	@echo "Limpiando la base de datos y volúmenes..."
	docker compose -f docker-compose-dev.yml down -v --remove-orphans
	@echo "Base de datos y volúmenes limpiados"

#-------------- Comandos DJANGO ----------------#
app-run:
	@echo "Iniciando el servidor de desarrollo Django..."
	poetry run python manage.py runserver

app-migrate:
	@echo "Aplicando migraciones de la base de datos..."
	poetry run python manage.py migrate
	@echo "Migraciones aplicadas correctamente"

check-admin-group:
	@echo "Verificando grupo Admin del sistema..."
	poetry run python scripts/check_admin_group.py

app-setup:
	@echo "Configurando el proyecto Django..."
	make db-clean
	make db-up
	sleep 5
	make app-migrate
#make check-admin-group

#-------------- Comandos de administración ----------------#

user:
	@echo "Creando usuario de desarrollo..."
	@if [ "$(OS)" = "Windows_NT" ]; then \
		scripts/create_user.bat $(filter-out $@,$(MAKECMDGOALS)); \
	else \
		scripts/create_user.sh $(filter-out $@,$(MAKECMDGOALS)); \
	fi

user-fast:
	@echo "Creando usuario de desarrollo (modo rápido)..."
	@if [ "$(OS)" = "Windows_NT" ]; then \
		scripts/create_user.bat $(filter-out $@,$(MAKECMDGOALS)) -f; \
	else \
		scripts/create_user.sh $(filter-out $@,$(MAKECMDGOALS)) -f; \
	fi

# Regla especial para manejar argumentos del comando user
%:
	@if [ "$@" != "user" ] && echo "$(MAKECMDGOALS)" | grep -q "^user "; then \
		true; \
	fi

#-------------- App tests ----------------#
app-test:
	@echo "Ejecutando todos los tests del proyecto..."
	poetry run python manage.py test -v 2
	@echo "Tests completados"