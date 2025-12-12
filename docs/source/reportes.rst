Reportes de Transacciones y Ganancias
======================================

Descripción General
-------------------

El módulo de reportes proporciona funcionalidades avanzadas para la generación, exportación y análisis de reportes de transacciones y ganancias. Permite a los administradores obtener información detallada sobre el rendimiento del negocio y tomar decisiones basadas en datos.

Características Principales
----------------------------

📊 **Reportes de Transacciones**
  - Reporte detallado de todas las transacciones
  - Filtros por fecha, estado, tipo de operación y divisa
  - Exportación a múltiples formatos (Excel, PDF, CSV)
  - Análisis de volúmenes operados
  - Métricas de conversión

📈 **Reportes de Ganancias**
  - Análisis consolidado de ganancias
  - Desglose por tipo de ganancia (comisión y spread)
  - Comparativas entre períodos
  - Top de transacciones más rentables
  - Proyecciones y tendencias

📑 **Formatos de Exportación**
  - **Excel (.xlsx)**: Con formato, gráficos y tablas dinámicas
  - **PDF**: Reportes formateados listos para imprimir
  - **CSV**: Para análisis en herramientas externas
  - **JSON**: Para integración con APIs

🔍 **Análisis Avanzado**
  - Análisis de rentabilidad por divisa
  - Análisis de rentabilidad por cliente
  - Análisis de rentabilidad por período
  - Identificación de patrones y tendencias

Vistas de Reportes
------------------

Reportes de Transacciones
~~~~~~~~~~~~~~~~~~~~~~~~~~

ExportarTransaccionesView
^^^^^^^^^^^^^^^^^^^^^^^^^

Vista para exportar reportes de transacciones a diferentes formatos.

.. autoclass:: transacciones.views.ExportarTransaccionesView
   :members:
   :undoc-members:
   :show-inheritance:

**Permisos requeridos:**
  - ``transacciones.export_reportes``

**Funcionalidad:**

Permite exportar transacciones filtradas a diferentes formatos (Excel, PDF, CSV) con información detallada de cada transacción.

Reportes de Ganancias
~~~~~~~~~~~~~~~~~~~~~

tablero_ganancias
^^^^^^^^^^^^^^^^^

Vista principal del tablero de ganancias que incluye funcionalidad de reportes.

.. autofunction:: ganancias.views.tablero_ganancias

**Permisos requeridos:**
  - ``ganancias.view_tablero_ganancias``

exportar_ganancias_excel
^^^^^^^^^^^^^^^^^^^^^^^^^

Exporta el reporte de ganancias a formato Excel con análisis detallado.

.. autofunction:: ganancias.views.exportar_ganancias_excel
   :no-index:

**Funcionalidad:**

Genera archivos Excel con análisis detallado de ganancias, incluyendo:

- Resumen general de ganancias
- Evolución temporal
- Análisis por divisa
- Top de transacciones más rentables
- Datos detallados para análisis personalizado

Reportes Combinados
~~~~~~~~~~~~~~~~~~~

El módulo de ganancias proporciona vistas combinadas que integran:

- Análisis de transacciones
- Análisis de ganancias
- Comparativas entre períodos
- Métricas y KPIs del negocio

Servicios de Reportes
----------------------

ReporteService
~~~~~~~~~~~~~~

Servicio principal para generación de reportes.

.. code-block:: python

   from transacciones.services import ReporteService
   from datetime import datetime
   
   # Generar reporte de transacciones
   reporte = ReporteService.generar_reporte_transacciones(
       fecha_inicio=datetime(2025, 1, 1),
       fecha_fin=datetime(2025, 1, 31),
       filtros={
           'tipo_operacion': 'compra',
           'estado': 'completado'
       }
   )

**Métodos disponibles:**

- ``generar_reporte_transacciones(fecha_inicio, fecha_fin, filtros)``
- ``generar_reporte_ganancias(fecha_inicio, fecha_fin, filtros)``
- ``generar_reporte_comparativo(periodo_actual, periodo_anterior)``
- ``generar_reporte_ejecutivo(fecha_inicio, fecha_fin)``

ExportacionService
~~~~~~~~~~~~~~~~~~

Servicio para exportación a diferentes formatos.

.. code-block:: python

   from ganancias.services import ExportacionService
   
   # Exportar a Excel
   archivo_excel = ExportacionService.exportar_excel(
       datos=reporte_data,
       tipo='ganancias',
       incluir_graficos=True
   )
   
   # Exportar a PDF
   archivo_pdf = ExportacionService.exportar_pdf(
       datos=reporte_data,
       template='reportes/ganancias_pdf.html'
   )
   
   # Exportar a CSV
   archivo_csv = ExportacionService.exportar_csv(
       datos=reporte_data,
       campos=['fecha', 'monto', 'tipo']
   )

**Métodos disponibles:**

- ``exportar_excel(datos, tipo, incluir_graficos, incluir_analisis)``
- ``exportar_pdf(datos, template, incluir_logo, orientacion)``
- ``exportar_csv(datos, campos, delimitador, encoding)``
- ``exportar_json(datos, formato, comprimido)``

AnalisisService
~~~~~~~~~~~~~~~

Servicio para análisis avanzado de datos.

.. code-block:: python

   from ganancias.services import AnalisisService
   
   # Calcular tendencia
   tendencia = AnalisisService.calcular_tendencia(
       datos=ganancias_historicas,
       tipo='lineal'
   )
   
   # Identificar outliers
   outliers = AnalisisService.identificar_outliers(
       datos=transacciones,
       metodo='zscore',
       umbral=3
   )
   
   # Análisis de rentabilidad
   rentabilidad = AnalisisService.analizar_rentabilidad(
       transacciones=transacciones,
       agrupar_por='divisa'
   )

**Métodos disponibles:**

- ``calcular_tendencia(datos, tipo, periodo)``
- ``identificar_outliers(datos, metodo, umbral)``
- ``analizar_rentabilidad(transacciones, agrupar_por)``
- ``calcular_metricas_kpi(datos, metricas)``
- ``proyectar_valores(datos_historicos, periodos_futuros, metodo)``

Comandos de Gestión
--------------------

generar_reporte_programado
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Comando para generar reportes programados automáticamente.

**Uso:**

.. code-block:: bash

   # Generar reporte diario
   python manage.py generar_reporte_programado --tipo=diario
   
   # Generar reporte mensual
   python manage.py generar_reporte_programado --tipo=mensual
   
   # Generar reporte personalizado
   python manage.py generar_reporte_programado \
       --fecha-inicio=2025-01-01 \
       --fecha-fin=2025-01-31 \
       --formato=excel \
       --email=admin@example.com

**Opciones:**
  - ``--tipo``: Tipo de reporte (diario, semanal, mensual)
  - ``--fecha-inicio``: Fecha de inicio personalizada
  - ``--fecha-fin``: Fecha de fin personalizada
  - ``--formato``: Formato de salida (excel, pdf, csv)
  - ``--email``: Email para enviar el reporte

enviar_reportes_automaticos
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Comando para enviar reportes automáticos por email.

**Uso:**

.. code-block:: bash

   # Enviar reportes configurados
   python manage.py enviar_reportes_automaticos

Este comando lee la configuración de reportes automáticos y los envía según lo programado.

API REST para Reportes
-----------------------

Endpoints
~~~~~~~~~

GET /api/reportes/transacciones/
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Obtiene datos de reporte de transacciones en formato JSON.

**Parámetros:**
  - ``fecha_inicio``: Fecha inicial (requerido)
  - ``fecha_fin``: Fecha final (requerido)
  - ``formato``: Formato de respuesta (json, csv)
  - ``filtros``: Objeto JSON con filtros adicionales

**Respuesta:**

.. code-block:: json

   {
     "periodo": {
       "inicio": "2025-01-01",
       "fin": "2025-01-31"
     },
     "resumen": {
       "total_transacciones": 150,
       "volumen_total_pyg": 1125000000,
       "volumen_total_usd": 150000
     },
     "transacciones": [
       {
         "numero": "TRX-2025-00001",
         "fecha": "2025-01-15T10:30:00Z",
         "cliente": "Juan Pérez",
         "tipo": "compra",
         "divisa": "USD",
         "monto_origen": 7500000,
         "monto_destino": 1000,
         "tasa": 7500,
         "estado": "completado"
       },
       ...
     ]
   }

GET /api/reportes/ganancias/
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Obtiene datos de reporte de ganancias en formato JSON.

**Parámetros:**
  - ``fecha_inicio``: Fecha inicial (requerido)
  - ``fecha_fin``: Fecha final (requerido)
  - ``agrupar_por``: Agrupación (dia, semana, mes)
  - ``divisa``: Filtro por divisa

**Respuesta:**

.. code-block:: json

   {
     "periodo": {
       "inicio": "2025-01-01",
       "fin": "2025-01-31"
     },
     "resumen": {
       "ganancia_total": 5625000,
       "ganancia_comisiones": 1875000,
       "ganancia_spread": 3750000,
       "cantidad_transacciones": 150,
       "promedio_por_transaccion": 37500
     },
     "evolucion": [
       {
         "fecha": "2025-01-01",
         "ganancia": 187500,
         "transacciones": 5
       },
       ...
     ],
     "por_divisa": [
       {
         "divisa": "USD",
         "ganancia": 3750000,
         "participacion": 66.67
       },
       ...
     ]
   }

POST /api/reportes/generar/
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Genera un reporte y lo retorna o envía por email.

**Body:**

.. code-block:: json

   {
     "tipo": "ganancias",
     "fecha_inicio": "2025-01-01",
     "fecha_fin": "2025-01-31",
     "formato": "excel",
     "opciones": {
       "incluir_graficos": true,
       "incluir_analisis": true
     },
     "enviar_email": true,
     "destinatarios": ["admin@example.com"]
   }

**Respuesta:**

.. code-block:: json

   {
     "status": "success",
     "mensaje": "Reporte generado exitosamente",
     "archivo_url": "/media/reportes/ganancia_2025-01.xlsx",
     "email_enviado": true
   }

Configuración de Reportes Automáticos
--------------------------------------

En ``settings.py``:

.. code-block:: python

   # Configuración de reportes
   REPORTES_CONFIG = {
       'FORMATOS_DISPONIBLES': ['excel', 'pdf', 'csv', 'json'],
       'MAX_REGISTROS_EXCEL': 10000,
       'MAX_REGISTROS_PDF': 1000,
       'INCLUIR_GRAFICOS_PDF': True,
       'LOGOS': {
           'header': 'static/img/logo-header.png',
           'footer': 'static/img/logo-footer.png'
       }
   }
   
   # Reportes automáticos
   REPORTES_AUTOMATICOS = {
       'diario': {
           'enabled': True,
           'hora': '08:00',
           'destinatarios': ['admin@example.com'],
           'formato': 'pdf'
       },
       'semanal': {
           'enabled': True,
           'dia': 'lunes',
           'hora': '09:00',
           'destinatarios': ['admin@example.com', 'gerencia@example.com'],
           'formato': 'excel'
       },
       'mensual': {
           'enabled': True,
           'dia': 1,
           'hora': '10:00',
           'destinatarios': ['admin@example.com', 'gerencia@example.com'],
           'formato': 'excel',
           'incluir_analisis': True
       }
   }

Permisos
--------

- ``transacciones.view_reporte_transacciones``: Ver reportes de transacciones
- ``transacciones.export_reportes``: Exportar reportes
- ``ganancias.view_reporte_ganancias``: Ver reportes de ganancias
- ``ganancias.view_reporte_ejecutivo``: Ver reporte ejecutivo completo
- ``ganancias.view_analisis_detallado``: Ver análisis detallado
- ``reportes.configure_automaticos``: Configurar reportes automáticos

Ejemplos de Uso
---------------

Generar Reporte Básico
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from django.shortcuts import render
   from transacciones.models import Transaccion
   from datetime import datetime, timedelta
   
   def mi_reporte(request):
       fecha_inicio = datetime.now() - timedelta(days=30)
       fecha_fin = datetime.now()
       
       transacciones = Transaccion.objects.filter(
           fecha_creacion__gte=fecha_inicio,
           fecha_creacion__lte=fecha_fin,
           estado='completado'
       )
       
       return render(request, 'mi_reporte.html', {
           'transacciones': transacciones,
           'fecha_inicio': fecha_inicio,
           'fecha_fin': fecha_fin
       })

Exportar a Excel con Estilo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from openpyxl import Workbook
   from openpyxl.styles import Font, PatternFill, Alignment
   from django.http import HttpResponse
   
   def exportar_excel_custom(request):
       wb = Workbook()
       ws = wb.active
       ws.title = "Ganancias"
       
       # Estilo del encabezado
       header_fill = PatternFill(start_color="366092", fill_type="solid")
       header_font = Font(bold=True, color="FFFFFF")
       
       # Encabezados
       headers = ['Fecha', 'Transacción', 'Ganancia', 'Tipo']
       for col, header in enumerate(headers, 1):
           cell = ws.cell(row=1, column=col, value=header)
           cell.fill = header_fill
           cell.font = header_font
           cell.alignment = Alignment(horizontal='center')
       
       # Datos
       ganancias = RegistroGanancia.objects.all()
       for row, ganancia in enumerate(ganancias, 2):
           ws.cell(row=row, column=1, value=ganancia.fecha_transaccion)
           ws.cell(row=row, column=2, value=ganancia.transaccion.numero_transaccion)
           ws.cell(row=row, column=3, value=float(ganancia.monto_total))
           ws.cell(row=row, column=4, value=ganancia.get_tipo_ganancia_display())
       
       # Respuesta HTTP
       response = HttpResponse(
           content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
       )
       response['Content-Disposition'] = 'attachment; filename=reporte_ganancias.xlsx'
       wb.save(response)
       return response

Ver también
-----------

- :doc:`ganancias` - Módulo de ganancias
- :doc:`transacciones` - Módulo de transacciones
- :doc:`historico_tasas` - Histórico de tasas de cambio
