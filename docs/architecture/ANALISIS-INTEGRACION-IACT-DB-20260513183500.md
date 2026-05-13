# Análisis — Flujo de Conexión IACT-api → IACT-db, drf-spectacular y Opciones de Despliegue

**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Repositorios:** `IACT-api` (Django 5.0, DRF, drf-spectacular 0.27.0, mysqlclient 2.2.1)
y `IACT-db` (MariaDB 10.11.14, ivr_legacy)

---

## Parte 1 — drf-spectacular: estado real de los endpoints que tocan MariaDB

### Arquitectura del schema OpenAPI

```
base.py → SPECTACULAR_SETTINGS
    POSTPROCESSING_HOOKS:
        1. drf_spectacular.hooks.postprocess_schema_enums
        2. config.spectacular_hooks.collect_app_tags    ← hook OCP propio

collect_app_tags():
    por cada app en INSTALLED_APPS que empiece con 'apps.':
        importa app.schema
        lee SPECTACULAR_TAGS = [{'name': ..., 'description': ...}]
        los agrega al schema si el nombre no existe aún
```

El principio que impone el hook es Open/Closed: agregar una app nueva nunca
requiere tocar `base.py` — solo crear su `schema.py` con `SPECTACULAR_TAGS`.

### Cobertura `@extend_schema` por endpoint

Todos los endpoints que tocan MariaDB usan `@extend_schema`, pero con
diferente nivel de completitud:

**Completamente documentados (6 de 8 endpoints IVR de reporte):**
```
GET /api/reports/ivr/clients/            → @extend_schema, tags, params, 200/400/503
GET /api/reports/ivr/transfer-centers/  → @extend_schema, tags, params, 200/503
GET /api/reports/ivr/abandoned/         → @extend_schema, tags, params, 200/503
GET /api/reports/ivr/menu-errors/       → @extend_schema, tags, params, 200/503
GET /api/reports/ivr/centers-by-segment/→ @extend_schema, tags, params, 200/503
GET /api/reports/ivr/menus/             → @extend_schema, tags, 3 params, 200/503
```

**Parcialmente documentados (2 de 8 endpoints IVR de reporte):**
```
GET /api/reports/ivr/menu-redirigidos/  → @extend_schema ✓, tags AUSENTE ✗
GET /api/reports/ivr/menu-centro/       → @extend_schema ✓, tags AUSENTE ✗
```
Estas dos views tienen el decorador pero sin `tags=`. En Swagger/Redoc
aparecerán bajo "default" — separadas del resto de los reportes IVR.

**Pipeline ETL (5 endpoints):**
```
GET  /api/pipeline/status/            → @extend_schema, tags="Estado del Pipeline"
GET  /api/pipeline/errors/            → @extend_schema, tags="Estado del Pipeline"
GET  /api/pipeline/data-availability/ → @extend_schema, tags="Estado del Pipeline"
POST /api/pipeline/retry/             → @extend_schema, tags="Estado del Pipeline"
GET  /api/pipeline/ivr-health/        → @extend_schema, tags="Estado del Pipeline"
```

**Logs (5 endpoints que tocan MariaDB):**
```
GET /api/logs/etl/tail/   → @extend_schema, tags="Registros del Sistema"
GET /api/logs/metrics/    → @extend_schema, tags="Registros del Sistema"
GET /api/logs/health/     → @extend_schema, tags="Registros del Sistema"
GET /api/logs/search/     → @extend_schema, tags="Registros del Sistema" (lee log Django)
GET /api/logs/export/     → @extend_schema, tags="Registros del Sistema"
```
Problema: `apps/logs/schema.py` **no existe**. El hook `collect_app_tags`
no puede agregar la descripción del tag `Registros del Sistema` — el tag
aparece en Swagger pero sin descripción.

### Gaps estructurales en el schema OpenAPI

**GAP-SPEC-01: `MenuRedirigidosView` y `MenuCentroView` sin tag**

```python
# Estado actual (ivr_views.py):
class MenuRedirigidosView(APIView):
    @extend_schema(
        parameters=[...],
        responses={200: OpenApiTypes.OBJECT, 503: ...},
        # ← FALTA: tags=["Reportes de Llamadas"]
    )

# Corrección:
    @extend_schema(
        parameters=[...],
        responses={200: OpenApiTypes.OBJECT, 503: ...},
        tags=["Reportes de Llamadas"],
    )
```

**GAP-SPEC-02: Cuerpos de respuesta sin schema tipado**

Todos los endpoints IVR usan `OpenApiResponse(description="...")` sin
serializer. En Swagger el body de respuesta aparece como `{}`. Esto es
un trade-off consciente: las columnas de los SPs son dinámicas —
`dict(zip(cols, row))` incluye automáticamente columnas nuevas. El precio
es que el schema OpenAPI no puede autogenerar tipos para el frontend.

Opciones para tipar las respuestas sin perder la aditividad:
- `inline_serializer` por SP (estático, requiere actualización manual al cambiar el SP)
- Documento externo de referencia de columnas (no afecta al schema)
- OpenAPI `additionalProperties: true` explícito

**GAP-SPEC-03: `apps/logs/schema.py` no existe**

```python
# Crear: apps/logs/schema.py
SPECTACULAR_TAGS = [
    {
        'name': 'Registros del Sistema',
        'description': (
            'Logs del sistema: tail de Django log, entradas del pipeline ETL, '
            'búsqueda, exportación y métricas. UC_LOG_01..07.'
        ),
    },
]
```

**GAP-SPEC-04: Tres objetos IACT-db sin endpoint ni presencia en OpenAPI**

`sp_rpt_resumen_abandono_rollup`, `v_etl_rendimiento` y `pipeline_event_log`
no tienen endpoint en IACT-api → no aparecen en el schema OpenAPI. Ver
ANALISIS-INTEGRACION-IACT-DB para el código de los endpoints faltantes.

---

## Parte 2 — Flujo de conexión en el ambiente actual (misma VPS)

### Stack completo capa por capa

```
REQUEST:
  Cliente HTTP
      │ HTTPS / HTTP (puerto 80 / 443)
      ▼
  Apache 2.4 + mod_wsgi
      │ WSGIDaemonProcess iact  processes=2  threads=4
      │ Django WSGI application (wsgi.py)
      │ Python → mysqlclient 2.2.1 (C extension sobre libmysqlclient)
      │ alias connections['ivr']
      │
      │  IPC: Unix Domain Socket
      │  /run/mysqld/mysqld.sock
      ▼
  MariaDB 10.11.14
      └── ivr_legacy
          ├── base_ivr_detalle
          ├── base_ivr_clientes
          ├── job_execution_log
          ├── etl_runs
          ├── pipeline_event_log     ← nuevo FASE 1
          ├── v_etl_rendimiento      ← nuevo FASE 3 (T3.1)
          └── sp_rpt_*, sp_etl_*
```

### Resolución del mecanismo de conexión

`base.py` tiene esta lógica:

```python
'ivr': {
    'ENGINE': 'django.db.backends.mysql',
    'NAME':   config('IVR_DB_NAME',     default='ivr_legacy'),
    'USER':   config('IVR_DB_USER',     default='django_user'),
    'PASSWORD': config('IVR_DB_PASSWORD', default='django_pass'),
    'HOST':   config('IVR_DB_HOST',     default='localhost'),
    'PORT':   config('IVR_DB_PORT',     default='3306'),
    'OPTIONS': {
        'charset': 'utf8mb4',
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        'unix_socket': config('IVR_DB_SOCKET', default='/run/mysqld/mysqld.sock'),
    },
}
```

Regla del driver `mysqlclient`:
- Si `OPTIONS['unix_socket']` tiene valor → **usa socket Unix, ignora HOST y PORT**
- Si `OPTIONS['unix_socket']` está vacío o ausente → usa **TCP hacia HOST:PORT**

Estado actual del `.env`:
```bash
IVR_DB_SOCKET=/run/mysqld/mysqld.sock   ← activo → socket Unix
IVR_DB_HOST=localhost                   ← ignorado
```

### Ciclo de vida de una llamada a SP

```
1. GET /api/reports/ivr/clients/?quarter=Q01_25

2. ClientesReportView.get(request)
     quarter = request.query_params.get('quarter', 'Q01_25')
     errors  = _validate(quarter=quarter)
         → svc.get_available_quarters()
             → connections['ivr'].cursor()
             → cursor.execute("SELECT DISTINCT trimestre FROM base_ivr_detalle")
             → retorna set de quarters disponibles
     if quarter not in available → Response({'errors': [...]}, 400)

3. _ivr_response(svc.get_clients, quarter, ...)

4. svc.get_clients('Q01_25')
     → _call_sp('sp_rpt_clientes', ['Q01_25'])

5. _call_sp:
   a. connections['ivr'].cursor()
      → mysqlclient abre socket /run/mysqld/mysqld.sock
      → autenticación: django_user / django_pass
      → MariaDB ejecuta init_command:
           SET sql_mode='STRICT_TRANS_TABLES'
   b. cursor.execute("SET SESSION MAX_STATEMENT_TIME=30")
      → timeout por query en MariaDB
   c. cursor.callproc('sp_rpt_clientes', ['Q01_25'])
      → MariaDB ejecuta el SP en ivr_legacy
      → retorna result set
   d. cursor.description → columnas
   e. cursor.fetchall() → filas
   f. [dict(zip(cols, row)) for row in rows]

6. Response({'total_rows': 3, 'data': [...]})
   → JSON al cliente
   → conexión se cierra (CONN_MAX_AGE=0 default)
```

### Servidor WSGI: Apache 2.4 + mod_wsgi

La configuración real del proyecto está en `scripts/apache/iact-apache.conf`:

```apache
WSGIDaemonProcess iact \
    python-home=${VENV_DIR} \
    python-path=${DJANGO_DIR} \
    processes=2 \
    threads=4 \
    display-name=%{GROUP}
```

Esto crea **2 procesos Python** con **4 threads cada uno** = hasta 8 requests
concurrentes. Las conexiones Django (`connections['ivr']`) son **thread-local**
en mod_wsgi daemon mode — cada thread mantiene su propia conexión, independiente
de los otros threads del mismo proceso.

Nota: `requirements/production.txt` incluye también `gunicorn==21.2.0` como
alternativa viable, pero el despliegue documentado usa Apache + mod_wsgi.

### Gestión de conexiones en Django con mod_wsgi

Django **no tiene connection pooling nativo**. Con `CONN_MAX_AGE=0` (default):
- Cada request abre una conexión al primer `cursor()`
- La conexión se cierra al terminar el request
- Con Unix socket (misma VPS), abrir/cerrar es gratuito (~microsegundos)
- Con 2 procesos × 4 threads: máximo **8 conexiones simultáneas** a MariaDB

Con `CONN_MAX_AGE=N` segundos (no configurado actualmente):
- Django reutiliza la conexión durante N segundos por thread
- Con mod_wsgi daemon mode: los threads son persistentes → la conexión se
  reutiliza entre requests del mismo thread durante N segundos
- Seguro con Unix socket (misma máquina)
- Con TCP requiere que MariaDB `wait_timeout` > N para no cerrar la conexión idle
- Reduce la tasa de apertura de conexiones bajo carga sostenida

### Garantías que provee el Unix socket

- **Sin red**: el tráfico nunca sale de la máquina, no puede ser interceptado
- **Autenticación OS**: el socket verifica el UID del proceso que conecta
- **Latencia cero**: IPC en kernel, sin TCP handshake, sin DNS
- **Sin firewall**: no hay puerto expuesto

---

## Parte 3 — Qué cambia con servidores separados

### El único cambio de código: una variable de entorno

```bash
# Misma VPS (actual):
IVR_DB_SOCKET=/run/mysqld/mysqld.sock

# Servidores separados (TCP):
IVR_DB_SOCKET=              ← vacío → activa TCP
IVR_DB_HOST=10.0.1.15      ← IP privada del servidor MariaDB
IVR_DB_PORT=3306
```

Nada más cambia en el código Python. El ciclo de vida de la query es idéntico.

### Implicaciones en MariaDB al separar servidores

**`bind-address`** — por defecto MariaDB escucha solo en `127.0.0.1`:
```ini
# /etc/mysql/mariadb.conf.d/50-server.cnf en IACT-db
bind-address = 10.0.1.15   # IP de la interfaz de red interna
# O para escuchar en todas: bind-address = 0.0.0.0
# (controlar acceso con firewall, no con bind-address)
```

**Grants** — el provisioner ya crea `django_user@'%'`:
```sql
-- Verificado en la sesión anterior:
GRANT SELECT ON `ivr_legacy`.* TO `django_user`@`%`
GRANT EXECUTE ON PROCEDURE `ivr_legacy`.`sp_rpt_clientes` TO `django_user`@`%`
-- ... (17 routines × 2 hosts = 34 grants)
```
El `%` cubre cualquier IP remota. No se necesita cambiar los grants.

**Firewall en el servidor MariaDB:**
```bash
# Permitir solo el servidor Django (IP: 10.0.1.10)
ufw allow from 10.0.1.10 to any port 3306 proto tcp
ufw deny 3306
```

---

## Parte 4 — Opciones de despliegue

### Opción A — Misma VPS / Unix socket (ambiente actual)

```
┌──────────────────────────────────────────────┐
│  VPS Ubuntu 24.04                            │
│                                              │
│  ┌─────────────────┐  unix   ┌──────────┐   │
│  │  IACT-api        │◄───────►│  IACT-db │   │
│  │  Apache+mod_wsgi │ socket  │  MariaDB │   │
│  │  2 proc × 4 thr  │ .sock   │          │   │
│  └─────────────────┘         └──────────┘   │
│  ┌──────────────────────────┐               │
│  │  PostgreSQL              │               │
│  └──────────────────────────┘               │
└──────────────────────────────────────────────┘
```

**`.env`:**
```bash
IVR_DB_SOCKET=/run/mysqld/mysqld.sock
```

**Ventajas:** latencia cero, sin red, sin firewall entre servicios, setup mínimo.

**Desventajas:** recursos compartidos (RAM/CPU), un fallo de la VPS baja todo,
escalar uno requiere escalar la VPS completa.

**Cuándo usar:** pruebas, staging, proyectos con volumen bajo donde la
simplicidad operacional supera la resiliencia.

---

### Opción B — Servidores separados, red privada LAN/VPC (producción estándar)

```
┌──────────────────────┐        Red privada       ┌──────────────────────┐
│  Servidor A           │        10.0.0.0/24        │  Servidor B           │
│  Ubuntu 24.04         │                           │  Ubuntu 24.04         │
│                      │                           │                      │
│  IACT-api            │◄──────── TCP 3306 ───────►│  IACT-db             │
│  Django + mod_wsgi   │        (sin SSL)          │  MariaDB 10.11        │
│  PostgreSQL           │                           │  ivr_legacy           │
└──────────────────────┘                           └──────────────────────┘
```

**`.env` en Servidor A:**
```bash
IVR_DB_SOCKET=
IVR_DB_HOST=10.0.1.15
IVR_DB_PORT=3306
```

**`/etc/mysql/mariadb.conf.d/50-server.cnf` en Servidor B:**
```ini
bind-address = 10.0.1.15
```

**Ventajas:** recursos independientes, escalar Django sin tocar MariaDB,
latencia despreciable en la misma LAN (~0.1-1 ms).

**Desventajas:** requiere configurar firewall y `bind-address`, tráfico sin
cifrar dentro de la red privada (aceptable en VPC del mismo proveedor).

**Cuándo usar:** producción estándar en el mismo datacenter o en la misma
VPC de un proveedor cloud (AWS, GCP, Hetzner, DigitalOcean).

---

### Opción C — Servidores separados con TLS (red semi-pública o compliance)

Idéntica a B pero con cifrado mutual entre IACT-api y IACT-db.

**`.env` en Servidor A:**
```bash
IVR_DB_SOCKET=
IVR_DB_HOST=10.0.1.15
IVR_DB_PORT=3306
```

**`base.py` `OPTIONS` ampliado:**
```python
'OPTIONS': {
    'charset': 'utf8mb4',
    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
    # IVR_DB_SOCKET vacío → usa TCP
    # Sin ssl_ca aquí: agregar en .env o settings_production.py:
    'ssl': {
        'ca':   '/etc/ssl/mariadb/ca-cert.pem',   # CA que firmó el cert del server
        'cert': '/etc/ssl/mariadb/client-cert.pem', # cert del cliente Django
        'key':  '/etc/ssl/mariadb/client-key.pem',  # clave privada del cliente
    },
},
```

**MariaDB con TLS:**
```ini
# 50-server.cnf
ssl-ca   = /etc/mysql/ssl/ca-cert.pem
ssl-cert = /etc/mysql/ssl/server-cert.pem
ssl-key  = /etc/mysql/ssl/server-key.pem
require-secure-transport = ON
```

**Ventajas:** tráfico cifrado punto a punto, autenticación mutua con
certificados, requerido para PCI-DSS/HIPAA.

**Desventajas:** overhead de cifrado (5-10% CPU en handshake), gestión de
certificados (renovación anual con Let's Encrypt o CA interna).

**Cuándo usar:** cuando la red entre servidores no está garantizada como
privada, o cuando hay requisitos de compliance.

---

### Opción D — SSH Tunnel (desarrollo remoto o mantenimiento puntual)

No es arquitectura de producción. Es la forma de que un desarrollador
acceda desde su máquina local a la MariaDB remota.

```bash
# Abrir túnel: puerto local 3307 → puerto 3306 del servidor remoto
ssh -L 3307:localhost:3306 usuario@servidor-iact-db -N &

# .env local
IVR_DB_SOCKET=
IVR_DB_HOST=127.0.0.1
IVR_DB_PORT=3307
```

**Cuándo usar:** debugging, migraciones manuales, acceso con DBeaver o
la CLI de MariaDB desde la máquina del desarrollador.

---

### Opción E — ProxySQL como middleware (alta disponibilidad)

Añade un proxy entre Django y MariaDB para connection pooling, routing
y failover. Útil si el número de threads de Apache mod_wsgi supera el
`max_connections` de MariaDB o cuando se necesitan réplicas de lectura.

```
IACT-api                ProxySQL              MariaDB
Apache mod_wsgi          (mismo servidor       ┌─────────────┐
    │                    o servidor propio)    │  Primary    │
    └─── TCP 6033 ───►  ┌──────────┐ ────────►│  ivr_legacy │
                        │ ProxySQL │           └─────────────┘
                        │ pool 100 │ ────────►┌─────────────┐
                        └──────────┘          │  Replica    │
                                              └─────────────┘
```

**`.env` en IACT-api:**
```bash
IVR_DB_SOCKET=
IVR_DB_HOST=127.0.0.1    # ProxySQL en el mismo servidor que Django
IVR_DB_PORT=6033          # puerto estándar de ProxySQL
```

**Ventajas:**
- Pool de conexiones real (Django con `CONN_MAX_AGE=0` crea N conexiones
  para N workers; ProxySQL las multiplexa en un pool menor hacia MariaDB)
- Read/write splitting: queries hacia réplica, escrituras hacia primary
- Failover automático: si primary cae, ProxySQL promueve réplica
- Query mirroring: ejecutar en primary y réplica simultáneamente para pruebas

**Desventajas:**
- Componente adicional para operar y monitorear
- ProxySQL necesita conocer los SPs para rutearlos correctamente
- Añade ~0.1-0.5 ms de latencia por query
- Si ProxySQL cae, toda la integración cae

**Cuándo usar:** producción de alta disponibilidad con más de 50 workers
de mod_wsgi o cuando se necesita réplica de lectura para los reportes pesados.

---

## Parte 5 — Tabla de decisión: qué opción usar

| Criterio | Opción A | Opción B | Opción C | Opción D | Opción E |
|---|---|---|---|---|---|
| Mismo servidor | ✓ obligatorio | ✗ | ✗ | ✗ | ✗ |
| Red privada LAN/VPC | — | ✓ ideal | ✓ | — | ✓ |
| Cifrado TLS | no | no | ✓ | SSH cifra | no (ProxySQL↔MariaDB opcional) |
| Compliance PCI/HIPAA | no | no | ✓ | no | condicional |
| Connection pooling | no | no | no | no | ✓ |
| Alta disponibilidad | no | no | no | no | ✓ |
| Complejidad operacional | mínima | baja | media | nula | alta |
| Latencia | ~0 µs | ~0.1-1 ms | ~0.5-2 ms | variable | ~0.1-0.5 ms extra |
| Cuándo usar | pruebas / staging | producción estándar | compliance | dev remoto | HA / escala |

---

## Parte 6 — Resumen de variables de entorno por opción

| Variable | Opción A | Opción B | Opción C | Opción D | Opción E |
|---|---|---|---|---|---|
| `IVR_DB_SOCKET` | `/run/mysqld/mysqld.sock` | `""` | `""` | `""` | `""` |
| `IVR_DB_HOST` | `localhost` (ignorado) | IP privada MariaDB | IP privada MariaDB | `127.0.0.1` | `127.0.0.1` |
| `IVR_DB_PORT` | `3306` (ignorado) | `3306` | `3306` | `3307` (túnel) | `6033` (ProxySQL) |
| `IVR_DB_USER` | `django_user` | `django_user` | `django_user` | `django_user` | `django_user` |
| `IVR_DB_PASSWORD` | dev | fuerte | fuerte | fuerte | fuerte |
| SSL en OPTIONS | no | no | sí (`ssl: {ca, cert, key}`) | no | no |
| `IVR_QUERY_TIMEOUT_SEC` | `30` | `30` | `30` | `30` | `30` |
