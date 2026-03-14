# Variables de entorno (.env)

Fuente unica de verdad para Django y scripts de provisioning.

## Principio

```
.env
 |
 |-- Django (config/settings/base.py)
 |     DATABASES['default'] usa DB_*
 |     DATABASES['ivr']     usa IVR_DB_*
 |
 |-- scripts/config/postgres.conf
 |     DB_HOST     --> POSTGRES_HOST
 |     DB_PORT     --> POSTGRES_PORT
 |     DB_NAME     (sin cambio)
 |     DB_USER     (sin cambio)
 |     DB_PASSWORD (sin cambio)
 |
 +-- scripts/config/mariadb.conf
       IVR_DB_HOST     --> MARIADB_HOST
       IVR_DB_PORT     --> MARIADB_PORT
       IVR_DB_NAME     --> DB_NAME
       IVR_DB_USER     --> DB_USER
       IVR_DB_PASSWORD --> DB_PASSWORD
```

## Variables

### Django

| Variable                 | Usado por | Ejemplo                          |
|--------------------------|-----------|----------------------------------|
| DJANGO_SETTINGS_MODULE   | Django    | config.settings.development      |
| SECRET_KEY               | Django    | django-insecure-CHANGE-ME        |
| DEBUG                    | Django    | True                             |
| ALLOWED_HOSTS            | Django    | localhost,127.0.0.1              |

### PostgreSQL (base de datos principal)

| Variable    | Usado por       | Ejemplo        |
|-------------|-----------------|----------------|
| DB_NAME     | Django + conf   | iact_analytics |
| DB_USER     | Django + conf   | django_user    |
| DB_PASSWORD | Django + conf   | django_pass    |
| DB_HOST     | Django + conf   | 127.0.0.1      |
| DB_PORT     | Django + conf   | 5432           |

### MariaDB (IVR Legacy, READ-ONLY)

| Variable        | Usado por       | Ejemplo     |
|-----------------|-----------------|-------------|
| IVR_DB_NAME     | Django + conf   | ivr_legacy  |
| IVR_DB_USER     | Django + conf   | django_user |
| IVR_DB_PASSWORD | Django + conf   | django_pass |
| IVR_DB_HOST     | Django + conf   | 127.0.0.1   |
| IVR_DB_PORT     | Django + conf   | 3306        |

### Provisioning (solo scripts, Django no las lee)

| Variable          | Usado por       | Ejemplo                  |
|-------------------|-----------------|--------------------------|
| MARIADB_VERSION   | mariadb.conf    | 11.4                     |
| POSTGRES_VERSION  | postgres.conf   | 16                       |
| DB_ROOT_PASSWORD  | mariadb install | root_pass_CHANGE_ME      |
| POSTGRES_PASSWORD | postgres install| postgres_pass_CHANGE_ME  |

## Variables prohibidas (CNST v2.2.1)

| Prefijo    | Razon                   |
|------------|-------------------------|
| EMAIL_*    | CNST-001                |
| SENTRY_*   | CNST_TECNICAS           |
| REDIS_*    | CNST_TECNICAS           |
| CELERY_*   | CNST-004 + CNST_TECNICAS|
| CHANNELS_* | CNST-004                |

## Gestion en git

- `.env` esta **trackeado** en git como plantilla con valores placeholder
- `.env.local` esta **ignorado** en git y se usa para credenciales reales

```bash
cp .env .env.local
# editar .env.local con valores reales del entorno
```
