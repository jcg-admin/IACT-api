# HALLAZGOS-FASE4-IACT-API-2026-05-16T21:18:35

**Documento:** HALLAZGOS-FASE4-IACT-API-2026-05-16T21:18:35  
**Fecha:** 2026-05-16  
**Repositorio:** IACT-api  
**Commit:** 92ff105  
**Plan base:** PLAN-IMPL-IACT-API-2026-05-16T17:53:35.md — FASE 4

---

## Estado antes de FASE 4

```
flake8 --select=E402: 16 ocurrencias en 6 archivos
  (reducción de 23→16 por las correcciones de FASE 2)
Suite: 1327 passed, 0 failed
```

---

## Hallazgos durante la implementación

### H-F4-001 — FASE 2 ya había eliminado 7 de los 23 E402 del plan

El plan original documentó 23 E402. Al comenzar FASE 4, el inventario real
era 16. La FASE 2 (correcciones de `reports/views.py`) ya eliminó los
siguientes imports mid-module como efecto secundario:

- `from rest_framework import viewsets` (redundante — ya en L8)
- `from rest_framework.permissions import IsAuthenticated` (redundante — ya en L11)
- `from apps.access.permissions.function_permissions import HasFunction` (×2 — redundante)
- `from rest_framework.views import APIView` — eliminado en K-005
- `from rest_framework.response import Response` — eliminado en K-005
- `from django.utils import timezone` — eliminado en K-005

Total: 7 E402 menos que el plan original. Esto es correcto — no son regresiones
sino eliminaciones ya realizadas.

### H-F4-002 — `audit/views.py` tenía el docstring después del primer import

El archivo comenzaba con:

```python
from drf_spectacular.utils import extend_schema, ...
"""
Views para consulta de AuditLog.
...
"""
from rest_framework import viewsets, ...
```

El docstring de módulo estaba en L2, después de un import en L1. Python
permite esto sintácticamente (el docstring no es `__doc__` del módulo cuando
está en esa posición), pero es confuso y produce E402 en los imports que
siguen al docstring.

Corrección: docstring movido a la primera línea, todos los imports
consolidados después.

### H-F4-003 — `audit/urls.py` tenía dos problemas combinados

El archivo tenía:
1. El docstring de módulo en la mitad del archivo (L9-11)
2. `AuditIntegrityView` importado en L26, dentro del bloque `urlpatterns`
3. El patrón `urlpatterns +=` para añadir rutas adicionales

La corrección consolidó todo en una sola lista `urlpatterns` con el
comentario `# B-08: UC_AUD_04 — integridad` antes de la ruta de integridad.
El `urlpatterns +=` fue eliminado — es funcional pero innecesario cuando
se puede declarar toda la lista de una vez.

### H-F4-004 — `users/serializers/__init__.py` tiene una clase definida entre imports

El archivo define la clase `PasswordResetConfirmSerializer` en la mitad
del bloque de imports:

```python
from apps.authentication.serializers.recovery import (
    PasswordResetRequestSerializer,
)

# PasswordResetConfirmSerializer: simple serializer de confirmación vía token
from rest_framework import serializers as _drf_serializers

class PasswordResetConfirmSerializer(_drf_serializers.Serializer):
    ...

# UserProfileSerializer alias for ProfileSerializer
UserProfileSerializer = ProfileSerializer

# Session serializer (1)  ← esto es el E402
from apps.users.serializers.session_serializer import (
    SessionHistorySerializer,
)
```

La clase y el alias deben estar después de todos los imports — ese patrón
es necesario porque `PasswordResetConfirmSerializer` hereda de un import.
El único E402 real era `SessionHistorySerializer` que estaba después de la
clase y el alias.

Corrección mínima aplicada: mover solo `SessionHistorySerializer` antes de
la clase, manteniendo el resto del archivo intacto.

### H-F4-005 — `reports/views.py`: `ScheduledReport` y `SavedView` movidos al import de `.models`

Al mover los imports de K-002/K-003 al bloque inicial, se consolidaron los
modelos:

```python
# Antes (K-002 mid-module):
from .models import Report, ExportJob
# ...
from .models import ScheduledReport, SavedView  # mid-module

# Después (inicio):
from .models import Report, ExportJob, ScheduledReport, SavedView
```

Lo mismo para los serializers. Se verificó F401=0 después del cambio
para confirmar que todos los nombres importados se usan.

---

## Cambios por archivo

| Archivo | E402 corregidos | Tipo de corrección |
|---|---|---|
| `users/views.py` | 4 | 4 imports DRF movidos antes del `logger` |
| `users/serializers/__init__.py` | 1 | `SessionHistorySerializer` movido al bloque inicial |
| `alerts/models.py` | 1 | `import uuid as _uuid` movido al inicio |
| `authentication/models.py` | 1 | `import uuid as _uuid` movido al inicio |
| `audit/views.py` | 3 | Docstring al inicio, `hashlib`/`hmac`/`settings` consolidados |
| `audit/urls.py` | 1 | Docstring al inicio, `AuditIntegrityView` consolidado, `urlpatterns +=` eliminado |
| `reports/views.py` | 5 | Bloque K-002/K-003 consolidado en imports iniciales |

---

## Verificaciones realizadas (T4.8)

| Verificación | Resultado |
|---|---|
| `flake8 --select=E402` en toda la base | 0 ocurrencias |
| `flake8 --select=F401` en toda la base | 0 ocurrencias |
| `python manage.py check` | 0 issues |
| Tests usuarios + alerts + authentication + reports + api | 309 passed, 0 failed |
| Suite unit + api completa | 1223 passed, 0 failed |
| Suite integration (mysqld fresco) | 104 passed, 0 failed |

---

## Estado después de FASE 4

```
flake8 --select=E402: 0 ocurrencias
Suite: 1327 passed, 0 failed

DT-API-004: RESUELTA
```

### DTs pendientes

| Código | Descripción |
|---|---|
| DT-API-007 | W291/W293/W391/W292×3450 — trailing whitespace (108 archivos) |
| DT-API-008 | Patrón `logs/` en `.gitignore` demasiado amplio (identificado en FASE 3) |

---

*Generado: 2026-05-16T21:18:35 | Commit: 92ff105 | Suite: 1327 passed, 0 failed*
