# Makefile para Django con Docker
# ===================================

.PHONY: help build up down logs shell migrate makemigrations createsuperuser collectstatic test clean reset dev prod restart status

# Variables
COMPOSE_FILE = docker-compose.yml
SERVICE_WEB = web
SERVICE_DB = db

# Detectar sistema operativo para colores
UNAME_S := $(shell uname -s 2>/dev/null || echo Windows)
ifeq ($(UNAME_S),Windows_NT)
	# Windows - sin colores para evitar caracteres extraños
	GREEN = 
	YELLOW = 
	RED = 
	NC = 
else
	# Unix/Linux/Mac - con colores
	GREEN = \033[0;32m
	YELLOW = \033[1;33m
	RED = \033[0;31m
	NC = \033[0m
endif

# Comando por defecto
help: ## Mostrar esta ayuda
	@echo "$(GREEN)Comandos disponibles:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ===================================
# COMANDOS DE CONFIGURACIÓN INICIAL
# ===================================

build: ## Construir las imágenes Docker
	@echo "$(GREEN)🐳 Construyendo imágenes Docker...$(NC)"
	docker-compose build

setup: build ## Configuración inicial completa (primera vez)
	@echo "$(GREEN)🚀 Configuración inicial...$(NC)"
	@$(MAKE) db-wait
	@$(MAKE) migrate
	@$(MAKE) createsuperuser-optional
	@echo "$(GREEN)✅ Configuración completada!$(NC)"
	@echo "$(YELLOW)Ejecuta 'make dev' para iniciar el desarrollo$(NC)"

# ===================================
# COMANDOS DE DESARROLLO DIARIO
# ===================================

dev: migrate up ## Ejecutar migraciones y iniciar en modo desarrollo
	@echo "$(GREEN)🎉 Servidor de desarrollo iniciado!$(NC)"

up: ## Iniciar todos los servicios
	@echo "$(GREEN)🚀 Iniciando servicios...$(NC)"
	docker-compose up

up-d: ## Iniciar servicios en segundo plano
	@echo "$(GREEN)🚀 Iniciando servicios en segundo plano...$(NC)"
	docker-compose up -d

down: ## Detener todos los servicios
	@echo "$(YELLOW)🛑 Deteniendo servicios...$(NC)"
	docker-compose down

restart: down up-d ## Reiniciar todos los servicios
	@echo "$(GREEN)🔄 Servicios reiniciados$(NC)"

# ===================================
# COMANDOS DE BASE DE DATOS
# ===================================

migrate: ## Ejecutar migraciones
	@echo "$(GREEN)📊 Ejecutando migraciones...$(NC)"
	docker-compose run --rm $(SERVICE_WEB) python manage.py makemigrations
	docker-compose run --rm $(SERVICE_WEB) python manage.py migrate

makemigrations: ## Crear nuevas migraciones
	@echo "$(GREEN)📝 Creando migraciones...$(NC)"
	docker-compose run --rm $(SERVICE_WEB) python manage.py makemigrations

db-reset: ## ⚠️ PELIGROSO: Resetear completamente la base de datos
	@echo "$(RED)⚠️  CUIDADO: Esto eliminará TODOS los datos$(NC)"
	@echo "¿Estás seguro? [y/N]" && read ans && [ ${ans:-N} = y ]
	@$(MAKE) down
	docker-compose down -v
	docker volume prune -f
	@$(MAKE) setup

db-wait: ## Esperar a que la base de datos esté lista
	@echo "$(YELLOW)⏳ Esperando a que la base de datos esté lista...$(NC)"
	@docker-compose up -d $(SERVICE_DB)
	@until docker-compose exec -T $(SERVICE_DB) pg_isready -U $${DB_USER:-postgres} -d $${DB_NAME:-mi_proyecto_db}; do \
		echo "$(YELLOW)Esperando a la DB...$(NC)"; \
		sleep 2; \
	done
	@echo "$(GREEN)✅ Base de datos lista!$(NC)"

# ===================================
# COMANDOS DE DJANGO
# ===================================

shell: ## Acceder al shell de Django
	docker-compose run --rm $(SERVICE_WEB) python manage.py shell

shell-plus: ## Acceder al shell plus de Django (si tienes django-extensions)
	docker-compose run --rm $(SERVICE_WEB) python manage.py shell_plus

createsuperuser: ## Crear un superusuario
	docker-compose run --rm $(SERVICE_WEB) python manage.py createsuperuser

createsuperuser-optional: ## Crear superusuario (opcional)
	@echo "$(YELLOW)¿Quieres crear un superusuario? [y/N]$(NC)" && \
	read ans && [ ${ans:-N} = y ] && $(MAKE) createsuperuser || echo "$(YELLOW)Saltando creación de superusuario$(NC)"

collectstatic: ## Recopilar archivos estáticos
	docker-compose run --rm $(SERVICE_WEB) python manage.py collectstatic --noinput

# ===================================
# COMANDOS DE TESTING Y CALIDAD
# ===================================

test: ## Ejecutar tests
	@echo "$(GREEN)🧪 Ejecutando tests...$(NC)"
	docker-compose run --rm $(SERVICE_WEB) python manage.py test

test-coverage: ## Ejecutar tests con coverage
	@echo "$(GREEN)📊 Ejecutando tests con coverage...$(NC)"
	docker-compose run --rm $(SERVICE_WEB) coverage run --source='.' manage.py test
	docker-compose run --rm $(SERVICE_WEB) coverage report
	docker-compose run --rm $(SERVICE_WEB) coverage html

test-verbose: ## Ejecutar tests con output detallado
	docker-compose run --rm $(SERVICE_WEB) python manage.py test --verbosity=2

lint: ## Ejecutar linting (requiere flake8 en requirements)
	docker-compose run --rm $(SERVICE_WEB) flake8 .

# ===================================
# COMANDOS DE LOGS Y DEBUGGING
# ===================================

logs: ## Ver logs de todos los servicios
	docker-compose logs -f

logs-web: ## Ver logs solo del servicio web
	docker-compose logs -f $(SERVICE_WEB)

logs-db: ## Ver logs solo de la base de datos
	docker-compose logs -f $(SERVICE_DB)

bash: ## Acceder al contenedor web con bash
	docker-compose exec $(SERVICE_WEB) bash

bash-run: ## Ejecutar nuevo contenedor web con bash
	docker-compose run --rm $(SERVICE_WEB) bash

# ===================================
# COMANDOS DE LIMPIEZA
# ===================================

clean: ## Limpiar contenedores e imágenes no usadas
	@echo "$(YELLOW)🧹 Limpiando contenedores e imágenes...$(NC)"
	docker system prune -f

clean-all: ## Limpieza completa (incluyendo volúmenes)
	@echo "$(RED)🗑️  Limpieza completa...$(NC)"
	@make down
	docker system prune -af
	docker volume prune -f

# ===================================
# COMANDOS DE ESTADO Y INFORMACIÓN
# ===================================

status: ## Mostrar estado de los contenedores
	@echo "$(GREEN)📊 Estado de los contenedores:$(NC)"
	docker-compose ps

ps: status ## Alias para status

top: ## Mostrar procesos de los contenedores
	docker-compose top

# ===================================
# COMANDOS DE PRODUCCIÓN
# ===================================

build-prod: ## Construir para producción
	@echo "$(GREEN)🏭 Construyendo para producción...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

prod: ## Ejecutar en modo producción (con nginx)
	@echo "$(GREEN)🏭 Iniciando en modo producción...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-logs: ## Ver logs de producción
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

prod-down: ## Detener producción
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

prod-restart: prod-down prod ## Reiniciar producción

nginx-reload: ## Recargar configuración de nginx (solo en producción)
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec nginx nginx -s reload

nginx-test: ## Probar configuración de nginx
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec nginx nginx -t

# ===================================
# COMANDOS DE UTILIDAD
# ===================================

requirements: ## Generar requirements.txt desde el contenedor
	docker-compose run --rm $(SERVICE_WEB) pip freeze > requirements.txt

backup-db: ## Backup de la base de datos
	@echo "$(GREEN)💾 Creando backup de la base de datos...$(NC)"
	docker-compose exec $(SERVICE_DB) pg_dump -U $${DB_USER:-postgres} $${DB_NAME:-mi_proyecto_db} > backup_$$(date +%Y%m%d_%H%M%S).sql

restore-db: ## Restaurar base de datos (especifica el archivo con FILE=backup.sql)
	@echo "$(YELLOW)📥 Restaurando base de datos desde $(FILE)...$(NC)"
	docker-compose exec -T $(SERVICE_DB) psql -U $${DB_USER:-postgres} $${DB_NAME:-mi_proyecto_db} < $(FILE)

# ===================================
# COMANDOS AVANZADOS
# ===================================

django-cmd: ## Ejecutar comando personalizado de Django (uso: make django-cmd CMD="comando")
	docker-compose run --rm $(SERVICE_WEB) python manage.py $(CMD)

pip-install: ## Instalar paquete de Python (uso: make pip-install PKG="paquete")
	docker-compose run --rm $(SERVICE_WEB) pip install $(PKG)
	@echo "$(YELLOW)No olvides actualizar requirements.txt con 'make requirements'$(NC)"
	@echo "$(YELLOW)Reconstruyendo imagen si es necesario...$(NC)"
	@$(MAKE) build

# ===================================
# SHORTCUTS (comandos cortos)
# ===================================

u: up ## Shortcut para 'up'
d: down ## Shortcut para 'down'  
b: build ## Shortcut para 'build'
m: migrate ## Shortcut para 'migrate'
s: shell ## Shortcut para 'shell'
l: logs ## Shortcut para 'logs'
t: test ## Shortcut para 'test'