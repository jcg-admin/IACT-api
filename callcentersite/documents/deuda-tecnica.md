# Deuda Técnica — IACT Call Center

**Última actualización:** 2026-05-07

---

## Pendientes

| # | Archivo | Descripción | Severidad | Impacto |
|---|---|---|---|---|
| — | — | Sin deuda técnica pendiente. | — | — |

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
| 8 | `config/wsgi.py` | `os.environ.setdefault` apuntaba a `config.settings.development`. Corregido a `config.settings.production`. | 2026-05-07 |
| 9 | `tests/fixtures/ivr.py` (nuevo) + `tests/conftest.py` | Fixtures de integración IVR implementados. `ivr_schema` crea `job_execution_log`, `base_ivr_detalle`, `base_ivr_clientes` via SQL directo en MariaDB. `ivr_job_execution_data` e `ivr_quarter_data` siembran datos de prueba. Tests marcados con `@pytest.mark.django_db(databases=["default", "ivr"])` funcionan sin mocks. | 2026-05-07 |
