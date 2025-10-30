#!/bin/bash
# Script para verificar y levantar todo el sistema de facturación electrónica

echo "======================================================================"
echo "VERIFICACIÓN Y LEVANTAMIENTO DEL SISTEMA DE FACTURACIÓN ELECTRÓNICA"
echo "======================================================================"
echo ""

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Verificar Docker
echo "1. Verificando Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker no está instalado${NC}"
    exit 1
fi

if ! docker ps &> /dev/null; then
    echo -e "${RED}✗ Docker no está ejecutándose${NC}"
    echo "   Inicia Docker Desktop o el servicio de Docker"
    exit 1
fi

echo -e "${GREEN}✓ Docker está funcionando${NC}"
echo ""

# 2. Levantar SQL Proxy
echo "2. Levantando SQL Proxy..."
cd /home/jose/proyecto_is2/sql-proxy01

# Detener contenedores previos
echo "   Deteniendo contenedores previos..."
docker compose -f docker-compose.test.yml down 2>/dev/null

# Levantar contenedores
echo "   Levantando contenedores..."
docker compose -f docker-compose.test.yml up -d

# Esperar a que los contenedores estén listos
echo "   Esperando a que los servicios estén listos (15 segundos)..."
sleep 15

# Verificar que los contenedores estén corriendo
CONTAINERS=$(docker compose -f docker-compose.test.yml ps --filter "status=running" | grep -c "Up")

if [ "$CONTAINERS" -lt 4 ]; then
    echo -e "${RED}✗ No todos los contenedores están corriendo${NC}"
    echo "   Ejecuta: docker compose -f docker-compose.test.yml logs"
    exit 1
fi

echo -e "${GREEN}✓ SQL Proxy levantado correctamente${NC}"
echo ""

# 3. Verificar conexión al SQL Proxy
echo "3. Verificando conexión al SQL Proxy..."
cd /home/jose/proyecto_is2/global-exchange

python3 facturacion_electronica/test_conexion.py
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ No se pudo conectar al SQL Proxy${NC}"
    exit 1
fi

echo ""

# 4. Verificar que psycopg2 esté instalado
echo "4. Verificando dependencias Python..."
python3 -c "import psycopg2" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠ psycopg2 no está instalado${NC}"
    echo "   Instalando..."
    pip install psycopg2-binary
fi
echo -e "${GREEN}✓ Dependencias instaladas${NC}"
echo ""

# 5. Levantar servidor Django
echo "5. Levantando servidor Django..."
echo -e "${YELLOW}   El servidor se levantará en: http://localhost:8000${NC}"
echo -e "${YELLOW}   Presiona Ctrl+C para detener${NC}"
echo ""
echo "======================================================================"
echo ""

# Ir al directorio de Django y levantar el servidor
cd /home/jose/proyecto_is2/global-exchange
python manage.py runserver

