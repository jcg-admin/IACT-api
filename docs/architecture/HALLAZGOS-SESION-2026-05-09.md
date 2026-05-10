# Hallazgos IACT-api — Sesión 2026-05-09

**Fecha:** 2026-05-09 | **Estado:** 686 unit + 39 integration passed

## H-CFG-001 — skip-grant-tables producía DEFINER vacío

conftest.py arrancaba MariaDB con --skip-grant-tables.
Fix: modo normal + credenciales explícitas en ivr.py.

## H-CFG-002 — testing_local.py sobreescribía DATABASES completo

Perdía OPTIONS y CONN_MAX_AGE de base.py.
Fix: solo agregar TEST config, heredar todo de base.py.

## H-CFG-003 — PostgreSQL conectaba por TCP en lugar de socket

Causa: pg_hba.conf solo tenía peer (requiere usuario OS).
Fix: línea scram-sha-256 para django_user + DB_SOCKET en .env.

## H-CFG-004 — .env mezclaba secretos con decisiones

DEBUG, AWS variables, variables redundantes.
Fix: solo secretos y valores de instancia en .env.

## H-TEST-001 — ivr_schema solo tenía 3 de 7 SPs

4 SPs faltantes → endpoints retornaban 503.
Fix: 7 SPs completos en fixture.

## H-TEST-002 — Tests pre-existentes fallidos (no son nuestros)

tests/api/ → 404 en /api/v1/ (no existe)
tests/integration/users/ → module_id NULL
Plan v3.1.0 los resuelve.

## H-BENCH-001 — Resultados T-083

| Endpoint | Filas | Máx | Umbral |
|---|---|---|---|
| clientes | 3 | 1ms | 500ms |
| centros | 5215 | 88ms | 3000ms |
| centros-segmento | 84 | 500ms | 8000ms |

Todos dentro del umbral. No se requiere optimización.
