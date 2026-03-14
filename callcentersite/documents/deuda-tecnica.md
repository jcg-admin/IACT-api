# Deuda Técnica — IACT Call Center

**Última actualización:** 2026-03-14

---

## Pendientes

| # | Archivo | Descripción | Severidad | Impacto |
|---|---|---|---|---|
| 1 | `config/wsgi.py` | `os.environ.setdefault` apunta a `config.settings.development`. En producción requiere que Apache/mod_wsgi exporte `DJANGO_SETTINGS_MODULE=config.settings.production` manualmente. Si no se configura, producción corre con `DEBUG=True`. | BAJO | Riesgo operativo si el deployment no setea la variable de entorno |
| 2 | `tests/conftest.py` + `apps/ivr/` | Tests de consumo IVR pendientes. `test_ivr_legacy` (MariaDB) se crea vacío porque `CallLog` tiene `managed=False`. Falta: (1) fixture `django_db_setup` que cree la tabla `call_logs` vía SQL directo, (2) `CallLogFactory` para sembrar datos, (3) tests de integración reales con `@pytest.mark.django_db(databases=['ivr'])`. Hasta entonces los tests IVR usan mocks. | MEDIO | Sin tests de integración reales para consumo de datos IVR |

---

## Resueltos

| # | Archivo | Descripción | Fecha |
|---|---|---|---|
| 1 | `config/database_router.py` | Router activo con `app_label='ivr_legacy'` incorrecto (debía ser `'ivr'`) y alias `'ivr_production'` inexistente. Eliminado y reemplazado por `db_router.DatabaseRouter`. | 2026-03-14 |
| 2 | `config/settings/development.py` | `CACHES` con `LocMemCache` violaba CNST-010. Removido. | 2026-03-14 |
| 3 | `config/settings/production.py` | `CACHES` con `LocMemCache` violaba CNST-010. Removido. | 2026-03-14 |
