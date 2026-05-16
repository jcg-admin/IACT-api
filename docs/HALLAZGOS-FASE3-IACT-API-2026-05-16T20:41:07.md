# HALLAZGOS-FASE3-IACT-API-2026-05-16T20:41:07

**Documento:** HALLAZGOS-FASE3-IACT-API-2026-05-16T20:41:07  
**Fecha:** 2026-05-16  
**Repositorio:** IACT-api  
**Commit:** 577ce99  
**Plan base:** PLAN-IMPL-IACT-API-2026-05-16T17:53:35.md — FASE 3

---

## Estado antes de FASE 3

```
flake8 --select=F541,E702,E741: 5 ocurrencias en 3 archivos
Suite: 1327 passed, 0 failed
```

---

## Estrategia de verificación — separación de subsistemas

A partir de esta fase se adopta la práctica de separar la verificación en
dos invocaciones distintas para evitar la inestabilidad de mysqld:

```bash
# Paso 1: unit + api (sin MariaDB) — siempre estables
python -m pytest tests/unit tests/api

# Paso 2: integration (mysqld fresco, conftest arranca mariadbd)
python -m pytest tests/integration
```

Los tests `unit` y `api` no usan MariaDB. Correrlos antes permite
verificar sin depender de que el daemon MariaDB esté activo. Al
terminar, se arranca mysqld fresco para los tests de `integration`,
donde `ensure_mariadb` (session-scoped) lo gestiona como proceso hijo.

Esto evita el patrón de fallo documentado en H-F2-003: mysqld cae durante
la suite larga de `unit` y los tests de `integration` fallan en setup.

---

## Cambios aplicados

### T3.1 — `apps/users/services/profile_service.py` (F541×2)

**Causa:** dos strings literales con prefijo `f` pero sin ninguna
expresión `{...}`. El prefijo `f` es innecesario y confunde al lector
haciéndole buscar interpolaciones que no existen.

```python
# Antes (F541):
raise UserServiceError(f"Formato no permitido. Use: jpg, png, gif")
raise UserServiceError(f"Archivo muy grande. Máximo: 2MB")

# Después:
raise UserServiceError("Formato no permitido. Use: jpg, png, gif")
raise UserServiceError("Archivo muy grande. Máximo: 2MB")
```

### T3.2 — `apps/access/separation_rule_view.py` (E702×2)

**Causa:** dos bloques `if` con asignación y `append` separados por
semicolón en la misma línea.

```python
# Antes (E702):
rule.name = data['name']; changed.append('name')
rule.description = data['description']; changed.append('description')

# Después:
rule.name = data['name']
changed.append('name')
rule.description = data['description']
changed.append('description')
```

### T3.3 — `apps/logs/views.py` (E741×1)

**Causa:** variable de loop `l` en un list comprehension. Es una variable
ambigua que se parece a `1` (número) e `I` (mayúscula) en muchas fuentes
tipográficas.

```python
# Antes (E741):
return [l.rstrip() for l in all_lines[-lines:]]

# Después:
return [line.rstrip() for line in all_lines[-lines:]]
```

---

## Hallazgos durante la implementación

### H-F3-001 — `apps/logs/` está cubierto por el patrón `logs/` del `.gitignore`

Al hacer `git add callcentersite/apps/logs/views.py`, git rechazó el
archivo con:

```
The following paths are ignored by one of your .gitignore files:
callcentersite/apps/logs
```

El `.gitignore` del repositorio contiene `logs/` — patrón que coincide con
cualquier directorio llamado `logs` en cualquier nivel del árbol, incluyendo
`callcentersite/apps/logs/`.

El propósito original del patrón era ignorar el directorio `logs/` de la
raíz del proyecto (archivos de log Django, rotación de logs, etc.),
**no** el código fuente en `apps/logs/`.

El archivo `apps/logs/views.py` ya tenía historial en git (visible con
`git log --follow`), por lo que fue añadido con `git add -f` (flag de fuerza).

**Impacto:** el patrón `logs/` en `.gitignore` es demasiado amplio. Debería
ser más específico para no capturar el código fuente. Sin embargo, corregir
el `.gitignore` está fuera del alcance de esta fase (requiere auditar todos
los archivos ignorados incorrectamente). Se documenta como deuda técnica
adicional para revisión posterior.

---

## Verificaciones realizadas (T3.4)

| Verificación | Comando | Resultado |
|---|---|---|
| 1. F541+E702+E741 en toda la base | `flake8 --select=F541,E702,E741` | 0 ocurrencias |
| 2. django check | `python manage.py check` | 0 issues |
| 3. Tests directamente afectados | avatar_api, separation_rule, log_tail, log_search | 51 passed, 0 failed |
| 4. Suite unit + api | `pytest tests/unit tests/api` | 1223 passed, 0 failed |
| 5. Suite integration (mysqld fresco) | `pytest tests/integration` | 104 passed, 0 failed |

---

## Estado después de FASE 3

```
flake8 --select=F541,E702,E741: 0 ocurrencias
Suite: 1327 passed, 0 failed
  tests/unit:        1215 passed
  tests/integration: 104 passed
  tests/api:         8 passed

DT-API-003: RESUELTA
DT-API-005: RESUELTA
DT-API-006: RESUELTA
```

### Deuda técnica adicional identificada

| Código | Descripción | Estado |
|---|---|---|
| DT-API-008 | Patrón `logs/` en `.gitignore` demasiado amplio — captura código fuente en `apps/logs/` | Documentado, fuera de scope de esta fase |

---

*Generado: 2026-05-16T20:41:07 | Commit: 577ce99 | Suite: 1327 passed, 0 failed*
