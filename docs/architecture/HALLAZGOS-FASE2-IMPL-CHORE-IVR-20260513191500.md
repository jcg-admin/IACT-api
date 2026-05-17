# Hallazgos — Implementación FASE 2

**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Alcance:** FASE 2 del plan PLAN-ACTUALIZACION-COMPLETO-20260513185000.md
**Objetivo:** Eliminar ``apps/ivr/`` — código muerto con fecha de baja 2026-03-21
**Commit:** ``769f302``
**Impacto:** 33 archivos — 24 eliminados, 9 modificados; 1068 líneas eliminadas

---

Resumen de tareas ejecutadas
=============================

.. list-table::
   :widths: 10 60 15 15
   :header-rows: 1

   * - Tarea
     - Descripción
     - Estado
     - Hallazgos
   * - T2.1
     - Quitar ``'apps.ivr'`` de INSTALLED_APPS
     - COMPLETO
     - —
   * - T2.2
     - Simplificar ``config/db_router.py``
     - COMPLETO
     - H-F2-001, H-F2-003
   * - T2.3
     - Eliminar ``apps/ivr/``, ``tests/unit/ivr_legacy/``, ``ivr_factories.py``
     - COMPLETO
     - —
   * - T2.4
     - Verificar cero referencias residuales
     - COMPLETO
     - H-F2-002, H-F2-004, H-F2-005
   * - T2.5
     - Documentar paso de migración en producción
     - DOCUMENTADO
     - H-F2-003

---

H-F2-001 — ``db_router.py`` tenía lógica activa dependiente de ``apps.ivr``
=============================================================================

**Severidad:** MEDIA — no producía errores, pero dejaba routing muerto sin la app.
**Estado:** CORREGIDO.

El plan original clasificó ``config/db_router.py`` como solo una
referencia en docstring. Al leer el código completo se encontró que
``ivr_apps = {'ivr'}`` era un atributo de clase activo usado en tres
métodos:

.. code-block:: python

   # ANTES — lógica dependiente de la app eliminada:
   ivr_apps = {'ivr'}

   def db_for_read(self, model, **hints):
       if app_label in self.ivr_apps:   # ← nunca True sin la app
           return 'ivr'

   def allow_migrate(self, db, app_label, ...):
       if app_label in self.ivr_apps:
           return db == 'ivr'           # ← lógica inerte sin la app
       return db == 'default'

Sin ``apps.ivr`` cargado, ``app_label`` nunca sería ``'ivr'`` en
llamadas ORM reales. La lógica era inerte pero dejaba el código
describiendo un invariante falso.

Adicionalmente, los tres test functions inline al final del archivo
probaban el comportamiento del router con la app ``'ivr'`` activa:

.. code-block:: python

   def test_router_write_readonly():
       class MockIVRModel:
           class _meta:
               app_label = 'ivr'
       assert router.db_for_write(MockIVRModel) is None   # ← probaba write bloqueado

   def test_router_migrations_readonly():
       assert router.allow_migrate('default', 'ivr') is False
       assert router.allow_migrate('ivr', 'ivr') is True  # ← lógica de app eliminada

Simplificación aplicada: el router ahora dirige todo el ORM a
``'default'`` y bloquea todas las migrations en ``'ivr'`` con
``return db == 'default'``, sin necesidad de mantener una lista
de apps. MariaDB sigue protegida: ninguna migration Django se
ejecuta en ella.

---

H-F2-002 — 5 archivos adicionales con referencias a ``apps.ivr`` no identificados en el plan
==============================================================================================

**Severidad:** BAJA — todas en comentarios, pero dejaban referencias a módulo inexistente.
**Estado:** CORREGIDO.

El plan original identificó 3 ubicaciones fuera de ``apps/ivr/``.
El análisis exhaustivo encontró 5 adicionales:

.. list-table::
   :widths: 50 50
   :header-rows: 1

   * - Archivo
     - Tipo de referencia
   * - ``tests/test_data/ivr_test_data.py``
     - Archivo entero con código comentado — referenciaba modelos
       inexistentes de ``apps.ivr``. **Eliminado.**
   * - ``tests/testdata/ivr_test_data.py``
     - Duplicado idéntico del anterior. **Eliminado.**
   * - ``tests/mocks/database_mocks.py``
     - Bloque de 6 fixtures comentadas (``mock_ivr_connection`` y
       derivadas). Incluía instrucción "Reactivar cuando..." que
       ya no era posible. **Limpiado.**
   * - ``apps/pipeline/services/etl_service.py``
     - Bloque DEUDA TÉCNICA con import comentado de
       ``apps.ivr.adapters.IVRAdapter``. **Limpiado.**
   * - ``apps/core/services/etl_service.py``
     - Ídem — mismo bloque con el import incorrecto original
       (``apps.ivr_legacy``) y el correcto. **Limpiado.**

---

H-F2-003 — La migración ``ivr/0001_initial`` está en MariaDB, no en PostgreSQL
===============================================================================

**Severidad:** MEDIA — paso de producción requerido antes del próximo deploy.
**Estado:** DOCUMENTADO — requiere ejecución manual en producción.

El ``allow_migrate`` del router original dirigía las migrations
de la app ``'ivr'`` al alias ``'ivr'`` (MariaDB):

.. code-block:: python

   if app_label in self.ivr_apps:    # 'ivr' estaba en el set
       return db == 'ivr'             # True → migrations iban a MariaDB

Si ``python manage.py migrate`` se ejecutó con esta configuración,
la tabla ``django_migrations`` en MariaDB contiene la entrada:

.. code-block:: text

   app='ivr', name='0001_initial'

Ahora que ``apps/ivr/`` está eliminado y el router ya no redirige
migrations a MariaDB, esta entrada es un registro huérfano.

**Acción requerida en producción antes del próximo deploy:**

.. code-block:: sql

   -- Ejecutar en MariaDB (ivr_legacy), NO en PostgreSQL:
   DELETE FROM django_migrations WHERE app = 'ivr';

Si la tabla ``django_migrations`` no existe en MariaDB (porque
``migrate`` nunca se ejecutó en ese alias), este paso no es
necesario. Verificar primero:

.. code-block:: sql

   SELECT * FROM django_migrations WHERE app = 'ivr';

El modelo ``TblTempPruebaIvr`` tenía ``managed=False`` — Django
nunca creó ni modificó la tabla ``tbl_temp_prueba_ivr`` en MariaDB.
El único efecto de revertir la migración es eliminar el registro
en ``django_migrations``.

---

H-F2-004 — Dos fixtures en ``conftest.py`` sin tests que las usaran
====================================================================

**Severidad:** BAJA — no producían errores, pero referenciaban código eliminado.
**Estado:** CORREGIDO — fixtures eliminados.

``tests/conftest.py`` tenía dos fixtures que importaban código de
``apps/ivr/`` o dependían de fixtures IVR eliminadas:

``quarterly_data_with_mocks``:

.. code-block:: python

   from tests.test_data.ivr_test_data import CompleteQuarterDataTestData
   # ← ImportError en cuanto ivr_test_data.py fue eliminado

``etl_job_with_mocks``:

.. code-block:: python

   def etl_job_with_mocks(db, mock_ivr_connection, mock_etl_service):
   # ← mock_ivr_connection eliminado de database_mocks.py

Verificación: ningún archivo de tests usaba ninguno de los dos
fixtures (``grep`` sin resultados). Ambos eliminados sin impacto.

---

H-F2-005 — ``tests/mocks/__init__.py`` referenciaba fixtures IVR eliminadas
============================================================================

**Severidad:** BAJA — comentario, no código activo.
**Estado:** CORREGIDO.

``tests/mocks/__init__.py`` contenía un bloque de texto sobre
fixtures ``mock_ivr_connection`` y derivadas con la instrucción
"Reactivar cuando el schema real de ivr_legacy esté provisionado."

Dado que ``apps/ivr/`` no existe y nunca existirá en su forma
original (la arquitectura real usa raw SQL via ``connections['ivr']``),
la instrucción "Reactivar" era incorrecta. Bloque eliminado.

---

Estado final de FASE 2
=======================

.. list-table::
   :widths: 50 50
   :header-rows: 1

   * - Indicador
     - Valor
   * - Archivos eliminados
     - 24 (19 de apps/ivr/ + 4 de tests/unit/ivr_legacy/ + 1 de factories)
   * - Archivos eliminados adicionales (H-F2-002)
     - 2 (ivr_test_data.py en test_data/ y testdata/)
   * - Archivos modificados
     - 9
   * - Líneas eliminadas netas
     - 1068
   * - Referencias residuales a apps.ivr
     - 0 (verificado con 15 patrones de búsqueda)
   * - Tests rotos
     - 0 (ningún test activo usaba los fixtures eliminados)
   * - Migraciones de BD
     - 0 aplicadas en esta FASE
   * - Deuda técnica generada
     - Ninguna
   * - Paso pendiente en producción
     - H-F2-003: DELETE FROM django_migrations WHERE app='ivr' en MariaDB
