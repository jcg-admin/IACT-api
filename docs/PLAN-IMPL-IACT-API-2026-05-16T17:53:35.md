# PLAN-IMPL-IACT-API-2026-05-16T17:53:35

**Documento:** PLAN-IMPL-IACT-API-2026-05-16T17:53:35  
**Fecha:** 2026-05-16  
**Repositorio:** IACT-api  
**Rama:** develop  
**Commit base:** 42563f5  
**Objetivo:** Deuda técnica CERO — 0 failed, 0 errores flake8 F*/E*, 0 whitespace

---

## Contexto: arquitectura dual-BD

IACT-api opera con dos bases de datos:

- **PostgreSQL** (`default` / alias `iact_analytics`): ORM Django, READ + WRITE.
  Todo el ORM va a esta BD. Las migraciones solo se aplican aquí (CNST-003).
- **MariaDB** (`ivr` / alias `ivr_legacy`): READ-ONLY via `connections['ivr'].cursor()`.
  El ORM Django nunca escribe aquí. El schema es responsabilidad de IACT-db.

El `DatabaseRouter` en `config/db_router.py` implementa esta separación.

La suite de tests refleja esta dualidad:

- `tests/unit/` + `tests/api/`: solo PostgreSQL. 1215 + 8 = 1223 passed.
- `tests/integration/pipeline/test_ivr_endpoints.py`: usa `databases=['default', 'ivr']`.
  Requiere MariaDB activa. El fixture `ivr_schema` crea las tablas en `test_ivr_legacy`.
- MariaDB en el sandbox es inestable (limitación de entorno documentada en
  ANALISIS-FALLOS-MASIVOS-SUITE-2026-05-15.md). El conftest de pipeline
  arranca MariaDB como proceso hijo de pytest para garantizar disponibilidad.

---

## Estado inicial verificado

```
tests/unit:        1215 passed, 0 failed
tests/integration: 103 passed, 1 failed
tests/api:         8 passed, 0 failed
Total:             1326 passed, 1 failed

flake8 --select=F401,F811,F841,F541,E711,E712,E741,E702,E402:
  E402: 23 ocurrencias en 7 archivos
  F811: 7 ocurrencias en 4 archivos
  F541: 2 ocurrencias en 1 archivo
  E702: 2 ocurrencias en 1 archivo
  E741: 1 ocurrencia en 1 archivo

flake8 --select=W291,W293,W391,W292:
  3450 ocurrencias en 108 archivos

django check: 0 issues
```

---

## Deuda técnica inventariada

| Código | Descripción | Prioridad |
|---|---|---|
| DT-API-001 | Test `test_timeout_at_pasado_marca_timeout` falla por datos sucios en `etl_runs` entre sesiones — falta fixture de cleanup | CRÍTICA |
| DT-API-002 | F811×7 — redefinición de nombres sin uso (4 archivos) | ALTA |
| DT-API-003 | F541×2 — f-strings sin placeholders en `profile_service.py` | ALTA |
| DT-API-004 | E402×23 — imports en mitad de módulo (7 archivos) | MEDIA |
| DT-API-005 | E702×2 — múltiples sentencias en una línea con `;` | MEDIA |
| DT-API-006 | E741×1 — variable ambigua `l` en `logs/views.py` | MEDIA |
| DT-API-007 | W291/W293/W391/W292×3450 — trailing whitespace (108 archivos) | BAJA |

---

## FASE 1 — DT-API-001: Corregir fallo en suite de integración

**Objetivo:** `tests/integration` pasa 104 tests, 0 failed.  
**Archivos:** `tests/fixtures/ivr.py`, `tests/integration/pipeline/test_ivr_endpoints.py`  
**Descripción del fallo:**

`TestHeartbeatTimeoutIntegration` inserta filas en `etl_runs` usando
`connections['ivr'].cursor()` con autocommit. El fixture `ivr_schema` es
`session-scoped` y crea la tabla pero no hace cleanup entre tests. Cada
corrida acumula filas con `status='en_ejecucion'` y `timeout_at` en el
pasado que contaminan el siguiente test.

El `UPDATE WHERE id=%s AND status='en_ejecucion' AND timeout_at < NOW()`
tiene el `id` correcto, pero si la lógica interna de MariaDB no aisla la
transacción correctamente entre tests (sin rollback), el `rowcount` puede
ser 0 si la fila ya fue actualizada por un test anterior con el mismo ID
reusado por el auto_increment.

**Corrección:** añadir un fixture `function-scoped` que limpie `etl_runs`
antes y después de cada test del `TestHeartbeatTimeoutIntegration`.

### T1.1 — Leer `tests/fixtures/ivr.py` completo

Regla: no modificar antes de leer. Verificar el scope y las dependencias
de todos los fixtures definidos en el archivo.

### T1.2 — Añadir fixture `etl_runs_clean` en `tests/fixtures/ivr.py`

```python
@pytest.fixture
def etl_runs_clean(ivr_schema):
    """
    Limpia la tabla etl_runs antes y después de cada test.
    Garantiza aislamiento entre tests que insertan en etl_runs directamente.
    Scope: function (default) — se ejecuta por cada test que lo solicita.
    """
    with connections['ivr'].cursor() as cur:
        cur.execute("DELETE FROM etl_runs;")
    yield
    with connections['ivr'].cursor() as cur:
        cur.execute("DELETE FROM etl_runs;")
```

### T1.3 — Actualizar `TestHeartbeatTimeoutIntegration` para usar `etl_runs_clean`

Reemplazar `ivr_schema` por `etl_runs_clean` en los dos métodos de la clase.
El fixture `etl_runs_clean` ya depende de `ivr_schema` — la cadena es:
`etl_runs_clean` → `ivr_schema` → `ensure_mariadb`.

### T1.4 — Verificación

```bash
python -m pytest tests/integration/pipeline/test_ivr_endpoints.py::TestHeartbeatTimeoutIntegration -v
# Esperado: 2 passed

python -m pytest tests/integration --tb=no -q
# Esperado: 104 passed, 0 failed
```

### T1.5 — Commit

```
fix(tests): corregir TestHeartbeatTimeoutIntegration — fixture etl_runs_clean
```

---

## FASE 2 — DT-API-002: Corregir F811 (redefinición de nombres)

**Objetivo:** `flake8 --select=F811` retorna 0 ocurrencias.  
**Archivos:** 4 archivos de producción.

### T2.1 — Leer y corregir `apps/access/views.py` L18 y L170

**Causa:** los modelos `AccessGroup`, `UserAccessGroup`, `SeparationRule`,
`ExceptionalPermission` están importados en el bloque de imports inicial (L18)
y luego reimportados en mitad del archivo (L170) antes de un nuevo ViewSet.

**Corrección:** eliminar el import redundante de L170 (el del bloque inicial
ya es suficiente). Verificar que el bloque inicial importa todos los modelos
necesarios para los ViewSets que siguen.

### T2.2 — Leer y corregir `apps/authentication/viewsets.py` L17-18

**Causa:** `LoginSerializer` importado desde dos rutas distintas en
líneas consecutivas (L17 y L18). Eliminar el import duplicado (L17).

### T2.3 — Leer y corregir `apps/reports/models.py` L249 y L257

**Causa:** `__str__` definido dos veces en `ExportJob`. La primera
definición (L249, con type hint `-> str`) es la correcta por convención
del proyecto. La segunda (L257, sin type hint) es un duplicado añadido
en una iteración posterior.

**Corrección:** eliminar la segunda definición (L257). Verificar que
el método eliminado no añade funcionalidad diferente a la primera.

### T2.4 — Leer y corregir `apps/reports/views.py` L10 y L354

**Causa 1:** `Response` importado en el bloque inicial (L10) y
reimportado en mitad del archivo (L354) dentro de un bloque de imports
de una sección nueva.

**Causa 2:** `HasFunction` importado en L12 (inicial) y dos veces más
en L254-255 (mitad).

**Corrección:** eliminar los tres imports redundantes (L354, L254, L255).

### T2.5 — Verificación

```bash
python -m flake8 apps/ --select=F811 --exclude=migrations,__pycache__
# Esperado: 0 líneas

python -m pytest tests/unit tests/integration tests/api --tb=no -q
# Esperado: sin regresiones
```

### T2.6 — Commit

```
fix(code-quality): F811=0 — eliminar redefiniciones de nombres (4 archivos)
```

---

## FASE 3 — DT-API-003 + DT-API-005 + DT-API-006: F541, E702, E741

**Objetivo:** `flake8 --select=F541,E702,E741` retorna 0 ocurrencias.  
**Archivos:** 3 archivos. Se agrupan porque son correcciones de una línea cada una.

### T3.1 — Leer y corregir `apps/users/services/profile_service.py` L190, L197

**Causa:** strings como `f"Formato no permitido. Use: jpg, png, gif"` usan
el prefijo `f` pero no tienen ninguna expresión `{...}`. Son strings literales.

**Corrección:** eliminar el prefijo `f`:
```python
# Antes:
raise UserServiceError(f"Formato no permitido. Use: jpg, png, gif")
# Después:
raise UserServiceError("Formato no permitido. Use: jpg, png, gif")
```

### T3.2 — Leer y corregir `apps/access/separation_rule_view.py` L327, L329

**Causa:** dos asignaciones en la misma línea separadas por `;`:
```python
rule.name = data['name']; changed.append('name')
```

**Corrección:** separar en dos líneas:
```python
rule.name = data['name']
changed.append('name')
```

### T3.3 — Leer y corregir `apps/logs/views.py` L38

**Causa:** variable `l` en list comprehension:
```python
return [l.rstrip() for l in all_lines[-lines:]]
```

**Corrección:** renombrar a `line`:
```python
return [line.rstrip() for line in all_lines[-lines:]]
```

### T3.4 — Verificación

```bash
python -m flake8 apps/ --select=F541,E702,E741 --exclude=migrations,__pycache__
# Esperado: 0 líneas

python -m pytest tests/unit/logs/ tests/unit/access/ tests/unit/users/ --tb=no -q
# Esperado: sin regresiones
```

### T3.5 — Commit

```
fix(code-quality): F541=0, E702=0, E741=0 — f-strings, semicolons, var ambigua
```

---

## FASE 4 — DT-API-004: E402 (imports en mitad de módulo)

**Objetivo:** `flake8 --select=E402` retorna 0 ocurrencias.  
**Archivos:** 7 archivos. Cada tarea es un archivo.

**Criterio de corrección:** los imports en mitad de módulo se reubican
al bloque de imports inicial del archivo. Si el import es parte de un
bloque que creció junto con el ViewSet/clase que lo usa (patrón de
desarrollo incremental), se mueve al inicio y se verifica que no haya
imports circulares.

### T4.1 — Leer y corregir `apps/users/views.py`

**Causa:** `logger = logging.getLogger(__name__)` en L8, luego imports
de DRF en L9-12. El `logger` se inicializó antes de completar los imports.

**Corrección:** mover los imports de DRF (L9-12) antes de la línea `logger`.

### T4.2 — Leer y corregir `apps/users/serializers/__init__.py`

**Causa:** `SessionHistorySerializer` importado en L68, después de
asignaciones y aliases intermedios.

**Corrección:** mover al bloque de imports inicial.

### T4.3 — Leer y corregir `apps/alerts/models.py`

**Causa:** `import uuid as _uuid` en L467, dentro del cuerpo del módulo
antes de la clase `AlertRule`. El uuid se usa solo en `AlertRule`.

**Corrección:** mover al bloque de imports iniciales del archivo.

### T4.4 — Leer y corregir `apps/authentication/models.py`

**Causa:** `import uuid as _uuid` en L614, antes de la clase `Session`.

**Corrección:** mover al bloque de imports iniciales. Verificar que
no haya colisión con otro `import uuid` ya presente.

### T4.5 — Leer y corregir `apps/audit/views.py`

**Causa:** `import hashlib`, `import hmac`, `from django.conf import settings`
en L104-106, antes de `AuditIntegrityView`.

**Corrección:** mover al bloque de imports iniciales.

### T4.6 — Leer y corregir `apps/audit/urls.py`

**Causa:** `from .views import AuditIntegrityView` en L26, después de
`urlpatterns`. Se importa para extender `urlpatterns` con una ruta adicional.

**Corrección:** mover al bloque de imports iniciales. Añadir `AuditIntegrityView`
al import existente de `.views`.

### T4.7 — Leer y corregir `apps/reports/views.py`

**Causa:** dos bloques de imports mid-module:
- L251-257: imports de drf-spectacular, viewsets, HasFunction (×2), modelos.
- L353-355: `APIView`, `Response`, `timezone`.

**Corrección:**
- Consolidar L251-257 con los imports iniciales. Eliminar los duplicados
  de `HasFunction` (ya importado en L12) y `Response` (ya en L10).
- Mover L353-355 al bloque inicial.

### T4.8 — Leer y corregir `apps/access/views.py`

**Causa:** L170-171: `from .models import AccessGroup, ...` y
`from apps.access.serializers.menu_item_serializers import MenuItemSerializer`.

**Corrección:** 
- Los modelos del import L170 ya están en el import inicial → eliminar L170.
- `MenuItemSerializer` mover al bloque de imports iniciales.

### T4.9 — Verificación

```bash
python -m flake8 apps/ --select=E402 --exclude=migrations,__pycache__
# Esperado: 0 líneas

python -m pytest tests/unit tests/integration tests/api --tb=no -q
# Esperado: sin regresiones (la reordenación de imports no cambia comportamiento)
```

### T4.10 — Commit

```
fix(code-quality): E402=0 — reordenar imports al inicio del módulo (7 archivos)
```

---

## FASE 5 — DT-API-007: Trailing whitespace (W291/W293/W391/W292)

**Objetivo:** `flake8 --select=W291,W293,W391,W292` retorna 0 ocurrencias.  
**Archivos:** 108 archivos, 3450 ocurrencias.

**Estrategia:** corrección programática con `sed` o script Python.
No modificar el contenido semántico — solo eliminar espacios en blanco
de final de línea y líneas en blanco con espacios.

### T5.1 — Listar todos los archivos afectados

```bash
python -m flake8 apps/ --select=W291,W293,W391,W292 \
  --exclude=migrations,__pycache__ \
  --format='%(path)s' | sort -u > /tmp/whitespace_files.txt
```

### T5.2 — Corrección programática

Script Python que:
1. Lee cada archivo.
2. Elimina espacios de final de línea en todas las líneas.
3. Elimina líneas en blanco al final del archivo.
4. Garantiza que el archivo termina con exactamente un `\n`.

```python
for path in files:
    content = open(path).read()
    lines = [line.rstrip() for line in content.splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    open(path, 'w').write('\n'.join(lines) + '\n')
```

### T5.3 — Verificación post-corrección

```bash
python -m flake8 apps/ --select=W291,W293,W391,W292 \
  --exclude=migrations,__pycache__ --count
# Esperado: 0

python -m pytest tests/unit tests/integration tests/api --tb=no -q
# Esperado: sin regresiones
```

### T5.4 — Commit

```
fix(code-quality): W291/W293/W391/W292=0 — eliminar trailing whitespace (108 archivos)
```

---

## Verificación final de todas las fases

```bash
# Suite completa (con MariaDB activa)
python -m pytest tests/unit tests/integration tests/api --tb=no -q
# Esperado: ≥1327 passed, 0 failed

# flake8 completo sin excepciones de whitespace
python -m flake8 apps/ \
  --select=F401,F811,F841,F541,E711,E712,E741,E702,E402,W291,W293,W391,W292 \
  --exclude=migrations,__pycache__
# Esperado: 0 ocurrencias

# django check
python manage.py check
# Esperado: 0 issues
```

---

## Restricciones y principios

1. **Leer antes de modificar:** ningún archivo se modifica sin leer su contenido completo primero.
2. **Verificar después de cada tarea:** cada tarea incluye su propia verificación con pytest antes del commit.
3. **Commits atómicos:** un commit por fase, con mensaje convencional.
4. **Scope MariaDB:** las correcciones de tests en FASE 1 respetan CNST-003 — solo raw SQL via `connections['ivr'].cursor()`, nunca ORM para la BD `ivr`.
5. **Sin modificar migraciones:** las correcciones de imports no tocan archivos en `migrations/`.
6. **Preservar contratos IVR:** los stored procedures, nombres de tablas y parámetros de vista en MariaDB son contratos de IACT-db — fuera del scope de estas correcciones.

---

## Resumen de fases

| Fase | DT | Archivos | Tipo | Commit esperado |
|---|---|---|---|---|
| FASE 1 | DT-API-001 | 2 | fix(tests) | 1 |
| FASE 2 | DT-API-002 | 4 | fix(code-quality) | 1 |
| FASE 3 | DT-API-003/005/006 | 3 | fix(code-quality) | 1 |
| FASE 4 | DT-API-004 | 7 | fix(code-quality) | 1 |
| FASE 5 | DT-API-007 | 108 | fix(code-quality) | 1 |
| **Total** | **7 DTs** | **~124** | | **5** |

---

*Generado: 2026-05-16T17:53:35 | Commit base: 42563f5 | Suite inicial: 1326 passed, 1 failed*
