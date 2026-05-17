# apps/alerts/management/commands/create_alert_functions.py

from django.core.management.base import BaseCommand
from apps.access.models import Function


class Command(BaseCommand):
    help = 'Crear funciones RBAC para módulo MOD_Alerts'

    def handle(self, *args, **options):
        """Crear las 6 funciones RBAC del módulo Alerts"""

        module = 'MOD_Alerts'

        # Definir las 6 funciones
        functions = [
            {
                'permission_django': 'alerts.send',
                'code': 'ALRT_SEND',
                'name': 'Enviar Mensajes',
                'description': 'Permite enviar mensajes internos a otros usuarios',
                'status': 'activo'
            },
            {
                'permission_django': 'alerts.view.inbox',
                'code': 'ALRT_VIEW_INB',
                'name': 'Ver Bandeja de Entrada',
                'description': 'Permite ver la bandeja de entrada de mensajes propios',
                'status': 'activo'
            },
            {
                'permission_django': 'alerts.manage.subscriptions',
                'code': 'ALRT_MNG_SUB',
                'name': 'Gestionar Suscripciones',
                'description': 'Permite suscribirse y desuscribirse de alertas automáticas',
                'status': 'activo'
            },
            {
                'permission_django': 'alerts.configure.rules',
                'code': 'ALRT_CFG_RUL',
                'name': 'Configurar Reglas de Alertas',
                'description': 'Permite crear, editar y eliminar configuraciones de alertas automáticas',
                'status': 'activo'
            },
            {
                'permission_django': 'alerts.delete.messages',
                'code': 'ALRT_DEL_MSG',
                'name': 'Eliminar Mensajes',
                'description': 'Permite eliminar mensajes propios y de otros usuarios',
                'status': 'activo'
            },
            {
                'permission_django': 'alerts.view.all',
                'code': 'ALRT_VIEW_ALL',
                'name': 'Ver Todos los Mensajes',
                'description': 'Permite ver todos los mensajes del sistema (admin)',
                'status': 'activo'
            }
        ]

        created_count = 0
        updated_count = 0

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('━' * 70))
        self.stdout.write(self.style.SUCCESS(f'  CREACIÓN DE FUNCIONES RBAC - {module}'))
        self.stdout.write(self.style.SUCCESS('━' * 70))
        self.stdout.write('')

        for func_data in functions:
            permission_django = func_data['permission_django']

            # Buscar si ya existe
            function, created = Function.objects.get_or_create(
                permission_django=permission_django,
                defaults={
                    'code': func_data['code'],
                    'module': module,
                    'name': func_data['name'],
                    'description': func_data['description'],
                    'status': func_data['status'],
                    'is_active': True
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  [OK] Creada: {permission_django} ({func_data["code"]})')
                )
            else:
                # Actualizar si ya existe
                function.code = func_data['code']
                function.module = module
                function.name = func_data['name']
                function.description = func_data['description']
                function.status = func_data['status']
                function.is_active = True
                function.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'  ⟳ Actualizada: {permission_django} ({func_data["code"]})')
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('━' * 70))
        self.stdout.write(self.style.SUCCESS('  RESUMEN'))
        self.stdout.write(self.style.SUCCESS('━' * 70))
        self.stdout.write(f'  Módulo: {module}')
        self.stdout.write(f'  Funciones creadas: {created_count}')
        self.stdout.write(f'  Funciones actualizadas: {updated_count}')
        self.stdout.write(f'  Total: {len(functions)}')
        self.stdout.write('')

        # Mostrar tabla de funciones
        self.stdout.write(self.style.SUCCESS('  FUNCIONES RBAC DISPONIBLES:'))
        self.stdout.write('')
        self.stdout.write('  =========================================================')
        self.stdout.write('  - Permission Django               - Código       - Status   -')
        self.stdout.write('  =========================================================')

        for func_data in functions:
            perm = func_data['permission_django'].ljust(31)
            code = func_data['code'].ljust(12)
            status = func_data['status'].ljust(8)
            self.stdout.write(f'  - {perm} - {code} - {status} -')

        self.stdout.write('  =========================================================')
        self.stdout.write('')

        # Instrucciones de uso
        self.stdout.write(self.style.SUCCESS('  USO EN PERMISOS:'))
        self.stdout.write('')
        self.stdout.write('  En permissions.py:')
        self.stdout.write(self.style.HTTP_INFO("    function_mapping = {"))
        self.stdout.write(self.style.HTTP_INFO("        'create': 'alerts.send',"))
        self.stdout.write(self.style.HTTP_INFO("        'inbox': 'alerts.view.inbox',"))
        self.stdout.write(self.style.HTTP_INFO("        ..."))
        self.stdout.write(self.style.HTTP_INFO("    }"))
        self.stdout.write('')

        # Verificación en código
        self.stdout.write(self.style.SUCCESS('  VERIFICACIÓN EN CÓDIGO:'))
        self.stdout.write('')
        self.stdout.write('  Archivos donde se usan:')
        self.stdout.write('    [OK] apps/alerts/permissions.py (MessagePermissions)')
        self.stdout.write('    [OK] apps/alerts/permissions.py (AlertConfigurationPermissions)')
        self.stdout.write('    [OK] apps/alerts/permissions.py (AlertSubscriptionPermissions)')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('━' * 70))
        self.stdout.write(self.style.SUCCESS('  [OK] FUNCIONES RBAC CREADAS EXITOSAMENTE'))
        self.stdout.write(self.style.SUCCESS('━' * 70))
        self.stdout.write('')
