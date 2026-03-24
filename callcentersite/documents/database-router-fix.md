# Fix: Database Router — CNST-003

**Fecha:** 2026-03-14
**Rama:** `claude/check-tools-ZDoAR`
**Archivos afectados:** `config/base.py`, `config/db_router.py`, ~~`config/database_router.py`~~ (eliminado)

---

## Contexto

El proyecto tiene arquitectura de **dos bases de datos**:

| Alias Django | Motor      | Nombre real en BD | Rol                             |
|---|---|---|---|
| `default`    | PostgreSQL | `iact_analytics`  | Analytics — lectura y escritura |
| `ivr`        | MariaDB    | `ivr_legacy`      | IVR legacy — **solo lectura**   |

Django necesita saber a qué base de datos enviar cada query. Para eso existe el **Database Router**: una clase que Django consulta antes de cada operación.

---

## Alias Django vs. Nombre real de la BD

Son dos cosas distintas que conviene no confundir:

```python
# config/settings/base.py
DATABASES = {
    'ivr': {                              # ← alias Django (nombre arbitrario interno)
        'NAME': config('IVR_DB_NAME'),    # ← nombre real de la BD en MariaDB
                                          #   valor en .env: IVR_DB_NAME=ivr_legacy
    }
}
```

| Concepto | Valor | Dónde vive |
|---|---|---|
| **Alias Django** | `ivr` | Clave en `DATABASES` — nombre que usa Django internamente |
| **Nombre real de la BD en MariaDB** | `ivr_legacy` | Variable `IVR_DB_NAME` en `.env` → el `CREATE DATABASE` real |

El alias Django puede llamarse `'ivr'`, `'mariadb'`, `'legacy'` o cualquier cosa — a Django no le importa que coincida con el nombre real de la BD. Lo que sí importa es que `DATABASE_ROUTERS` devuelva **exactamente ese alias** en sus métodos `db_for_read` y `db_for_write`.

En este proyecto el alias pasó de `'ivr_legacy'` a `'ivr'` para mayor claridad. El nombre real de la BD en MariaDB sigue siendo `ivr_legacy` (variable `IVR_DB_NAME=ivr_legacy` en `.env`).

---

## El problema original — dos archivos, el incorrecto activo

Existían dos archivos de router en `config/`:

```
config/
├── database_router.py   ← el que base.py usaba (INCORRECTO) → eliminado
└── db_router.py         ← el correcto (estaba huérfano)      → activo
```

`base.py` apuntaba al incorrecto:

```python
# ANTES — incorrecto
DATABASE_ROUTERS = ['config.database_router.IVRRouter']
```

---

## Bug 1 — `app_label` incorrecto

Django identifica a qué app pertenece un modelo con `app_label`.
Ese valor se deriva del `name` declarado en `apps.py`:

```python
# apps/ivr/apps.py
class IvrConfig(AppConfig):
    name = 'apps.ivr'
    #       ^^^^^^^^
    #       Django deriva: app_label = 'ivr'
```

El router incorrecto (`database_router.py`) buscaba `'ivr_legacy'`:

```python
# INCORRECTO — nunca matchea
ivr_legacy_apps = {'ivr_legacy'}
#                   ^^^^^^^^^^
#                   app_label real es 'ivr' → nunca va a matchear
#                   Router ignora todos los modelos IVR
```

**Consecuencia:** El router nunca identificaba los modelos de `apps.ivr`.
Todas las queries de `CallLog` caían al comportamiento por defecto → PostgreSQL.

---

## Bug 2 — devuelve un alias que no existe en DATABASES

Aun si el `app_label` hubiera matcheado, el router devolvía un alias inexistente:

```python
# INCORRECTO
def db_for_read(self, model, **hints):
    if model._meta.app_label in self.ivr_legacy_apps:
        return 'ivr_production'
        #       ^^^^^^^^^^^^^^
        #       No existe en DATABASES
        #       Django lanzaría: django.db.utils.ConnectionDoesNotExist
```

**Consecuencia:** Si el bug 1 se hubiera corregido solo, este bug habría provocado un error en runtime en cualquier query IVR.

---

## El router correcto — `db_router.py`

```python
# db_router.py — activo y correcto
class DatabaseRouter:

    ivr_apps = {'ivr'}     # ← app_label real de apps.ivr
    default_apps = {'core', 'authentication', 'users', 'reports'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.ivr_apps:
            return 'ivr'       # ← alias correcto en DATABASES
        if model._meta.app_label in self.default_apps:
            return 'default'
        return None            # Django usa 'default' por defecto

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.ivr_apps:
            return None        # CNST-003: write bloqueado
        if model._meta.app_label in self.default_apps:
            return 'default'
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.ivr_apps:
            return db == 'ivr'     # CallLog tiene managed=False, sin efecto real
        if app_label in self.default_apps:
            return db == 'default'
        return None
```

---

## Los dos cambios aplicados en `base.py`

```python
# 1. Alias de la conexión MariaDB: 'ivr_legacy' → 'ivr'
DATABASES = {
    'default': { ... },   # PostgreSQL — sin cambio
    'ivr': {              # MariaDB — alias cambiado
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('IVR_DB_NAME'),   # sigue siendo 'ivr_legacy' en .env
        ...
    }
}

# 2. Router: apuntar al archivo correcto
# ANTES:
DATABASE_ROUTERS = ['config.database_router.IVRRouter']

# DESPUÉS:
DATABASE_ROUTERS = ['config.db_router.DatabaseRouter']
```

---

## Flujo completo

```
Request HTTP
     │
     ▼
Vista / ViewSet
     │
     ├─── CallLog.objects.all()
     │         │
     │         ▼
     │    Django ORM pregunta al router:
     │    DatabaseRouter.db_for_read(CallLog)
     │         │
     │         │   CallLog._meta.app_label = 'ivr'
     │         │   'ivr' in ivr_apps  →  True
     │         │
     │         ▼
     │    return 'ivr'
     │         │
     │         ▼
     │    Conexión MariaDB  (alias='ivr', NAME='ivr_legacy')
     │    Usuario: django_user / ivr_readonly (solo SELECT)
     │         │
     │         ▼
     │    tabla: call_logs
     │
     └─── User.objects.create(...)
               │
               ▼
          DatabaseRouter.db_for_write(User)
               │
               │   User._meta.app_label = 'users'
               │   'users' not in ivr_apps
               │   'users' in default_apps  →  True
               │
               ▼
          return 'default'
               │
               ▼
          Conexión PostgreSQL  (alias='default', NAME='iact_analytics')
          tabla: users_user
```

> **Nota:** Apps como `access`, `audit`, `pipeline`, `alerts`, `dashboard`
> no están listadas en `default_apps`, pero el router devuelve `None` y
> Django las envía a `'default'` automáticamente. Funciona correctamente.

---

## Comparativa de los dos routers

| Aspecto | `database_router.IVRRouter` — eliminado | `db_router.DatabaseRouter` — activo |
|---|---|---|
| `app_label` buscado | `'ivr_legacy'` (incorrecto) | `'ivr'` (correcto) |
| Alias devuelto en lecturas IVR | `'ivr_production'` (no existe) | `'ivr'` |
| Bloquea writes IVR | Sí, pero nunca llegaba aquí | Sí — devuelve `None` |
| Bloquea migrations IVR | Sí | Sí (`managed=False` en CallLog) |

---

## CNST-003 — cumplimiento después del fix

| Regla | Estado |
|---|---|
| IVR solo lectura | `db_for_write` devuelve `None` para `app_label='ivr'` |
| Sin migrations en IVR | `CallLog` tiene `managed = False` |
| Usuario DB sin privilegios write | Credencial `ivr_readonly` / `django_user` en MariaDB (solo SELECT) |
| Django ORM no puede escribir en IVR | Router bloquea + usuario sin permisos (doble protección) |

---

## Archivos modificados

| Archivo | Acción |
|---|---|
| `config/settings/base.py` | Alias `'ivr_legacy'` → `'ivr'` en `DATABASES`; router apunta a `db_router.DatabaseRouter` |
| `config/settings/production.py` | `DATABASES['ivr_legacy']` → `DATABASES['ivr']` |
| `config/db_router.py` | Alias `'ivr_legacy'` → `'ivr'` en todo el archivo |
| `apps/ivr/adapters.py` | `.using('ivr_legacy')` → `.using('ivr')` |
| `tests/conftest.py` | Alias en config SQLite de tests |
| `tests/mocks/database_mocks.py` | Alias en mocks y router mock |
| `tests/conftest_COMPLETE.py` | `databases=['ivr_legacy']` → `databases=['ivr']` |
| `tests/factories/pipeline_factories.py` | `'database': 'ivr_legacy'` → `'database': 'ivr'` |
| `config/database_router.py` | **Eliminado** — router incorrecto y huérfano |
