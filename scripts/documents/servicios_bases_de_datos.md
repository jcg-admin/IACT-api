# Servicios de Bases de Datos — Inicio Manual

## Por que los servicios aparecen como NO activos

Este entorno (contenedor / sandbox) no tiene systemd como proceso 1.
Eso significa que los servicios no se autoinician al arrancar la maquina.
Cada sesion nueva, PostgreSQL y MariaDB comienzan detenidos hasta que
alguien los levanta manualmente.

El diagnostico de check_tools.sh es correcto cuando reporta WARN:
intenta conectarse por TCP a los puertos 5432 y 3306, y si el servicio
no esta corriendo el puerto no existe, la conexion falla.

```
# Estado real antes de iniciarlos:
pg_ctl: no server running
MariaDB is stopped.

# check_tools reporta:
WARN  PostgreSQL NO alcanzable en 127.0.0.1:5432
WARN  MariaDB NO alcanzable en 127.0.0.1:3306
```

No es un falso positivo — los servicios estaban efectivamente detenidos.

---

## Comandos de control

### PostgreSQL

```bash
# Iniciar
sudo pg_ctlcluster 16 main start

# Detener
sudo pg_ctlcluster 16 main stop

# Reiniciar
sudo pg_ctlcluster 16 main restart

# Ver estado
sudo pg_ctlcluster 16 main status
```

### MariaDB

```bash
# Iniciar
sudo service mariadb start

# Detener
sudo service mariadb stop

# Reiniciar
sudo service mariadb restart

# Ver estado
sudo service mariadb status
```

---

## Verificar que estan activos

```bash
# Opcion 1 — ver estado completo del entorno (recomendado):
bash scripts/provisioners/system/check_tools.sh

# Opcion 2 — estado directo de cada servicio:
sudo pg_ctlcluster 16 main status
sudo service mariadb status

# Opcion 3 — verificar que los puertos TCP responden:
pg_isready -h 127.0.0.1 -p 5432
mysqladmin -h 127.0.0.1 ping
```

Cuando ambos servicios estan activos, check_tools muestra:

```
SUCCESS  PostgreSQL alcanzable en 127.0.0.1:5432
SUCCESS  MariaDB alcanzable en 127.0.0.1:3306
OK: 59  Advertencias: 0  Errores: 0
```

---

## Flujo recomendado al inicio de cada sesion

```bash
# 1. Iniciar servicios
sudo pg_ctlcluster 16 main start
sudo service mariadb start

# 2. Verificar que todo esta OK
bash scripts/provisioners/system/check_tools.sh

# 3. Activar el entorno virtual Python
source venv/bin/activate
```

O en un solo paso, que hace todo lo anterior y ademas provisiona
si algo falta:

```bash
sudo bash scripts/bootstrap.sh
```

---

## Por que no se puede usar systemctl enable

En un servidor real con systemd activo, los servicios se habilitarian
para arrancar automaticamente con cada inicio del sistema:

```bash
# En servidor real con systemd (NO aplica aqui):
sudo systemctl enable postgresql
sudo systemctl enable mariadb
```

En este entorno el proceso 1 no es systemd sino el proceso del
contenedor, por lo que systemctl no esta disponible o no tiene efecto.
La alternativa es `service` (SysV init compatible), que si funciona
pero solo levanta el servicio para la sesion actual.

---

## Resumen

| Situacion                         | PostgreSQL        | MariaDB              |
|-----------------------------------|-------------------|----------------------|
| Al iniciar la maquina/sesion      | Detenido          | Detenido             |
| Despues de start manual           | Activo (PID xxxx) | Activo (Uptime: Xs)  |
| Con systemctl enable (servidor)   | Arranca solo      | Arranca solo         |
| Con systemctl enable (contenedor) | No aplica         | No aplica            |

---

## Ver también

- [relacion_con_iact_db.md](relacion_con_iact_db.md) — separación de responsabilidades entre IACT-api e IACT-db
