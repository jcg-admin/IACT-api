"""
apps/access/management/commands/create_functions.py

Catálogo canónico RBAC v5.4.0 — 61 funciones en 8 módulos.

Fuente: arquitectura-tecnica/rbac/modelo-rbac-iact.rst v5.4.0
CNST-033: nombres de función en inglés, formato MOD-NNN.
BR-006: RBAC flat NIST — sin jerarquía de roles.

Uso:
    python manage.py create_functions
    python manage.py create_functions --dry-run
    python manage.py create_functions --clear
"""
from django.core.management.base import BaseCommand
from django.db import transaction


# ---------------------------------------------------------------------------
# CATÁLOGO v5.4.0 — 61 funciones
# Formato: (code, name, module_code, description)
# code: MOD-NNN  (valida con validate_function_code)
# name: snake_case inglés (CNST-033)
# module_code: MOD_AUTH | MOD_USR | MOD_ACC | MOD_PIP | MOD_RPT | MOD_ALR | MOD_AUD | MOD_LOG
# ---------------------------------------------------------------------------

FUNCTIONS_V540 = [
    # =========================================
    # MOD_AUTH — 4 funciones
    # =========================================
    ('AUTH-001', 'view_own_sessions',       'MOD_AUTH', 'Ver sesiones propias activas (AUTH-001)'),
    ('AUTH-002', 'close_user_session',      'MOD_AUTH', 'Cerrar sesión de usuario (AUTH-002)'),
    ('AUTH-003', 'reset_password',          'MOD_AUTH', 'Generar contraseña temporal para usuario (AUTH-003)'),
    ('AUTH-004', 'view_all_active_sessions','MOD_AUTH', 'Ver todas las sesiones activas del sistema (AUTH-004)'),

    # =========================================
    # MOD_USR — 9 funciones
    # =========================================
    ('USR-001', 'create_users',    'MOD_USR', 'Crear nuevos usuarios (USR-001)'),
    ('USR-002', 'update_users',    'MOD_USR', 'Modificar datos de usuarios existentes (USR-002)'),
    ('USR-003', 'deactivate_users','MOD_USR', 'Dar de baja usuarios — baja lógica BR-009 (USR-003)'),
    ('USR-004', 'list_users',      'MOD_USR', 'Listar usuarios paginados (USR-004)'),
    ('USR-005', 'search_users',    'MOD_USR', 'Buscar usuarios con filtros (USR-005)'),
    ('USR-006', 'block_users',     'MOD_USR', 'Bloquear acceso de usuario (USR-006)'),
    ('USR-007', 'unblock_users',   'MOD_USR', 'Desbloquear usuario (USR-007)'),
    ('USR-008', 'reactivate_users','MOD_USR', 'Reactivar usuario inactivo (USR-008)'),
    ('USR-009', 'view_users',      'MOD_USR', 'Ver perfil y detalle de usuario (USR-009)'),

    # =========================================
    # MOD_ACC — 12 funciones
    # =========================================
    ('ACC-001', 'assign_functions',          'MOD_ACC', 'Asignar funciones RBAC a usuario (ACC-001)'),
    ('ACC-002', 'revoke_functions',          'MOD_ACC', 'Revocar funciones de usuario (ACC-002)'),
    ('ACC-003', 'view_assignments',          'MOD_ACC', 'Ver asignaciones y permisos efectivos (ACC-003)'),
    ('ACC-004', 'assign_function_groups',    'MOD_ACC', 'Asignar AccessGroup a usuario (ACC-004)'),
    ('ACC-005', 'view_separation_rules',     'MOD_ACC', 'Ver reglas SoD configuradas (ACC-005)'),
    ('ACC-006', 'create_function_group',     'MOD_ACC', 'Crear grupo de funciones custom (ACC-006)'),
    ('ACC-007', 'assign_functions_to_group', 'MOD_ACC', 'Asignar funciones a un grupo (ACC-007)'),
    ('ACC-008', 'grant_exceptional_permission','MOD_ACC','Conceder permiso excepcional temporal (ACC-008)'),
    ('ACC-009', 'revoke_exceptional_permission','MOD_ACC','Revocar permiso excepcional (ACC-009)'),
    ('ACC-010', 'revoke_function_group',     'MOD_ACC', 'Revocar AccessGroup de usuario (ACC-010)'),
    ('ACC-011', 'update_separation_rule',    'MOD_ACC', 'Actualizar parámetros de regla SoD (ACC-011)'),
    ('ACC-012', 'disable_separation_rule',   'MOD_ACC', 'Desactivar regla SoD temporalmente (ACC-012)'),

    # =========================================
    # MOD_PIP — 4 funciones
    # =========================================
    ('PIP-001', 'view_pipeline_status',   'MOD_PIP', 'Ver estado y métricas del pipeline ETL (PIP-001)'),
    ('PIP-002', 'view_pipeline_errors',   'MOD_PIP', 'Ver errores de ejecución del ETL (PIP-002)'),
    ('PIP-003', 'view_data_availability', 'MOD_PIP', 'Ver disponibilidad de datos por período (PIP-003)'),
    ('PIP-004', 'request_pipeline_retry', 'MOD_PIP', 'Solicitar reintento de pipeline fallido (PIP-004)'),

    # =========================================
    # MOD_RPT — 11 funciones
    # =========================================
    ('RPT-001', 'view_reports',           'MOD_RPT', 'Ver reportes del sistema IVR (RPT-001)'),
    ('RPT-002', 'view_dashboard',         'MOD_RPT', 'Ver dashboard ejecutivo con KPIs (RPT-002)'),
    ('RPT-003', 'filter_reports',         'MOD_RPT', 'Filtrar reportes por dimensiones (RPT-003)'),
    ('RPT-004', 'export_csv',             'MOD_RPT', 'Exportar reporte a CSV (RPT-004)'),
    ('RPT-005', 'export_excel',           'MOD_RPT', 'Exportar reporte a Excel (RPT-005)'),
    ('RPT-006', 'export_pdf',             'MOD_RPT', 'Exportar reporte a PDF (RPT-006)'),
    ('RPT-007', 'view_kpis',              'MOD_RPT', 'Ver KPIs operativos en dashboard (RPT-007)'),
    ('RPT-008', 'view_charts',            'MOD_RPT', 'Ver gráficos y visualizaciones (RPT-008)'),
    ('RPT-009', 'schedule_report',        'MOD_RPT', 'Programar ejecución periódica de reportes (RPT-009)'),
    ('RPT-010', 'save_view',              'MOD_RPT', 'Guardar configuración de vista de reporte (RPT-010)'),
    ('RPT-011', 'share_report',           'MOD_RPT', 'Compartir reporte con otros usuarios (RPT-011)'),
    # Prerequisito FASE 3 (2026-05-13): UC_RPT_02 requiere esta función.
    # No existía en el catálogo original — omitida en v5.4.0 inicial.
    # Hallazgo H-F3-PRE-005: RPT-002 estaba asignado a view_dashboard;
    # view_realtime_metrics se añade como función adicional sin código RPT-NNN
    # asignado porque los 11 slots RPT-001..011 están ocupados.
    # Se usa el código RPT-012 para mantener coherencia MOD-NNN.
    ('RPT-012', 'view_realtime_metrics',  'MOD_RPT', 'Ver métricas en tiempo real vía SSE (UC_RPT_02). Requiere infraestructura ASGI.'),

    # =========================================
    # MOD_ALR — 10 funciones
    # =========================================
    ('ALR-001', 'view_alerts',                   'MOD_ALR', 'Ver alertas activas del sistema (ALR-001)'),
    ('ALR-002', 'configure_alerts',              'MOD_ALR', 'Configurar umbrales de alerta (ALR-002)'),
    ('ALR-003', 'configure_team_alerts',         'MOD_ALR', 'Configurar alertas de equipo (ALR-003)'),
    ('ALR-004', 'pause_alerts',                  'MOD_ALR', 'Pausar alertas temporalmente (ALR-004)'),
    ('ALR-005', 'disable_alerts',                'MOD_ALR', 'Desactivar alertas — BR-009 toggle (ALR-005)'),
    ('ALR-006', 'view_alert_history',            'MOD_ALR', 'Ver historial de alertas disparadas (ALR-006)'),
    ('ALR-007', 'acknowledge_alert',             'MOD_ALR', 'Reconocer alerta — closed-loop (ALR-007)'),
    ('ALR-008', 'subscribe_to_alert',            'MOD_ALR', 'Suscribirse a alertas específicas (ALR-008)'),
    ('ALR-009', 'unsubscribe_from_alert',        'MOD_ALR', 'Cancelar suscripción a alertas (ALR-009)'),
    ('ALR-010', 'configure_subscription_severity','MOD_ALR','Configurar severidad de suscripción (ALR-010)'),

    # =========================================
    # MOD_AUD — 4 funciones
    # =========================================
    ('AUD-001', 'view_audit_log',            'MOD_AUD', 'Consultar log de auditoría (AUD-001)'),
    ('AUD-002', 'search_audit_log',          'MOD_AUD', 'Buscar en log de auditoría (AUD-002)'),
    ('AUD-003', 'export_audit_log',          'MOD_AUD', 'Exportar log de auditoría (AUD-003)'),
    ('AUD-004', 'generate_compliance_report','MOD_AUD', 'Generar reporte de compliance (AUD-004)'),

    # =========================================
    # MOD_LOG — 7 funciones
    # =========================================
    ('LOG-001', 'view_application_logs',   'MOD_LOG', 'Ver logs de aplicación Django (LOG-001)'),
    ('LOG-002', 'export_logs',             'MOD_LOG', 'Exportar logs del sistema (LOG-002)'),
    ('LOG-003', 'search_logs',             'MOD_LOG', 'Buscar en logs del sistema (LOG-003)'),
    ('LOG-004', 'view_etl_logs',           'MOD_LOG', 'Ver logs del pipeline ETL (LOG-004)'),
    ('LOG-005', 'view_infrastructure_logs','MOD_LOG', 'Ver logs de infraestructura (LOG-005)'),
    ('LOG-006', 'view_system_health',      'MOD_LOG', 'Ver estado de salud del sistema (LOG-006)'),
    ('LOG-007', 'view_technical_metrics',  'MOD_LOG', 'Ver métricas técnicas del sistema (LOG-007)'),
]

# Módulos del sistema — 8 módulos canónicos
MODULES_V540 = [
    ('MOD_AUTH', 'Autenticacion y Sesiones',         1),
    ('MOD_USR',  'Gestion de Identidades',           2),
    ('MOD_ACC',  'Control de Acceso RBAC',           3),
    ('MOD_PIP',  'Supervision ETL Pipeline',         4),
    ('MOD_RPT',  'Visualizacion y Reportes',         5),
    ('MOD_ALR',  'Alertas Operativas',               6),
    ('MOD_AUD',  'Auditoria',                        7),
    ('MOD_LOG',  'Bitacoras Tecnicas',               8),
]


class Command(BaseCommand):
    help = 'Carga el catálogo canónico RBAC v5.4.0 — 61 funciones en 8 módulos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Simular sin guardar en BD',
        )
        parser.add_argument(
            '--clear', action='store_true',
            help='Eliminar funciones y módulos existentes antes de crear',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        clear   = options['clear']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY-RUN: no se guardará nada'))

        if clear and not dry_run:
            self._clear()

        modules = self._ensure_modules(dry_run)
        created, updated = self._load_functions(modules, dry_run)
        self._print_summary(created, updated, dry_run)

    def _clear(self):
        from apps.access.models import Function, Module
        fn_count  = Function.objects.count()
        mod_count = Module.objects.count()
        Function.objects.all().delete()
        Module.objects.all().delete()
        self.stdout.write(self.style.WARNING(
            f'Eliminadas {fn_count} funciones y {mod_count} módulos'
        ))

    @transaction.atomic
    def _ensure_modules(self, dry_run: bool) -> dict:
        """
        Crea o actualiza los 8 módulos canónicos.
        Retorna dict {module_code: Module instance}.
        """
        from apps.access.models import Module
        modules = {}

        for code, name, order in MODULES_V540:
            if dry_run:
                self.stdout.write(f'  [DRY] módulo {code}: {name}')
                modules[code] = None
                continue

            mod, created = Module.objects.update_or_create(
                code=code,
                defaults={'name': name, 'order': order},
            )
            modules[code] = mod
            verb = 'Creado' if created else 'Actualizado'
            self.stdout.write(f'  [{verb}] módulo {code}')

        return modules

    @transaction.atomic
    def _load_functions(self, modules: dict, dry_run: bool) -> tuple[int, int]:
        """
        Carga las 61 funciones del catálogo v5.4.0.
        Usa Module FK correcto (no string).
        """
        from apps.access.models import Function

        created_count = updated_count = 0

        for code, name, module_code, description in FUNCTIONS_V540:
            if dry_run:
                exists = Function.objects.filter(code=code).exists()
                verb = 'actualizaría' if exists else 'crearía'
                self.stdout.write(f'  [DRY] {verb}: {code} ({name})')
                if exists:
                    updated_count += 1
                else:
                    created_count += 1
                continue

            module = modules[module_code]
            fn, created = Function.objects.update_or_create(
                code=code,
                defaults={
                    'name':        name,
                    'module':      module,
                    'description': description,
                    'is_active':   True,
                    'status':      'activo',
                },
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Creada: {code} ({name})'))
            else:
                updated_count += 1
                self.stdout.write(f'  Actualizada: {code} ({name})')

        return created_count, updated_count

    def _print_summary(self, created: int, updated: int, dry_run: bool):
        from apps.access.models import Function
        self.stdout.write('')
        self.stdout.write('=' * 60)
        if dry_run:
            self.stdout.write(self.style.WARNING('RESUMEN (DRY-RUN)'))
        else:
            self.stdout.write(self.style.SUCCESS('RESUMEN'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'  Creadas:     {created}')
        self.stdout.write(f'  Actualizadas:{updated}')
        if not dry_run:
            total = Function.objects.count()
            self.stdout.write(f'  Total en BD: {total} (esperado: 61)')
            if total != 61:
                self.stdout.write(self.style.ERROR(
                    f'ADVERTENCIA: se esperaban 61 funciones, hay {total}'
                ))
        self.stdout.write('=' * 60)
