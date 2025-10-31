#!/bin/bash
# Script para hacer una prueba completa del sistema de facturación

echo "======================================================================"
echo "PRUEBA COMPLETA DEL SISTEMA DE FACTURACIÓN ELECTRÓNICA"
echo "======================================================================"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd /home/jose/proyecto_is2/global-exchange

# 1. Verificar conexión al SQL Proxy
echo "1. Verificando conexión al SQL Proxy..."
python3 facturacion_electronica/test_conexion.py
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Prueba fallida: No se pudo conectar al SQL Proxy${NC}"
    echo ""
    echo "Solución:"
    echo "  cd /home/jose/proyecto_is2/sql-proxy01"
    echo "  docker compose -f docker-compose.test.yml up -d"
    exit 1
fi

echo ""
echo "======================================================================"
echo ""

# 2. Generar factura de prueba
echo "2. Generando factura de prueba..."
python3 facturacion_electronica/ejemplo_uso.py

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================================================"
    echo -e "${GREEN}✓✓✓ PRUEBA EXITOSA ✓✓✓${NC}"
    echo "======================================================================"
    echo ""
    echo "Ahora puedes:"
    echo ""
    echo "1. Ver las facturas generadas en:"
    echo "   http://localhost:40080/kude/"
    echo "   Usuario: sqlproxy"
    echo "   Contraseña: kude1234"
    echo ""
    echo "2. Levantar tu servidor Django:"
    echo "   python manage.py runserver"
    echo ""
    echo "3. Generar facturas desde transacciones:"
    echo "   Ver ejemplos en facturacion_electronica/utils.py"
    echo ""
else
    echo ""
    echo -e "${RED}✗ Error al generar factura de prueba${NC}"
    echo ""
    echo "Revisa los logs anteriores para ver el error"
fi

