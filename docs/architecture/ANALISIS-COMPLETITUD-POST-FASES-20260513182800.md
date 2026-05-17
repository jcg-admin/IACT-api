# Análisis — pipeline/models.py vs IACT-db: fuente de verdad

**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Alcance:** Relación entre los modelos Django de ``apps/pipeline/models.py``
(IACT-api) y el esquema real de MariaDB (IACT-db).
**Fuente de verdad:** ``/tmp/references/IACT-db`` — esquema vigente tras FASE 1-4.

----

Resumen ejecutivo
=================

Los modelos Django en ``apps/pipeline/models.py`` se dividen en dos grupos
completamente distintos que nunca deben confundirse:

.. list-table::
   :widths: 20 20 20 40
   :header-rows: 1

   * - Modelo Django
     - BD real
     - Tabla física
     - Acceso
   * - ``ETLExecution``
     - PostgreSQL (iact_analytics)
     - ``etl_executions``
     - ORM Django — solo en tests; no en producción
   * - ``Center``
     - PostgreSQL (iact_analytics)
     - ``core_centers``
     - ORM Django — activo en viewsets, servicios, dashboard
   * - ``Service``
     - PostgreSQL (iact_analytics)
     - ``core_services``
     - ORM Django — activo en viewsets y servicios
   * - ``CallRecord``
     - PostgreSQL (iact_analytics)
     - ``core_call_records``
     - ORM Django — activo en reportes, alertas, dashboard
   * - ``CallNote``
     - PostgreSQL (iact_analytics)
     - ``pipeline_call_notes``
     - ORM Django — activo en tests

Ninguno de estos modelos mapea a tablas de MariaDB (IACT-db). Son
entidades independientes en la base de datos analítica PostgreSQL.

----

Tablas reales en IACT-db (MariaDB ivr_legacy)
==============================================

Las seis tablas que existen en IACT-db tras la implementación FASE 1-4:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Tabla MariaDB
     - Propósito
   * - ``base_ivr_detalle``
     - Datos analíticos del IVR: métricas por (trimestre, fecha, segmento,
       centro_transferencia, menu, opcion). Cargada por ``sp_etl_maestro``.
   * - ``base_ivr_clientes``
     - Clientes únicos por (trimestre, segmento). Cargada por el ETL.
   * - ``job_execution_log``
     - Log granular de cada paso del pipeline ETL. Leído por
       ``pipeline/views.py`` y ``logs/views.py`` via raw SQL.
   * - ``etl_runs``
     - Registro del management command ``run_etl.py`` (heartbeat, timeout).
       Escrito por Django via raw SQL — NO via ORM.
   * - ``pipeline_event_log``
     - Eventos y errores de los SPs. Escrito por SPs MariaDB; sin endpoint
       en IACT-api aún (GAP-03 del análisis de integración).
   * - ``job_config``
     - Configuración operacional de jobs. Solo lectura de MariaDB.

**No existe en IACT-db:** ninguna tabla ``center``, ``service``,
``call_record``, ``call_note`` ni ``campaign``. Estos conceptos en IACT-db
son valores de columna dentro de ``base_ivr_detalle``:

- ``centro_transferencia`` — atributo de dimensión, no entidad
- ``segmento`` — atributo de dimensión
- ``menu``, ``opcion`` — atributos de dimensión

----

Cómo accede IACT-api a MariaDB
================================

IACT-api no usa el ORM Django para acceder a IACT-db. Todo el acceso es
via ``connections['ivr'].cursor()`` (raw SQL):

.. list-table::
   :widths: 35 30 35
   :header-rows: 1

   * - Capa Django
     - Método
     - Tabla o SP en MariaDB
   * - ``ivr_services.py``
     - ``cursor.callproc()``
     - ``sp_rpt_*`` (8 SPs de reporte)
   * - ``pipeline/views.py``
     - ``cursor.execute()``
     - ``job_execution_log``, ``job_execution_log``
   * - ``run_etl.py`` (management command)
     - ``cursor.execute()`` + ``cursor.callproc()``
     - ``etl_runs`` (INSERT/UPDATE), ``sp_etl_maestro``
   * - ``pipeline/views.etl_retry``
     - ``cursor.callproc()``
     - ``sp_etl_historico``
   * - ``logs/views.py``
     - ``cursor.execute()``
     - ``job_execution_log``

El ``DatabaseRouter`` prohíbe writes Django ORM a la base ``ivr``.
Los únicos writes a MariaDB desde Django son los ``cursor.execute()``
directos en ``run_etl.py`` sobre la tabla ``etl_runs``.

----

Impacto en PLAN-NOMENCLATURA-INGLES-20260513184800.md
======================================================

El hallazgo anterior no cambia la validez de la FASE 5 del plan de
nomenclatura. Los campos en español (``nombre``, ``codigo``, ``activo``,
``fecha``, ``telefono``, ``total_llamadas``, etc.) están en los modelos
PostgreSQL de IACT-api — son violaciones de RA-011 independientemente
de lo que exista en IACT-db.

Lo que sí aclara este análisis:

**FASE 5 — pipeline/models.py — el riesgo es PostgreSQL, no MariaDB.**

La migración Django de ``RenameField`` afecta únicamente la base
``iact_analytics`` (PostgreSQL). No requiere ningún cambio en IACT-db.
Los strings de columnas SQL en queries raw de MariaDB no se tocan
(son contratos de BD, no identificadores Python — RA-011 § 6.2).

**ETLExecution.** Solo se usa en tests. No en producción (el management
command ``run_etl.py`` escribe directamente a ``etl_runs`` en MariaDB
via raw SQL, nunca via ``ETLExecution.objects``). Candidato a eliminación,
pero fuera del alcance del plan de nomenclatura.

**Center, Service, CallRecord, CallNote.** Son modelos activos en
producción (viewsets, servicios, alertas, dashboard). Sus campos
en español son una deuda real que la FASE 5 debe resolver.

----

Relación IACT-docs vs realidad actual
======================================

IACT-docs (rama ``feature/wp-content-5-6-diagram-types``) documenta un
modelo de dominio canónico v1.0.0 con 25 clases en 7 bounded contexts.
Ese modelo fue producido aplicando el filtro de Abbott sobre 61 UCs.

La divergencia entre ese modelo y IACT-api no es un error a corregir en
este momento — es una deuda documentada. El modelo IACT-docs es un artefacto
de requisitos/arquitectura; IACT-api es el código que implementa el sistema
en su estado actual de evolución.

**IACT-docs no se actualiza.** Se deja en su estado vigente.

Las decisiones de implementación de IACT-api se documentan en
``docs/architecture/`` de este repositorio.
