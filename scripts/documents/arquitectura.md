# Arquitectura del Proyecto

**Stack:** Python 3.11+ / Django 5 / Django REST Framework 3.14
**Compliance:** CNST v2.2.1

## Bases de datos

```
+-----------------------------+    +-----------------------------+
|     PostgreSQL 16           |    |     MariaDB 11.4            |
|     iact_analytics          |    |     ivr_legacy  (READ-ONLY) |
|     127.0.0.1:5432          |    |     127.0.0.1:3306          |
|     DB_HOST / DB_PORT       |    |     IVR_DB_HOST / IVR_DB_PORT|
+-----------------------------+    +-----------------------------+
              |                                      |
              +------------------+-------------------+
                                 |
                        +--------+--------+
                        |   Django ORM    |
                        |  DATABASES = {  |
                        |   'default'     |  <- PostgreSQL
                        |   'ivr'         |  <- MariaDB
                        |  }              |
                        +--------+--------+
                                 |
                        +--------+--------+
                        |  DRF API Layer  |
                        |  /api/v1/...    |
                        +-----------------+
```

## Estructura de directorios

```
IACT-api/
|-- .env                        <- fuente unica de verdad (Django + scripts)
|-- callcentersite/             <- proyecto Django principal
|   |-- manage.py
|   |-- config/
|   |   +-- settings/
|   |       |-- base.py
|   |       |-- development.py
|   |       +-- production.py
|   |-- apps/
|   +-- static/
|       +-- icons/
|           |-- menu/
|           |-- submenu/
|           +-- defaults/
|-- requirements/
|   |-- base.txt
|   +-- development.txt
|-- scripts/
|   |-- bootstrap.sh
|   |-- check_tools.sh
|   |-- config/
|   |   |-- mariadb.conf
|   |   +-- postgres.conf
|   |-- provisioners/
|   |   |-- mariadb/
|   |   |   |-- bootstrap.sh
|   |   |   |-- install.sh
|   |   |   +-- setup.sh
|   |   +-- postgres/
|   |       |-- bootstrap.sh
|   |       |-- install.sh
|   |       +-- setup.sh
|   |-- utils/
|   |   |-- core.sh
|   |   |-- database.sh
|   |   |-- logging.sh
|   |   |-- network.sh
|   |   |-- provisioning.sh
|   |   |-- system.sh
|   |   +-- validation.sh
|   |-- documents/
|   +-- logs/                   <- gitignored, generado en runtime
+-- venv/                       <- gitignored
```

## Restricciones CNST v2.2.1

Las siguientes integraciones estan **prohibidas** en este proyecto:

| Variable        | Razon                  |
|-----------------|------------------------|
| EMAIL_*         | CNST-001               |
| SENTRY_*        | CNST_TECNICAS          |
| REDIS_*         | CNST_TECNICAS          |
| CELERY_*        | CNST-004 + CNST_TECNICAS|
| CHANNELS_*      | CNST-004               |
