"""
Management command para crear modulos iniciales del sistema IACT.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Crea los modulos iniciales del sistema IACT'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Muestra informacion detallada durante la creacion',
        )

    def handle(self, *args, **options):
        from apps.access.models import Module

        verbose = options['verbose']

        self.stdout.write('Inicializando modulos del sistema IACT...')
        self.stdout.write('=' * 80)

        modules_data = [
            {
                'code': 'MOD_REPORTES',
                'name': 'Reportes',
                'description': 'Modulo principal de reportes del sistema',
                'parent_code': None,
                'order': 1,
                'url_path': '/reportes',
                'children': [
                    {
                        'code': 'MOD_REPORTES_DIARIO',
                        'name': 'Reporte Diario',
                        'description': 'Reporte de actividad diaria',
                        'order': 1,
                        'url_path': '/reportes/diario',
                    },
                    {
                        'code': 'MOD_REPORTES_ACUMULADO',
                        'name': 'Reporte Acumulado',
                        'description': 'Reporte acumulado de periodo',
                        'order': 2,
                        'url_path': '/reportes/acumulado',
                    },
                ],
            },
            {
                'code': 'MOD_ONBOARDING',
                'name': 'OnBoarding',
                'description': 'Modulo de onboarding de asesores',
                'parent_code': None,
                'order': 2,
                'url_path': '/onboarding',
                'children': [
                    {
                        'code': 'MOD_ONBOARDING_MATRIZ',
                        'name': 'Matriz de Asesores',
                        'description': 'Matriz de desempeno de asesores',
                        'order': 1,
                        'url_path': '/onboarding/matriz-asesores',
                    },
                ],
            },
        ]

        created_count = 0

        for parent_data in modules_data:
            children = parent_data.pop('children', [])
            parent_data.pop('parent_code', None)

            parent, created = Module.objects.get_or_create(
                code=parent_data['code'],
                defaults={**parent_data, 'is_active': True},
            )
            if created:
                created_count += 1
                if verbose:
                    self.stdout.write(
                        self.style.SUCCESS(f'Creado: {parent.code} - {parent.name}')
                    )

            for child_data in children:
                child, created = Module.objects.get_or_create(
                    code=child_data['code'],
                    defaults={**child_data, 'parent': parent, 'is_active': True},
                )
                if created:
                    created_count += 1
                    if verbose:
                        self.stdout.write(
                            self.style.SUCCESS(f'  Creado: {child.code} - {child.name}')
                        )

        self.stdout.write('')
        self.stdout.write('=' * 80)
        self.stdout.write(f'Total modulos creados: {created_count}')
        self.stdout.write(self.style.SUCCESS('Inicializacion completada'))
