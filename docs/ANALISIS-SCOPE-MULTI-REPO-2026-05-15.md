# ANALISIS-SCOPE-MULTI-REPO-2026-05-15

**Documento:** ANALISIS-SCOPE-MULTI-REPO-2026-05-15
**Fecha:** 2026-05-15
**Propósito:** Inventario de deuda técnica en los tres repositorios del sistema IACT

---

## 1. Diagnóstico: trabajo previo acotado a IACT-api

Todo el trabajo de las sesiones FASE 7B-7F se enfocó exclusivamente en IACT-api.
IACT-ui e IACT-db no fueron inspeccionados ni corregidos.

---

## 2. IACT-api — estado tras las sesiones FASE 7

| Métrica | Inicio | Final |
|---|---|---|
| Tests | 434 passed / 710 errors | **1335 passed / 0 errors** |
| xfailed | 137 (strict=False) | **0** |
| skipped | 61 | **0** |
| flake8 F401 | 122 | **0** |
| flake8 F841 | 15 | **0** |
| TODOs | 4 | **0** |
| except:pass silenciosos | 7 | **0** |
| django check W001/W002 | 9 | **0** |

---

## 3. IACT-ui — estado actual (no trabajado)

**Tests:** 2366 passed, 250 suites — OK.

**ESLint: 469 problemas (8 errores, 461 warnings)**

### Errores críticos (severity=error, rompen build):

| Archivo | Línea | Regla | Problema |
|---|---|---|---|
| `src/pages/alerts/AlertConfig.jsx` | 76, 272 | `no-undef` | `setDryRunResult` usado pero **no declarado** |
| `src/pages/reports/AgentsReport.jsx` | 62 | `no-empty` | `catch (_) {}` vacío |
| `src/pages/reports/CampaignsReport.jsx` | 60 | `no-empty` | `catch (_) {}` vacío |
| `src/pages/reports/QueuesReport.jsx` | 62 | `no-empty` | `catch (_) {}` vacío |
| `src/mocks/mockInterceptor.js` | 1935, 2012, 2062 | `no-empty` | `catch (_) {}` vacíos |

**Análisis de `setDryRunResult` (no-undef):**
`AlertConfig.jsx` lee `dryRunResult` del store Redux (`useSelector(selectDryRunResult)`)
pero en la línea 76 (`handleCreate`) y 272 (`Limpiar`) llama a `setDryRunResult(null)`,
que nunca se declara. El estado vive en Redux, no en estado local. Las llamadas
a `setDryRunResult(null)` son de una refactorización incompleta: el código
migró de `useState(null)` a Redux pero dejó llamadas al setter local.
**Impacto:** la función `handleCreate` y el botón "Limpiar" lanzan
`ReferenceError: setDryRunResult is not defined` en runtime.

**Análisis de `catch (_) {}` en Reports:**
Los tres reportes (`AgentsReport`, `CampaignsReport`, `QueuesReport`) tienen
`try { const name = prompt(...) } catch (_) {}` — bloque vacío donde si
`prompt()` falla o el usuario cancela el guardado de filtros, el error
se consume silenciosamente sin feedback al usuario.

### Warnings (461):

| Regla | Count | Descripción |
|---|---|---|
| `react/prop-types` | 257 | Props sin declaración de tipo |
| `no-unused-vars` | 145 | Variables declaradas pero no usadas |
| `no-console` | 41 | `console.log/warn/error` en producción |
| `react-hooks/exhaustive-deps` | 18 | Dependencias faltantes en `useEffect`/`useCallback` |
| `no-empty` | 6 | (incluidos en errores arriba) |

**Archivos con más `no-unused-vars`:**
- `mocks/mockInterceptor.js` — 10 variables
- `layouts/DashboardLayout/DashboardLayout.jsx` — 4 variables
- `components/pages/JobMonitoring/JobMonitoring.jsx` — 3 variables

---

## 4. IACT-db — estado actual (no trabajado)

**Script de verificación:** `test/check_db_connections.py`

El script tiene `sys.exit(1)` a nivel de módulo cuando faltan dependencias.
Esto hace que pytest lo recoja pero falle con `INTERNALERROR: SystemExit: 1`
en lugar de un test que falle descriptivamente.

**Scripts SQL:** 13 stored procedures + vistas + funciones en MariaDB.
No se auditaron para errores silenciosos en SQL (DECLARE EXIT HANDLER vacíos,
SIGNAL SQLSTATE sin mensaje, etc.).

**Verify script (`verify.sh`):** bien estructurado, verifica conectividad
MariaDB + PostgreSQL + schema completo. No se ejecutó para ver el estado real.

---

## 5. Plan de trabajo pendiente por repositorio

### IACT-ui (prioridad alta — hay errors que rompen runtime)

1. **Corregir `no-undef` en AlertConfig.jsx** — eliminar llamadas a
   `setDryRunResult(null)` o restaurar el `useState` si era intencional.
2. **Corregir `no-empty` en Reports** — añadir `console.warn` o comentario
   explicativo en los `catch (_) {}`.
3. **Corregir `no-empty` en mockInterceptor.js** — idem (archivo de mocks).
4. **Reducir `no-unused-vars`** — las 145 variables no usadas son ruido
   que oculta variables que SÍ deberían usarse.
5. **Reducir `no-console`** — reemplazar con logger estructurado o eliminar.
6. **`react-hooks/exhaustive-deps`** — 18 casos pueden causar bugs de stale
   closures en producción.

### IACT-db (prioridad media)

1. **Corregir `check_db_connections.py`** — eliminar `sys.exit(1)` a nivel
   de módulo; convertir a test descriptivo que falle con mensaje claro.
2. **Auditar stored procedures** — verificar DECLARE EXIT HANDLER, SIGNAL
   SQLSTATE, y manejo de errores en los 13 SPs.
3. **Ejecutar `verify.sh`** — verificar el estado real del schema.

---

*Generado: 2026-05-15*
