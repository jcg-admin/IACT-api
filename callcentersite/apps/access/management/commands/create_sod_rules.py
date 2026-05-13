"""
apps/access/management/commands/create_sod_rules.py

Las 3 reglas SoD predefinidas del catálogo RBAC v5.4.0.

Fuente: arquitectura-tecnica/rbac/modelo-rbac-iact.rst v5.4.0
BR-007: SoD obligatorio en asignación de funciones.
Prerequisito: python manage.py create_functions

Uso:
    python manage.py create_sod_rules
    python manage.py create_sod_rules --dry-run
"""
from django.core.management.base import BaseCommand
from django.db import transaction


SOD_RULES_V540 = [
    (
        'SOD-001',
        'pipeline_audit_separation',
        'Un usuario NO puede tener funciones de Pipeline Y de Auditoría. '
        'Evita que quien opera el ETL audite sus propias acciones.',
        # Set A — Pipeline
        ['PIP-001', 'PIP-002', 'PIP-003', 'PIP-004'],
        # Set B — Auditoría
        ['AUD-001', 'AUD-002', 'AUD-003', 'AUD-004'],
    ),
    (
        'SOD-002',
        'user_management_audit_separation',
        'Un usuario NO puede tener funciones de gestión de Usuarios Y de Auditoría. '
        'Evita que quien administra usuarios audite sus propias acciones.',
        # Set A — Users
        ['USR-001', 'USR-002', 'USR-003', 'USR-004', 'USR-005',
         'USR-006', 'USR-007', 'USR-008', 'USR-009'],
        # Set B — Auditoría
        ['AUD-001', 'AUD-002', 'AUD-003', 'AUD-004'],
    ),
    (
        'SOD-003',
        'access_management_audit_separation',
        'Un usuario NO puede tener funciones de gestión de Acceso Y de Auditoría. '
        'Evita que quien administra RBAC audite sus propias acciones.',
        # Set A — Access
        ['ACC-001', 'ACC-002', 'ACC-003', 'ACC-004', 'ACC-005',
         'ACC-006', 'ACC-007', 'ACC-008', 'ACC-009', 'ACC-010',
         'ACC-011', 'ACC-012'],
        # Set B — Auditoría
        ['AUD-001', 'AUD-002', 'AUD-003', 'AUD-004'],
    ),
]


class Command(BaseCommand):
    help = 'Carga las 3 reglas SoD predefinidas del catálogo RBAC v5.4.0'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY-RUN: no se guardará nada'))

        created, updated = self._load_rules(dry_run)
        self._print_summary(created, updated, dry_run)

    @transaction.atomic
    def _load_rules(self, dry_run: bool) -> tuple[int, int]:
        from apps.access.models import SeparationRule, Function

        created_count = updated_count = 0

        for code, name, description, set_a_codes, set_b_codes in SOD_RULES_V540:
            if dry_run:
                a_count = Function.objects.filter(code__in=set_a_codes).count()
                b_count = Function.objects.filter(code__in=set_b_codes).count()
                self.stdout.write(
                    f'  [DRY] {code} {name}: '
                    f'set_a={a_count}/{len(set_a_codes)} '
                    f'set_b={b_count}/{len(set_b_codes)}'
                )
                continue

            rule, created = SeparationRule.objects.update_or_create(
                code=code,
                defaults={'name': name, 'description': description, 'state': 'ENABLED'},
            )

            fns_a = Function.objects.filter(code__in=set_a_codes, is_active=True)
            fns_b = Function.objects.filter(code__in=set_b_codes, is_active=True)
            rule.functions_set_a.set(fns_a)
            rule.functions_set_b.set(fns_b)

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f'  Creada: {code} — '
                    f'set_a={fns_a.count()}, set_b={fns_b.count()}'
                ))
            else:
                updated_count += 1
                self.stdout.write(
                    f'  Actualizada: {code} — '
                    f'set_a={fns_a.count()}, set_b={fns_b.count()}'
                )

        return created_count, updated_count

    def _print_summary(self, created: int, updated: int, dry_run: bool):
        from apps.access.models import SeparationRule
        self.stdout.write('')
        self.stdout.write('=' * 60)
        if not dry_run:
            total = SeparationRule.objects.filter(state='ENABLED').count()
            self.stdout.write(f'Creadas: {created}  Actualizadas: {updated}  Total: {total}')
        else:
            self.stdout.write(f'DRY-RUN — Crearía: {created}  Actualizaría: {updated}')
        self.stdout.write('=' * 60)
