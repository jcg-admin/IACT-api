"""
Migration 0006 — FASE 0: Funciones SQL canónicas PostgreSQL.

Crea las 5 funciones PL/pgSQL definidas en ADR-BACK-006 § 2.3.
Estas funciones son el "single source of truth" para verificación
de permisos (ADR-BACK-006: el ORM nunca implementa lógica de auth).

Funciones creadas:
  1. user_has_function(user_id, function_code) → BOOLEAN
  2. get_user_functions(user_id) → VARCHAR[]
  3. get_user_groups(user_id) → JSONB
  4. check_function_and_audit(user_id, function_code) → BOOLEAN
  5. get_user_menu(user_id) → JSONB  (CNST-032: obligatoria)

Solo se ejecutan en PostgreSQL (vendor check).
SQLite (testing local) las omite silenciosamente.

Fuente: ADR-BACK-006 § 2.3, CNST-032, CNST-010.
"""
from django.db import migrations, connection


def create_sql_functions(apps, schema_editor):
    """Crea las 5 funciones canónicas solo en PostgreSQL."""
    if schema_editor.connection.vendor != 'postgresql':
        # SQLite u otro motor: omitir silenciosamente
        return

    sql_functions = [
        # ============================================================
        # 1. user_has_function — verificación booleana O(log n)
        # ADR-BACK-006: punto de entrada principal para autenticación.
        # UC_PERM_07: PermissionService.check() lo llama por cada miss de cache.
        # ============================================================
        """
        CREATE OR REPLACE FUNCTION user_has_function(
            p_user_id       INTEGER,
            p_function_code VARCHAR(50)
        )
        RETURNS BOOLEAN
        LANGUAGE plpgsql
        STABLE
        SECURITY DEFINER
        AS $$
        DECLARE
            v_has BOOLEAN := FALSE;
        BEGIN
            -- 1. Revocación excepcional activa → DENEGADO (P-50 precedencia)
            IF EXISTS (
                SELECT 1
                FROM   access_exceptional_permission ep
                JOIN   access_function fn ON fn.id = ep.function_id
                WHERE  ep.user_id   = p_user_id
                AND    fn.code      = p_function_code
                AND    ep.status    = 'revoked'
                AND    (ep.valid_until IS NULL OR ep.valid_until > NOW())
            ) THEN
                RETURN FALSE;
            END IF;

            -- 2. Concesión excepcional activa → AUTORIZADO (P-50)
            IF EXISTS (
                SELECT 1
                FROM   access_exceptional_permission ep
                JOIN   access_function fn ON fn.id = ep.function_id
                WHERE  ep.user_id   = p_user_id
                AND    fn.code      = p_function_code
                AND    ep.status    = 'approved'
                AND    ep.valid_from <= NOW()
                AND    (ep.valid_until IS NULL OR ep.valid_until > NOW())
            ) THEN
                RETURN TRUE;
            END IF;

            -- 3. Asignación directa ACTIVE no expirada (UserFunctionAssignment)
            IF EXISTS (
                SELECT 1
                FROM   access_user_function_assignment ufa
                JOIN   access_function fn ON fn.id = ufa.function_id
                WHERE  ufa.user_id  = p_user_id
                AND    fn.code      = p_function_code
                AND    ufa.state    = 'ACTIVE'
                AND    (ufa.expires_at IS NULL OR ufa.expires_at > NOW())
            ) THEN
                RETURN TRUE;
            END IF;

            -- 4. Via AccessGroup activo
            IF EXISTS (
                SELECT 1
                FROM   access_user_group uag
                JOIN   access_group ag       ON ag.id  = uag.access_group_id
                JOIN   access_group_functions agf ON agf.accessgroup_id = ag.id
                JOIN   access_function fn    ON fn.id  = agf.function_id
                WHERE  uag.user_id = p_user_id
                AND    fn.code     = p_function_code
                AND    ag.is_active = TRUE
                AND    fn.is_active = TRUE
            ) THEN
                RETURN TRUE;
            END IF;

            RETURN FALSE;
        END;
        $$;
        """,

        # ============================================================
        # 2. get_user_functions — array de códigos efectivos
        # UC_ACC_03: usada para construir la vista consolidada de permisos.
        # ============================================================
        """
        CREATE OR REPLACE FUNCTION get_user_functions(
            p_user_id INTEGER
        )
        RETURNS VARCHAR[]
        LANGUAGE plpgsql
        STABLE
        SECURITY DEFINER
        AS $$
        DECLARE
            v_codes VARCHAR[];
        BEGIN
            SELECT ARRAY(
                SELECT DISTINCT fn.code
                FROM access_function fn
                WHERE fn.is_active = TRUE
                AND (
                    -- Via UserFunctionAssignment ACTIVE
                    EXISTS (
                        SELECT 1 FROM access_user_function_assignment ufa
                        WHERE ufa.user_id    = p_user_id
                        AND   ufa.function_id = fn.id
                        AND   ufa.state      = 'ACTIVE'
                        AND   (ufa.expires_at IS NULL OR ufa.expires_at > NOW())
                    )
                    OR
                    -- Via AccessGroup activo
                    EXISTS (
                        SELECT 1
                        FROM access_user_group uag
                        JOIN access_group ag  ON ag.id  = uag.access_group_id
                        JOIN access_group_functions agf ON agf.accessgroup_id = ag.id
                        WHERE uag.user_id   = p_user_id
                        AND   agf.function_id = fn.id
                        AND   ag.is_active  = TRUE
                    )
                )
                -- Excluir revocaciones excepcionales activas
                AND NOT EXISTS (
                    SELECT 1 FROM access_exceptional_permission ep
                    WHERE ep.user_id    = p_user_id
                    AND   ep.function_id = fn.id
                    AND   ep.status     = 'revoked'
                    AND   (ep.valid_until IS NULL OR ep.valid_until > NOW())
                )
                ORDER BY fn.code
            ) INTO v_codes;

            RETURN COALESCE(v_codes, ARRAY[]::VARCHAR[]);
        END;
        $$;
        """,

        # ============================================================
        # 3. get_user_groups — JSONB de grupos del usuario
        # ============================================================
        """
        CREATE OR REPLACE FUNCTION get_user_groups(
            p_user_id INTEGER
        )
        RETURNS JSONB
        LANGUAGE plpgsql
        STABLE
        SECURITY DEFINER
        AS $$
        DECLARE
            v_result JSONB;
        BEGIN
            SELECT COALESCE(
                jsonb_agg(jsonb_build_object(
                    'code',        ag.code,
                    'name',        ag.name,
                    'granted_at',  uag.granted_at
                ) ORDER BY ag.code),
                '[]'::JSONB
            )
            INTO v_result
            FROM access_user_group uag
            JOIN access_group ag ON ag.id = uag.access_group_id
            WHERE uag.user_id  = p_user_id
            AND   ag.is_active = TRUE;

            RETURN v_result;
        END;
        $$;
        """,

        # ============================================================
        # 4. check_function_and_audit — atómico: check + write audit
        # ADR-BACK-006 § 2.3: sin race condition entre check y audit.
        # CNST-025: audit inmutable.
        # ============================================================
        """
        CREATE OR REPLACE FUNCTION check_function_and_audit(
            p_user_id       INTEGER,
            p_function_code VARCHAR(50)
        )
        RETURNS BOOLEAN
        LANGUAGE plpgsql
        VOLATILE
        SECURITY DEFINER
        AS $$
        DECLARE
            v_has    BOOLEAN;
            v_result VARCHAR(10);
        BEGIN
            v_has    := user_has_function(p_user_id, p_function_code);
            v_result := CASE WHEN v_has THEN 'SUCCESS' ELSE 'FAILURE' END;

            INSERT INTO audit_logs (
                user_id, action, resource, result, timestamp, details
            ) VALUES (
                p_user_id,
                'FUNCTION_CHECK',
                'Function:' || p_function_code,
                v_result,
                NOW(),
                jsonb_build_object(
                    'function_code', p_function_code,
                    'allowed',       v_has
                )
            );

            RETURN v_has;
        END;
        $$;
        """,

        # ============================================================
        # 5. get_user_menu — menú dinámico (CNST-032: obligatoria)
        # UC_PERM_08: NavigationMenuAssembler la llama al login.
        # ============================================================
        """
        CREATE OR REPLACE FUNCTION get_user_menu(
            p_user_id INTEGER
        )
        RETURNS JSONB
        LANGUAGE plpgsql
        STABLE
        SECURITY DEFINER
        AS $$
        DECLARE
            v_codes  VARCHAR[];
            v_result JSONB;
        BEGIN
            v_codes := get_user_functions(p_user_id);

            SELECT COALESCE(
                jsonb_build_object(
                    'user_id', p_user_id,
                    'modules', jsonb_agg(jsonb_build_object(
                        'code',   m.code,
                        'name',   m.name,
                        'order',  m.order,
                        'functions', (
                            SELECT jsonb_agg(jsonb_build_object(
                                'code',  fn.code,
                                'name',  fn.name
                            ) ORDER BY fn.name)
                            FROM access_function fn
                            WHERE fn.module_id = m.id
                            AND   fn.code = ANY(v_codes)
                            AND   fn.is_active = TRUE
                        )
                    ) ORDER BY m.order)
                ),
                jsonb_build_object('user_id', p_user_id, 'modules', '[]'::jsonb)
            )
            INTO v_result
            FROM access_module m
            WHERE m.is_active = TRUE
            AND EXISTS (
                SELECT 1 FROM access_function fn
                WHERE fn.module_id = m.id
                AND   fn.code      = ANY(v_codes)
                AND   fn.is_active = TRUE
            );

            RETURN COALESCE(v_result, jsonb_build_object(
                'user_id', p_user_id, 'modules', '[]'::jsonb
            ));
        END;
        $$;
        """,
    ]

    for sql in sql_functions:
        schema_editor.execute(sql)


def drop_sql_functions(apps, schema_editor):
    """Reversa: eliminar las funciones SQL."""
    if schema_editor.connection.vendor != 'postgresql':
        return

    for fn_name in [
        'get_user_menu',
        'check_function_and_audit',
        'get_user_groups',
        'get_user_functions',
        'user_has_function',
    ]:
        schema_editor.execute(f'DROP FUNCTION IF EXISTS {fn_name} CASCADE;')


class Migration(migrations.Migration):

    dependencies = [
        ('access', '0005_fase0_schema_canonico'),
    ]

    operations = [
        migrations.RunPython(
            create_sql_functions,
            reverse_code=drop_sql_functions,
        ),
    ]
