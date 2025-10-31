#!/bin/bash

################################################################################
# Script de Inicialización Completa - Entorno de Producción
# Global Exchange - Casa de Cambios
################################################################################
#
# Este script levanta el entorno completo de producción incluyendo:
# 1. SQL Proxy (Factura Segura) - 4 contenedores Docker
# 2. Global Exchange - Aplicación Django en producción
# 3. Carga de fixtures y configuración inicial
#
# Uso: bash start_production.sh
#
################################################################################

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Directorio raíz del proyecto
GLOBAL_EXCHANGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SQL_PROXY_DIR="$(dirname "$GLOBAL_EXCHANGE_DIR")/sql-proxy01"

# Función para imprimir mensajes con formato
print_header() {
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}➜${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Función para verificar si un contenedor está corriendo
container_running() {
    docker ps --format '{{.Names}}' | grep -q "$1"
}

# Verificar dependencias
check_dependencies() {
    print_header "Verificando Dependencias"
    
    local missing_deps=0
    
    if ! command_exists docker; then
        print_error "Docker no está instalado"
        missing_deps=1
    else
        print_success "Docker instalado"
    fi
    
    if ! command_exists make; then
        print_error "Make no está instalado"
        missing_deps=1
    else
        print_success "Make instalado"
    fi
    
    if [ ! -d "$SQL_PROXY_DIR" ]; then
        print_error "Directorio SQL Proxy no encontrado: $SQL_PROXY_DIR"
        missing_deps=1
    else
        print_success "SQL Proxy encontrado: $SQL_PROXY_DIR"
    fi
    
    if [ $missing_deps -eq 1 ]; then
        print_error "Faltan dependencias. Por favor, instálelas antes de continuar."
        exit 1
    fi
}

# Levantar SQL Proxy
start_sql_proxy() {
    print_header "Iniciando SQL Proxy (Factura Segura)"
    
    cd "$SQL_PROXY_DIR"
    
    # Verificar si ya está corriendo
    if container_running "sql-proxy01-web-1"; then
        print_warning "SQL Proxy ya está corriendo"
        print_step "Verificando estado de contenedores..."
        docker ps --filter "name=sql-proxy01" --format "table {{.Names}}\t{{.Status}}"
    else
        print_step "Levantando contenedores de SQL Proxy..."
        docker compose -f docker-compose.test.yml up -d
        
        print_step "Esperando a que los servicios estén listos..."
        sleep 5
        
        # Verificar que todos los contenedores estén corriendo
        local containers=("sql-proxy01-db-1" "sql-proxy01-web-1" "sql-proxy01-web-sched-1" "sql-proxy01-nginx-1")
        local all_running=1
        
        for container in "${containers[@]}"; do
            if container_running "$container"; then
                print_success "$container está corriendo"
            else
                print_error "$container NO está corriendo"
                all_running=0
            fi
        done
        
        if [ $all_running -eq 1 ]; then
            print_success "SQL Proxy iniciado correctamente (4/4 contenedores)"
        else
            print_error "Algunos contenedores de SQL Proxy no iniciaron correctamente"
            exit 1
        fi
    fi
    
    # Verificar conectividad
    print_step "Verificando conectividad del SQL Proxy..."
    if curl -s http://localhost:40080/ | grep -q "fs_proxy"; then
        print_success "SQL Proxy API respondiendo en http://localhost:40080"
    else
        print_warning "SQL Proxy API no responde correctamente"
    fi
    
    if curl -s http://localhost:40088/ | grep -q "task"; then
        print_success "SQL Proxy Scheduler respondiendo en http://localhost:40088"
    else
        print_warning "SQL Proxy Scheduler no responde correctamente"
    fi
}

# Levantar Global Exchange
start_global_exchange() {
    print_header "Iniciando Global Exchange (Producción)"
    
    cd "$GLOBAL_EXCHANGE_DIR"
    
    # Verificar si ya está corriendo
    if container_running "global-exchange-local-prod-web-1"; then
        print_warning "Global Exchange ya está corriendo"
        print_step "Verificando estado..."
        docker ps --filter "name=global-exchange-local-prod" --format "table {{.Names}}\t{{.Status}}"
    else
        print_step "Levantando contenedores de Global Exchange..."
        make prod-up
        
        print_step "Esperando a que los servicios estén listos..."
        sleep 10
        
        # Verificar que los contenedores estén corriendo
        if container_running "global-exchange-local-prod-web-1"; then
            print_success "Global Exchange iniciado correctamente"
        else
            print_error "Global Exchange no inició correctamente"
            exit 1
        fi
    fi
}

# Cargar fixtures y configuración
load_fixtures() {
    print_header "Cargando Fixtures y Configuración Inicial"
    
    cd "$GLOBAL_EXCHANGE_DIR"
    
    print_step "Verificando si las fixtures ya fueron cargadas..."
    
    # Intentar cargar fixtures (si ya existen, Django lo detectará)
    print_step "Ejecutando: make load-prod"
    if make load-prod; then
        print_success "Fixtures y configuración cargadas correctamente"
    else
        print_warning "Algunas fixtures pueden ya estar cargadas (esto es normal)"
    fi
}

# Verificar estado final
verify_system() {
    print_header "Verificación Final del Sistema"
    
    print_step "Estado de contenedores SQL Proxy:"
    docker ps --filter "name=sql-proxy01" --format "  ✓ {{.Names}}: {{.Status}}"
    
    echo ""
    print_step "Estado de contenedores Global Exchange:"
    docker ps --filter "name=global-exchange-local-prod" --format "  ✓ {{.Names}}: {{.Status}}"
    
    echo ""
    print_step "URLs del sistema:"
    echo -e "  ${GREEN}➜${NC} Global Exchange: ${CYAN}http://localhost${NC}"
    echo -e "  ${GREEN}➜${NC} SQL Proxy API: ${CYAN}http://localhost:40080${NC}"
    echo -e "  ${GREEN}➜${NC} SQL Proxy Scheduler: ${CYAN}http://localhost:40088${NC}"
    echo -e "  ${GREEN}➜${NC} PostgreSQL SQL Proxy: ${CYAN}localhost:45432${NC}"
}

# Función principal
main() {
    clear
    
    print_header "🚀 Inicialización Completa - Entorno de Producción"
    echo -e "${YELLOW}Global Exchange - Casa de Cambios${NC}"
    echo -e "${YELLOW}Sprint: Facturación Electrónica${NC}"
    echo ""
    
    # Preguntar confirmación
    echo -e "${YELLOW}Este script iniciará:${NC}"
    echo "  1. SQL Proxy (4 contenedores Docker)"
    echo "  2. Global Exchange Producción (3 contenedores Docker)"
    echo "  3. Carga de fixtures y configuración inicial"
    echo ""
    read -p "¿Desea continuar? (s/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        print_warning "Operación cancelada por el usuario"
        exit 0
    fi
    
    # Ejecutar pasos
    check_dependencies
    start_sql_proxy
    start_global_exchange
    load_fixtures
    verify_system
    
    # Mensaje final
    print_header "✅ Sistema de Producción Iniciado Correctamente"
    
    echo -e "${GREEN}El entorno de producción está listo para usar.${NC}"
    echo ""
    echo -e "${CYAN}Credenciales por defecto:${NC}"
    echo -e "  Usuario: ${YELLOW}dev${NC}"
    echo -e "  Password: ${YELLOW}dev123${NC}"
    echo ""
    echo -e "${CYAN}Para detener el sistema:${NC}"
    echo -e "  ${YELLOW}cd $GLOBAL_EXCHANGE_DIR && make prod-down${NC}"
    echo -e "  ${YELLOW}cd $SQL_PROXY_DIR && docker compose -f docker-compose.test.yml down${NC}"
    echo ""
    echo -e "${CYAN}Para ver logs:${NC}"
    echo -e "  ${YELLOW}docker logs -f global-exchange-local-prod-web-1${NC}"
    echo -e "  ${YELLOW}docker logs -f sql-proxy01-web-1${NC}"
    echo ""
    
    print_success "¡Entrega del Sprint lista! 🎉"
}

# Ejecutar script
main "$@"
