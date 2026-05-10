"""
config/settings_local.py

Settings para ejecucion local en desarrollo.

Las bases de datos (PostgreSQL + MariaDB) son gestionadas por IACT-db.
Este archivo asume que IACT-db ya tiene los servicios corriendo.

Ver: IACT-db/docs/architecture/SEPARACION-IACT-API.md
Ver: IACT-db/docs/getting-started/QUICKSTART.md
"""
from .settings.development import *
