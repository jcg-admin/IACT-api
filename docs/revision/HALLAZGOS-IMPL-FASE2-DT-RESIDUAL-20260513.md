# Hallazgos — Implementación FASE 2: endpoints IVR en español → inglés

**Artefacto:** HALLAZGOS-IMPL-FASE2-DT-RESIDUAL-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Commit:** `4f19034` en rama `refactor/std008-sod-naming`
**Autor:** Nestor Monroy
**Estado:** Cerrado — todos los hallazgos resueltos en este commit

----

## Resumen ejecutivo

FASE 2 se ejecutó exactamente en el alcance planeado. No se encontraron
hallazgos adicionales. El cambio afecta tres archivos, 20 líneas modificadas.

| Métrica | Antes | Después |
|---|---|---|
| Endpoints REST en español | 2 | 0 |
| URL path `ivr/menu-redirigidos/` | presente | eliminada |
| URL path `ivr/menu-centro/` | presente | eliminada |
| URL path `ivr/menu-redirected/` | inexistente | activa |
| URL path `ivr/menu-center/` | inexistente | activa |
| `reverse('reports:ivr-menu-redirigidos')` | funciona | `NoReverseMatch` |
| `reverse('reports:ivr-menu-centro')` | funciona | `NoReverseMatch` |
| drf-spectacular Field warnings nuevos | — | 0 |
| Tests actualizados | 12 referencias | 12 referencias |
| Clases de test renombradas | `TestIVRMenuRedirigidos` | `TestIVRMenuRedirected` |
| " | `TestIVRMenuCentro` | `TestIVRMenuCenter` |
| Método de test renombrado | `test_semantica_distinta_de_menu_redirigidos` | `test_distinct_url_from_menu_redirected` |

----

## Cambios ejecutados

### `apps/reports/urls.py`

```python
# Antes
path('ivr/menu-redirigidos/', RedirectedMenusView.as_view(), name='ivr-menu-redirigidos'),
path('ivr/menu-centro/',      CenterMenuView.as_view(),      name='ivr-menu-centro'),

# Después
path('ivr/menu-redirected/',  RedirectedMenusView.as_view(), name='ivr-menu-redirected'),
path('ivr/menu-center/',      CenterMenuView.as_view(),      name='ivr-menu-center'),
```

### `apps/reports/ivr_views.py`

Solo se actualizaron las referencias de URL en los docstrings de las
clases (líneas de la forma `GET /api/reports/ivr/menu-redirigidos/...`).

Las siguientes referencias NO se modificaron:
- `sp_rpt_menu_redirigidos` — nombre de stored procedure en MariaDB.
  Es un contrato de base de datos fuera del scope de STD-008 §3.5
  (que cubre Endpoints REST, no objetos de BD).
- `sp_rpt_menu_centro` — ídem.
- Los nombres internos en `@extend_schema` descriptions que describen
  el SP invocado siguen siendo precisos (el SP no se renombra).

### `tests/integration/pipeline/test_ivr_endpoints.py`

Cambios aplicados:

| Tipo | Antes | Después |
|---|---|---|
| Clase | `TestIVRMenuRedirigidos` | `TestIVRMenuRedirected` |
| Clase | `TestIVRMenuCentro` | `TestIVRMenuCenter` |
| Método | `test_semantica_distinta_de_menu_redirigidos` | `test_distinct_url_from_menu_redirected` |
| Docstring | `T-005: endpoint GET /api/reports/ivr/menu-redirigidos/` | `T-005: endpoint GET /api/reports/ivr/menu-redirected/` |
| Docstring | `T-005: endpoint GET /api/reports/ivr/menu-centro/` | `T-005: endpoint GET /api/reports/ivr/menu-center/` |
| Comentario | `# T-005 — Endpoints menu-redirigidos y menu-centro` | `# T-005 — Endpoints menu-redirected y menu-center` |
| reverse ×6 | `reverse('reports:ivr-menu-redirigidos')` | `reverse('reports:ivr-menu-redirected')` |
| reverse ×3 | `reverse('reports:ivr-menu-centro')` | `reverse('reports:ivr-menu-center')` |
| parametrize | `('menu-redirigidos', 'reports:ivr-menu-redirigidos', ...)` | `('menu-redirected', 'reports:ivr-menu-redirected', ...)` |
| parametrize | `('menu-centro', 'reports:ivr-menu-centro', ...)` | `('menu-center', 'reports:ivr-menu-center', ...)` |

----

## Lo que NO cambió y por qué

### `IvrMenusView` — parámetro `vista`

`IvrMenusView` es un tercer endpoint (`GET /api/reports/ivr/menus/?vista=...`)
que agrega ambas vistas en un solo endpoint mediante un parámetro de
selección:

```python
@extend_schema(
    parameters=[
        OpenApiParameter('vista', str,
            enum=['redirigidos', 'menu_centro'], default='redirigidos'),
    ],
)
class IvrMenusView(APIView):
    ...
    fn = svc.get_redirected_menus if vista == 'redirigidos' else svc.get_center_menus
```

Los valores `'redirigidos'` y `'menu_centro'` son valores de un query
parameter de un endpoint diferente. Renombrarlos:
1. Cambiaría el contrato público de `IvrMenusView`, un endpoint no
   incluido en FASE 2.
2. Requiere verificar si IACT-ui o cualquier otro consumidor llama
   `/api/reports/ivr/menus/?vista=redirigidos`.

Se documenta como pendiente para una FASE futura independiente si
se confirma que el parámetro `vista` también debe seguir STD-008 §3.5.

### SP names en `ivr_services.py` y `tests/fixtures/ivr.py`

`sp_rpt_menu_redirigidos` y `sp_rpt_menu_centro` son stored procedures
en MariaDB. STD-008 §3.5 cubre Endpoints REST, no objetos de base de
datos. El servicio Python ya envuelve los SPs con nombres en inglés
(`get_redirected_menus`, `get_center_menus`). Los SP names no cambian.

----

## drf-spectacular — schema IVR post-FASE 2

Paths IVR en el schema generado:

```
/api/reports/ivr/abandoned/
/api/reports/ivr/abandonment-summary/
/api/reports/ivr/centers-by-segment/
/api/reports/ivr/clients/
/api/reports/ivr/menu-center/        ← nuevo
/api/reports/ivr/menu-errors/
/api/reports/ivr/menu-redirected/    ← nuevo
/api/reports/ivr/menus/
/api/reports/ivr/transfer-centers/
```

Los paths `ivr/menu-redirigidos/` e `ivr/menu-centro/` no aparecen.

Operation IDs generados:
```
reports_ivr_menu_center_retrieve
reports_ivr_menu_redirected_retrieve
```

Sin colisiones. Sin Field warnings nuevos relacionados con el cambio.

----

## Verificación ejecutada

```
[PASS] T-2.A: ivr-menu-redirected → /api/reports/ivr/menu-redirected/
[PASS] T-2.A: ivr-menu-center     → /api/reports/ivr/menu-center/
[PASS] T-2.B: reports:ivr-menu-redirigidos → NoReverseMatch (eliminada)
[PASS] T-2.B: reports:ivr-menu-centro → NoReverseMatch (eliminada)
[PASS] T-2.C: URLs distintas entre sí y de ivr-menus
[PASS] T-2.D: menu-redirected despacha correctamente (status=503 sin MariaDB)
[PASS] T-2.D: menu-center despacha correctamente (status=503 sin MariaDB)
[PASS] T-2.E: drf-spectacular — paths IVR correctos
[PASS] T-2.F: operation_ids IVR menu correctos
[DONE] T-2 — todos los criterios PASS
```

Los status 503 en T-2.D son el comportamiento esperado: el entorno
de testing no tiene MariaDB disponible. El 503 confirma que el routing
funcionó (el endpoint despachó) pero la consulta a MariaDB falló,
como está diseñado.
