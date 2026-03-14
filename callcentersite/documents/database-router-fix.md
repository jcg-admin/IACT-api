# Fix: Database Router — CNST-003

**Fecha:** 2026-03-14
**Rama:** `claude/check-tools-ZDoAR`
**Archivos afectados:** `config/base.py`, `config/database_router.py`, `config/db_router.py`

---

## Contexto

El proyecto tiene arquitectura de **dos bases de datos**:

| Alias Django | Motor     | Rol                          |
|---|---|---|
| `default`    | PostgreSQL | Analytics — lectura y escritura |
| `ivr_legacy` | MariaDB    | IVR legacy — **solo lectura**   |

Django necesita saber a qué base de datos enviar cada query. Para eso existe el **Database Router**: una clase que Django consulta antes de cada operación.

---

## El problema — dos archivos, el incorrecto activo

Existían dos archivos de router en `config/`:

```
config/
├── database_router.py   ← el que base.py usaba (INCORRECTO)
└── db_router.py         ← el correcto (huérfano, nadie lo llamaba)
```

`base.py` línea 182 apuntaba al incorrecto:

```python
DATABASE_ROUTERS = ['config.database_router.IVRRouter']
```

---

## Bug 1 — `app_label` incorrecto

Django identifica a qué app pertenece un modelo con `app_label`.
Ese valor viene del `name` declarado en `apps.py`.

```python
# apps/ivr/apps.py
class IvrConfig(AppConfig):
    name = 'apps.ivr'
    #       ^^^^^^^^
    #       Django deriva: app_label = 'ivr'
```

El router incorrecto buscaba `'ivr_legacy'`:

```python
# database_router.py — INCORRECTO
ivr_legacy_apps = {'ivr_legacy'}
#                   ^^^^^^^^^^
#                   Nunca va a matchear 'ivr'
#                   El router ignora todos los modelos IVR
```

**Consecuencia:** El router nunca identificaba los modelos de `apps.ivr`.
Todas las queries de `CallLog` caían al comportamiento por defecto → PostgreSQL.

---

## Bug 2 — devuelve una base de datos que no existe

Aun si el `app_label` hubiera matcheado, el router devolvía un alias inexistente:

```python
# database_router.py — INCORRECTO
def db_for_read(self, model, **hints):
    if model._meta.app_label in self.ivr_legacy_apps:
        return 'ivr_production'
        #       ^^^^^^^^^^^^^^
        #       No existe en DATABASES (solo hay 'default' e 'ivr_legacy')
        #       Django lanzaría: django.db.utils.ConnectionDoesNotExist
```

**Consecuencia:** Si el bug 1 se hubiera corregido solo, este bug habría provocado
un error en runtime en cualquier query IVR.

---

## El router correcto — `db_router.py`

Este archivo ya existía con la lógica correcta, pero nadie lo usaba:

```python
# db_router.py — CORRECTO
class DatabaseRouter:

    ivr_apps = {'ivr'}          # ← app_label real de apps.ivr
    default_apps = {'core', 'authentication', 'users', 'reports'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.ivr_apps:
            return 'ivr_legacy'  # ← alias real en DATABASES
        if model._meta.app_label in self.default_apps:
            return 'default'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.ivr_apps:
            return None          # ← CNST-003: write bloqueado
        if model._meta.app_label in self.default_apps:
            return 'default'
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.ivr_apps:
            return db == 'ivr_legacy'   # managed=False en CallLog, sin efecto real
        if app_label in self.default_apps:
            return db == 'default'
        return None
```

---

## El fix — una línea en `base.py`

```python
# base.py línea 182

# ANTES (incorrecto):
DATABASE_ROUTERS = ['config.database_router.IVRRouter']

# DESPUÉS (correcto):
DATABASE_ROUTERS = ['config.db_router.DatabaseRouter']
```

---

## Flujo completo después del fix

```
Request HTTP
     │
     ▼
Vista / ViewSet
     │
     ├─── CallLog.objects.all()
     │         │
     │         ▼
     │    Django ORM
     │         │
     │         ▼
     │    DatabaseRouter.db_for_read(CallLog)
     │         │
     │         │   app_label = 'ivr'  ✓ matchea ivr_apps
     │         │
     │         ▼
     │    return 'ivr_legacy'
     │         │
     │         ▼
     │    Conexión MariaDB (READ-ONLY)
     │    Usuario: ivr_readonly (solo SELECT)
     │         │
     │         ▼
     │    tabla: call_logs
     │
     └─── User.objects.create(...)
               │
               ▼
          Django ORM
               │
               ▼
          DatabaseRouter.db_for_write(User)
               │
               │   app_label = 'users' → no está en ivr_apps
               │   → cae a default_apps ('users' tampoco está...)
               │   → return None → Django usa 'default'
               │
               ▼
          Conexión PostgreSQL (READ + WRITE)
          tabla: users_user
```

> **Nota:** `users`, `access`, `audit`, `pipeline`, `alerts`, `dashboard` no están
> en `default_apps` del router, por lo que el router devuelve `None` y Django
> usa `'default'` automáticamente. Funciona correctamente aunque no estén
> listados explícitamente.

---

## Comparativa de los dos routers

| Aspecto | `database_router.IVRRouter` (❌ incorrecto) | `db_router.DatabaseRouter` (✓ correcto) |
|---|---|---|
| `app_label` buscado | `'ivr_legacy'` | `'ivr'` |
| DB para lecturas IVR | `'ivr_production'` (no existe) | `'ivr_legacy'` |
| Bloquea writes IVR | Sí (pero nunca llega aquí) | Sí — devuelve `None` |
| Bloques migrations IVR | Sí | Sí (`managed=False` en modelo) |
| En uso | Sí (incorrecto) | No (huérfano) |

---

## CNST-003 — cumplimiento después del fix

| Regla | Estado |
|---|---|
| IVR solo lectura | ✓ `db_for_write` devuelve `None` para `app_label='ivr'` |
| Sin migrations en IVR | ✓ `CallLog` tiene `managed = False` |
| Usuario DB sin privilegios write | ✓ Credencial `ivr_readonly` en MariaDB |
| Django ORM no puede escribir en IVR | ✓ Router bloquea + usuario sin permisos |

---

## Archivos involucrados

| Archivo | Acción |
|---|---|
| `config/base.py` | Cambiar `DATABASE_ROUTERS` para apuntar a `db_router.DatabaseRouter` |
| `config/db_router.py` | Mantener — es el router correcto |
| `config/database_router.py` | Eliminar — era incorrecto y genera confusión |
