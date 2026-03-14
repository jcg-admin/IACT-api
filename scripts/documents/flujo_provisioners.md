# Flujo: Provisioners de Base de Datos

Scripts en `scripts/provisioners/{mariadb,postgres}/`.

Instalan y configuran las bases de datos en el servidor Linux local.
Cada provisioner es idempotente: puede ejecutarse multiples veces sin efectos colaterales.

## Fuente de configuracion

```
.env  (fuente unica de verdad)
 |
 |-- scripts/config/mariadb.conf   (adapter)
 |     IVR_DB_HOST     --> MARIADB_HOST
 |     IVR_DB_PORT     --> MARIADB_PORT
 |     IVR_DB_NAME     --> DB_NAME
 |     IVR_DB_USER     --> DB_USER
 |     IVR_DB_PASSWORD --> DB_PASSWORD
 |     MARIADB_VERSION  (default: 11.4)
 |     DB_ROOT_PASSWORD (requerido)
 |
 +-- scripts/config/postgres.conf  (adapter)
       DB_HOST     --> POSTGRES_HOST
       DB_PORT     --> POSTGRES_PORT
       DB_NAME     (sin cambio)
       DB_USER     (sin cambio)
       DB_PASSWORD (sin cambio)
       POSTGRES_VERSION  (default: 16)
       POSTGRES_PASSWORD (requerido)
```

## Provisioner MariaDB

```
scripts/provisioners/mariadb/bootstrap.sh
     |
     |-- source scripts/config/mariadb.conf
     |-- require_vars: MARIADB_HOST, DB_NAME, DB_USER, DB_ROOT_PASSWORD
     |
     |-- install.sh
     |       |
     |       |-- mariadbd instalado?
     |       |     SI --> skip (idempotente)
     |       |     NO --> agregar repo MariaDB oficial
     |       |             apt-get install mariadb-server mariadb-client
     |       |
     |       |-- bind-address = 0.0.0.0  en my.cnf
     |       |
     |       |-- service mariadb start
     |       |     (fallback: systemctl si disponible)
     |       |
     |       +-- mysql_secure_installation equivalente:
     |             SET PASSWORD FOR root
     |             DELETE anonymous users
     |             DROP test database
     |
     |-- setup.sh
     |       |
     |       |-- DB ${DB_NAME} existe?
     |       |     SI --> skip (idempotente)
     |       |     NO --> CREATE DATABASE ${DB_NAME}
     |       |             CHARACTER SET utf8mb4
     |       |             COLLATE utf8mb4_unicode_ci
     |       |
     |       |-- usuario ${DB_USER} existe?
     |       |     SI --> skip
     |       |     NO --> CREATE USER '${DB_USER}'@'%'
     |       |
     |       |-- GRANT ALL ON ${DB_NAME}.* TO '${DB_USER}'@'%'
     |       |
     |       +-- CREATE TABLE IF NOT EXISTS schema_version (...)
     |
     +-- show_connection_info
           Host: ${MARIADB_HOST}:${MARIADB_PORT}
           DB:   ${DB_NAME}
           User: ${DB_USER}
```

## Provisioner PostgreSQL

```
scripts/provisioners/postgres/bootstrap.sh
     |
     |-- source scripts/config/postgres.conf
     |-- require_vars: POSTGRES_HOST, DB_NAME, DB_USER, POSTGRES_PASSWORD
     |
     |-- install.sh
     |       |
     |       |-- postgresql instalado?
     |       |     SI --> skip (idempotente)
     |       |     NO --> agregar repo PostgreSQL apt oficial
     |       |             apt-get install postgresql-16
     |       |
     |       |-- ALTER USER postgres PASSWORD '${POSTGRES_PASSWORD}'
     |       |     (psql -U postgres directamente como root)
     |       |
     |       |-- listen_addresses = '*'  en postgresql.conf
     |       |
     |       |-- pg_hba.conf: host all all 0.0.0.0/0 md5
     |       |
     |       +-- service postgresql restart
     |
     |-- setup.sh
     |       |
     |       |-- rol ${DB_USER} existe?
     |       |     SI --> skip (idempotente)
     |       |     NO --> CREATE ROLE ${DB_USER} WITH LOGIN PASSWORD ...
     |       |
     |       |-- base ${DB_NAME} existe?
     |       |     SI --> skip
     |       |     NO --> CREATE DATABASE ${DB_NAME} OWNER ${DB_USER}
     |       |
     |       |-- GRANT ALL ON SCHEMA public TO ${DB_USER}
     |       |
     |       +-- CREATE TABLE IF NOT EXISTS schema_version (...)
     |             (usa PGPASSWORD env var, sin sudo -u postgres)
     |
     +-- show_connection_info
           Host: ${POSTGRES_HOST}:${POSTGRES_PORT}
           DB:   ${DB_NAME}
           User: ${DB_USER}
```

## Tabla de idempotencia

| Accion                    | Comprobacion previa          |
|---------------------------|------------------------------|
| Instalar paquete          | dpkg / command -v            |
| Crear base de datos       | SHOW DATABASES / \l          |
| Crear usuario             | SELECT User / \du            |
| Modificar configuracion   | grep antes de sed            |
| Iniciar servicio          | service status               |

## Ejecucion

```bash
# PostgreSQL
bash scripts/provisioners/postgres/bootstrap.sh

# MariaDB
bash scripts/provisioners/mariadb/bootstrap.sh
```
