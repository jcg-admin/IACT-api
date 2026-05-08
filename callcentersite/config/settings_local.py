"""
config/settings_local.py

Settings para ejecucion local en desarrollo.
Usa PostgreSQL real y MariaDB real — no SQLite.

Las credenciales leen del .env (python-decouple).
Override solo cuando sea necesario para experimentacion local.
"""
from .settings.development import *
