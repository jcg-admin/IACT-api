"""
Management command: create_modules
Creates the default module hierarchy for the IACT navigation system.

Usage:
    python manage.py create_modules
    python manage.py create_modules --verbose
    python manage.py create_modules --reset
"""
from django.core.management.base import BaseCommand, CommandError


DEFAULT_MODULES = [
    {
        'name': 'Reportes',
        'code': 'REPORTS',
        'icon': 'icons/menu/reports.svg',
        'order': 1,
        'children': [
            {
                'name': 'Reporte Diario',
                'code': 'REPORTS_DAILY',
                'icon': 'icons/submenu/report_daily.svg',
                'order': 1,
            },
            {
                'name': 'Reporte Acumulado',
                'code': 'REPORTS_CUMULATIVE',
                'icon': 'icons/submenu/report_cumulative.svg',
                'order': 2,
            },
        ],
    },
    {
        'name': 'OnBoarding',
        'code': 'ONBOARDING',
        'icon': 'icons/menu/onboarding.svg',
        'order': 2,
        'children': [
            {
                'name': 'Matriz de Asesores',
                'code': 'ONBOARDING_MATRIX',
                'icon': 'icons/submenu/advisor_matrix.svg',
                'order': 1,
            },
        ],
    },
    {
        'name': 'Usuarios',
        'code': 'USERS',
        'icon': 'icons/menu/users.svg',
        'order': 3,
        'children': [],
    },
    {
        'name': 'Auditoria',
        'code': 'AUDIT',
        'icon': 'icons/menu/audit.svg',
        'order': 4,
        'children': [],
    },
    {
        'name': 'Alertas',
        'code': 'ALERTS',
        'icon': 'icons/menu/alerts.svg',
        'order': 5,
        'children': [],
    },
    {
        'name': 'Dashboard',
        'code': 'DASHBOARD',
        'icon': 'icons/menu/dashboard.svg',
        'order': 6,
        'children': [],
    },
]


class Command(BaseCommand):
    help = 'Creates the default module hierarchy for the IACT navigation system.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each module created.',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete all existing modules before creating (USE WITH CAUTION).',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        reset = options['reset']

        try:
            from apps.access.models import Module
        except ImportError:
            raise CommandError(
                "Cannot import apps.access.models.Module. "
                "Make sure the 'access' app is installed and migrated."
            )

        if reset:
            count, _ = Module.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'[WARN] Deleted {count} existing modules.'))

        created_count = 0
        updated_count = 0

        for module_data in DEFAULT_MODULES:
            children = module_data.pop('children', [])

            parent, created = Module.objects.get_or_create(
                code=module_data['code'],
                defaults={
                    'name': module_data['name'],
                    'icon': module_data.get('icon', ''),
                    'order': module_data.get('order', 0),
                    'parent': None,
                },
            )

            if created:
                created_count += 1
                if verbose:
                    self.stdout.write(
                        self.style.SUCCESS(f'[SUCCESS] Created module: {parent.name} ({parent.code})')
                    )
            else:
                updated_count += 1
                if verbose:
                    self.stdout.write(f'[INFO] Module already exists: {parent.name} ({parent.code})')

            for child_data in children:
                child, child_created = Module.objects.get_or_create(
                    code=child_data['code'],
                    defaults={
                        'name': child_data['name'],
                        'icon': child_data.get('icon', ''),
                        'order': child_data.get('order', 0),
                        'parent': parent,
                    },
                )
                if child_created:
                    created_count += 1
                    if verbose:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  [SUCCESS] Created sub-module: {child.name} ({child.code})'
                            )
                        )
                else:
                    updated_count += 1
                    if verbose:
                        self.stdout.write(
                            f'  [INFO] Sub-module already exists: {child.name} ({child.code})'
                        )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'[SUCCESS] Done. Created: {created_count}, Already existed: {updated_count}.'
        ))
