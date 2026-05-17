# HALLAZGOS-IMPL-ERRORES-SILENCIOSOS-2026-05-15

**Documento:** HALLAZGOS-IMPL-ERRORES-SILENCIOSOS-2026-05-15
**Fecha:** 2026-05-15
**Rama:** develop
**Commit:** 8e7d024
**Alcance:** IACT-api — eliminación de errores silenciosos en código de producción
**Resultado:** 1335 passed · 0 except:pass sin log en producción

---

## 1. Principio aplicado

**Toda excepción capturada que no se re-lanza debe registrarse en el log.**

Un `except: pass` sin log oculta fallos reales en producción:
- Un archivo huérfano en storage nunca se detecta.
- Un `etl_runs` que queda en `'en_ejecucion'` indefinidamente no genera alerta.
- Un token JWT malformado en logout nunca aparece en métricas de error.

El criterio para decidir si usar `logger.warning` vs `logger.error`:
- `warning`: el flujo principal continúa correctamente (cleanup secundario).
- `error`: el fallo tiene impacto operativo aunque no interrumpa el request.

---

## 2. Correcciones aplicadas

### apps/users/views.py — avatar.delete() silencioso

**Antes:**
```python
try:
    user.avatar.delete(save=False)
except Exception:
    pass
```

**Después:**
```python
try:
    user.avatar.delete(save=False)
except Exception as exc:
    # El archivo puede no existir en storage (borrado externo o CDN).
    logger.warning("avatar.delete() falló para user=%s: %s", user.pk, exc)
```

**Por qué importa:** si `avatar.delete()` falla silenciosamente, el archivo anterior
queda huérfano en el storage. Con el log, el operador puede detectar y limpiar
archivos no referenciados.

Afecta a `upload_avatar_view` (línea 51) y `delete_avatar_view` (línea 80).

---

### apps/pipeline/scheduler.py — ETL scheduler silencioso

**_update_run (línea 73):**
```python
# Antes: pass
# Después:
logger.warning("_update_run falló (run_id=%s, status=%s): %s", run_id, status, exc)
```

**Por qué importa:** si `etl_runs` no se actualiza a `'success'` o `'failed'`,
el run queda como `'en_ejecucion'` indefinidamente. Esto bloquea la idempotencia
del scheduler (CA-05: no puede re-intentar si cree que ya hay uno corriendo).

**run_etl handlers (líneas 93, 101):**
```python
# Antes: pass
# Después:
logger.warning("No se pudo registrar fallo ETL en etl_runs (run_id=%s): %s", run_id, exc2)
```

---

### apps/pipeline/management/commands/run_etl.py — heartbeat y cleanup

**Heartbeat (línea 161):**
```python
# Antes: pass (con comentario "El heartbeat no debe matar el thread principal")
# Después: logger.warning con contexto
```

**_update_run en finally (línea 184):**
```python
# Antes: pass (con comentario "Si la BD no está disponible en el finally")
# Después: logger.warning con contexto
```

Adicionalmente: faltaba `import logging` y `logger = getLogger(__name__)`.
Sin estos, cualquier llamada a `logger.warning` causaba `NameError` en runtime.

---

### apps/authentication/logout_view.py — token JWT malformado

**Antes:**
```python
except ValueError:
    pass
```

**Después:**
```python
except ValueError as exc:
    # Token con formato inválido — el logout continúa.
    logger.warning("blacklist_jwt: token inválido para user=%s: %s", user.pk, exc)
```

Adicionalmente: faltaba `import logging` y `logger = getLogger(__name__)`.
Sin esto, el logout fallaba con `NameError: name 'logger' is not defined`
produciendo HTTP 500 en lugar de completar el logout.

**Este era el bug de producción más grave:** un usuario con un token
JWT malformado no podía hacer logout — recibía 500.

---

### apps/audit/middleware/session_security.py — auditoría silenciosa

**Antes:**
```python
except Exception:
    # No fallar si auditoria falla
    pass
```

**Después:**
```python
except Exception as exc:
    _log.getLogger(__name__).error(
        "session_security middleware: error de auditoría (path=%s): %s",
        request.path, exc
    )
```

**Por qué importa:** el middleware de seguridad puede fallar silenciosamente
ante cualquier excepción (ej: tabla de auditoría no disponible). Sin log,
brechas de seguridad potenciales nunca aparecen en los registros.

---

### apps/alerts/services/alert_service.py — stack trace incompleto

**Antes:**
```python
logger.error(f"Error evaluando config {config.id} '{config.name}': {e}")
```

**Después:**
```python
logger.error(f"Error evaluando config {config.id} '{config.name}': {e}", exc_info=True)
```

**Por qué importa:** sin `exc_info=True` se registra el mensaje del error pero
no el stack trace. El operador no puede diagnosticar la causa raíz.

---

## 3. Patrón de clasificación aplicado

| Tipo | Tratamiento | Ejemplo |
|---|---|---|
| Cleanup de archivo/storage | `logger.warning` + continuar | `avatar.delete()` |
| Registro en BD de auditoría | `logger.warning` + continuar | `etl_runs` update |
| Token malformado en auth | `logger.warning` + continuar | JWT inválido en logout |
| Error en evaluación de alertas | `logger.error(exc_info=True)` | config evaluación |
| Error en auditoría de seguridad | `logger.error` | session_security middleware |
| Error fatal en flujo principal | `raise` | Nunca silenciar |

---

## 4. Verificación

```
$ python3 -m flake8 apps/ --select=E722 --exclude=migrations,__pycache__
(sin output — no hay bare except:)

$ grep -rn "except.*:\s*$" apps/ --include="*.py" \
  --exclude-dir=migrations --exclude-dir=__pycache__ | \
  grep -v "test_" | wc -l
0

$ python3 -m pytest tests/ --no-header -q --tb=no
1335 passed in 47s
```

---

*Generado: 2026-05-15 | Commit: 8e7d024*
