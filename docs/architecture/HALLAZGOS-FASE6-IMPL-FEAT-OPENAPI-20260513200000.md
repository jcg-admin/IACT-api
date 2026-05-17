# Hallazgos — Implementación FASE 6

**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Alcance:** FASE 6 del plan PLAN-ACTUALIZACION-COMPLETO-20260513185000.md
**Objetivo:** Completar cobertura OpenAPI (drf-spectacular) en todos los endpoints
**Commit:** `0338c0d`
**Impacto:** 3 archivos modificados, 40 inserciones / 24 eliminaciones

---

## Resumen de tareas ejecutadas

| Tarea | Descripción | Estado |
|---|---|---|
| T6.1 | Tags + metadata completa en `RedirectedMenusView` y `CenterMenuView` | COMPLETO |
| T6.2 | Crear `apps/logs/schema.py` con `SPECTACULAR_TAGS` | COMPLETO |
| T6.3 | Verificar cobertura en endpoints de FASE 4 | COMPLETO — ya cubiertos |
| Adicional | Eliminar tag `'Llamadas'` huérfano de `pipeline/schema.py` | COMPLETO |

---

## H-F6-001 — `RedirectedMenusView` y `CenterMenuView` tenían `@extend_schema` en el método `get()`, no en la clase

**Severidad:** MEDIA — drf-spectacular genera documentación incompleta para esas dos views.
**Estado:** CORREGIDO.

El plan identificaba solo la ausencia del tag `"Reportes de Llamadas"`. La auditoría reveló tres problemas adicionales en ambas vistas:

**Problema 1 — Posición del decorador:**

El `@extend_schema` estaba en el método `get()`, no en la clase:

```python
# ANTES — @extend_schema en el método
class RedirectedMenusView(APIView):
    permission_classes = [IsAuthenticated, HasFunction]

    @extend_schema(          # ← en get(), no en la clase
        parameters=[...],
        responses={200: OpenApiTypes.OBJECT, ...},
    )
    def get(self, request): ...
```

drf-spectacular recomienda colocar `@extend_schema` en la clase para views basadas en clase. Colocarlo en `get()` funciona, pero el esquema generado puede omitir metadatos de la clase.

**Problema 2 — Ausencia de `summary`, `description` y `tags`:**

Los campos obligatorios para una documentación completa no estaban presentes. drf-spectacular generaría auto-títulos a partir del nombre de la clase (poco descriptivos: "Redirected Menus View").

**Problema 3 — `required_function` faltaba:**

Ambas clases tenían `permission_classes = [IsAuthenticated, HasFunction]` pero no `required_function`. La clase `HasFunction` lee el atributo `required_function` de la view para determinar qué función RBAC verificar. Sin él, `HasFunction` no tiene qué verificar y la autenticación RBAC falla silenciosamente o usa un fallback.

```python
# ANTES — sin required_function (bug de autenticación)
class RedirectedMenusView(APIView):
    permission_classes = [IsAuthenticated, HasFunction]  # HasFunction sin función

# DESPUÉS — correcto
class RedirectedMenusView(APIView):
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'reports.view_ivr'              # función RBAC declarada
```

**Corrección aplicada:**

```python
@extend_schema(
    summary="UC_RPT_16 — Menús redirigidos: opciones elegidas por el llamante",
    description="Invoca sp_rpt_menu_redirigidos(p_quarter, p_segmento) en MariaDB...",
    parameters=[_IVR_QUARTER_PARAM, _IVR_SEGMENTO_PARAM],
    responses={
        200: OpenApiResponse(description="Distribución de opciones por menú IVR"),
        400: OpenApiResponse(description="Quarter o segmento inválido"),
        503: OpenApiResponse(description="MariaDB no disponible"),
    },
    tags=["Reportes de Llamadas"],
)
class RedirectedMenusView(APIView):
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'reports.view_ivr'
```

---

## H-F6-002 — Tag `'Llamadas'` en `pipeline/schema.py` era huérfano tras FASE 3

**Severidad:** BAJA — producía una sección vacía en el OpenAPI UI.
**Estado:** CORREGIDO — tag eliminado.

`pipeline/schema.py` definía el tag `'Llamadas'` con la descripción:

> "Registro de llamadas del call center: centros, servicios, llamadas y notas."

Este tag era para `CenterViewSet`, `ServiceViewSet`, `CallRecordViewSet` y `CallNoteViewSet` — todos eliminados en FASE 3. Ningún endpoint activo usaba `tags=["Llamadas"]` al momento de FASE 6.

`collect_app_tags` lo agregaba al schema OpenAPI. En el Swagger UI aparecería como una sección sin endpoints — confunde al lector sobre qué funcionalidad existe.

Adicionalmente, la descripción del tag `'Estado del Pipeline'` se actualizó para incluir el nuevo endpoint `v_etl_rendimiento` (FASE 4):

```python
# ANTES
'Lee directamente de job_execution_log en MariaDB ivr_legacy. UC_PIP_01..04.'

# DESPUÉS
'Lee directamente de job_execution_log y v_etl_rendimiento en MariaDB ivr_legacy. UC_PIP_01..04.'
```

---

## H-F6-003 — 8 tags definidos en `schema.py` sin `tags=` explícito en `@extend_schema`

**Severidad:** Informativo — no es un problema.
**Estado:** Documentado.

El análisis de cobertura detectó 8 tags definidos en `schema.py` de distintas apps que no aparecen en ningún `@extend_schema(..., tags=[...])`:

| Tag | App | Tipo de endpoint |
|---|---|---|
| `'Alertas'` | alerts | ViewSets con auto-tagging |
| `'Autenticacion'` | authentication | APIViews con auto-tagging |
| `'Configuracion'` | users | ViewSets con auto-tagging |
| `'Core'` | core | Views con auto-tagging |
| `'Dashboard'` | dashboard | ViewSets con auto-tagging |
| `'Perfil'` | users | ViewSets con auto-tagging |
| `'Sesiones'` | users | ViewSets con auto-tagging |
| `'Usuarios'` | users | ViewSets con auto-tagging |

Estos tags son válidos. drf-spectacular asigna tags automáticamente a ViewSets basándose en el basename del router o el nombre del recurso. Los `schema.py` definen la descripción del tag para enriquecer la documentación auto-generada. La ausencia de `tags=[...]` explícito es intencional — los ViewSets de esas apps no necesitan especificarlo si drf-spectacular los asigna correctamente.

El único tag que era un problema real era `'Llamadas'` en `pipeline/schema.py` (H-F6-002), ya eliminado.

---

## H-F6-004 — T6.3 ya estaba completo desde FASE 4

**Severidad:** Informativo.
**Estado:** Documentado — verificación confirmó cobertura completa.

El plan indicaba verificar el `@extend_schema` de los 3 endpoints de FASE 4. La verificación confirmó que los tres fueron implementados con metadata completa desde el primer commit de FASE 4:

| Endpoint | summary | description | tags | responses |
|---|---|---|---|---|
| `AbandonmentSummaryView` | ✓ | ✓ | ✓ | ✓ |
| `PipelineEventLogView` | ✓ | ✓ | ✓ | ✓ |
| `etl_performance` | ✓ | ✓ | ✓ | ✓ |

T6.3 no requirió cambios — era una verificación de calidad, no una tarea de implementación.

---

## Cobertura OpenAPI final

Todos los endpoints IVR, los de FASE 4 y los corregidos en FASE 6 tienen:

| Endpoint | summary | description | tags | responses | required_function |
|---|---|---|---|---|---|
| `ClientsReportView` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `TransferCentersView` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `AbandonedCallsView` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `CMENUErrorView` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `CentersBySegmentView` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `IvrMenusView` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `RedirectedMenusView` | ✓ | ✓ | ✓ | ✓ | ✓ (corregido) |
| `CenterMenuView` | ✓ | ✓ | ✓ | ✓ | ✓ (corregido) |
| `AbandonmentSummaryView` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `PipelineEventLogView` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `etl_performance` | ✓ | ✓ | ✓ | ✓ | — (func-based) |

---

## Estado final de FASE 6

| Indicador | Valor |
|---|---|
| Archivos modificados | 3 |
| Archivos creados | 1 (`logs/schema.py`) |
| Tags corregidos | 2 (`RedirectedMenusView`, `CenterMenuView`) |
| Tags huérfanos eliminados | 1 (`'Llamadas'` en `pipeline/schema.py`) |
| Tags sin cobertura explícita | 0 (todos los usados tienen `schema.py`) |
| Bugs adicionales corregidos | 1 (`required_function` faltaba en 2 views) |
| Errores de sintaxis | 0 |
| Deuda técnica generada | Ninguna |
