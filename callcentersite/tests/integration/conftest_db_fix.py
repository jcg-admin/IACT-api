"""
conftest_db_fix.py — Fixture de sesión para resolver migraciones con conflictos
en la BD de integración (iact_analytics tiene columnas añadidas manualmente
que la migración 0007 intenta añadir nuevamente).

Usar con: pytest --co tests/integration/ (no se importa directamente, es un helper)
"""
