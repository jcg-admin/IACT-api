# Prerequisitos de infraestructura — MariaDB (ivr_legacy)

**Versión:** 1.0.0 | **Fecha:** 2026-05-10  
**Referencia:** `IACT-db/docs/architecture/ANALISIS-MARIADB-PROVISIONAMIENTO-2026-05-10.md`

---

## Contexto

IACT-api se conecta a MariaDB 10.11 via socket Unix en producción y via TCP en
desarrollo. La base de datos `ivr_legacy` contiene el historial de llamadas IVR,
las tablas analíticas del pipeline ETL y los stored procedures de reporte.

La conexión usa el alias `'ivr'` en `DATABASES` de `base.py` y es enrutada por
el `DatabaseRouter` a modelos bajo `apps.ivr`. **`django_user` tiene acceso
READ-ONLY al schema histórico** y DML en las tablas analíticas creadas por el
pipeline ETL.

---

## Método de conexión por ambiente

| Ambiente | Variable activa | Mecanismo |
|---|---|---|
| Producción | `IVR_DB_SOCKET=/run/mysqld/mysqld.sock` | Socket Unix |
| Desarrollo | `IVR_DB_HOST=127.0.0.1` + `IVR_DB_PORT=3306` | TCP |
| Testing | `IVR_DB_HOST=127.0.0.1` + `IVR_DB_PORT=3306` | TCP |

`base.py` resuelve el mecanismo via `OPTIONS`:

```python
'ivr': {
    'ENGINE': 'django.db.backends.mysql',
    'HOST': config('IVR_DB_HOST', default='localhost'),
    'OPTIONS': {
        'unix_socket': config('IVR_DB_SOCKET', default='/run/mysqld/mysqld.sock'),
    },
}
```

Cuando `IVR_DB_SOCKET` tiene valor, el driver MySQL usa el socket y **ignora
`HOST` y `PORT`**. Para forzar TCP, vaciar `IVR_DB_SOCKET` en el `.env`.

---

## Usuario requerido: `django_user`

El provisioner `IACT-db/provisioners/mariadb/setup.sh` crea:

| Objeto | Valor |
|---|---|
| Base de datos | `ivr_legacy` |
| Usuario | `django_user` |
| Privilegios base | `SELECT ON ivr_legacy.*` (READ-ONLY — CNST-003) |
| Privilegios analíticos | `SELECT, INSERT, UPDATE, DELETE` en tablas `base_ivr_*`, `job_*`, `etl_runs` |

Los privilegios analíticos son otorgados **después** de aplicar
`schema_base_ivr.sql` en el paso 4 de `provision-mariadb.sh`. Sin el
provisionamiento `--full`, `django_user` tiene acceso de solo lectura.

Si los objetos deben crearse manualmente:

```sql
CREATE DATABASE ivr_legacy CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'django_user'@'localhost' IDENTIFIED BY 'django_pass';
CREATE USER 'django_user'@'%'        IDENTIFIED BY 'django_pass';
GRANT SELECT ON ivr_legacy.* TO 'django_user'@'localhost';
GRANT SELECT ON ivr_legacy.* TO 'django_user'@'%';
FLUSH PRIVILEGES;
```

---

## Objetos de BD requeridos para el pipeline ETL

El pipeline ETL necesita los objetos creados por `--full`. Sin ellos los
endpoints IVR fallan con `OperationalError: Table doesn't exist`.

### Tablas analíticas (`schema_base_ivr.sql`)

| Tabla | Propósito |
|---|---|
| `base_ivr_detalle` | Detalle normalizado por llamada |
| `base_ivr_clientes` | Resumen por cliente |
| `job_execution_log` | Log de ejecuciones ETL |
| `etl_runs` | Registro de corridas |
| `job_config` | Configuración de jobs |

### Funciones de utilidad (`funciones_utilidad.sql`)

Prerequisito de los SPs ETL: `fn_did_segmento`, `fn_normalizar_menu`,
`fn_normalizar_centro`, `fn_duracion_seg`, `ivr_es_dia_semana`.

### Stored Procedures

- **`sp_etl_*`** — pipeline de transformación histórico → analítico
- **`sp_rpt_*`** — reportes de llamadas IVR

---

## Comandos de aprovisionamiento

```bash
# Setup básico: BD + usuario + grants (sin schema completo)
sudo bash setup.sh mariadb

# Provisionamiento completo: schema + SPs + seed de datos
sudo bash setup.sh mariadb --full

# Solo schema + SPs, sin seed (entornos sin datos históricos)
SKIP_SEED=1 sudo bash setup.sh mariadb --full
```

---

## Variables `.env` requeridas

```bash
# Conexión MariaDB
DB_MARIADB_NAME=ivr_legacy
DB_MARIADB_USER=django_user
DB_MARIADB_PASSWORD=django_pass

# Producción (socket Unix — IVR_DB_HOST y IVR_DB_PORT se ignoran)
IVR_DB_SOCKET=/run/mysqld/mysqld.sock

# Desarrollo (TCP — dejar IVR_DB_SOCKET vacío o eliminarlo)
IVR_DB_HOST=127.0.0.1
IVR_DB_PORT=3306
```

---

## Diagnóstico rápido

```bash
# 1. MariaDB responde
mysqladmin --socket=/run/mysqld/mysqld.sock ping

# 2. Conexión TCP con credenciales django
mysql -h 127.0.0.1 -P 3306 -u django_user -pdjango_pass ivr_legacy \
    -e "SELECT CONCAT(DATABASE(), '@', USER());"

# 3. Conexión socket
mysql --socket=/run/mysqld/mysqld.sock -u django_user -pdjango_pass ivr_legacy \
    -e "SELECT CONCAT(DATABASE(), '@', USER());"

# 4. Verificar tablas analíticas
mysql --socket=/run/mysqld/mysqld.sock -u root ivr_legacy \
    -e "SELECT table_name FROM information_schema.tables
        WHERE table_schema='ivr_legacy'
        ORDER BY table_name;"

# 5. Verificar stored procedures
mysql --socket=/run/mysqld/mysqld.sock -u root \
    -e "SELECT routine_type, routine_name
        FROM information_schema.routines
        WHERE routine_schema='ivr_legacy'
        ORDER BY routine_type, routine_name;"

# 6. Verificación completa del entorno IACT-db
bash verify.sh
```

---

## Ver también

- `docs/setup/CONFIGURACION-ENTORNOS.md` — jerarquía de settings y variables `.env`
- `IACT-db/docs/architecture/ANALISIS-MARIADB-PROVISIONAMIENTO-2026-05-10.md` — análisis de hallazgos y correcciones
- `IACT-db/docs/architecture/HALLAZGOS-PROVISIONER-MARIADB-2026-05-10.md` — hallazgos H-MDB-001..015
