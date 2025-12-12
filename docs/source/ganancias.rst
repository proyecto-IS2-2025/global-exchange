Módulo de Ganancias
===================

Descripción General
-------------------

El módulo de ganancias proporciona un sistema completo de seguimiento, análisis y visualización de las ganancias generadas por las transacciones en Global Exchange.

Características Principales
----------------------------

📊 **Tablero de Control de Ganancias**
  - Visualización de ganancias totales por período (día, semana, mes, año)
  - Seguimiento detallado de comisiones cobradas
  - Análisis del spread (margen) en operaciones de cambio
  - Gráficos interactivos de evolución temporal
  - Distribución de ganancias por tipo de operación

📈 **Comparación de Períodos**
  - Comparación mes actual vs mes anterior
  - Comparación año actual vs año anterior
  - Evolución de últimos 12 meses
  - Cálculo automático de variaciones porcentuales

🎯 **Métricas y KPIs**
  - Ganancia total consolidada
  - Promedio de ganancia por transacción
  - Top 10 transacciones con mayor ganancia
  - Cantidad de transacciones procesadas
  - Distribución porcentual por tipo de ganancia

📊 **Análisis por Divisa**
  - Desglose de ganancias por cada divisa operada
  - Filtros específicos por tipo de divisa
  - Comparación de rendimiento entre divisas

Modelos
-------

RegistroGanancia
~~~~~~~~~~~~~~~~

Registra las ganancias generadas por cada transacción individual.

.. autoclass:: ganancias.models.RegistroGanancia
   :members:
   :undoc-members:
   :show-inheritance:

**Campos principales:**

- ``transaccion``: Relación uno a uno con la transacción que generó la ganancia
- ``tipo_ganancia``: Tipo de ganancia ('comision' o 'spread')
- ``monto_comision``: Ganancia por comisión cobrada al cliente
- ``monto_spread``: Ganancia por diferencia entre tasa de compra y venta
- ``monto_total``: Ganancia total en PYG (comisión + spread)
- ``divisa_referencia``: Divisa extranjera involucrada
- ``porcentaje_comision``: Porcentaje de comisión aplicado
- ``fecha_transaccion``: Fecha de la transacción asociada

ResumenGananciaDiaria
~~~~~~~~~~~~~~~~~~~~~

Almacena resúmenes agregados de ganancias por día.

.. autoclass:: ganancias.models.ResumenGananciaDiaria
   :members:
   :undoc-members:
   :show-inheritance:

**Campos principales:**

- ``fecha``: Fecha del resumen
- ``total_comisiones``: Total de comisiones del día
- ``total_spread``: Total de spread del día
- ``total_general``: Ganancia total del día
- ``cantidad_transacciones``: Número de transacciones del día

ResumenGananciaMensual
~~~~~~~~~~~~~~~~~~~~~~

Almacena resúmenes agregados de ganancias por mes.

.. autoclass:: ganancias.models.ResumenGananciaMensual
   :members:
   :undoc-members:
   :show-inheritance:

**Campos principales:**

- ``mes``: Mes del resumen (formato YYYY-MM)
- ``total_comisiones``: Total de comisiones del mes
- ``total_spread``: Total de spread del mes
- ``total_general``: Ganancia total del mes
- ``cantidad_transacciones``: Número de transacciones del mes
- ``promedio_por_transaccion``: Promedio de ganancia por transacción

Vistas
------

tablero_ganancias
~~~~~~~~~~~~~~~~~

Vista principal del tablero de control de ganancias.

.. autofunction:: ganancias.views.tablero_ganancias

**Permisos requeridos:**
  - ``ganancias.view_tablero_ganancias``

**Parámetros GET:**
  - ``fecha_inicio``: Fecha de inicio del período (formato YYYY-MM-DD)
  - ``fecha_fin``: Fecha de fin del período (formato YYYY-MM-DD)
  - ``periodo``: Período predefinido (dia, semana, mes_actual, mes_anterior, año, todo)
  - ``divisa``: ID de la divisa para filtrar

**Retorna:**
  Renderiza el template con:
  
  - Ganancias totales del período
  - Gráficos de evolución
  - Métricas comparativas
  - Top de transacciones
  - Análisis por divisa

exportar_ganancias_excel
~~~~~~~~~~~~~~~~~~~~~~~~~

Exporta el reporte de ganancias a formato Excel.

.. autofunction:: ganancias.views.exportar_ganancias_excel

**Permisos requeridos:**
  - ``ganancias.export_ganancias``

**Retorna:**
  Archivo Excel (.xlsx) con:
  
  - Resumen general de ganancias
  - Detalle de transacciones
  - Gráficos y tablas dinámicas
  - Análisis por período y divisa

api_ganancias_evolucion
~~~~~~~~~~~~~~~~~~~~~~~

API endpoint que retorna datos de evolución de ganancias en formato JSON.

.. autofunction:: ganancias.views.api_ganancias_evolucion

**Retorna:**
  JSON con estructura de evolución temporal de ganancias.

Signals
-------

calcular_ganancia_automatica
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Signal que se ejecuta automáticamente cuando una transacción cambia de estado a 'completado' o 'pagada'.

.. autofunction:: ganancias.signals.calcular_ganancia_automatica

**Comportamiento:**

1. Verifica si la transacción está completada
2. Calcula la ganancia por spread (diferencia entre tasa aplicada y tasa base)
3. Calcula la ganancia por comisión si aplica
4. Crea o actualiza el registro de ganancia
5. Actualiza los resúmenes diarios y mensuales

Comandos de Gestión
--------------------

calcular_ganancias
~~~~~~~~~~~~~~~~~~

Comando para calcular las ganancias de transacciones existentes.

**Uso:**

.. code-block:: bash

   # Calcular ganancias de transacciones sin registro
   python manage.py calcular_ganancias

   # Recalcular todas las ganancias (incluso las existentes)
   python manage.py calcular_ganancias --recalcular

**Opciones:**
  - ``--recalcular``: Recalcula todas las ganancias, incluso si ya existen

generar_resumenes_ganancias
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Comando para generar resúmenes diarios y mensuales de ganancias.

**Uso:**

.. code-block:: bash

   # Generar resúmenes de ganancias
   python manage.py generar_resumenes_ganancias

Permisos
--------

El módulo define los siguientes permisos personalizados:

- ``ganancias.view_tablero_ganancias``: Ver tablero de ganancias
- ``ganancias.export_ganancias``: Exportar reportes de ganancias
- ``ganancias.view_analisis_detallado``: Ver análisis detallado de ganancias
- ``ganancias.view_ganancias_ocultas``: Ver información sensible de ganancias

Instalación y Configuración
----------------------------

1. Ejecutar migraciones
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python manage.py makemigrations ganancias
   python manage.py migrate ganancias

2. Calcular ganancias existentes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Para calcular las ganancias de todas las transacciones completadas:

.. code-block:: bash

   python manage.py calcular_ganancias

3. Configurar permisos
~~~~~~~~~~~~~~~~~~~~~~

Asignar los permisos necesarios a los roles:

.. code-block:: python

   from django.contrib.auth.models import Group, Permission

   # Asignar permisos al grupo de administradores
   admin_group = Group.objects.get(name='Administrador')
   permisos = Permission.objects.filter(
       codename__in=[
           'view_tablero_ganancias',
           'export_ganancias',
           'view_analisis_detallado'
       ]
   )
   admin_group.permissions.add(*permisos)

URLs
----

El módulo expone las siguientes URLs:

- ``/ganancias/tablero/``: Tablero principal de ganancias
- ``/ganancias/exportar/excel/``: Exportar reporte a Excel
- ``/ganancias/api/evolucion/``: API de datos de evolución

Ejemplo de Uso
--------------

Acceso al Tablero
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # En una vista o template
   from django.urls import reverse
   
   url_tablero = reverse('ganancias:tablero_ganancias')
   # /ganancias/tablero/

Filtrar por Período
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # URLs con parámetros de filtro
   url_mes_actual = '/ganancias/tablero/?periodo=mes_actual'
   url_rango = '/ganancias/tablero/?fecha_inicio=2025-01-01&fecha_fin=2025-01-31'
   url_divisa = '/ganancias/tablero/?periodo=mes_actual&divisa=1'

Calcular Ganancia Manualmente
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ganancias.models import RegistroGanancia
   from transacciones.models import Transaccion
   from decimal import Decimal
   
   transaccion = Transaccion.objects.get(id=123)
   
   # Calcular ganancia por spread
   spread = transaccion.tasa_de_cambio_aplicada - transaccion.tasa_base
   monto_spread = spread * transaccion.monto_origen
   
   # Crear registro de ganancia
   ganancia = RegistroGanancia.objects.create(
       transaccion=transaccion,
       tipo_ganancia='spread',
       monto_spread=monto_spread,
       monto_total=monto_spread,
       divisa_referencia=transaccion.divisa_origen,
       fecha_transaccion=transaccion.fecha_creacion
   )

Ver también
-----------

- :doc:`transacciones` - Módulo de transacciones
- :doc:`divisas` - Módulo de divisas y tasas de cambio
- :doc:`clientes` - Módulo de gestión de clientes
