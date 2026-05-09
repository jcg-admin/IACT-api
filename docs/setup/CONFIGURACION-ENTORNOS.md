# Arquitectura de configuración — IACT-api

**Versión:** 1.0.0 | **Fecha:** 2026-05-09

## Principio fundamental

> Las decisiones de configuración van en los archivos de settings.
> Los secretos y valores específicos de la instancia van en `.env`.

## Jerarquía de settings

```
base.py
├── development.py    DJANGO_SETTINGS_MODULE=config.settings.development
├── production.py     DJANGO_SETTINGS_MODULE=config.settings.production
├── testing_local.py  DJANGO_SETTINGS_MODULE=config.settings.testing_local
└── testing.py        DJANGO_SETTINGS_MODULE=config.settings.testing
```

## ¿Qué va en `.env`?

Solo secretos y valores específicos de la instancia:
- `SECRET_KEY`
- `DB_PASSWORD`, `IVR_DB_PASSWORD`
- `DB_HOST` / `DB_SOCKET`
- `IVR_DB_HOST` / `IVR_DB_SOCKET`
- `ALLOWED_HOSTS`
- `DJANGO_SETTINGS_MODULE`

## Lo que NO va en `.env`

- `DEBUG` → `production.py` / `development.py`
- `connect_timeout` → `base.py`
- `SECURE_SSL_REDIRECT` → `production.py`
- Headers de seguridad → `production.py`

## El `.env` de producción (esta instancia)

```
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=<clave-segura>
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=iact_analytics
DB_USER=django_user
DB_PASSWORD=django_pass
DB_SOCKET=/var/run/postgresql

IVR_DB_NAME=ivr_legacy
IVR_DB_USER=django_user
IVR_DB_PASSWORD=django_pass
IVR_DB_SOCKET=/run/mysqld/mysqld.sock

IVR_QUERY_TIMEOUT_SEC=30
```

## Prerequisito para socket Unix en PostgreSQL

`pg_hba.conf` necesita antes de la línea `peer` genérica:
```
local   all   django_user   scram-sha-256
local   all   all           peer
```

`django_user` no existe como usuario OS — `peer` auth falla.
`scram-sha-256` local permite auth con password.

## Guía rápida

| Quiero cambiar... | Va en |
|---|---|
| Hostname de BD en producción | `.env` → `DB_HOST` |
| Timeout de conexión | `base.py` |
| Activar HTTPS | `production.py` |
| Contraseña de BD | `.env` → `DB_PASSWORD` |
| DEBUG | `production.py` / `development.py` |
| Socket Unix | `.env` → `DB_SOCKET` |
