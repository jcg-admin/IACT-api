# Hallazgos — Implementación FASE 5

**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Alcance:** FASE 5 del plan PLAN-ACTUALIZACION-COMPLETO-20260513185000.md
**Objetivo:** Renombres de nomenclatura en código de producción — alineación con RA-011
**Commit:** `601303e`
**Referencia:** `docs/conventions/CLEAN_CODE_NAMING_PRINCIPLES_v1_0_0.md`
**Impacto:** 7 archivos, 38 inserciones / 38 eliminaciones (sustituciones exactas)

---

## Resumen de tareas ejecutadas

| Tarea | Cambio | Archivos | Estado |
|---|---|---|---|
| T5.1 | `_build_resumen_salud` → `_build_pipeline_health_summary` | `pipeline/views.py` | COMPLETO |
| T5.2 | 7 clases de vistas IVR en español → inglés | `ivr_views.py`, `reports/urls.py` | COMPLETO |
| T5.3 | `MenuBuilder` → `NavigationMenuAssembler` | `builders.py`, `views.py`, 2 archivos de tests | COMPLETO |

---

## H-F5-001 — `test_navigation_views.py` prueba métodos inexistentes en la view real

**Severidad:** MEDIA — los tests ya fallaban silenciosamente antes de FASE 5.
**Estado:** DOCUMENTADO — fuera del scope de FASE 5 (es un bug de tests, no de nomenclatura). Aplaza a FASE 7 (limpieza de tests).

Los tests en `test_navigation_views.py` usan `@patch` sobre `NavigationMenuAssembler` (antes `MenuBuilder`) y configuran el mock para el método `build_user_menu`:

```python
@patch('apps.core.navigation.views.NavigationMenuAssembler')
def test_menu_endpoint_returns_user_menu(self, mock_builder_class, ...):
    mock_builder = Mock()
    mock_builder.build_user_menu.return_value = sample_menu   # ← método inexistente
    mock_builder_class.return_value = mock_builder
```

Sin embargo, `navigation/views.py` usa `build_from_modules()` y `build_flat()` — nunca llama a `build_user_menu`:

```python
# navigation/views.py — método real usado:
builder = NavigationMenuAssembler()
menu = builder.build_from_modules(modules, user=request.user)   # ← no build_user_menu
```

El test parchea el constructor de la clase y configura el mock con un método que no existe en la implementación real. Al ejecutar el test, el mock acepta cualquier llamada (por ser `Mock()`), por lo que la prueba no falla — pero tampoco verifica el comportamiento real. El test `test_menu_endpoint_serializes_menu` también usa un `MenuSerializer` que no existe en la view real.

En FASE 5 se actualizaron los patch paths (de `MenuBuilder` a `NavigationMenuAssembler`) sin cambiar la lógica de los tests. Esa corrección pertenece a FASE 7 (tests), no a FASE 5 (nomenclatura).

---

## H-F5-002 — `test_navigation_builders.py` importa `NavigationMenuAssembler` sin usarla

**Severidad:** BAJA — import huérfano, no falla, pero viola el principio de no tener código muerto.
**Estado:** DOCUMENTADO — fuera del scope de FASE 5.

`test_navigation_builders.py` importa `NavigationMenuAssembler` (antes `MenuBuilder`) en la línea 16:

```python
from apps.core.navigation.builders import MenuValidator, NavigationMenuAssembler
```

El archivo contiene tests para `MenuValidator` (clase `TestMenuValidator`). La sección `# TESTS NavigationMenuAssembler` al final del archivo está vacía — el comentario existe pero no hay métodos de test.

El archivo documenta que:

> "TestMenuBuilder, TestMenuSerializer, TestMenuBuilderIntegration eliminados: pertenecen a T-102 (MenuItem) — se crearán cuando la funcionalidad esté implementada."

El import de `NavigationMenuAssembler` se mantiene actualizado (el renombre se aplicó correctamente). El import huérfano y la sección vacía se limpiarán en FASE 7.

---

## H-F5-003 — `CMENUErrorView` no se renombró — decisión correcta confirmada

**Severidad:** Informativo — confirma la decisión del plan.
**Estado:** Documentado.

`CMENUErrorView` no fue renombrada. El prefijo `cMENU` es la referencia al campo `cMenu` de la tabla `base_ivr_detalle` en MariaDB — es un término del dominio de la base de datos IVR, no una palabra en español.

Verificación: la columna existe en IACT-db:

```sql
-- base_ivr_detalle
menu  VARCHAR(100) NOT NULL
      COMMENT 'Valor raw de cMenu normalizado...'
```

El SP correspondiente también usa el término: `sp_rpt_cMENU_ERROR`. `cMENU` es parte del vocabulario controlado del sistema IVR y no está sujeto a RA-011 (los strings de contrato de BD no son identificadores Python). La clase mantiene este prefijo para claridad de qué concepto del dominio representa.

---

## H-F5-004 — Scope real de T5.3: 4 archivos en lugar de 2

**Severidad:** Informativo — el plan subestimó el alcance del renombre.
**Estado:** Implementado correctamente.

El plan de FASE 5 identificó 2 archivos para el renombre de `MenuBuilder`:
- `apps/core/navigation/builders.py` (definición)
- `apps/core/navigation/views.py` (uso)

La auditoría encontró 2 archivos adicionales con referencias activas:
- `tests/unit/core/test_navigation_views.py` — 9 ocurrencias en decoradores `@patch`
- `tests/unit/core/test_navigation_builders.py` — 4 ocurrencias (1 import + 3 en sección de comentarios/estructura)

Sin actualizar los tests, `@patch('apps.core.navigation.views.MenuBuilder')` hubiera roto la canalización de patches (Python no encontraría el atributo `MenuBuilder` en el módulo — la clase ya se llama `NavigationMenuAssembler`). Los 4 archivos se actualizaron en el mismo commit.

---

## Tabla de renombres aplicados

| Identificador original | Identificador nuevo | Archivo | Motivo |
|---|---|---|---|
| `_build_resumen_salud` | `_build_pipeline_health_summary` | `pipeline/views.py` | Español en función privada de producción |
| `ClientesReportView` | `ClientsReportView` | `ivr_views.py`, `urls.py` | `Clientes` en español |
| `CentrosTransferenciaView` | `TransferCentersView` | `ivr_views.py`, `urls.py` | `Centros`, `Transferencia` en español |
| `LlamadasAbandonadasView` | `AbandonedCallsView` | `ivr_views.py`, `urls.py` | `Llamadas`, `Abandonadas` en español |
| `CentrosXSegmentoView` | `CentersBySegmentView` | `ivr_views.py`, `urls.py` | `Centros`, `Segmento` en español |
| `MenusIVRView` | `IvrMenusView` | `ivr_views.py`, `urls.py` | Orden incorrecto; `IVR` debe preceder |
| `MenuRedirigidosView` | `RedirectedMenusView` | `ivr_views.py`, `urls.py` | `Redirigidos` en español |
| `MenuCentroView` | `CenterMenuView` | `ivr_views.py`, `urls.py` | `Centro` en español |
| `MenuBuilder` | `NavigationMenuAssembler` | `builders.py`, `views.py`, 2 tests | Sufijo `Builder` prohibido por RA-011 |

**Sin cambio:**
- `CMENUErrorView` — `cMENU` es término del dominio IVR (contrato de BD), no español

---

## Estado final de FASE 5

| Indicador | Valor |
|---|---|
| Archivos modificados | 7 |
| Renombres aplicados | 9 identificadores |
| Referencias residuales a nombres anteriores | 0 |
| Archivos con errores de sintaxis | 0 |
| Deuda técnica generada | Ninguna |
| Hallazgos que aplaza a FASE 7 | H-F5-001 (mock incorrecto en tests de navigation), H-F5-002 (import huérfano en test_navigation_builders) |
