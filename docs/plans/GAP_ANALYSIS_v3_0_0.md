# Gap Analysis v3.0.0 — Spec ETL IVR v2.1 vs Implementación

**Fecha:** 2026-05-08
**Spec fuente:** `feature/etl-ivr-pipeline-spec` commit `c987d529`
**Archivos spec:** `source/arquitectura-tecnica/pipeline-etl-iact/` (8 archivos, ~1970 líneas)
**Base de código:** `/tmp/references/IACT-api/callcentersite` rama `develop`
**Estado de partida:** 640 passed, 0 failed, 4 skipped en `tests/unit/`

---

## Resumen ejecutivo

El spec v2.1 define 6 niveles arquitectónicos para el pipeline ETL IVR.
Los niveles 0–5 son puramente MariaDB y están desplegados.
El nivel 6 (Django) tiene **3 brechas reales** y **2 no-brechas** confirmadas
después del análisis profundo.

| Brecha | Tipo | Severidad | Tarea |
|--------|------|-----------|-------|
| `manage.py run_etl` no existe | Real | Alta | T-001 |
| ETLScheduler llama ETLService desactivado, no sp_etl_maestro | Real | Alta | T-002 |
| `sp_rpt_menu_redirigidos` y `sp_rpt_menu_centro` fusionados en un único endpoint | Real | Media | T-003 |
| Alias `ivr_cliente` (spec) vs `ivr` (settings) | No-brecha — nomenclatura | Info | — |
| URL `/api/ivr/` (spec) vs `/api/reports/ivr/` (API) | No-brecha — organización válida | Info | — |

---

## Distinción crítica: dos conceptos de "menú"

Este es el punto de mayor confusión en el análisis. Son dos dominios completamente
distintos que comparten la palabra "menú".

### Menú IVR (campo de datos de llamadas)

El campo `cMenu` en `tbl_historico_*` registra la opción del árbol de decisión
telefónico que navegó el llamante durante una llamada. El ETL lo normaliza con
`fn_normalizar_menu()` y lo materializa en `base_ivr_detalle.menu`.

Dos SPs producen reportes analíticos distintos sobre este campo:

| SP | Grain | Semántica |
|----|-------|-----------|
| `sp_rpt_menu_redirigidos` | `menu × opcion` (excluye `SIN_OPCION`) | Distribución de opciones que el llamante eligió en cada menú |
| `sp_rpt_menu_centro` | `menu × centro_transferencia` | A qué centro de transferencia llegó cada menú IVR |

El spec v2.1 los define como **endpoints separados**:
`ivr/menu-redirigidos/` y `ivr/menu-centro/`.

La implementación actual los fusiona en **un único endpoint**
`GET /api/reports/ivr/menus/?vista=redirigidos|menu_centro`.

Adicionalmente, el spec define los SPs con solo `p_quarter` como parámetro,
pero la implementación pasa también `p_segmento`. Los integration tests
pasan (13/13), indicando que los SPs desplegados aceptan el parámetro extra.
Pendiente de verificación cuando MariaDB esté estable en el entorno.

### Menú del sistema (navegación UX del usuario IACT)

El árbol de módulos `Domain → Section → Action` que cada usuario autenticado
ve en la interfaz. Definido por `CNST-032` y `UC_PERM_08`.

El spec v5.6.x define `MenuItem` como wrapper UX 1:1 sobre `Function` con
lifecycle propio (DRAFT/ACTIVE/DEPRECATED/ARCHIVED).

La implementación actual usa `Module` (modelo anterior) con:
- `navigation_menu_view` en `GET /api/navigation/menu/`
- `MyModulesView` en `GET /api/access/my-modules/`

**`MenuItem` del spec v5.6.x no está implementado como modelo Django.**
Es deuda del módulo de permisos RBAC — no del pipeline ETL.
Se resuelve en el plan v3.1.0, no en v3.0.0.

---

## Análisis nivel por nivel

### Nivel 0 — Funciones SQL utilitarias

| Componente | Estado spec | Estado API |
|-----------|-------------|------------|
| 7 funciones (`fn_did_segmento`, `fn_normalizar_centro`, `fn_normalizar_menu`, `fn_duracion_seg`, `ivr_es_dia_semana` y derivadas) | Desplegadas en MariaDB | No aplica — son objetos MariaDB |

Sin brecha.

### Nivel 1A — `evt_etl_diario` (MySQL Event Scheduler)

| Componente | Estado spec | Estado API |
|-----------|-------------|------------|
| `evt_etl_diario` | `pendiente-implementacion` | No existe. El `ETLScheduler` usa `IntervalTrigger(hours=12)` y llama código desactivado |

El MySQL Event es infraestructura de base de datos — se despliega con
`CREATE EVENT evt_etl_diario` vía script SQL por ops, no por este plan.
**No es tarea del API.**

El `ETLScheduler` sí debe complementar el MySQL Event pero actualmente
llama código desactivado — ver Nivel 6D.

### Nivel 1B — `manage.py run_etl` + heartbeat

| Componente | Estado spec | Estado API |
|-----------|-------------|------------|
| Management command `run_etl` | `pendiente-implementacion` | **NO EXISTE** |

No hay management command `run_etl` en ningún `apps/*/management/commands/`.

El spec (`triggers.rst`) define el contrato exacto:

```python
# Contrato requerido por el spec
class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--quarter', type=str, default=None)
        parser.add_argument('--force',   action='store_true')

    def handle(self, *args, **options):
        # INSERT en etl_runs con timeout_at = NOW() + 30 MINUTE
        # Thread heartbeat daemon con threading.Event, check cada 2 min
        # connections['ivr'].cursor().callproc('sp_etl_maestro', [])
        # UPDATE etl_runs.status en finally
```

Nota: el spec usa el alias `ivr_cliente` pero el settings real usa `ivr`.
El command debe usar `connections['ivr']`.

**Brecha real → T-001.**

### Nivel 2 — `sp_etl_maestro`

| Componente | Estado spec | Estado API |
|-----------|-------------|------------|
| `sp_etl_maestro` | Desplegado en MariaDB | `EtlRetryView` invoca `sp_etl_historico` (no `sp_etl_maestro`) directamente |

El scheduler no llama `sp_etl_maestro` — ver Nivel 6D.

### Niveles 3, 4 — SPs ETL y tablas

Sin brecha. Son objetos MariaDB, no código Django.
`EtlStatusView` lee `job_execution_log` via `connections['ivr']`.
`EtlRetryView` lee `etl_runs` via `connections['ivr']`.

### Nivel 5 — SPs de reporte (7 `sp_rpt_*`)

Sin brecha. `apps/reports/ivr_services.py` invoca los 7 SPs.
Verificado por 13 integration tests en `tests/integration/pipeline/`.

### Nivel 6A — DATABASES dual

| Spec | API |
|------|-----|
| Alias `ivr_cliente` | Alias `ivr` (en `config/settings/base.py`) |

No-brecha funcional. Solo nomenclatura. El código usa `connections['ivr']`
correctamente. El spec v2.1 fue escrito después del código y usó un nombre
distinto. No requiere cambio.

### Nivel 6B — `services/ivr_reports.py`

Sin brecha. `apps/reports/ivr_services.py` existe con los 7 SPs:
`get_clients`, `get_transfer_centers`, `get_abandoned_calls`,
`get_cmenu_errors`, `get_centers_by_segment`, `get_redirected_menus`,
`get_center_menus`.

### Nivel 6C — 7 endpoints REST

| SP | URL spec | URL API | Estado |
|----|----------|---------|--------|
| `sp_rpt_centros_transferencia` | `ivr/centros-transferencia/` | `ivr/transfer-centers/` | OK |
| `sp_rpt_centros_xsegmento` | `ivr/centros-xsegmento/` | `ivr/centers-by-segment/` | OK |
| `sp_rpt_llamadas_abandonadas` | `ivr/llamadas-abandonadas/` | `ivr/abandoned/` | OK |
| `sp_rpt_menu_redirigidos` | `ivr/menu-redirigidos/` | fusionado en `ivr/menus/?vista=redirigidos` | **GAP** |
| `sp_rpt_menu_centro` | `ivr/menu-centro/` | fusionado en `ivr/menus/?vista=menu_centro` | **GAP** |
| `sp_rpt_cMENU_ERROR` | `ivr/menu-error/` | `ivr/menu-errors/` | OK |
| `sp_rpt_clientes` | `ivr/clientes/` | `ivr/clients/` | OK |

Los dos endpoints de menú IVR tienen semántica distinta y deben ser
independientes. `MenusIVRView` los fusiona en un parámetro `?vista=`
que el spec no contempla.

**Brecha real → T-003.**

### Nivel 6D — APScheduler → `sp_etl_maestro`

Cadena actual (incorrecta):
```
APScheduler (cada 12h, IntervalTrigger)
  → ETLScheduler.run_etl()
    → ETLExecution.objects.create() en PostgreSQL  ← modelo v1
    → ETLService.run()                             ← desactivado desde 2026-03-21
    → return {'extracted': 0, 'loaded': 0}
```

Cadena requerida por el spec:
```
APScheduler (02:00 AM, CronTrigger)
  → ETLScheduler.run_etl()
    → etl_runs INSERT en MariaDB                   ← modelo v2.1
    → connections['ivr'].callproc('sp_etl_maestro')
    → etl_runs UPDATE status
```

**Brecha real → T-002.**

---

## Integration tests: cobertura actual vs objetivo

| Test | Endpoint | Estado actual |
|------|----------|---------------|
| `TestETLStatus` (2) | `GET /api/pipeline/status/` | Pasa |
| `TestETLRetry` (4) | `POST /api/pipeline/retry/` | Pasa |
| `TestIVRClientsReport` (3) | `GET /api/reports/ivr/clients/` | Pasa |
| `TestIVRHealth` (1) | `GET /api/pipeline/ivr-health/` | Pasa |
| `TestETLLogTail` (3) | log endpoint | Pasa |
| `TestIVRMenuRedirigidos` | `GET /api/reports/ivr/menu-redirigidos/` | **Falta — T-005** |
| `TestIVRMenuCentro` | `GET /api/reports/ivr/menu-centro/` | **Falta — T-005** |

---

## Lo que este análisis descartó como no-brecha

1. **Alias `ivr_cliente`**: el settings usa `ivr`. Diferencia de nomenclatura
   entre el spec y el código preexistente. No requiere cambio.

2. **URL base `/api/ivr/` vs `/api/reports/ivr/`**: el spec usó un prefijo
   simplificado. La implementación organiza los endpoints bajo `reports/`
   de forma consistente con el resto de la API. Es una decisión de diseño
   válida, no un error.

3. **`evt_etl_diario`**: es infraestructura MariaDB, no código Django.
   Se despliega por ops con un script SQL.
