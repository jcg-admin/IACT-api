"""
integration_ivr.py — alias de fase0_testing para tests de integración.

Desde la migración de fase0_testing a BDs reales, ambos settings
son equivalentes. Este archivo existe para mantener la compatibilidad
con pytest.ini y scripts existentes.

Ref: H-INT-007 — eliminación de SQLite.
"""
from .fase0_testing import *  # noqa: F401, F403
