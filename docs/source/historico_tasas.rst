Histórico de Tasas de Cambio
==============================

Descripción General
-------------------

El sistema de histórico de tasas de cambio permite registrar, consultar y visualizar la evolución de las tasas de cambio de divisas a lo largo del tiempo. Esta funcionalidad es fundamental para el análisis de mercado, auditoría y toma de decisiones.

Características Principales
----------------------------

📈 **Registro Automático de Tasas**
  - Almacenamiento automático de cada cambio de tasa
  - Timestamp preciso de cada modificación
  - Registro del usuario que realizó el cambio
  - Historial completo sin eliminaciones

📊 **Visualización de Evolución**
  - Gráficos de evolución temporal de tasas
  - Comparación entre tasas de compra y venta
  - Visualización de spread histórico
  - Filtros por período y divisa

🔍 **Consultas y Análisis**
  - Consulta de tasa en fecha específica
  - Análisis de tendencias
  - Identificación de picos y valles
  - Comparación entre divisas

Modelos
-------

TasaCambio
~~~~~~~~~~

Modelo que almacena el histórico completo de tasas de cambio.

.. autoclass:: divisas.models.TasaCambio
   :members:
   :undoc-members:
   :show-inheritance:

**Campos principales:**

- ``divisa``: Divisa asociada a la tasa
- ``fecha``: Fecha y hora de registro de la tasa
- ``precio_base``: Precio base de referencia (Gs por unidad de divisa)
- ``comision_compra``: Comisión aplicada en operaciones de compra
- ``comision_venta``: Comisión aplicada en operaciones de venta
- ``precio_compra``: Precio final de compra (precio_base - comision_compra)
- ``precio_venta``: Precio final de venta (precio_base + comision_venta)
- ``activa``: Indica si es la tasa actualmente vigente
- ``creado_por``: Usuario que registró la tasa
- ``notas``: Observaciones sobre el cambio de tasa

**Métodos:**

- ``get_tasa_vigente(divisa)``: Obtiene la tasa actualmente vigente para una divisa
- ``get_tasa_en_fecha(divisa, fecha)``: Obtiene la tasa vigente en una fecha específica
- ``get_historico(divisa, fecha_inicio, fecha_fin)``: Obtiene el historial de tasas en un período

CotizacionSegmento
~~~~~~~~~~~~~~~~~~

Modelo que almacena las cotizaciones específicas por segmento de cliente.

.. autoclass:: divisas.models.CotizacionSegmento
   :members:
   :undoc-members:
   :show-inheritance:

**Características:**

- Cotización personalizada según el segmento del cliente
- Descuentos aplicados según nivel de cliente
- Snapshot de la tasa utilizada (histórico inmutable)
- Valores pre-calculados para optimizar consultas

**Campos principales:**

- ``divisa``: Divisa cotizada
- ``segmento``: Segmento de cliente
- ``fecha``: Fecha y hora de la cotización
- ``precio_base``: Precio base congelado
- ``comision_compra``: Comisión de compra congelada
- ``comision_venta``: Comisión de venta congelada
- ``porcentaje_descuento``: Descuento del segmento (0-100)
- ``valor_compra_unit``: Valor final de compra con descuento
- ``valor_venta_unit``: Valor final de venta con descuento
- ``creado_por``: Usuario que generó la cotización

**Métodos:**

- ``calcular_valores()``: Calcula los valores finales con descuentos
- ``comision_compra_ajustada``: Property que retorna comisión de compra con descuento
- ``comision_venta_ajustada``: Property que retorna comisión de venta con descuento

QuerySets Personalizados
~~~~~~~~~~~~~~~~~~~~~~~~

CotizacionSegmentoQuerySet
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: divisas.models.CotizacionSegmentoQuerySet
   :members:
   :undoc-members:

**Métodos útiles:**

- ``recientes()``: Ordena las cotizaciones por fecha descendente
- ``ultima_para(divisa, segmento)``: Obtiene la última cotización para un segmento específico

Vistas
------

TasaCambioListView
~~~~~~~~~~~~~~~~~~

Vista de lista para visualizar el histórico de tasas de cambio.

.. autoclass:: divisas.views.TasaCambioListView
   :members:
   :undoc-members:
   :show-inheritance:

**Permisos requeridos:**
  - ``divisas.view_tasas_cambio``

**Características:**

- Muestra historial completo de tasas por divisa
- Filtros por rango de fechas
- Paginación automática
- Visualización de cambios y tendencias

**Parámetros GET:**
  - ``divisa_id``: ID de la divisa a consultar
  - ``fecha_inicio``: Fecha inicial del período (opcional)
  - ``fecha_fin``: Fecha final del período (opcional)

TasaCambioCreateView
~~~~~~~~~~~~~~~~~~~~

Vista para crear nuevas tasas de cambio.

.. autoclass:: divisas.views.TasaCambioCreateView
   :members:
   :undoc-members:
   :show-inheritance:

**Permisos requeridos:**
  - ``divisas.manage_tasas_cambio``

**Comportamiento:**

1. Valida los datos de la nueva tasa
2. Desactiva la tasa anterior
3. Crea la nueva tasa como activa
4. Genera cotizaciones para todos los segmentos
5. Registra el cambio en el log

**Actualización de Tasas:**

La actualización de tasas se realiza creando una nueva tasa y desactivando la anterior, manteniendo así un historial completo e inmutable.

visualizador_tasas
~~~~~~~~~~~~~~~~~~

Vista pública para visualizar tasas de cambio actuales.

.. autofunction:: divisas.views.visualizador_tasas

**Características:**

- Vista pública (no requiere autenticación)
- Muestra tasas vigentes de todas las divisas activas
- Formato amigable para clientes
- Información de spread y comisiones

Signals
-------

actualizar_cotizaciones_segmento
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Signal que se ejecuta automáticamente al crear o actualizar una tasa de cambio.

**Comportamiento:**

1. Se activa al guardar un objeto ``TasaCambio``
2. Genera cotizaciones para todos los segmentos activos
3. Aplica descuentos según configuración de segmento
4. Calcula valores finales de compra y venta
5. Almacena snapshot inmutable de la cotización

.. code-block:: python

   @receiver(post_save, sender=TasaCambio)
   def actualizar_cotizaciones_segmento(sender, instance, created, **kwargs):
       """
       Genera cotizaciones para todos los segmentos cuando se crea/actualiza una tasa.
       """
       if instance.activa:
           segmentos = Segmento.objects.filter(activo=True)
           for segmento in segmentos:
               CotizacionSegmento.objects.create(
                   divisa=instance.divisa,
                   segmento=segmento,
                   precio_base=instance.precio_base,
                   comision_compra=instance.comision_compra,
                   comision_venta=instance.comision_venta,
                   porcentaje_descuento=segmento.porcentaje_descuento,
                   creado_por=instance.creado_por
               )

Servicios
---------

Gestión de Tasas
~~~~~~~~~~~~~~~~

El módulo incluye servicios para la gestión avanzada de tasas:

.. code-block:: python

   from divisas.services import TasaCambioService
   
   # Obtener tasa vigente
   tasa = TasaCambioService.get_tasa_vigente(divisa)
   
   # Obtener histórico
   historico = TasaCambioService.get_historico(
       divisa=divisa,
       fecha_inicio=fecha_inicio,
       fecha_fin=fecha_fin
   )
   
   # Crear nueva tasa
   nueva_tasa = TasaCambioService.crear_tasa(
       divisa=divisa,
       precio_base=7500,
       comision_compra=50,
       comision_venta=50,
       usuario=request.user,
       notas="Ajuste por variación del mercado"
   )

Análisis de Tendencias
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from divisas.services import AnalisisService
   
   # Obtener tendencia
   tendencia = AnalisisService.calcular_tendencia(
       divisa=divisa,
       periodo_dias=30
   )
   
   # Obtener volatilidad
   volatilidad = AnalisisService.calcular_volatilidad(
       divisa=divisa,
       periodo_dias=30
   )
   
   # Comparar divisas
   comparacion = AnalisisService.comparar_divisas(
       divisas=[usd, eur, brl],
       fecha_inicio=fecha_inicio,
       fecha_fin=fecha_fin
   )

URLs
----

El módulo expone las siguientes URLs para el histórico de tasas:

- ``/divisas/<int:divisa_id>/tasas/``: Lista de histórico de tasas
- ``/divisas/<int:divisa_id>/tasas/nueva/``: Crear nueva tasa
- ``/divisas/<int:divisa_id>/tasas/<int:pk>/editar/``: Editar tasa
- ``/divisas/<int:divisa_id>/tasas/<int:pk>/``: Detalle de tasa
- ``/divisas/visualizador/``: Visualizador público de tasas
- ``/divisas/api/tasas/historico/``: API de histórico (JSON)

API REST
--------

Endpoints de API
~~~~~~~~~~~~~~~~

GET /divisas/api/tasas/historico/
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Retorna el histórico de tasas en formato JSON.

**Parámetros:**
  - ``divisa``: ID de la divisa (requerido)
  - ``fecha_inicio``: Fecha inicial (opcional)
  - ``fecha_fin``: Fecha final (opcional)
  - ``formato``: Formato de respuesta (json, csv)

**Respuesta:**

.. code-block:: json

   {
     "divisa": {
       "id": 1,
       "code": "USD",
       "nombre": "Dólar Estadounidense"
     },
     "tasas": [
       {
         "fecha": "2025-01-15T10:30:00Z",
         "precio_base": 7500.00,
         "precio_compra": 7450.00,
         "precio_venta": 7550.00,
         "spread": 100.00,
         "creado_por": "admin"
       },
       ...
     ],
     "estadisticas": {
       "promedio": 7500.00,
       "minimo": 7400.00,
       "maximo": 7600.00,
       "volatilidad": 2.5
     }
   }

GET /divisas/api/tasas/actual/
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Retorna las tasas actuales de todas las divisas.

**Respuesta:**

.. code-block:: json

   {
     "fecha_consulta": "2025-01-15T10:30:00Z",
     "tasas": [
       {
         "divisa": "USD",
         "precio_compra": 7450.00,
         "precio_venta": 7550.00,
         "ultima_actualizacion": "2025-01-15T08:00:00Z"
       },
       ...
     ]
   }

Permisos
--------

El módulo define los siguientes permisos para el histórico de tasas:

- ``divisas.view_tasas_cambio``: Ver histórico de tasas
- ``divisas.manage_tasas_cambio``: Crear y modificar tasas
- ``divisas.delete_tasas_cambio``: Eliminar registros de tasas
- ``divisas.view_analisis_tasas``: Ver análisis avanzado de tasas
- ``divisas.export_tasas``: Exportar histórico de tasas

Ejemplos de Uso
---------------

Consultar Histórico en Vista
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from divisas.models import TasaCambio, Divisa
   from datetime import datetime, timedelta
   
   def ver_historico_tasas(request, divisa_id):
       divisa = Divisa.objects.get(id=divisa_id)
       fecha_inicio = datetime.now() - timedelta(days=30)
       
       tasas = TasaCambio.objects.filter(
           divisa=divisa,
           fecha__gte=fecha_inicio
       ).order_by('-fecha')
       
       return render(request, 'tasas/historico.html', {
           'divisa': divisa,
           'tasas': tasas
       })

Crear Nueva Tasa con Validación
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from divisas.models import TasaCambio
   from django.core.exceptions import ValidationError
   
   def crear_nueva_tasa(divisa, precio_base, comision_compra, comision_venta, usuario):
       # Validar que el precio base sea positivo
       if precio_base <= 0:
           raise ValidationError("El precio base debe ser positivo")
       
       # Desactivar tasa anterior
       TasaCambio.objects.filter(
           divisa=divisa,
           activa=True
       ).update(activa=False)
       
       # Crear nueva tasa
       nueva_tasa = TasaCambio.objects.create(
           divisa=divisa,
           precio_base=precio_base,
           comision_compra=comision_compra,
           comision_venta=comision_venta,
           precio_compra=precio_base - comision_compra,
           precio_venta=precio_base + comision_venta,
           activa=True,
           creado_por=usuario,
           notas=f"Tasa actualizada por {usuario.username}"
       )
       
       return nueva_tasa

Generar Gráfico de Evolución
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import matplotlib.pyplot as plt
   from divisas.models import TasaCambio
   
   def generar_grafico_evolucion(divisa, dias=30):
       fecha_inicio = datetime.now() - timedelta(days=dias)
       tasas = TasaCambio.objects.filter(
           divisa=divisa,
           fecha__gte=fecha_inicio
       ).order_by('fecha')
       
       fechas = [t.fecha for t in tasas]
       precios_compra = [t.precio_compra for t in tasas]
       precios_venta = [t.precio_venta for t in tasas]
       
       plt.figure(figsize=(12, 6))
       plt.plot(fechas, precios_compra, label='Compra', marker='o')
       plt.plot(fechas, precios_venta, label='Venta', marker='s')
       plt.xlabel('Fecha')
       plt.ylabel('Precio (Gs)')
       plt.title(f'Evolución de Tasas - {divisa.code}')
       plt.legend()
       plt.grid(True)
       plt.xticks(rotation=45)
       plt.tight_layout()
       
       return plt

Buscar Tasa en Fecha Específica
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from divisas.models import TasaCambio
   from django.utils import timezone
   
   def obtener_tasa_en_fecha(divisa, fecha):
       """
       Obtiene la tasa vigente en una fecha específica.
       Si hay múltiples tasas ese día, retorna la más reciente.
       """
       tasa = TasaCambio.objects.filter(
           divisa=divisa,
           fecha__date=fecha.date()
       ).order_by('-fecha').first()
       
       if not tasa:
           # Si no hay tasa ese día, buscar la más reciente anterior
           tasa = TasaCambio.objects.filter(
               divisa=divisa,
               fecha__lt=fecha
           ).order_by('-fecha').first()
       
       return tasa

Templates
---------

El módulo incluye templates para visualización del histórico:

tasa_list.html
~~~~~~~~~~~~~~

Template principal para mostrar el listado de tasas históricas.

**Variables de contexto:**
  - ``tasas``: QuerySet de tasas ordenadas por fecha
  - ``divisa``: Objeto Divisa actual
  - ``fecha_inicio``: Fecha de inicio del filtro (opcional)
  - ``fecha_fin``: Fecha de fin del filtro (opcional)

visualizador_tasas.html
~~~~~~~~~~~~~~~~~~~~~~~

Template público para visualizar las tasas actuales.

**Variables de contexto:**
  - ``divisas``: Lista de divisas activas con sus tasas vigentes
  - ``ultima_actualizacion``: Timestamp de la última actualización

Ver también
-----------

- :doc:`divisas` - Módulo principal de divisas
- :doc:`transacciones` - Módulo de transacciones
- :doc:`ganancias` - Módulo de análisis de ganancias
