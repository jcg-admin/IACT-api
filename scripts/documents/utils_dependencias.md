# Utils: Mapa de dependencias

## Dependencias entre modulos

```
logging.sh          (sin dependencias externas -- base de todo)
     ^
     | source
     |-- core.sh
     |       ^
     |       | source
     |   database.sh
     |       ^
     |       | source
     |   network.sh
     |
     +-- validation.sh
               source logging.sh
               source network.sh

provisioning.sh
     source logging.sh
     source core.sh
     source network.sh
     source validation.sh

system.sh
     source logging.sh
     source core.sh
     (standalone: puede ejecutarse directamente)
```

## Arbol de carga por script

```
bootstrap.sh
+-- utils/core.sh
+-- utils/logging.sh
+-- utils/network.sh
+-- utils/database.sh
+-- utils/validation.sh
+-- utils/provisioning.sh

check_tools.sh
+-- utils/logging.sh
+-- utils/core.sh
+-- utils/database.sh

provisioners/*/bootstrap.sh
+-- provisioning.sh
      +-- core.sh
      +-- logging.sh
      +-- network.sh
      +-- validation.sh
```

## Funciones por modulo

### logging.sh

| Funcion              | Descripcion                              |
|----------------------|------------------------------------------|
| init_log(name)       | Inicializa archivo de log                |
| log_debug/info       | Imprime con color y timestamp            |
| log_success          | Nivel success (verde)                    |
| log_warn             | Nivel advertencia (amarillo)             |
| log_error            | Nivel error (rojo)                       |
| log_fatal            | Nivel fatal (rojo, sale del script)      |
| log_header(title)    | Seccion con separador                    |
| log_separator(w, c)  | Linea separadora de ancho w con char c   |
| start_timer()        | Guarda timestamp inicial                 |
| show_elapsed()       | Retorna tiempo transcurrido              |
| step_header(app,desc)| Banner de inicio de script               |

### core.sh

| Funcion                  | Descripcion                              |
|--------------------------|------------------------------------------|
| command_exists(cmd)      | Verifica si comando existe               |
| require_command(cmd)     | Idem con log_error si falta             |
| is_package_installed(p)  | dpkg -l check                           |
| is_service_active(svc)   | systemctl con fallback a service status  |
| start_service(svc)       | service start (sin systemctl requerido)  |
| enable_service(svc)      | systemctl enable con fallback update-rc.d|
| exists_file(path)        | [ -f path ]                              |
| exists_dir(path)         | [ -d path ]                              |

### database.sh

| Funcion                    | Descripcion                              |
|----------------------------|------------------------------------------|
| tcp_is_reachable(h,p,t)    | timeout t bash /dev/tcp/h/p             |
| can_reach_port(h,p,t)      | alias de tcp_is_reachable               |
| mysql_wait_ready(h,p,u)    | Loop mysqladmin ping hasta ready         |
| postgres_wait_ready(h,p,u) | Loop pg_isready hasta ready              |
| mysql_exec(sql,h,p,u,pw)   | Ejecuta SQL en MariaDB                   |
| psql_exec(sql,h,p,u,pw)    | Ejecuta SQL en PostgreSQL                |

### network.sh

| Funcion                 | Descripcion                                      |
|-------------------------|--------------------------------------------------|
| is_port_listening(port) | ss -tlnp (iproute2, no netstat)                 |
| find_process_on_port(p) | ss -tlnp con grep pid                           |
| wait_for_port(h,p,t)    | Loop TCP hasta que puerto responda               |

### validation.sh

| Funcion                 | Descripcion                          |
|-------------------------|--------------------------------------|
| validate_file_exists(f) | Error si archivo no existe           |
| validate_dir_exists(d)  | Error si directorio no existe        |
| validate_var_set(var)   | Error si variable vacia              |
| require_vars(v1 v2...)  | Valida multiples variables de una vez|

### provisioning.sh

| Funcion               | Descripcion                                    |
|-----------------------|------------------------------------------------|
| init_env()            | Detecta PROJECT_ROOT via git rev-parse         |
| load_utils()          | Carga todos los utils desde scripts/utils/     |
| run_step(name, fn)    | Ejecuta paso con log y manejo de error         |
| run_all(steps[])      | Orquesta lista de pasos                        |
| show_results()        | Resumen OK/WARN/ERROR al final                 |
| show_connection_info()| Muestra datos de conexion de la DB             |
| mark_done(key)        | Crea marker de idempotencia en .iact/          |
| is_done(key)          | Verifica si el step ya fue ejecutado           |

### system.sh

| Funcion                | Descripcion                                   |
|------------------------|-----------------------------------------------|
| configure_timezone(tz) | timedatectl con fallback a /etc/timezone      |
| set_hostname(name)     | hostnamectl con fallback a hostname cmd       |
| install_packages(p...) | apt-get install con retry                     |
| update_apt_cache()     | apt-get update -qq                            |

## Compatibilidad sin systemd

El entorno es Ubuntu 24.04 en contenedor sin systemd.
Cada funcion con systemctl tiene fallback automatico:

```
is_service_active(svc)
    if systemctl is-active --quiet svc  --> OK
    else service svc status             --> fallback

enable_service(svc)
    if systemctl enable svc             --> OK
    else update-rc.d svc defaults       --> fallback

configure_timezone(tz)
    if timedatectl set-timezone tz      --> OK
    else echo tz > /etc/timezone        --> fallback
```
