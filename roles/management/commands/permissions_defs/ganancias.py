"""
Definiciones de permisos personalizados para la app 'ganancias'.

ARQUITECTURA DE PERMISOS:
- Nivel 1 (Bajo riesgo): Solo visualización básica
- Nivel 2 (Medio riesgo): Visualización de reportes detallados
- Nivel 3 (Alto riesgo): Exportación y actualización de datos
"""

PERMISOS_GANANCIAS = [
    # ═══════════════════════════════════════════════════════════════════
    # NIVEL 1: VISUALIZACIÓN DEL TABLERO (MEDIO RIESGO)
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'ganancias',
        'model': 'registroganancia',
        'codename': 'view_tablero_ganancias',
        'name': 'Puede ver el tablero de ganancias',
        'modulo': 'ganancias',
        'descripcion': 'Permite acceder al dashboard principal de ganancias con métricas y gráficos.',
        'ejemplo': 'Un administrador consulta las ganancias del mes en el tablero.',
        'nivel_riesgo': 'medio',
        'orden': 10,
        'categoria': 'visualizacion_ganancias',
        'requiere_auditoria': False,
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # NIVEL 2: COMPARACIÓN DE PERÍODOS (MEDIO RIESGO)
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'ganancias',
        'model': 'registroganancia',
        'codename': 'view_comparacion_ganancias',
        'name': 'Puede ver comparación de ganancias',
        'modulo': 'ganancias',
        'descripcion': 'Permite comparar ganancias entre diferentes períodos de tiempo.',
        'ejemplo': 'Un supervisor compara las ganancias del mes actual vs el mes anterior.',
        'nivel_riesgo': 'medio',
        'orden': 20,
        'categoria': 'visualizacion_ganancias',
        'requiere_auditoria': False,
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # NIVEL 3: EXPORTACIÓN DE REPORTES (ALTO RIESGO)
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'ganancias',
        'model': 'registroganancia',
        'codename': 'export_ganancias',
        'name': 'Puede exportar reportes de ganancias',
        'modulo': 'ganancias',
        'descripcion': 'Permite descargar reportes de ganancias en formato Excel.',
        'ejemplo': 'Un administrador exporta el reporte de ganancias para auditoría.',
        'nivel_riesgo': 'alto',
        'orden': 30,
        'categoria': 'exportacion_ganancias',
        'requiere_auditoria': True,
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # NIVEL 4: ACTUALIZACIÓN DE CÁLCULOS (ALTO RIESGO)
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'ganancias',
        'model': 'registroganancia',
        'codename': 'actualizar_ganancias',
        'name': 'Puede actualizar cálculos de ganancias',
        'modulo': 'ganancias',
        'descripcion': 'Permite recalcular y actualizar los registros de ganancias del sistema.',
        'ejemplo': 'Un desarrollador ejecuta el recálculo de ganancias después de una corrección.',
        'nivel_riesgo': 'alto',
        'orden': 40,
        'categoria': 'administracion_ganancias',
        'requiere_auditoria': True,
    },
]
