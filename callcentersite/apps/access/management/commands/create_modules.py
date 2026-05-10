"""
Management command para inicializar módulos del sistema.

Uso:
    python manage.py create_modules
    python manage.py create_modules --dry-run
    python manage.py create_modules --clear
"""
from django.core.management.base import BaseCommand
from apps.access.models import Module


class Command(BaseCommand):
    help = 'Inicializa módulos del sistema IACT'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular creación sin guardar',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Eliminar módulos existentes antes de crear',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        clear = options['clear']

        self.stdout.write('='*80)
        self.stdout.write('INICIALIZACION DE MODULOS IACT')
        self.stdout.write('='*80)

        if dry_run:
            self.stdout.write(self.style.NOTICE('\nModo DRY-RUN (no se guardaran cambios)\n'))

        if clear and not dry_run:
            self.stdout.write(self.style.WARNING('\nEliminando modulos existentes...'))
            deleted = Module.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Eliminados: {deleted[0]} modulos\n'))

        # Definir estructura de módulos del sistema IACT
        # Basado en: docs/MODULOS_CASOS_USO.md
        modules = [
            # =================================================================
            # MODULOS RAIZ (Nivel 1)
            # =================================================================
            
            # Dashboard
            {
                'code': 'MOD_Dashboard',
                'name': 'Dashboard',
                'description': 'Panel principal del sistema',
                'parent_code': None,
                'order': 1,
                'icon': None,
                'url_path': '/dashboard',
            },
            
            # Centers
            {
                'code': 'MOD_Centers',
                'name': 'Centros',
                'description': 'Gestion de centros de atencion',
                'parent_code': None,
                'order': 3,
                'icon': None,
                'url_path': '/centers',
            },
            
            # Services
            {
                'code': 'MOD_Services',
                'name': 'Servicios',
                'description': 'Gestion de servicios 800',
                'parent_code': None,
                'order': 4,
                'icon': None,
                'url_path': '/services',
            },
            
            # Users
            {
                'code': 'MOD_Users',
                'name': 'Usuarios',
                'description': 'Gestion de usuarios del sistema',
                'parent_code': None,
                'order': 5,
                'icon': None,
                'url_path': '/users',
            },
            
            # Reports
            {
                'code': 'MOD_Reports',
                'name': 'Reportes',
                'description': 'Generacion y gestion de reportes',
                'parent_code': None,
                'order': 6,
                'icon': None,
                'url_path': '/reports',
            },
            
            # Audit
            {
                'code': 'MOD_Audit',
                'name': 'Auditoria',
                'description': 'Auditoria de acciones del sistema',
                'parent_code': None,
                'order': 7,
                'icon': None,
                'url_path': '/audit',
            },
            
            # Access
            {
                'code': 'MOD_Access',
                'name': 'Control Acceso',
                'description': 'Gestion de modulos y funciones',
                'parent_code': None,
                'order': 8,
                'icon': None,
                'url_path': '/access',
            },
            
            # Pipeline
            {
                'code': 'MOD_Pipeline',
                'name': 'Estado del Pipeline',
                'description': 'Pipeline ETL de datos',
                'parent_code': None,
                'order': 9,
                'icon': None,
                'url_path': '/pipeline',
            },
            
            # Settings
            {
                'code': 'MOD_Settings',
                'name': 'Configuracion',
                'description': 'Configuracion del sistema',
                'parent_code': None,
                'order': 10,
                'icon': None,
                'url_path': '/settings',
            },
            
            # IVR (NUEVO - Modelo Granular)
            {
                'code': 'MOD_IVR',
                'name': 'IVR - Logs Legacy',
                'description': 'Acceso a logs de llamadas legacy (READ-ONLY)',
                'parent_code': None,
                'status': 'activo',
                'order': 11,
                'icon': None,
                'url_path': '/ivr',
            },
            
            # =================================================================
            # SUBMODULOS CENTERS (Nivel 2)
            # =================================================================
            
            {
                'code': 'MOD_Centers_View',
                'name': 'Ver Centros',
                'description': 'Visualizar centros',
                'parent_code': 'MOD_Centers',
                'order': 1,
                'icon': None,
                'url_path': '/centers/view',
            },
            {
                'code': 'MOD_Centers_Create',
                'name': 'Crear Centro',
                'description': 'Crear centros',
                'parent_code': 'MOD_Centers',
                'order': 2,
                'icon': None,
                'url_path': '/centers/create',
            },
            {
                'code': 'MOD_Centers_Edit',
                'name': 'Editar Centro',
                'description': 'Editar centros',
                'parent_code': 'MOD_Centers',
                'order': 3,
                'icon': None,
                'url_path': '/centers/edit',
            },
            {
                'code': 'MOD_Centers_Delete',
                'name': 'Eliminar Centro',
                'description': 'Eliminar centros (soft delete)',
                'parent_code': 'MOD_Centers',
                'order': 4,
                'icon': None,
                'url_path': '/centers/delete',
            },
            
            # =================================================================
            # SUBMODULOS SERVICES (Nivel 2)
            # =================================================================
            
            {
                'code': 'MOD_Services_View',
                'name': 'Ver Servicios',
                'description': 'Visualizar servicios',
                'parent_code': 'MOD_Services',
                'order': 1,
                'icon': None,
                'url_path': '/services/view',
            },
            {
                'code': 'MOD_Services_Create',
                'name': 'Crear Servicio',
                'description': 'Crear servicios',
                'parent_code': 'MOD_Services',
                'order': 2,
                'icon': None,
                'url_path': '/services/create',
            },
            {
                'code': 'MOD_Services_Edit',
                'name': 'Editar Servicio',
                'description': 'Editar servicios',
                'parent_code': 'MOD_Services',
                'order': 3,
                'icon': None,
                'url_path': '/services/edit',
            },
            {
                'code': 'MOD_Services_Assign',
                'name': 'Asignar Servicio',
                'description': 'Asignar servicios a usuarios',
                'parent_code': 'MOD_Services',
                'order': 4,
                'icon': None,
                'url_path': '/services/assign',
            },
            
            # =================================================================
            # SUBMODULOS USERS (Nivel 2)
            # =================================================================
            
            {
                'code': 'MOD_Users_View',
                'name': 'Ver Usuarios',
                'description': 'Visualizar usuarios',
                'parent_code': 'MOD_Users',
                'order': 1,
                'icon': None,
                'url_path': '/users/view',
            },
            {
                'code': 'MOD_Users_Create',
                'name': 'Crear Usuario',
                'description': 'Crear usuarios',
                'parent_code': 'MOD_Users',
                'order': 2,
                'icon': None,
                'url_path': '/users/create',
            },
            {
                'code': 'MOD_Users_Edit',
                'name': 'Editar Usuario',
                'description': 'Editar usuarios',
                'parent_code': 'MOD_Users',
                'order': 3,
                'icon': None,
                'url_path': '/users/edit',
            },
            {
                'code': 'MOD_Users_Delete',
                'name': 'Eliminar Usuario',
                'description': 'Eliminar usuarios (soft delete)',
                'parent_code': 'MOD_Users',
                'order': 4,
                'icon': None,
                'url_path': '/users/delete',
            },
            {
                'code': 'MOD_Users_Permissions',
                'name': 'Permisos Usuario',
                'description': 'Gestionar permisos de usuarios',
                'parent_code': 'MOD_Users',
                'order': 5,
                'icon': None,
                'url_path': '/users/permissions',
            },
            
            # =================================================================
            # SUBMODULOS REPORTS (Nivel 2)
            # =================================================================
            
            {
                'code': 'MOD_Reports_View',
                'name': 'Ver Reportes',
                'description': 'Visualizar reportes',
                'parent_code': 'MOD_Reports',
                'order': 1,
                'icon': None,
                'url_path': '/reports/view',
            },
            {
                'code': 'MOD_Reports_Create',
                'name': 'Crear Reporte',
                'description': 'Crear reportes',
                'parent_code': 'MOD_Reports',
                'order': 2,
                'icon': None,
                'url_path': '/reports/create',
            },
            {
                'code': 'MOD_Reports_Export',
                'name': 'Exportar Reporte',
                'description': 'Exportar reportes (PDF, Excel, CSV)',
                'parent_code': 'MOD_Reports',
                'order': 3,
                'icon': None,
                'url_path': '/reports/export',
            },
            {
                'code': 'MOD_Reports_Schedule',
                'name': 'Programar Reporte',
                'description': 'Programar reportes automaticos',
                'parent_code': 'MOD_Reports',
                'order': 4,
                'icon': None,
                'url_path': '/reports/schedule',
            },
            
            # =================================================================
            # SUBMODULOS AUDIT (Nivel 2)
            # =================================================================
            
            {
                'code': 'MOD_Audit_View',
                'name': 'Ver Auditoria',
                'description': 'Visualizar logs de auditoria',
                'parent_code': 'MOD_Audit',
                'order': 1,
                'icon': None,
                'url_path': '/audit/view',
            },
            {
                'code': 'MOD_Audit_Export',
                'name': 'Exportar Auditoria',
                'description': 'Exportar logs de auditoria',
                'parent_code': 'MOD_Audit',
                'order': 2,
                'icon': None,
                'url_path': '/audit/export',
            },
            
            # =================================================================
            # SUBMODULOS ACCESS (Nivel 2)
            # =================================================================
            
            {
                'code': 'MOD_Access_Modules',
                'name': 'Gestionar Modulos',
                'description': 'Gestionar modulos del sistema',
                'parent_code': 'MOD_Access',
                'order': 1,
                'icon': None,
                'url_path': '/access/modules',
            },
            {
                'code': 'MOD_Access_Functions',
                'name': 'Gestionar Funciones',
                'description': 'Gestionar funciones atomicas',
                'parent_code': 'MOD_Access',
                'order': 2,
                'icon': None,
                'url_path': '/access/functions',
            },
            {
                'code': 'MOD_Access_Assign',
                'name': 'Asignar Accesos',
                'description': 'Asignar modulos/funciones a usuarios',
                'parent_code': 'MOD_Access',
                'order': 3,
                'icon': None,
                'url_path': '/access/assign',
            },
            
            # =================================================================
            # SUBMODULOS PIPELINE (Nivel 2)
            # =================================================================
            
            {
                'code': 'MOD_Pipeline_View',
                'name': 'Ver Pipeline',
                'description': 'Visualizar ejecuciones ETL',
                'parent_code': 'MOD_Pipeline',
                'order': 1,
                'icon': None,
                'url_path': '/pipeline/view',
            },
            {
                'code': 'MOD_Pipeline_Execute',
                'name': 'Ejecutar Pipeline',
                'description': 'Ejecutar pipeline manualmente',
                'parent_code': 'MOD_Pipeline',
                'order': 2,
                'icon': None,
                'url_path': '/pipeline/execute',
            },
            {
                'code': 'MOD_Pipeline_Schedule',
                'name': 'Programar Pipeline',
                'description': 'Configurar ejecuciones programadas',
                'parent_code': 'MOD_Pipeline',
                'order': 3,
                'icon': None,
                'url_path': '/pipeline/schedule',
            },
            
            # =================================================================
            # SUBMODULOS SETTINGS (Nivel 2)
            # =================================================================
            
            {
                'code': 'MOD_Settings_General',
                'name': 'Configuracion General',
                'description': 'Configuracion general',
                'parent_code': 'MOD_Settings',
                'order': 1,
                'icon': None,
                'url_path': '/settings/general',
            },
            {
                'code': 'MOD_Settings_Security',
                'name': 'Configuracion Seguridad',
                'description': 'Configuracion de seguridad',
                'parent_code': 'MOD_Settings',
                'order': 2,
                'icon': None,
                'url_path': '/settings/security',
            },
            {
                'code': 'MOD_Settings_Notifications',
                'name': 'Configuracion Notificaciones',
                'description': 'Configuracion de notificaciones',
                'parent_code': 'MOD_Settings',
                'order': 3,
                'icon': None,
                'url_path': '/settings/notifications',
            },
        ]

        # Cache para módulos creados
        created_modules = {}

        # Crear módulos
        self.stdout.write('\nCreando modulos...\n')
        for module_data in modules:
            # Resolver padre
            parent = None
            if module_data['parent_code']:
                parent = created_modules.get(module_data['parent_code'])
                if not parent:
                    parent = Module.objects.filter(code=module_data['parent_code']).first()

            # Preparar datos
            data = {
                'code': module_data['code'],
                'name': module_data['name'],
                'description': module_data['description'],
                'parent': parent,
                'order': module_data['order'],
                'icon': module_data['icon'],
                'url_path': module_data['url_path'],
                'is_active': True,
            }

            if dry_run:
                # Solo mostrar
                level = 0 if not parent else parent.get_level() + 1
                indent = '  ' * level
                self.stdout.write(
                    f"{indent}[{module_data['code']}] {module_data['name']}"
                )
            else:
                # Crear o actualizar
                module, created = Module.objects.update_or_create(
                    code=module_data['code'],
                    defaults=data
                )
                created_modules[module_data['code']] = module

                status = 'CREADO' if created else 'ACTUALIZADO'
                level = module.get_level()
                indent = '  ' * level
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{indent}{status}: {module.code} - {module.name}"
                    )
                )

        # Mostrar jerarquía final
        if not dry_run:
            self.stdout.write('\n' + '='*80)
            self.stdout.write(self.style.SUCCESS('JERARQUIA FINAL:'))
            self.stdout.write('='*80 + '\n')

            for root in Module.objects.filter(parent__isnull=True).order_by('order'):
                self.show_tree(root, 0)

            total = Module.objects.count()
            self.stdout.write(f'\nTotal modulos: {total}')

        self.stdout.write('\n' + self.style.SUCCESS('Inicializacion completada'))

    def show_tree(self, module, level):
        """Mostrar arbol de modulos."""
        indent = '  ' * level
        prefix = '  ' if module.children.exists() else '- '
        self.stdout.write(f'{indent}{prefix}{module.code} - {module.name}')
        self.stdout.write(f'{indent}   URL: {module.url_path}')

        for child in module.children.all().order_by('order'):
            self.show_tree(child, level + 1)
