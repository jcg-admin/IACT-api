"""
IMPORTANTE, ESTE MODULO DEBE DE IR DENTRO DE IVR O PIPELINE
Script para crear Functions de MOD_Calls.

FASE A.2 - DT-002
Basado en ANÁLISIS apps/access/ v3.0.0

MOD_Calls (5 funciones):
  - CALL_VIEW: Ver llamadas
  - CALL_EDIT: Editar llamadas
  - CALL_DELETE: Eliminar llamadas
  - CALL_EXP_CSV: Exportar llamadas
  - CALL_STATS: Estadísticas llamadas
"""

from django.core.management.base import BaseCommand
from apps.access.models import Function, Module


class Command(BaseCommand):
    help = 'Crear Functions para MOD_Calls (FASE A.2 - DT-002)'

    def handle(self, *args, **options):
        self.stdout.write('=' * 70)
        self.stdout.write('FASE A.2: Crear Functions MOD_Calls')
        self.stdout.write('=' * 70)

        # 1. Obtener o crear MOD_Calls
        mod_calls, created = Module.objects.get_or_create(
            code='MOD_Calls',
            defaults={
                'name': 'Llamadas',
                'description': 'Módulo de gestión de llamadas y registros',
                'icon': 'phone',
                'url_path': '/calls',
                'order': 5,
                'is_active': True,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Módulo creado: {mod_calls.code}'))
        else:
            self.stdout.write(f'Módulo existente: {mod_calls.code}')

        # 2. Definir functions
        functions_data = [
            {
                'code': 'CALL_VIEW',
                'name': 'Ver Llamadas',
                'description': 'Permiso para ver registros de llamadas',
            },
            {
                'code': 'CALL_EDIT',
                'name': 'Editar Llamadas',
                'description': 'Permiso para crear y editar registros de llamadas',
            },
            {
                'code': 'CALL_DELETE',
                'name': 'Eliminar Llamadas',
                'description': 'Permiso para eliminar registros de llamadas',
            },
            {
                'code': 'CALL_EXP_CSV',
                'name': 'Exportar Llamadas CSV',
                'description': 'Permiso para exportar registros de llamadas a CSV',
            },
            {
                'code': 'CALL_STATS',
                'name': 'Estadísticas de Llamadas',
                'description': 'Permiso para ver estadísticas de llamadas',
            },
        ]

        # 3. Crear functions
        created_count = 0
        existing_count = 0

        for func_data in functions_data:
            function, created = Function.objects.get_or_create(
                code=func_data['code'],
                defaults={
                    'name': func_data['name'],
                    'description': func_data['description'],
                    'module': mod_calls,
                    'is_active': True,
                }
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'{function.code}: {function.name}'))
            else:
                existing_count += 1
                self.stdout.write(f'{function.code}: Ya existe')

        # 4. Resumen
        self.stdout.write('')
        self.stdout.write('=' * 70)
        self.stdout.write('RESUMEN:')
        self.stdout.write(f'  Módulo: {mod_calls.code}')
        self.stdout.write(f'  Functions creadas: {created_count}')
        self.stdout.write(f'  Functions existentes: {existing_count}')
        self.stdout.write(f'  Total: {created_count + existing_count}')
        self.stdout.write('=' * 70)

        if created_count > 0:
            self.stdout.write(self.style.SUCCESS('Functions creadas exitosamente'))
        else:
            self.stdout.write('Todas las functions ya existían')
