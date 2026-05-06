# Relación con IACT-db — Separación de responsabilidades

**Fecha:** 2026-05-05  
**Estado:** Documentado — implementación pendiente

---

## Contexto

`IACT-api` tiene en `scripts/` dos categorías de scripts que hasta ahora
convivían sin distinción clara:

1. Scripts de **infraestructura de bases de datos** — crean BDs, usuarios,
   privilegios, siembran datos de prueba.
2. Scripts del **ciclo de vida de la aplicación** — migraciones Django,
   tests, verificación de código, Apache.

El repositorio `IACT-db` existe específicamente para gestionar la
infraestructura de bases de datos (MariaDB `ivr_legacy` y PostgreSQL
`iact_analytics`). Mantener los scripts de BD en ambos repositorios
genera duplicación y divergencia.

---

## Qué gestiona cada repositorio

### IACT-db — Infraestructura de BD

Responsabilidad exclusiva: instalar, configurar, arrancar y verificar
MariaDB y PostgreSQL.

```
IACT-db/
├── bootstrap.sh                          # instala y configura todo
├── setup.sh                              # solo configura (sin instalar)
├── verify.sh                             # verificación completa (7 secciones)
├── scripts/install-clients.sh           # instala mysql/psql CLI
├── provisioners/mariadb/
│   ├── install.sh                        # instala MariaDB 11.4
│   ├── setup.sh                          # crea ivr_legacy, usuario, READ-ONLY
│   └── schema_seed.sh                    # tbl_temp_prueba_ivr + 3000 registros
└── provisioners/postgres/
    ├── install.sh                        # instala PostgreSQL 16
    └── setup.sh                          # crea iact_analytics, usuario, CREATEDB
```

### IACT-api — Ciclo de vida de la aplicación

Responsabilidad: dependencias Python, migraciones Django, tests, Apache.
**No gestiona la infraestructura de BD.**

```
IACT-api/scripts/
├── bootstrap.sh          # provisioning del entorno de la aplicación
│                         # (phases: os, system_packages, python, apache, verify)
│                         # phase_databases → DELEGA en IACT-db
├── run_db.sh             # makemigrations, migrate, check, fresh reset Django
├── run_tests.sh          # ejecuta pytest
├── verificar_implementacion.sh
├── apache/               # instala y configura Apache para la API
└── provisioners/system/
    ├── check_os.sh       # verifica Ubuntu/Debian
    ├── check_tools.sh    # verifica herramientas del sistema
    └── install_packages.sh   # Python, pip, build-essential, clientes de BD
```

---

## Scripts de BD que se eliminan de IACT-api

Los siguientes scripts son funcionalidad de IACT-db y no deben mantenerse
en IACT-api. Su equivalente en IACT-db es más completo y está probado:

| Script en IACT-api | Reemplazado por en IACT-db | Diferencias |
|---|---|---|
| `provisioners/mariadb/db_setup.sh` | `provisioners/mariadb/setup.sh` | IACT-db añade verificación CNST-003 post-GRANT |
| `provisioners/mariadb/schema_temp_prueba.sh` | `provisioners/mariadb/schema_seed.sh` | IACT-db añade verificación de longitud de `numero` y muestra representativa |
| `provisioners/postgres/db_setup.sh` | `provisioners/postgres/setup.sh` | Equivalentes |
| `utils/database.sh` | `utils/database.sh` (v1.1.0) | IACT-db tiene funciones de arranque y detección más robustas |
| `bootstrap.sh phase_databases` | `IACT-db/setup.sh` | IACT-db verifica 7 puntos, IACT-api solo arranca los servicios |

---

## Cómo IACT-api usa las BDs de IACT-db

Las credenciales de `config/settings/testing_local.py` coinciden
exactamente con lo que IACT-db configura. No requiere ningún cambio
en los settings de Django.

```python
# config/settings/testing_local.py — sin cambios
DATABASES = {
    'default': {                      # PostgreSQL
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':     'iact_analytics', # = DB_POSTGRES_NAME en IACT-db/.env
        'USER':     'django_user',    # = DB_POSTGRES_USER
        'PASSWORD': 'django_pass',    # = DB_POSTGRES_PASSWORD
        'HOST':     '127.0.0.1',      # = POSTGRES_HOST
        'PORT':     '5432',           # = POSTGRES_PORT
    },
    'ivr': {                          # MariaDB ivr_legacy (READ-ONLY)
        'ENGINE': 'django.db.backends.mysql',
        'NAME':     'ivr_legacy',     # = DB_MARIADB_NAME en IACT-db/.env
        'USER':     'django_user',    # = DB_MARIADB_USER
        'PASSWORD': 'django_pass',    # = DB_MARIADB_PASSWORD
        'HOST':     '127.0.0.1',      # = MARIADB_HOST
        'PORT':     '3306',           # = MARIADB_PORT
    },
}
```

---

## Orden de ejecución en una sesión nueva

Las BDs no persisten entre reinicios del entorno (sin systemd como
proceso 1). El orden correcto al iniciar una sesión de desarrollo es:

```
1. IACT-db levanta y configura las BDs
   └── bash /ruta/a/IACT-db/setup.sh

2. IACT-api migra y ejecuta tests
   ├── DJANGO_SETTINGS_MODULE=config.settings.testing_local
   │   python manage.py migrate
   └── pytest .
```

La `phase_databases` del `bootstrap.sh` de IACT-api se refactorizará
para delegar en `IACT-db/setup.sh` en lugar de llamar a sus propios
scripts de BD.

---

## Estado de la implementación

| Tarea | Estado |
|---|---|
| Documentar la separación de responsabilidades | Completado |
| Crear `IACT-db` con scripts equivalentes | Completado |
| Verificar que IACT-api funciona con BDs de IACT-db | Completado (287 tests pasan) |
| Eliminar scripts de BD de IACT-api | Pendiente |
| Refactorizar `phase_databases` en bootstrap.sh | Pendiente |

---

## Referencias

- `IACT-db/docs/architecture/SEPARACION-IACT-API.md` — visión desde IACT-db
- `IACT-db/docs/getting-started/QUICKSTART.md` — cómo levantar las BDs
- `IACT-db/verify.sh` — verificación completa del entorno de BD
