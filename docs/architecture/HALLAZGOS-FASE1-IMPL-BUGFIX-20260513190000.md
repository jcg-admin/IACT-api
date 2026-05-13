# Hallazgos — Implementación FASE 1

**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Alcance:** FASE 1 del plan PLAN-ACTUALIZACION-COMPLETO-20260513185000.md
**Tarea:** T1.1 — corregir ``NameError`` en ``etl_data_availability``
**Commit:** ``3a87d5e``
**Archivo:** ``apps/pipeline/views.py``

---

Resumen de tareas ejecutadas
=============================

.. list-table::
   :widths: 15 50 20 15
   :header-rows: 1

   * - Tarea
     - Descripción
     - Estado
     - Hallazgos
   * - T1.1
     - Corregir NameError: ``trimestre`` → ``quarter``
     - COMPLETO
     - H-F1-001, H-F1-002, H-F1-003, H-F1-004

---

H-F1-001 — ``NameError: name 'trimestre' is not defined`` en producción
========================================================================

**Severidad:** CRÍTICA — produce HTTP 500 en producción.
**Estado:** CORREGIDO en commit ``3a87d5e``.
**Línea original:** 398.

Descripción
-----------

La función ``etl_data_availability`` tiene tres ramas de retorno:

.. code-block:: text

   1. quarter vacío → HTTP 400
   2. quarter sin datos en job_execution_log → HTTP 200 sin_datos   ← BUG
   3. quarter con datos → HTTP 200 con estado de frescura            ← OK

En la rama 2 (``if not row``), el dict de respuesta usaba la variable
``trimestre`` que no existe en el scope de la función:

.. code-block:: python

   # ANTES — línea 398 (ROTO):
   if not row:
       return Response({
           'trimestre':   trimestre,   # ← NameError: 'trimestre' no definida
           ...
       })

   # Variables disponibles en ese punto:
   #   request, quarter (L375), sql (L379), row (L391)
   #   quarter_name, ultima_carga, registros → se definen en L405,
   #                                           DESPUÉS del if not row

El parámetro disponible con el valor correcto es ``quarter``,
definido en la línea 375 como:

.. code-block:: python

   quarter = request.query_params.get('quarter')

Corrección aplicada
-------------------

.. code-block:: python

   # DESPUÉS — línea 398 (CORREGIDO):
   if not row:
       return Response({
           'trimestre':   quarter,   # ← variable correcta
           ...
       })

La clave de respuesta ``'trimestre'`` se mantiene igual — es el contrato
de API establecido (ver H-F1-002). Solo cambia el valor de la variable.

Verificación
------------

Tres ramas verificadas por simulación directa:

.. list-table::
   :widths: 30 20 50
   :header-rows: 1

   * - Entrada
     - HTTP
     - Respuesta
   * - ``quarter`` vacío
     - 400
     - ``{'error': 'Parameter quarter is required.'}``
   * - ``quarter=Q99_99`` (sin datos)
     - 200
     - ``{'trimestre': 'Q99_99', 'status_frescura': 'sin_datos', ...}``
   * - ``quarter=Q01_25`` (con datos, < 14h)
     - 200
     - ``{'status_frescura': 'fresco', 'minutos_desde_etl': N}``

Sintaxis: ``python3 -m py_compile apps/pipeline/views.py`` → OK.

---

H-F1-002 — Contrato de API con claves en español (informativo, no corregido)
=============================================================================

**Severidad:** BAJA — no produce error, viola RA-011 en strings de respuesta.
**Estado:** DOCUMENTADO — fuera del scope de FASE 1, aplaza a FASE 5.

La función retorna un dict con claves en español:

.. code-block:: python

   return Response({
       'trimestre':             quarter_name,   # ← español
       'status_frescura':       frescura,       # ← español
       'ultima_carga':          ultima_carga,   # ← español
       'registros_disponibles': registros,      # ← español
       'minutos_desde_etl':     minutos,        # ← español
   })

Lo mismo ocurre en ``_format_run()`` (L156):

.. code-block:: python

   return {
       'trimestre':   run['quarter_name'],   # ← español
       'source_table': ...,                  # ← inglés
       ...
   }

Estos son contratos de API pública consumida por el frontend.
Cambiarlos requiere coordinación con IACT-ui y es una decisión
explícita de versionado de API. No se cambian en FASE 1.

El renombre de las claves de respuesta (``'trimestre'`` → ``'quarter'``,
``'status_frescura'`` → ``'freshness_status'``, etc.) se aplaza a
FASE 5 del plan como parte de la alineación RA-011 con control de
impacto en el frontend.

---

H-F1-003 — Por qué el bug no fue detectado antes
=================================================

**Severidad:** Informativo.
**Estado:** Documentado — sin acción adicional requerida.

El entorno de desarrollo actual tiene datos de ``Q01_25`` en
``job_execution_log`` con ``step_name='etl_base_detalle'`` y
``status='SUCCESS'``. La query SQL siempre retorna una fila para
ese quarter y la rama ``if not row:`` nunca se ejecutó.

El bug se activa con cualquier quarter que no tenga datos:
- Un entorno recién provisionado (sin ETL ejecutado)
- Cualquier quarter futuro (``Q02_26``, ``Q03_26``)
- Un quarter con ETL fallido o sin ``step_name='etl_base_detalle'``

En producción, el frontend envía el quarter actual o uno reciente.
Si alguna vez envía un quarter sin datos (timeout, quarter nuevo,
primer despliegue) → HTTP 500 en lugar de HTTP 200 ``sin_datos``.

---

H-F1-004 — La función no valida el formato del quarter
======================================================

**Severidad:** BAJA — no bloquea funcionalidad, posible mejora defensiva.
**Estado:** Documentado — fuera del scope de FASE 1.

La función acepta cualquier string como ``quarter``:

.. code-block:: python

   quarter = request.query_params.get('quarter')
   if not quarter:
       return Response({'error': 'Parameter quarter is required.'}, status=400)
   # No hay validación de formato: 'HOLA' sería aceptado

Los SPs de MariaDB validan el formato con ``REGEXP '^Q0[1-4]_[0-9]{2}$'``
y retornarían una excepción. La función de disponibilidad solo ejecuta
un ``SELECT`` sin pasar por un SP — un quarter inválido produciría
0 filas y retornaría ``sin_datos`` en lugar de ``400 Bad Request``.

Esto no es un bug (no produce error), pero es inconsistente con los
SPs que rechazan con HTTP 400. Se aplaza a FASE 5 como mejora defensiva.

---

Estado final de FASE 1
=======================

.. list-table::
   :widths: 50 50
   :header-rows: 1

   * - Indicador
     - Valor
   * - Archivos modificados
     - ``apps/pipeline/views.py`` (1 línea)
   * - Tests afectados
     - Ninguno (el bug no tenía test que lo ejercitara)
   * - Migración de BD
     - No requerida
   * - Deuda técnica generada
     - Ninguna
   * - Deuda documentada (aplazada)
     - H-F1-002 (claves API en español) → FASE 5 H-F1-004 (validación de formato) → FASE 5
