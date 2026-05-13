"""
apps/access/management/commands/create_access_groups.py

Los 10 AccessGroups predefinidos del catálogo RBAC v5.4.0.

Fuente: arquitectura-tecnica/rbac/modelo-rbac-iact.rst v5.4.0
Prerequisito: python manage.py create_functions (módulos + funciones v5.4.0)

Uso:
    python manage.py create_access_groups
    python manage.py create_access_groups --dry-run
"""
from django.core.management.base import BaseCommand
from django.db import transaction


# Definición de AGRs: (code, name, function_codes)
# function_codes: lista de códigos canónicos MOD-NNN
ACCESS_GROUPS_V540 = [
    (
        'AGR-001', 'basic_operator_group',
        [
            'AUTH-001', 'AUTH-004',   # view_own_sessions, view_all_active_sessions
            'RPT-001', 'RPT-002',     # view_reports, view_dashboard
            'RPT-007', 'RPT-008',     # view_kpis, view_charts
        ],
        'Operador básico — solo visualización de KPIs y dashboard.',
    ),
    (
        'AGR-002', 'report_viewer_group',
        [
            # Todas de AGR-001 +
            'AUTH-001', 'AUTH-004',
            'RPT-001', 'RPT-002', 'RPT-007', 'RPT-008',
            # Adicionales:
            'RPT-003', 'USR-009',   # filter_reports, view_users
        ],
        'Analista — puede filtrar reportes pero no exportar.',
    ),
    (
        'AGR-003', 'quality_supervisor_group',
        [
            # Todas de AGR-002 +
            'AUTH-001', 'AUTH-004',
            'RPT-001', 'RPT-002', 'RPT-007', 'RPT-008', 'RPT-003', 'USR-009',
            # Adicionales:
            'ALR-001', 'ALR-002', 'ALR-006',   # view/configure/history alerts
        ],
        'Supervisor de calidad — análisis completo + alertas.',
    ),
    (
        'AGR-004', 'data_exporter_group',
        [
            # Todas de AGR-003 +
            'AUTH-001', 'AUTH-004',
            'RPT-001', 'RPT-002', 'RPT-007', 'RPT-008', 'RPT-003', 'USR-009',
            'ALR-001', 'ALR-002', 'ALR-006',
            # Adicionales:
            'RPT-004', 'RPT-005', 'RPT-006',   # export_csv, export_excel, export_pdf
            'RPT-009', 'RPT-010', 'RPT-011',   # schedule, save_view, share_report
        ],
        'Analista de datos — exportación autorizada.',
    ),
    (
        'AGR-005', 'alert_manager_group',
        [
            'ALR-001', 'ALR-002', 'ALR-003', 'ALR-004', 'ALR-005', 'ALR-006',
            # view, configure, configure_team, pause, disable, history
        ],
        'Gestor de alertas — gestión completa.',
    ),
    (
        'AGR-006', 'user_admin_group',
        [
            'USR-001', 'USR-002', 'USR-003', 'USR-004', 'USR-005',
            'USR-006', 'USR-007', 'USR-008', 'USR-009',
            # create, update, deactivate, list, search, block, unblock, reactivate, view
        ],
        'Administrador de usuarios — gestión completa de identidades. SoD: sin AUD.',
    ),
    (
        'AGR-007', 'permission_admin_group',
        [
            'ACC-001', 'ACC-002', 'ACC-003', 'ACC-004', 'ACC-005',
            # assign, revoke, view_assignments, assign_groups, view_sod_rules
        ],
        'Administrador de permisos — gestión RBAC. SoD: sin AUD.',
    ),
    (
        'AGR-008', 'auditor_group',
        [
            'AUD-001', 'AUD-002', 'AUD-003', 'AUD-004',
            # view, search, export, compliance_report
        ],
        'Auditor — solo auditoría y compliance. SoD CRÍTICA: sin AGR-006/007/009.',
    ),
    (
        'AGR-009', 'pipeline_admin_group',
        [
            'PIP-001', 'PIP-002', 'PIP-003', 'PIP-004',
            # view_status, view_errors, view_availability, request_retry
        ],
        'Administrador de pipeline — supervisión ETL. SoD: sin AUD.',
    ),
    (
        'AGR-010', 'system_admin_group',
        [
            'AUTH-002', 'AUTH-003', 'AUTH-004',
            'USR-001', 'USR-002', 'USR-006',
            # close_session, reset_password, view_all_sessions, create_users, update_users, block_users
        ],
        'Sysadmin — administración del sistema.',
    ),
]


class Command(BaseCommand):
    help = 'Carga los 10 AccessGroups predefinidos del catálogo RBAC v5.4.0'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--clear', action='store_true')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        clear   = options['clear']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY-RUN: no se guardará nada'))

        if clear and not dry_run:
            from apps.access.models import AccessGroup
            count = AccessGroup.objects.count()
            AccessGroup.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Eliminados {count} AccessGroups'))

        created, updated = self._load_groups(dry_run)
        self._print_summary(created, updated, dry_run)

    @transaction.atomic
    def _load_groups(self, dry_run: bool) -> tuple[int, int]:
        from apps.access.models import AccessGroup, Function

        created_count = updated_count = 0

        for code, name, fn_codes, description in ACCESS_GROUPS_V540:
            if dry_run:
                fn_count = Function.objects.filter(code__in=fn_codes).count()
                self.stdout.write(
                    f'  [DRY] {code} {name}: {fn_count}/{len(fn_codes)} funciones encontradas'
                )
                continue

            agr, created = AccessGroup.objects.update_or_create(
                code=code,
                defaults={'name': name, 'description': description},
            )

            # Asignar funciones
            functions = Function.objects.filter(code__in=fn_codes, is_active=True)
            agr.functions.set(functions)
            actual = agr.functions.count()

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f'  Creado: {code} {name} — {actual}/{len(fn_codes)} funciones'
                ))
            else:
                updated_count += 1
                self.stdout.write(
                    f'  Actualizado: {code} {name} — {actual}/{len(fn_codes)} funciones'
                )

            if actual != len(fn_codes):
                self.stdout.write(self.style.WARNING(
                    f'    ADVERTENCIA: {len(fn_codes) - actual} funciones no encontradas. '
                    f'Ejecutar create_functions primero.'
                ))

        return created_count, updated_count

    def _print_summary(self, created: int, updated: int, dry_run: bool):
        from apps.access.models import AccessGroup
        self.stdout.write('')
        self.stdout.write('=' * 60)
        prefix = 'DRY-RUN — ' if dry_run else ''
        self.stdout.write(f'{prefix}Creados: {created}  Actualizados: {updated}')
        if not dry_run:
            total = AccessGroup.objects.count()
            self.stdout.write(f'Total en BD: {total} (esperado: 10)')
        self.stdout.write('=' * 60)
