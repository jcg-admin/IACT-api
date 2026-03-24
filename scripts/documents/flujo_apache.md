# Apache + mod_wsgi — Setup para Ubuntu 24.04 LTS

Despliega el proyecto Django (IACT Call Center) bajo Apache con mod_wsgi
en Ubuntu 24.04 Noble sin depender de `apt-get` ni resolución de hostname.

---

## Qué hace el usuario (pasos)

```bash
# 1. Clonar el repositorio
git clone <repo-url> && cd IACT-api

# 2. Instalar Apache y mod_wsgi (solo la primera vez)
sudo bash scripts/apache/install_apache_deb.sh

# 3. Configurar el sitio y crear el symlink (idempotente, re-ejecutable)
sudo bash scripts/apache/setup_apache.sh

# 4. Verificar que todo está correcto
bash scripts/apache/check_apache.sh
```

> Los pasos 2 y 3 son idempotentes: se pueden ejecutar varias veces
> sin efectos adversos.

---

## Arquitectura de archivos

```
IACT-api/
└── scripts/apache/
    ├── iact-apache.conf      ← en git | valores de desarrollo (Define)
    ├── install_apache_deb.sh ← descarga e instala .deb sin apt-get
    ├── setup_apache.sh       ← crea symlink, directorios, collectstatic
    └── check_apache.sh       ← verifica el estado de todo el stack

/etc/apache2/
├── sites-available/
│   └── iact.conf  →  (symlink) /home/user/IACT-api/scripts/apache/iact-apache.conf
└── sites-enabled/
    └── iact.conf  →  (symlink creado por a2ensite) ../sites-available/iact.conf
```

El archivo de configuración **vive en el repositorio** (`iact-apache.conf`).
Apache lo referencia mediante un symlink, por lo que cualquier cambio al
archivo en el repo se refleja inmediatamente sin re-ejecutar el setup
(solo requiere `sudo apache2ctl graceful`).

---

## Paso 1 — install_apache_deb.sh

Descarga los `.deb` necesarios directamente desde `archive.ubuntu.com`
usando `wget` (evita los problemas de DNS de `sudo apt-get`) y los instala
con `dpkg`. Luego compila `mod_wsgi` desde el código fuente contra el
Python del virtualenv del proyecto.

### Paquetes instalados

| Paquete                        | Versión (Noble)      | Descripción                       |
|-------------------------------|----------------------|-----------------------------------|
| `libapr1t64`                  | 1.7.2-3.1build2      | Apache Portable Runtime           |
| `libaprutil1t64`              | 1.6.3-1.1ubuntu7     | APR utility library               |
| `libaprutil1-dbd-sqlite3`     | 1.6.3-1.1ubuntu7     | Backend SQLite para APR           |
| `libaprutil1-ldap`            | 1.6.3-1.1ubuntu7     | Backend LDAP para APR             |
| `liblua5.4-0`                 | 5.4.6-3build2        | Requerido por apache2-bin         |
| `apache2-data`                | 2.4.58-1ubuntu8.11   | Archivos de datos comunes         |
| `apache2-utils`               | 2.4.58-1ubuntu8.11   | Herramientas (htpasswd, ab, etc.) |
| `apache2-bin`                 | 2.4.58-1ubuntu8.11   | Binario principal de Apache       |
| `apache2`                     | 2.4.58-1ubuntu8.11   | Meta-paquete                      |
| `apache2-dev`                 | 2.4.58-1ubuntu8.11   | Headers + apxs2 (para compilar)   |
| `mod_wsgi` (fuente PyPI)      | 5.0.2                | Compilado contra el venv Python   |

### Dónde quedan los archivos

```
/usr/lib/apache2/modules/mod_wsgi-py3XX.cpython-3XX-x86_64-linux-gnu.so
/etc/apache2/mods-available/wsgi.load   ← apunta al .so anterior
/etc/apache2/mods-available/wsgi.conf   ← declara WSGIPythonHome
```

---

## Paso 2 — setup_apache.sh

### Qué hace (5 pasos internos)

```
setup_apache.sh
     |
     v
+----------------------------------------------------------+
|  PASO 1/5 -- Prerequisitos                  BLOQUEANTE  |
|                                                          |
|  · Verifica que se ejecuta como root                    |
|  · Comprueba que apache2 está instalado                 |
|  · Comprueba que mod_wsgi está activo (a2enmod)         |
|  · Verifica manage.py, wsgi.py, venv, iact-apache.conf  |
+----------------------------------------------------------+
     |
     v
+----------------------------------------------------------+
|  PASO 2/5 -- VirtualHost + symlink          IDEMPOTENTE |
|                                                          |
|  · Si el symlink ya apunta al archivo correcto → skip   |
|  · Si apunta a otro lado o es un archivo real → reemplaza|
|  · a2dissite 000-default  →  a2ensite iact.conf         |
|  · a2enmod headers                                      |
|  · apache2ctl configtest  (falla si hay error)          |
+----------------------------------------------------------+
     |
     v
+----------------------------------------------------------+
|  PASO 3/5 -- Directorios static/media/logs  IDEMPOTENTE |
|                                                          |
|  · Crea /var/www/iact/static  si no existe              |
|  · Crea /var/www/iact/media   si no existe              |
|  · Crea /var/log/apache2      si no existe              |
|  · chown www-data, chmod 755 en static y media          |
+----------------------------------------------------------+
     |
     v
+----------------------------------------------------------+
|  PASO 4/5 -- collectstatic                              |
|                                                          |
|  · python manage.py collectstatic --noinput             |
|  · DJANGO_SETTINGS_MODULE=config.settings.production    |
+----------------------------------------------------------+
     |
     v
+----------------------------------------------------------+
|  PASO 5/5 -- Iniciar / recargar Apache      IDEMPOTENTE |
|                                                          |
|  · Si ya corre  → graceful restart                      |
|  · Si no corre  → start                                 |
|  · Compatible con systemd, SysV (service) y contenedores|
+----------------------------------------------------------+
```

---

## Paso 3 — check_apache.sh

Verifica el estado del stack completo. No requiere `sudo`.

| Sección | Qué comprueba |
|---------|--------------|
| 1. Apache | Instalado, activo, `configtest` OK |
| 2. mod_wsgi | Módulo habilitado (`apache2ctl -M`) |
| 3. Config IACT | Symlink en sites-available y sites-enabled |
| 4. Archivos del proyecto | `manage.py`, `wsgi.py`, `production.py`, venv |
| 5. Static / media | Directorios existen, propietario `www-data`, archivos > 0 |
| 6. Django check | `manage.py check --deploy` sin errores |
| 7. Conectividad | `curl http://localhost/` responde 200/301/302 |

---

## Configuración del VirtualHost (iact-apache.conf)

Los valores del servidor se definen en un bloque `Define` al inicio del
archivo. Cada línea lleva el comentario `# TEMPLATE` para indicar que
debe revisarse al cambiar de entorno.

```apache
# TEMPLATE: ruta raíz del repositorio clonado
Define PROJECT_ROOT    /home/user/IACT-api

# TEMPLATE: directorio del proyecto Django
Define DJANGO_DIR      /home/user/IACT-api/callcentersite

# TEMPLATE: virtualenv del proyecto
Define VENV_DIR        /home/user/IACT-api/venv
...
```

Para aplicar un cambio de rutas:
1. Editar los `Define` en `scripts/apache/iact-apache.conf`
2. `sudo apache2ctl graceful` — no requiere re-ejecutar `setup_apache.sh`

---

## Idempotencia

| Situación | Comportamiento |
|-----------|---------------|
| Apache ya instalado | Se detecta y se salta la instalación |
| Symlink ya correcto | No se toca |
| Symlink apunta a otro lugar | Se reemplaza |
| Directorios ya existen | Se deja, solo se ajustan permisos |
| Apache ya corriendo | `graceful restart` en lugar de `start` |
| Sin systemd (contenedor) | Usa `service` o `apache2ctl` como fallback |

---

## Solución de problemas frecuentes

**`sudo: unable to resolve host (none)`**
Solo es un aviso del hostname del contenedor. No afecta la ejecución.

**`apt-get` falla con DNS pero `wget` funciona**
Usar `install_apache_deb.sh` que descarga los `.deb` directamente con `wget`.

**mod_wsgi compilado para Python X pero el venv usa Python Y**
El script compila `mod_wsgi` contra `$VENV_DIR/bin/python`. Verifica que
el venv exista antes de ejecutar `install_apache_deb.sh`.

**`apache2ctl configtest` falla tras editar iact-apache.conf**
Revisar la sintaxis de los bloques `<Directory>` y que todas las rutas
de los `Define` existen en el servidor.

**Cambios en el conf no se reflejan**
Ejecutar `sudo apache2ctl graceful` para recargar sin cortar conexiones.
