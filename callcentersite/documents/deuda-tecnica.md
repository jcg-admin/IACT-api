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
| 4 | `tests/unit/authentication/test_views.py` | Tests obsoletos para endpoint JWT (`authentication:token_obtain_pair`) que ya no existe. El sistema usa DRF Token via `AuthViewSet`. Reescritos para cubrir todos los flujos del endpoint `POST /api/v1/auth/login/` (exitoso, credenciales invalidas, cuenta bloqueada, usuario inactivo, campos vacios, first_login). | 2026-03-15 |
| 5 | `tests/integration/authentication/test_auth_flow.py` | Status codes incorrectos: `test_login_with_invalid_credentials` y `test_login_with_nonexistent_user` esperaban HTTP 400, pero `InvalidCredentialsError` retorna HTTP 401. Corregidos a 401. Tambien corregido `test_account_lockout_after_5_failed_attempts` (400 → 401 para los primeros 4 intentos). | 2026-03-15 |
| 6 | `tests/unit/authentication/test_services.py` | Faltaban tests para `AccountLockedError`, `UserInactiveError`, `first_login=True` y `first_login=False` en `AuthenticationService.login_user`. Agregados 4 tests nuevos. | 2026-03-15 |
| 7 | `config/settings/base.py` + `tests/conftest.py` | `DEFAULT_AUTHENTICATION_CLASSES` usaba `JWTAuthentication` pero el `AuthViewSet.login` retorna DRF Token. `TokenAuthentication` no estaba configurado. Corregido: reemplazado `JWTAuthentication` por `TokenAuthentication`. `conftest.py` actualizados fixtures `authenticated_client`, `admin_client` y `authenticated_client_with_rbac` de JWT Bearer a DRF Token. | 2026-03-15 |
