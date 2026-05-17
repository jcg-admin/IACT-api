# HALLAZGOS-FASE5-IACT-API-2026-05-16T21:34:49

**Documento:** HALLAZGOS-FASE5-IACT-API-2026-05-16T21:34:49  
**Fecha:** 2026-05-16  
**Repositorio:** IACT-api  
**Commit:** dd23f1c  
**Plan base:** PLAN-IMPL-IACT-API-2026-05-16T17:53:35.md — FASE 5

---

## Estado antes de FASE 5

```
flake8 --select=W291,W293,W391,W292: 3448 ocurrencias en 108 archivos
  W291: trailing whitespace           125
  W292: no newline at end of file       1
  W293: blank line contains whitespace 3316
  W391: blank line at end of file       6
Suite: 1327 passed, 0 failed
```

---

## Cambios aplicados

### T5.1 — Inventario

108 archivos afectados, todos `.py` en `apps/`. Ningún archivo binario ni
generado. Lista almacenada en `/tmp/whitespace_files.txt`.

### T5.2 — Corrección programática

Script Python aplicado a los 108 archivos:

```python
lines = text.split('\n')
lines = [line.rstrip() for line in lines]      # W291, W293
while lines and lines[-1] == '':
    lines.pop()                                 # W391
result = '\n'.join(lines) + '\n'               # W292
```

El script solo escribe el archivo si el contenido cambia (comparación
de bytes). Resultado: 107 archivos modificados, 1 sin cambio.

### DT-API-008 — Corrección de `.gitignore`

Patrón `logs/` (L279) reemplazado por patrones explícitos:

```gitignore
# Antes (capturaba apps/logs/ — código fuente):
logs/

# Después (solo directorios de logs en la raíz):
/logs/
/callcentersite/logs/
```

---

## Hallazgos durante la implementación

### H-F5-001 — `apps/logs/__init__.py`: falso negativo en el script de corrección

El archivo contenía exactamente 1 byte: `b'\n'` (un newline solitario).

El script de corrección:
1. Lee `b'\n'`
2. Divide por `\n` → `['', '']`
3. `rstrip()` cada línea → `['', '']`
4. Elimina líneas en blanco del final → `[]`
5. Une con `\n` y añade `\n` → `'\n'`
6. Compara `'\n'.encode()` con `b'\n'` → **iguales → no modifica**

El resultado era idéntico al original, por lo que el script no lo marcó
como modificado. Sin embargo, flake8 seguía reportando `W391` porque el
archivo es una línea en blanco.

**La causa raíz:** `W391 blank line at end of file` aplica cuando el archivo
termina con una línea en blanco (incluyendo el caso de que el archivo
completo sea solo esa línea). La corrección correcta para un `__init__.py`
vacío es 0 bytes, no `'\n'`.

**Corrección manual:** `open(path, 'w').write('')` → archivo de 0 bytes.
Verificado: `flake8` deja de reportar `W391`.

### H-F5-002 — DT-API-008: `.gitignore` con patrón `logs/` capturaba código fuente

Documentado como deuda técnica en FASE 3 (H-F3-001). En esta fase se resuelve.

El patrón `logs/` sin `/` inicial en `.gitignore` coincide con cualquier
directorio llamado `logs` a cualquier nivel del árbol. `callcentersite/apps/logs/`
es código fuente (app Django completa con modelos, vistas, URLs, servicios).

La corrección usa `/logs/` y `/callcentersite/logs/` — el `/` inicial
ancla el patrón a la raíz del repositorio. Verificado:

- `git add callcentersite/apps/logs/views.py` funciona sin `-f`
- `logs/django.log` sigue siendo ignorado

### H-F5-003 — 3448 ocurrencias vs 3450 del plan original

El plan documentó 3450 ocurrencias. Al comenzar FASE 5 el conteo era 3448.
La diferencia de 2: FASE 3 modificó `separation_rule_view.py` (E702 — separar
sentencias en líneas distintas), lo que eliminó 2 trailing whitespace al
reformatear las líneas. Correcto — no es regresión.

---

## Estado final completo — IACT-api deuda técnica CERO

```
flake8 --select=F401,F811,F841,F541,E402,E702,E741,W291,W293,W391,W292:
  0 ocurrencias (TODOS LOS ERRORES = 0)

Suite:
  tests/unit:        1215 passed, 0 failed
  tests/integration: 104  passed, 0 failed
  tests/api:         8    passed, 0 failed
  Total:             1327 passed, 0 failed

django check: 0 issues
```

### Resumen de todas las fases

| Fase | DT | Archivos | Commit |
|---|---|---|---|
| FASE 1 | DT-API-001 | 2 (tests) | baaf09f |
| FASE 2 | DT-API-002 | 5 (4 prod + 1 test) | 1eec802 |
| FASE 3 | DT-API-003/005/006 | 3 | 577ce99 |
| FASE 4 | DT-API-004 | 7 | 92ff105 |
| FASE 5 | DT-API-007/008 | 111 | dd23f1c |

**Commits de implementación:** 5  
**Deuda técnica residual:** 0  
**Tests delta:** 1326 → 1327 (+1 test de integración que antes fallaba)

---

*Generado: 2026-05-16T21:34:49 | Commit: dd23f1c | Suite: 1327 passed, 0 failed*  
*IACT-api — Deuda técnica: CERO*
