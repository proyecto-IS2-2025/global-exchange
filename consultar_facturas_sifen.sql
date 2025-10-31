-- ============================================================================
-- CONSULTA DE FACTURAS ELECTRÓNICAS EN SIFEN
-- ============================================================================
-- Este script consulta directamente la base de datos para obtener información
-- sobre las facturas electrónicas ya generadas.
-- 
-- USO:
-- 1. Conectarse al SQL Proxy o a la base de datos de producción
-- 2. Ejecutar estas consultas para ver el estado actual
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. ÚLTIMA FACTURA GENERADA (CUALQUIER ESTADO)
-- ----------------------------------------------------------------------------
SELECT 
    numero_factura,
    establecimiento,
    punto_expedicion,
    cdc,
    estado_sifen,
    fecha_emision,
    monto_total,
    cliente_nombre
FROM facturacion_electronica_facturaelectronica
ORDER BY numero_factura DESC
LIMIT 1;

-- ----------------------------------------------------------------------------
-- 2. ÚLTIMO NÚMERO DE FACTURA APROBADA
-- ----------------------------------------------------------------------------
SELECT 
    numero_factura,
    establecimiento,
    punto_expedicion,
    cdc,
    estado_sifen,
    fecha_emision,
    monto_total
FROM facturacion_electronica_facturaelectronica
WHERE estado_sifen IN ('Aprobado', 'Aprobado con observación')
ORDER BY numero_factura DESC
LIMIT 1;

-- ----------------------------------------------------------------------------
-- 3. CONTAR FACTURAS POR ESTADO
-- ----------------------------------------------------------------------------
SELECT 
    estado_sifen,
    COUNT(*) as cantidad,
    MIN(numero_factura) as numero_minimo,
    MAX(numero_factura) as numero_maximo
FROM facturacion_electronica_facturaelectronica
GROUP BY estado_sifen
ORDER BY estado_sifen;

-- ----------------------------------------------------------------------------
-- 4. ÚLTIMAS 20 FACTURAS GENERADAS (RESUMEN)
-- ----------------------------------------------------------------------------
SELECT 
    numero_factura,
    estado_sifen,
    fecha_emision,
    monto_total,
    cdc,
    CASE 
        WHEN estado_sifen = 'Aprobado' THEN '✅'
        WHEN estado_sifen = 'Aprobado con observación' THEN '⚠️'
        WHEN estado_sifen = 'Rechazado' THEN '❌'
        WHEN estado_sifen = 'ENVIADO_A_SIFEN' THEN '📤'
        WHEN estado_sifen = 'SOL.APROBACION' THEN '⏳'
        ELSE '❓'
    END as icono_estado
FROM facturacion_electronica_facturaelectronica
ORDER BY numero_factura DESC
LIMIT 20;

-- ----------------------------------------------------------------------------
-- 5. RANGO DE NÚMEROS DISPONIBLES
-- ----------------------------------------------------------------------------
-- Esta consulta identifica "huecos" en la numeración
-- (números que no fueron utilizados entre facturas existentes)
WITH numeros_usados AS (
    SELECT CAST(numero_factura AS INTEGER) as num
    FROM facturacion_electronica_facturaelectronica
    WHERE numero_factura ~ '^[0-9]+$'  -- Solo números válidos
)
SELECT 
    MIN(num) as primer_numero_usado,
    MAX(num) as ultimo_numero_usado,
    MAX(num) + 1 as proximo_numero_sugerido,
    COUNT(*) as total_facturas,
    MAX(num) - MIN(num) + 1 - COUNT(*) as numeros_saltados
FROM numeros_usados;

-- ----------------------------------------------------------------------------
-- 6. VERIFICAR SI UN NÚMERO ESPECÍFICO YA EXISTE
-- ----------------------------------------------------------------------------
-- Reemplaza '0000051' con el número que quieres verificar
SELECT 
    numero_factura,
    estado_sifen,
    cdc,
    fecha_emision,
    monto_total,
    CASE 
        WHEN numero_factura = '0000051' THEN '⚠️ ESTE NÚMERO YA EXISTE'
        ELSE 'OK'
    END as verificacion
FROM facturacion_electronica_facturaelectronica
WHERE numero_factura = '0000051';

-- ----------------------------------------------------------------------------
-- 7. FACTURAS GENERADAS HOY
-- ----------------------------------------------------------------------------
SELECT 
    numero_factura,
    estado_sifen,
    fecha_emision,
    monto_total,
    cliente_nombre
FROM facturacion_electronica_facturaelectronica
WHERE DATE(fecha_emision) = CURRENT_DATE
ORDER BY fecha_emision DESC;

-- ----------------------------------------------------------------------------
-- 8. FACTURAS POR DÍA (ÚLTIMOS 7 DÍAS)
-- ----------------------------------------------------------------------------
SELECT 
    DATE(fecha_emision) as fecha,
    COUNT(*) as cantidad_facturas,
    COUNT(CASE WHEN estado_sifen = 'Aprobado' THEN 1 END) as aprobadas,
    COUNT(CASE WHEN estado_sifen = 'Rechazado' THEN 1 END) as rechazadas,
    MIN(numero_factura) as numero_min,
    MAX(numero_factura) as numero_max
FROM facturacion_electronica_facturaelectronica
WHERE fecha_emision >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(fecha_emision)
ORDER BY fecha DESC;

-- ----------------------------------------------------------------------------
-- 9. EXPORTAR INFORMACIÓN PARA COORDINACIÓN DEL EQUIPO
-- ----------------------------------------------------------------------------
-- Esta consulta genera información útil para coordinar entre desarrolladores
SELECT 
    '=== INFORMACIÓN PARA COORDINACIÓN DE EQUIPO ===' as titulo
UNION ALL
SELECT CONCAT('Último número usado: ', MAX(numero_factura))
FROM facturacion_electronica_facturaelectronica
UNION ALL
SELECT CONCAT('Próximo número disponible: ', LPAD(CAST(MAX(CAST(numero_factura AS INTEGER)) + 1 AS TEXT), 7, '0'))
FROM facturacion_electronica_facturaelectronica
WHERE numero_factura ~ '^[0-9]+$'
UNION ALL
SELECT CONCAT('Total de facturas: ', COUNT(*))
FROM facturacion_electronica_facturaelectronica
UNION ALL
SELECT CONCAT('Facturas aprobadas: ', COUNT(*))
FROM facturacion_electronica_facturaelectronica
WHERE estado_sifen IN ('Aprobado', 'Aprobado con observación');

-- ============================================================================
-- INSTRUCCIONES DE USO
-- ============================================================================
-- 
-- OPCIÓN 1: Desde Docker (SQL Proxy)
-- docker exec -it sql-proxy01-db-1 psql -U postgres -d fs_db -f /ruta/a/este/archivo.sql
-- 
-- OPCIÓN 2: Desde psql local
-- psql -h localhost -p 45432 -U postgres -d fs_db -f consultar_facturas_sifen.sql
-- 
-- OPCIÓN 3: Desde Django shell
-- python manage.py dbshell < consultar_facturas_sifen.sql
-- 
-- OPCIÓN 4: Copiar y pegar consultas individuales en tu cliente SQL favorito
-- 
-- ============================================================================
