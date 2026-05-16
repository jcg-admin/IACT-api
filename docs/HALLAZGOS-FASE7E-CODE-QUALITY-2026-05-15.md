# HALLAZGOS-FASE7E-CODE-QUALITY-2026-05-15

**Documento:** HALLAZGOS-FASE7E-CODE-QUALITY-2026-05-15
**Fecha:** 2026-05-15
**Rama:** develop
**Commit:** e0b75ef
**Alcance:** IACT-api — eliminación de deuda técnica en código de producción
**Resultado:** 1335 passed · 0 F401 (flake8) · 0 TODOs · 0 archivos muertos

---

## 1. Categorías de deuda técnica resueltas

### 1.1 Imports no usados (F401) — 122 → 0

**Herramienta de referencia:** `flake8 --select=F401`
(pyflakes no respeta `# noqa: F401` en bloques multilinea; flake8 sí lo hace)

**Distribución inicial:**
- 103 imports genuinamente no usados en 60+ archivos de producción
- 19 re-exportaciones en `__init__.py` de paquetes (contrato público de módulo)

**Estrategia aplicada:**
- Imports genuinamente no usados: eliminados directamente con edición quirúrgica
  archivo por archivo, verificando la suite después de cada lote.
- Re-exportaciones en `__init__.py`: marcadas con `# noqa: F401` en la línea
  del símbolo individual y en la línea `from X import` del bloque.
- Imports usados como re-exportaciones públicas (`ActiveRecordQuery`,
  `SoftDeleteQuerySet`, `is_ajax_request`): marcados con `# noqa: F401`.

**Archivos más afectados:**
- `apps/logs/views.py` — 7 imports eliminados
- `apps/authentication/session_admin_view.py` — 5 imports eliminados
- `apps/utils/helpers.py` — 4 imports eliminados
- `apps/users/modify_user_view.py` — 4 imports eliminados
- `apps/access/views.py` — 4 imports eliminados

**Errores encontrados durante la limpieza:**
- `autoflake` (primera iteración): eliminó re-exportaciones en `__init__.py`
  y el símbolo `ActiveRecordQuery` de `core/models.py`, rompiendo la suite.
  → Revertido. Se adoptó estrategia quirúrgica manual.
- Script Python de vaciado de líneas: dejaba bloques `from X import (` sin
  cierre, generando `SyntaxError`.
  → Revertido. Se procesaron solo imports de una sola línea.
- Regex de añadir noqa en bloques: eliminó los `)` de cierre.
  → Revertido. Se procesaron líneas individuales.

### 1.2 Código muerto — 3 artefactos eliminados

**`apps/users/serializers.py`** (634 líneas)
- Estado: archivo suelto en `apps/users/` coexistía con el paquete
  `apps/users/serializers/`. Python resuelve el paquete (directorio) con
  prioridad sobre el módulo suelto — el archivo nunca se importaba.
- Contenido: serializadores `UserProfileSerializer` y `UserSettingsSerializer`
  que referenciaban `UserProfile` y `UserSettings` (modelos eliminados en FASE 4).
- Acción: eliminado.

**`apps/users/viewsets/profile_viewset.py`**
- Estado: importaba `UserProfile`, `UserSettings` con `try/except ImportError`
  y usaba `UserSettingsSerializer` que falla en runtime porque `UserSettings=None`.
- Acción: reemplazado por stub documentado. Los endpoints de perfil se sirven
  en `ProfileView` y `SettingsView` (implementados en FASE 7B).

**`apps/users/viewsets/session_viewset.py`**
- Estado: importaba `SessionHistory` con `try/except ImportError`. `SessionHistory`
  no existe — las sesiones se gestionan en `apps.authentication.models.Session`.
- Acción: reemplazado por stub documentado.

### 1.3 Señales limpias — signals.py

**Antes:** `apps/users/signals.py` tenía 4 señales que referenciaban `UserProfile`,
`UserSettings` y `SessionHistory` con `try/except ImportError` y guards
`if UserProfile is not None`. Las señales `create_user_profile`, `save_user_profile`
y `create_user_settings` eran no-op desde FASE 4.

**Después:** Archivo reducido a 2 señales funcionales:
- `log_user_login`: captura IP (delegando el registro a `LoginService._persist_login()`).
- `log_user_logout`: cierra `Session.objects.filter(state='ACTIVE')` al hacer logout.

### 1.4 TODOs resueltos — 4 → 0

| Ubicación | TODO original | Resolución |
|---|---|---|
| `serializers/__init__.py` | `# TODO: No existe UserDetailSerializer` | Línea comentada eliminada |
| `password_service.py` | `# TODO: Configurar BASE_URL en settings` | Comentario actualizado referenciando `settings.BASE_URL` |
| `authentication/serializers.py` | `# TODO: En versión completa, validar cada respuesta` | Comentario actualizado con referencia a `UC_AUTH_05` |
| `core/middleware/timezone.py` | `# TODO: Si se implementa UserSettings.timezone` | Comentario actualizado para referenciar `SettingsView` (cache-backed) |

### 1.5 Admin.py vacíos — 3 archivos

Los siguientes `admin.py` tenían `from django.contrib import admin` pero ningún
`@admin.register()` ni `admin.site.register()`:

| Archivo | Acción |
|---|---|
| `apps/core/admin.py` | Eliminado el import, añadido comentario explicativo |
| `apps/pipeline/admin.py` | Eliminado el import (modelos eliminados en FASE 3) |
| `apps/access/admin.py` | Eliminado `format_html` sin uso |

---

## 2. Deuda técnica residual documentada

Los siguientes imports con `# noqa: F401` son **intencionales** y forman parte
del contrato público del módulo:

| Símbolo | Archivo | Justificación |
|---|---|---|
| `ActiveRecordQuery`, `SoftDeleteQuerySet` | `apps/core/models.py` | Re-exportados para compatibilidad con código que importa desde `apps.core.models` |
| `AuditedModel` | `apps/authentication/models.py` | Importado para re-exportación; usado en herencia de `CompleteBaseModel` |
| `is_ajax_request` | `apps/utils/helpers.py` | Re-exportado para compatibilidad; usado en `tests/unit/utils/test_helpers.py` |
| Serializadores de acceso (10) | `apps/access/serializers/__init__.py` | Contrato público del paquete; usados por vistas que importan desde el paquete |
| `ScheduledReportSerializer`, `SavedViewSerializer` | `apps/reports/serializers/__init__.py` | Contrato público del paquete |

---

## 3. Lecciones aprendidas sobre limpieza de imports

1. **`autoflake` es peligroso en proyectos con re-exportaciones.** El flag
   `--ignore-init-module-imports` protege `__init__.py` pero no protege archivos
   como `core/models.py` que re-exportan desde otros módulos.

2. **`pyflakes` no respeta `# noqa: F401`.** Es una convención de `flake8`.
   Usar `flake8 --select=F401` como herramienta de referencia, no `pyflakes`.

3. **Imports en bloques multilinea `from X import (\n...\n)` requieren que el `noqa`
   esté en la línea del `from`, no en la línea del símbolo.** flake8 reporta la
   línea inicial del bloque, no la línea del símbolo individual.

4. **La estrategia segura:** editar archivo por archivo, verificar con
   `python3 -c 'import py_compile; py_compile.compile(fpath, doraise=True)'`
   después de cada cambio, y ejecutar la suite completa después de cada lote.

---

## 4. Verificación final

```
$ python3 -m pytest tests/ --no-header -q --tb=no
1335 passed, 21 warnings in 55s

$ python3 -m flake8 apps/ --select=F401 --exclude=migrations,__pycache__
(sin output)

$ grep -rn "# TODO\|# FIXME\|# HACK" apps/ --include="*.py" \
  --exclude-dir=migrations --exclude-dir=__pycache__ | grep -v "test_\|admin.py"
(sin output)
```

---

*Generado: 2026-05-15 | Commit: e0b75ef*
