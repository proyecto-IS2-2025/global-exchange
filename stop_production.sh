#!/bin/bash

################################################################################
# Script de Detención Completa - Entorno de Producción
# Global Exchange - Casa de Cambios
################################################################################
#
# Este script detiene el entorno completo de producción incluyendo:
# 1. Global Exchange - Aplicación Django en producción
# 2. SQL Proxy (Factura Segura) - 4 contenedores Docker
#
# Uso: bash stop_production.sh
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

# Detener Global Exchange
stop_global_exchange() {
    print_header "Deteniendo Global Exchange (Producción)"
    
    cd "$GLOBAL_EXCHANGE_DIR"
    
    print_step "Ejecutando: make prod-down"
    if make prod-down 2>/dev/null; then
        print_success "Global Exchange detenido correctamente"
    else
        print_warning "Global Exchange no estaba corriendo o ya fue detenido"
    fi
}

# Detener SQL Proxy
stop_sql_proxy() {
    print_header "Deteniendo SQL Proxy (Factura Segura)"
    
    cd "$SQL_PROXY_DIR"
    
    print_step "Deteniendo contenedores de SQL Proxy..."
    if docker compose -f docker-compose.test.yml down 2>/dev/null; then
        print_success "SQL Proxy detenido correctamente"
    else
        print_warning "SQL Proxy no estaba corriendo o ya fue detenido"
    fi
}

# Verificar que todo esté detenido
verify_stopped() {
    print_header "Verificación Final"
    
    local containers_running=$(docker ps --filter "name=sql-proxy01" --filter "name=global-exchange-local-prod" --format '{{.Names}}' | wc -l)
    
    if [ "$containers_running" -eq 0 ]; then
        print_success "Todos los contenedores han sido detenidos"
    else
        print_warning "Algunos contenedores aún están corriendo:"
        docker ps --filter "name=sql-proxy01" --filter "name=global-exchange-local-prod" --format "  - {{.Names}}: {{.Status}}"
    fi
}

# Función principal
main() {
    clear
    
    print_header "🛑 Detención Completa - Entorno de Producción"
    echo -e "${YELLOW}Global Exchange - Casa de Cambios${NC}"
    echo ""
    
    # Preguntar confirmación
    echo -e "${YELLOW}Este script detendrá:${NC}"
    echo "  1. Global Exchange Producción (todos los contenedores)"
    echo "  2. SQL Proxy (todos los contenedores)"
    echo ""
    read -p "¿Desea continuar? (s/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        print_warning "Operación cancelada por el usuario"
        exit 0
    fi
    
    # Ejecutar pasos
    stop_global_exchange
    stop_sql_proxy
    verify_stopped
    
    # Mensaje final
    print_header "✅ Sistema de Producción Detenido"
    
    echo -e "${GREEN}Todos los servicios han sido detenidos.${NC}"
    echo ""
    echo -e "${CYAN}Para reiniciar el sistema:${NC}"
    echo -e "  ${YELLOW}bash start_production.sh${NC}"
    echo ""
}

# Ejecutar script
main "$@"
