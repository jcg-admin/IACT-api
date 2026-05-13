# Plan de Actualización IACT-api — Completo por Fases

**Versión:** 2.0.0
**Fecha:** 2026-05-13
**Fuente de verdad de datos:** IACT-db (MariaDB ivr_legacy, rama develop)
**Referencia de convenciones:** ``docs/conventions/CLEAN_CODE_NAMING_PRINCIPLES_v1_0_0.md``
**Regla de idioma:** RA-011 — todo identificador Python en inglés.

---

Contexto
========

El proyecto tiene cuatro tipos de problemas que este plan resuelve
en orden de dependencia:

1. **Bug crítico en producción** — ``NameError`` en endpoint activo.
2. **Código muerto** — ``apps/ivr/`` y modelos de pipeline fuera de scope
   (``Center``, ``Service``, ``CallRecord``, ``CallNote``, ``ETLExecution``).
   Los UCs que los justificarían (UC_OPR, UC_SUP, UC_CLI) están fuera
   del scope de IACT-api — son capa de telefonía/CTI, no analítica.
3. **Objetos de IACT-db sin endpoint** — ``sp_rpt_resumen_abandono_rollup``,
   ``v_etl_rendimiento`` y ``pipeline_event_log`` implementados en FASE 3
   de IACT-db pero sin exposición en IACT-api.
4. **Violaciones de nomenclatura** (RA-011) — clases en español,
   sufijos ``Builder`` y ``Factory`` prohibidos, función helper en español.

Principio de eliminación vs renombre
-------------------------------------

Los modelos ``Center``, ``Service``, ``CallRecord``, ``CallNote`` y
``ETLExecution`` **se eliminan**, no se renombran. Son conceptos de la
capa de telefonía (CTI) que el dominio analítico de IACT-api no opera.
En IACT-db no existe ninguna tabla ``center``, ``service`` ni
``call_record`` — son atributos de dimensión dentro de ``base_ivr_detalle``.

IACT-docs se deja en su estado vigente — no se actualiza.

---

FASE 1 — Bug crítico: ``NameError`` en ``etl_data_availability``
================================================================

**Riesgo:** CRÍTICO — produce HTTP 500 en producción.
**Archivos:** ``apps/pipeline/views.py``
**Commits:** 1

T1.1 — Corregir variable ``trimestre`` no definida
----------------------------------------------------

Archivo: ``apps/pipeline/views.py``, función ``etl_data_availability``,
bloque ``if not row``.

.. code-block:: python

   # ANTES (línea ~398):
   return Response({
       'trimestre':             trimestre,    # ← NameError
       'status_frescura':       'sin_datos',
       ...
   })

   # DESPUÉS:
   return Response({
       'trimestre':             quarter,      # ← parámetro real
       'status_frescura':       'sin_datos',
       ...
   })

Verificación: ``curl GET /api/pipeline/data-availability/?quarter=INEXISTENTE``
debe retornar HTTP 200 con ``status_frescura: sin_datos``, no HTTP 500.

**Commit:** ``fix(pipeline): NameError en etl_data_availability — trimestre → quarter``

---

FASE 2 — Eliminar ``apps/ivr/`` (código muerto desde 2026-03-21)
=================================================================

**Riesgo:** Bajo — los endpoints de la app no están en ``config/urls.py``.
**Archivos:** ``apps/ivr/``, ``tests/unit/ivr_legacy/``, ``tests/factories/ivr_factories.py``
**Commits:** 1

T2.1 — Quitar ``apps.ivr`` de ``INSTALLED_APPS``
--------------------------------------------------

``config/settings/base.py``: eliminar la línea ``'apps.ivr'``.

T2.2 — Eliminar directorio ``apps/ivr/``
-----------------------------------------

.. code-block:: bash

   rm -rf callcentersite/apps/ivr/

T2.3 — Eliminar tests de la app ivr
-------------------------------------

.. code-block:: bash

   rm -rf callcentersite/tests/unit/ivr_legacy/
   rm -f  callcentersite/tests/factories/ivr_factories.py

T2.4 — Verificar que no quedan referencias
-------------------------------------------

.. code-block:: bash

   grep -r "apps.ivr\|from apps.ivr\|TblTempPruebaIvr" \
       callcentersite/ --include="*.py"
   # Resultado esperado: 0 líneas

T2.5 — Manejar la migración de la app ivr
------------------------------------------

Si Django ya ejecutó ``migrate`` con esta migración registrada
en ``django_migrations`` (modelo ``managed=False``):

.. code-block:: bash

   python manage.py migrate ivr zero   # revertir registro
   # Luego eliminar el directorio (T2.2)

La tabla ``tbl_temp_prueba_ivr`` en MariaDB no se toca —
pertenece a IACT-db.

**Commit:** ``chore(ivr): eliminar apps/ivr/ — código muerto desde 2026-03-21``

---

FASE 3 — Eliminar modelos fuera de scope de ``pipeline/models.py``
===================================================================

Eliminación de ``Center``, ``Service``, ``CallRecord``, ``CallNote``
y ``ETLExecution`` — modelos de capa CTI/telefonía incompatibles con
el scope analítico de IACT-api. Los UCs que los requieren (UC_OPR,
UC_SUP, UC_CLI) están fuera del scope del proyecto.

**Riesgo:** ALTO — cascada a 40+ archivos en 8 apps.
**Estrategia:** eliminar de dentro hacia afuera (dependientes → modelos → migración).
**Commits:** 4

T3.1 — Eliminar ``pipeline/admin.py`` — registros de los 5 modelos
--------------------------------------------------------------------

Quitar las líneas ``admin.site.register()`` de Center, Service,
CallRecord, CallNote y ETLExecution. Conservar cualquier otro
registro que exista en el archivo.

T3.2 — Eliminar ``pipeline/viewsets.py`` — 4 viewsets
-------------------------------------------------------

Eliminar completamente:
- ``CenterViewSet``
- ``ServiceViewSet``
- ``CallRecordViewSet``
- ``CallNoteViewSet``

Si el archivo solo contiene estos viewsets, eliminar el archivo entero.

T3.3 — Limpiar ``pipeline/urls.py`` — router y imports
--------------------------------------------------------

.. code-block:: python

   # Eliminar estas líneas:
   from .viewsets import CenterViewSet, ServiceViewSet, CallRecordViewSet, CallNoteViewSet
   router.register(r'centers',    CenterViewSet, ...)
   router.register(r'services',   ServiceViewSet, ...)
   router.register(r'calls',      CallRecordViewSet, ...)
   router.register(r'call-notes', CallNoteViewSet, ...)

   # Conservar las rutas UC_PIP_01..04 y ivr-health.

T3.4 — Eliminar serializers de los modelos eliminados
------------------------------------------------------

Archivos a eliminar:

.. code-block:: bash

   rm apps/pipeline/serializers/center_serializers.py
   rm apps/pipeline/serializers/service_serializers.py
   rm apps/pipeline/serializers/callrecord_serializers.py
   rm apps/pipeline/serializers/callnote_serializers.py

Actualizar ``apps/pipeline/serializers/__init__.py``: eliminar
los imports de los 4 serializers eliminados.

T3.5 — Eliminar servicios de los modelos eliminados
----------------------------------------------------

Archivos a eliminar:

.. code-block:: bash

   rm apps/pipeline/services/center_service.py
   rm apps/pipeline/services/service_service.py
   rm apps/pipeline/services/callrecord_service.py
   rm apps/pipeline/services/etl_service.py   # ETL service desactivado

Actualizar ``apps/pipeline/services/__init__.py``.

T3.6 — Limpiar ``pipeline/filters.py``
---------------------------------------

Eliminar los filtros de Center, Service y CallRecord.
Si el archivo queda vacío, eliminarlo.

T3.7 — Limpiar ``core/serializers.py``
----------------------------------------

Eliminar las clases ``CallRecordSerializer``, ``CenterSerializer``,
``ServiceSerializer`` y sus imports.

T3.8 — Limpiar ``core/views.py`` y ``core/urls.py``
-----------------------------------------------------

``core/views.py``: eliminar las views de Center, Service, CallRecord
que no son parte del scope analítico.

``core/urls.py``: eliminar el import y registro de
``CallRecordViewSet``, ``CenterViewSet``, ``ServiceViewSet``.

T3.9 — Limpiar ``core/services/etl_service.py``
-------------------------------------------------

Este archivo es el ETL service del ``core`` que también está
desactivado (usa ``IVRAdapter`` comentado). Eliminar el archivo.

T3.10 — Limpiar ``reports/services.py``
-----------------------------------------

Eliminar el import lazy de ``CallRecord`` (línea ~184) y la lógica
que lo usa. Si esa lógica es el único uso de los datos de calls en
el export service, reemplazar con ``pass`` o nota documentada.

T3.11 — Limpiar ``alerts/services/alert_service.py``
------------------------------------------------------

Eliminar las consultas ``CallRecord.objects.filter(...)`` que generan
alertas basadas en datos ORM. Estos datos deben venir de MariaDB
via SPs o queries raw. Documentar el gap como trabajo futuro
si la funcionalidad de alertas basada en llamadas es necesaria.

T3.12 — Limpiar ``dashboard/services/`` y ``dashboard/permissions.py``
-----------------------------------------------------------------------

``dashboard/services/filter_service.py``: eliminar el filtro por
``CallRecord``.
``dashboard/services/widget_service.py``: eliminar los widgets que
consultan ``CallRecord.objects``. Los widgets de llamadas deben
usar datos de MariaDB cuando se reimplementen.
``dashboard/permissions.py``: eliminar referencias a ``CallRecord``.

T3.13 — Limpiar ``access/management/commands/create_functions.py``
-------------------------------------------------------------------

Eliminar el bloque comentado sobre ``CallRecord`` (solo texto, no import).
Verificar que no hay import real.

T3.14 — Limpiar tests afectados
---------------------------------

Eliminar o vaciar (según corresponda) los tests que prueban
funcionalidad de los modelos eliminados:

- ``tests/unit/pipeline/test_models.py`` — prueba ETLExecution, Center,
  CallRecord. Eliminar o reemplazar con tests de ETL via MariaDB.
- ``tests/unit/core/test_core_etl_service.py`` — eliminar.
- ``tests/unit/core/test_core_serializers.py`` — eliminar referencias
  a Center, Service, CallRecord.
- ``tests/unit/core/test_service_access.py`` — revisar.
- ``apps/pipeline/tests/test_call_notes.py`` — eliminar.
- Revisar ``tests/conftest.py``, ``tests/api/test_core_api.py``,
  ``tests/integration/users/`` por referencias residuales.

T3.15 — Eliminar los modelos de ``pipeline/models.py``
--------------------------------------------------------

Eliminar las clases:
- ``ETLExecution``
- ``Center``
- ``Service``
- ``CallRecord``
- ``CallNote``

Conservar el archivo (puede quedar vacío o con un comentario de estado).

T3.16 — Generar y aplicar migración ``DeleteModel``
----------------------------------------------------

.. code-block:: bash

   python manage.py makemigrations pipeline \
       --name delete_out_of_scope_models

La migración generará:

.. code-block:: python

   operations = [
       migrations.DeleteModel('CallNote'),
       migrations.DeleteModel('CallRecord'),
       migrations.DeleteModel('Service'),
       migrations.DeleteModel('Center'),
       migrations.DeleteModel('ETLExecution'),
   ]

Aplicar en ese orden (FK: CallNote → CallRecord → Service → Center).

.. code-block:: bash

   python manage.py migrate pipeline

**Commits:**
- ``refactor(pipeline): eliminar servicios y serializers de modelos CTI fuera de scope``
- ``refactor(core,alerts,dashboard): limpiar referencias a modelos CTI eliminados``
- ``chore(pipeline): migración delete_out_of_scope_models``
- ``test(pipeline): eliminar tests de modelos CTI fuera de scope``

---

FASE 4 — Nuevos endpoints para objetos de IACT-db
==================================================

Tres objetos implementados en IACT-db durante FASE 3 de ese repositorio
que aún no tienen endpoint en IACT-api.

**Archivos:** ``apps/reports/ivr_services.py``, ``apps/reports/ivr_views.py``,
``apps/reports/urls.py``, ``apps/logs/views.py``, ``apps/logs/urls.py``,
``apps/pipeline/views.py``, ``apps/pipeline/urls.py``
**Commits:** 3

T4.1 — ``sp_rpt_resumen_abandono_rollup`` → endpoint de reporte
----------------------------------------------------------------

**En ``apps/reports/ivr_services.py``:**

.. code-block:: python

   def get_abandonment_summary(quarter: str) -> list[dict]:
       """
       Resumen ejecutivo de abandono con jerarquía completa.
       Llama: sp_rpt_resumen_abandono_rollup(p_quarter)
       Retorna: 13 filas — detalle + subtotales por segmento + TOTAL.
       Denominador: total de los 3 menús de abandono (no total del quarter).
       Fila TOTAL siempre muestra pct_del_quarter = 100.00.
       """
       return _call_sp('sp_rpt_resumen_abandono_rollup', [quarter])

**En ``apps/reports/ivr_views.py``:**

.. code-block:: python

   @extend_schema(
       summary="UC_RPT — Resumen ejecutivo de abandono",
       description=(
           "Jerarquía completa: detalle + subtotal por segmento + TOTAL. "
           "Invoca sp_rpt_resumen_abandono_rollup(p_quarter). "
           "13 filas. pct_del_quarter sobre total de abandonos (fila TOTAL = 100.00)."
       ),
       parameters=[_IVR_QUARTER_PARAM],
       responses={200: OpenApiResponse(description="13 filas de abandono con jerarquía"),
                  400: OpenApiResponse(description="Quarter inválido"),
                  503: OpenApiResponse(description="MariaDB no disponible")},
       tags=["Reportes de Llamadas"],
   )
   class AbandonmentSummaryView(APIView):
       """
       GET /api/reports/ivr/abandonment-summary/
       Resumen ejecutivo de abandono con sp_rpt_resumen_abandono_rollup.
       """
       permission_classes = [IsAuthenticated, HasFunction]
       required_function  = 'reports.view_ivr'

       def get(self, request):
           quarter = request.query_params.get('quarter', 'Q01_25')
           errors  = _validate(quarter=quarter)
           if errors:
               return Response({'errors': errors}, status=400)
           return _ivr_response(svc.get_abandonment_summary, quarter,
                                extra={'quarter': quarter})

**En ``apps/reports/urls.py``:**

.. code-block:: python

   from .ivr_views import (..., AbandonmentSummaryView)

   path('ivr/abandonment-summary/', AbandonmentSummaryView.as_view(),
        name='ivr-abandonment-summary'),

**Commit:** ``feat(reports): endpoint AbandonmentSummaryView → sp_rpt_resumen_abandono_rollup``

T4.2 — ``pipeline_event_log`` → endpoint de lectura en logs
------------------------------------------------------------

**En ``apps/logs/views.py``:**

.. code-block:: python

   @extend_schema(
       summary="UC_LOG_08 — Eventos del pipeline analítico",
       description=(
           "Lee pipeline_event_log en MariaDB ivr_legacy. "
           "Filtra por quarter, error_type y ventana de horas. "
           "Registra PARAM_INVALIDO, ETL_FALLO, ETL_PARTIAL, "
           "VALIDACION, REPORTE_VACIO, SISTEMA."
       ),
       parameters=[
           OpenApiParameter('quarter',    str, required=False),
           OpenApiParameter('error_type', str,
               enum=['PARAM_INVALIDO','ETL_FALLO','ETL_PARTIAL',
                     'VALIDACION','REPORTE_VACIO','SISTEMA'],
               required=False),
           OpenApiParameter('hours',      int, default=48,
               description="Ventana de búsqueda en horas (máx 168)"),
           OpenApiParameter('page_size',  int, default=20,
               description="Registros por página (máx 100)"),
       ],
       responses={200: OpenApiResponse(description="Eventos del pipeline"),
                  503: OpenApiResponse(description="MariaDB no disponible")},
       tags=["Registros del Sistema"],
   )
   class PipelineEventLogView(APIView):
       """
       GET /api/logs/pipeline-events/
       Lee pipeline_event_log de MariaDB ivr_legacy.
       """
       permission_classes = [IsAuthenticated, HasFunction]
       required_function  = 'logs.view'

       def get(self, request):
           from django.db import connections, OperationalError
           quarter    = request.query_params.get('quarter')
           error_type = request.query_params.get('error_type')
           try:
               hours     = min(168, int(request.query_params.get('hours', 48)))
               page_size = min(100, int(request.query_params.get('page_size', 20)))
           except (ValueError, TypeError):
               hours, page_size = 48, 20

           conditions = ["ts >= DATE_SUB(NOW(), INTERVAL %s HOUR)"]
           params = [hours]
           if quarter:
               conditions.append("p_quarter = %s"); params.append(quarter)
           if error_type:
               conditions.append("error_type = %s"); params.append(error_type)

           where = ' AND '.join(conditions)
           sql = f"""
               SELECT id, ts, error_type, severity, sp_nombre,
                      sql_state, p_quarter, p_segmento,
                      LEFT(error_message, 200) AS error_message,
                      job_log_id, ejecutado_por
               FROM pipeline_event_log
               WHERE {where}
               ORDER BY ts DESC LIMIT %s
           """
           try:
               with connections['ivr'].cursor() as cursor:
                   cursor.execute(sql, params + [page_size])
                   cols   = [c[0] for c in cursor.description]
                   events = [dict(zip(cols, row)) for row in cursor.fetchall()]
           except OperationalError as e:
               return Response({'error': str(e)}, status=503)

           return Response({'total': len(events), 'events': events})

**En ``apps/logs/urls.py``:**

.. code-block:: python

   from .views import (..., PipelineEventLogView)

   path('pipeline-events/', PipelineEventLogView.as_view(),
        name='pipeline-events'),

**Commit:** ``feat(logs): endpoint PipelineEventLogView → pipeline_event_log (UC_LOG_08)``

T4.3 — ``v_etl_rendimiento`` → endpoint de observabilidad ETL
--------------------------------------------------------------

**En ``apps/pipeline/views.py``:**

.. code-block:: python

   @extend_schema(
       summary="ETL step performance — regresiones vía LAG()",
       description=(
           "Lee v_etl_rendimiento en MariaDB ivr_legacy. "
           "Muestra duracion_seg, duracion_anterior_seg y delta_seg "
           "por step. delta_seg > 0: regresión; < 0: mejora; NULL: "
           "primera ejecución registrada del step."
       ),
       parameters=[
           OpenApiParameter('step_name', str, required=False,
               description="Filtrar por step: etl_base_detalle, maestro, etc."),
           OpenApiParameter('limit', int, default=50,
               description="Máx registros (máx 200)"),
       ],
       responses={200: OpenApiResponse(description="Regresiones de rendimiento por step"),
                  503: OpenApiResponse(description="MariaDB no disponible")},
       tags=["Estado del Pipeline"],
   )
   @api_view(['GET'])
   @permission_classes([IsAuthenticated, HasFunction])
   def etl_performance(request):
       """
       GET /api/pipeline/performance/
       Lee v_etl_rendimiento — duracion, anterior y delta por step.
       """
       from django.db import connections, OperationalError
       step_name = request.query_params.get('step_name')
       try:
           limit = min(200, int(request.query_params.get('limit', 50)))
       except (ValueError, TypeError):
           limit = 50

       conditions = []
       params = []
       if step_name:
           conditions.append("step_name = %s"); params.append(step_name)
       where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

       sql = f"""
           SELECT job_name, quarter_name, step_name, start_time,
                  duracion_seg, duracion_anterior_seg, delta_seg
           FROM v_etl_rendimiento
           {where}
           ORDER BY step_name, start_time DESC
           LIMIT %s
       """
       try:
           with connections['ivr'].cursor() as cursor:
               cursor.execute(sql, params + [limit])
               cols = [c[0] for c in cursor.description]
               rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
       except OperationalError as e:
           return Response({'error': str(e)}, status=503)

       return Response({'total': len(rows), 'steps': rows})

**En ``apps/pipeline/urls.py``:**

.. code-block:: python

   from .views import (..., etl_performance)

   path('performance/', etl_performance, name='etl-performance'),

**Commit:** ``feat(pipeline): endpoint etl_performance → v_etl_rendimiento``

---

FASE 5 — Nomenclatura: renombres en código de producción (RA-011)
=================================================================

**Archivos:** ``apps/pipeline/views.py``, ``apps/reports/ivr_views.py``,
``apps/reports/urls.py``, ``apps/core/navigation/builders.py``
**Commits:** 2

T5.1 — ``_build_resumen_salud`` → ``_build_pipeline_health_summary``
---------------------------------------------------------------------

``apps/pipeline/views.py``:

.. code-block:: python

   # Renombrar función y su única llamada en etl_status
   def _build_pipeline_health_summary(runs: list[dict]) -> dict: ...

   resumen = _build_pipeline_health_summary(runs)   # en etl_status

T5.2 — 7 clases de vistas en ``ivr_views.py``
----------------------------------------------

.. list-table::
   :widths: 50 50
   :header-rows: 1

   * - Clase actual
     - Clase nueva
   * - ``ClientesReportView``
     - ``ClientsReportView``
   * - ``CentrosTransferenciaView``
     - ``TransferCentersView``
   * - ``LlamadasAbandonadasView``
     - ``AbandonedCallsView``
   * - ``CentrosXSegmentoView``
     - ``CentersBySegmentView``
   * - ``MenusIVRView``
     - ``IvrMenusView``
   * - ``MenuRedirigidosView``
     - ``RedirectedMenusView``
   * - ``MenuCentroView``
     - ``CenterMenuView``

Actualizar ``apps/reports/urls.py``: imports y cualquier referencia
por nombre de clase.

T5.3 — ``MenuBuilder`` → ``NavigationMenuAssembler``
-----------------------------------------------------

``apps/core/navigation/builders.py``:

.. code-block:: python

   class NavigationMenuAssembler:   # era: MenuBuilder
       """Construye la estructura de navegacion a partir de los modulos."""

Buscar todos los imports y usos:

.. code-block:: bash

   grep -r "MenuBuilder" callcentersite/ --include="*.py" -l
   # Reemplazar en todos los archivos encontrados

**Commits:**
- ``refactor(pipeline,reports): renombrar _build_resumen_salud y 7 clases IVR (RA-011)``
- ``refactor(core): MenuBuilder → NavigationMenuAssembler (sufijo Builder prohibido)``

---

FASE 6 — OpenAPI/drf-spectacular: completar cobertura
======================================================

**Archivos:** ``apps/reports/ivr_views.py``, ``apps/logs/schema.py`` (nuevo)
**Commits:** 1

T6.1 — Tags en ``MenuRedirigidosView`` y ``MenuCentroView``
------------------------------------------------------------

Agregar ``tags=["Reportes de Llamadas"]`` en el ``@extend_schema``
de ambas views. (Después de T5.2 ya tendrán nuevos nombres:
``RedirectedMenusView`` y ``CenterMenuView``.)

T6.2 — Crear ``apps/logs/schema.py``
--------------------------------------

.. code-block:: python

   """
   schema.py — apps.logs
   OCP: SPECTACULAR_TAGS declarados aquí; collect_app_tags los recoge.
   """
   SPECTACULAR_TAGS = [
       {
           'name': 'Registros del Sistema',
           'description': (
               'Logs del sistema: tail Django, pipeline ETL, búsqueda, '
               'exportación, infraestructura y métricas. UC_LOG_01..08.'
           ),
       },
   ]

T6.3 — Verificar cobertura de nuevos endpoints
------------------------------------------------

Confirmar que todos los endpoints de FASE 4 tienen:
- ``@extend_schema`` con ``summary``, ``tags`` y ``responses``.
- Al menos HTTP 200 y HTTP 503 documentados.

**Commit:** ``feat(openapi): logs/schema.py + tags en RedirectedMenusView y CenterMenuView``

---

FASE 7 — Limpiar tests: modelos eliminados en FASE 3
=====================================================

**Archivos:** hasta 36 archivos en ``tests/``
**Commits:** 1

T7.1 — Eliminar tests de modelos ya eliminados
------------------------------------------------

Archivos a eliminar:

.. code-block:: bash

   rm tests/unit/pipeline/test_models.py
   rm tests/unit/core/test_core_etl_service.py

T7.2 — Limpiar referencias residuales en tests restantes
---------------------------------------------------------

Archivos a revisar y actualizar:

- ``tests/unit/core/test_core_serializers.py`` — eliminar tests de
  ``CallRecordSerializer``, ``CenterSerializer``, ``ServiceSerializer``.
- ``tests/unit/core/test_core_models.py`` — eliminar tests de modelos
  eliminados.
- ``tests/unit/core/test_permissions.py`` — eliminar permisos de
  modelos eliminados.
- ``tests/unit/core/test_service_access.py`` — limpiar.
- ``tests/api/test_core_api.py`` — eliminar tests de endpoints eliminados.
- ``tests/conftest.py`` — limpiar fixtures de Center, Service, CallRecord.
- ``tests/mocks/service_mocks.py`` — limpiar mocks de servicios eliminados.
- ``tests/test_data/core_test_data.py`` — limpiar datos de prueba de
  Center, Service, CallRecord.
- ``tests/integration/users/`` — revisar referencias indirectas.
- ``tests/unit/access/`` — verificar si algún test referencia CallRecord
  via los permisos de RBAC definidos en ``create_functions.py``.
- ``tests/unit/reports/test_cnst007_compliance.py`` — revisar.
- ``dashboard/tests/test_filter_service.py`` — eliminar tests de
  filtros por ``CallRecord``.

T7.3 — Verificar que los tests pasan
--------------------------------------

.. code-block:: bash

   python manage.py test --settings=config.settings.testing_local

**Commit:** ``test: limpiar tests de modelos CTI fuera de scope (FASE 3)``

---

FASE 8 — Nomenclatura en tests: ``Factory`` → ``TestData``
===========================================================

**Archivos:** ~90 clases en ``tests/factories/`` (8 archivos),
todos los tests que las importan.
**Commits:** 2

T8.1 — Renombrar clases en ``tests/factories/``
------------------------------------------------

Regla mecánica: ``s/Factory/TestData/g`` en nombres de clase.
La herencia ``factory.django.DjangoModelFactory`` se mantiene.

Archivos afectados:

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Archivo
     - Clases a renombrar (muestra)
   * - ``access_factories.py``
     - ``ModuleFactory`` → ``ModuleTestData``, etc. (11 clases)
   * - ``alert_factories.py``
     - ``AlertFactory`` → ``AlertTestData``, etc. (~30 clases)
   * - ``audit_factories.py``
     - ``AuditLogFactory`` → ``AuditLogTestData``, etc. (12 clases)
   * - ``authentication_factories.py``
     - ``LoginAttemptFactory`` → ``LoginAttemptTestData``, etc. (4 clases)
   * - ``core.py``
     - ``CenterFactory`` → ``CenterTestData`` (eliminado en T7 si Center fue eliminado)
   * - ``dashboard_factories.py``
     - ``DashboardConfigFactory`` → ``DashboardConfigTestData``, etc. (15 clases)
   * - ``pipeline_factories.py``
     - ``ETLJobFactory`` → ``ETLJobTestData``, etc. (18 clases — revisar si aplican)
   * - ``report_factories.py``
     - ``ReportFactory`` → ``ReportTestData``, etc. (19 clases)
   * - ``user_factory.py``
     - ``UserFactory`` → ``UserTestData``, etc. (5 clases)

T8.2 — Actualizar todos los imports
-------------------------------------

.. code-block:: bash

   # Encontrar todos los archivos que importan desde factories/
   grep -r "from tests.factories\|from .factories" \
       callcentersite/tests/ --include="*.py" -l

   # Para cada archivo, actualizar:
   # from tests.factories.user_factory import UserFactory
   # → from tests.test_data.user_test_data import UserTestData

T8.3 — Mover archivos a ``tests/test_data/`` y eliminar duplicados
-------------------------------------------------------------------

Verificar conflictos entre ``tests/factories/*.py`` y
``tests/test_data/*_test_data.py`` antes de mover:

.. code-block:: bash

   diff tests/factories/access_factories.py \
        tests/test_data/access_test_data.py

Si hay diferencias: fusionar contenido en ``tests/test_data/``.
Si son equivalentes: el ``tests/factories/`` es redundante.

Después de verificar:

.. code-block:: bash

   rm -rf callcentersite/tests/factories/
   rm -rf callcentersite/tests/testdata/    # duplicado idéntico de test_data/

T8.4 — Verificar tests pasan
------------------------------

.. code-block:: bash

   python manage.py test --settings=config.settings.testing_local

**Commits:**
- ``refactor(tests): Factory → TestData en tests/factories/ (RA-011)``
- ``chore(tests): eliminar tests/factories/ y tests/testdata/ — consolidar en test_data/``

---

Resumen de FASES, archivos y commits
=====================================

.. list-table::
   :widths: 8 30 25 12 15 10
   :header-rows: 1

   * - FASE
     - Descripción
     - Archivos principales
     - Riesgo
     - BD afectada
     - Commits
   * - 1
     - Bug NameError etl_data_availability
     - pipeline/views.py
     - CRÍTICO
     - Ninguna
     - 1
   * - 2
     - Eliminar apps/ivr/ (código muerto)
     - apps/ivr/, tests/unit/ivr_legacy/
     - Bajo
     - PostgreSQL (django_migrations)
     - 1
   * - 3
     - Eliminar modelos CTI fuera de scope
     - pipeline/models.py + 40 archivos
     - Alto
     - PostgreSQL (DeleteModel × 5)
     - 4
   * - 4
     - Nuevos endpoints IACT-db
     - ivr_services, ivr_views, logs/views, pipeline/views
     - Bajo
     - MariaDB (solo lectura)
     - 3
   * - 5
     - Renombres RA-011 en producción
     - ivr_views.py, pipeline/views.py, builders.py
     - Bajo
     - Ninguna
     - 2
   * - 6
     - OpenAPI completeness
     - logs/schema.py (nuevo), ivr_views.py
     - Bajo
     - Ninguna
     - 1
   * - 7
     - Limpiar tests FASE 3
     - hasta 36 archivos en tests/
     - Medio
     - Ninguna
     - 1
   * - 8
     - Factory → TestData
     - tests/factories/ (8 archivos)
     - Medio
     - Ninguna
     - 2

**Total:** 8 FASES, ~15 commits, ~50 archivos modificados o eliminados.

Orden de ejecución recomendado
================================

.. code-block:: text

   FASE 1 → FASE 2 → FASE 3 → FASE 7 → FASE 4 → FASE 5 → FASE 6 → FASE 8

   FASE 1: fix inmediato, independiente
   FASE 2: independiente, sin dependencias
   FASE 3: debe ir antes de FASE 7 (tests dependen de modelos)
   FASE 7: inmediatamente después de FASE 3
   FASE 4: independiente, puede ir en paralelo con FASE 5
   FASE 5: independiente
   FASE 6: después de FASE 4 (verifica @extend_schema de nuevos endpoints)
   FASE 8: al final (tests deben estar limpios de FASE 7)

Lo que NO cambia
=================

.. list-table::
   :widths: 50 50
   :header-rows: 1

   * - Elemento
     - Razón
   * - Strings de SPs: ``'sp_rpt_clientes'``, etc.
     - Contratos de BD (RA-011 § 6.2)
   * - Columnas SQL en queries raw: ``'trimestre'``, ``'total_llamadas'``
     - Contratos de BD
   * - ``CMENUErrorView``
     - cMENU es término del dominio, no español
   * - ``ivr_views.py`` e ``ivr_services.py`` (nombres de archivo)
     - IVR es acrónimo inglés — nombres aceptables
   * - Endpoints activos: UC_PIP_01..04, UC_RPT_12..17, UC_LOG_01..07
     - En scope — no se tocan
   * - IACT-docs
     - No se actualiza
