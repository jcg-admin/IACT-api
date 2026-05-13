"""
Management command para crear funciones RBAC v6.0.0.

Crea funciones con namespaces Django (permission_django).

Uso:
    python manage.py create_functions
    python manage.py create_functions --dry-run
    python manage.py create_functions --clear
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.access.models import Function


class Command(BaseCommand):
    help = 'Crea funciones RBAC v6.0.0 con namespaces Django'
    
    def add_arguments(self, parser):
        """Argumentos del comando."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la creación sin guardar en DB',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Elimina todas las funciones antes de crear',
        )
    
    def handle(self, *args, **options):
        """Ejecuta el comando."""
        dry_run = options.get('dry_run', False)
        clear = options.get('clear', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('[SEARCH] Modo DRY-RUN: No se guardará nada'))
        
        if clear and not dry_run:
            self._clear_functions()
        
        # Crear funciones
        functions_data = self._get_functions_data()
        
        created, updated = self._create_functions(functions_data, dry_run)
        
        # Resumen
        self._print_summary(created, updated, dry_run)
    
    def _clear_functions(self):
        """Elimina todas las funciones."""
        count = Function.objects.count()
        Function.objects.all().delete()
        self.stdout.write(
            self.style.WARNING(f'🗑️  Eliminadas {count} funciones existentes')
        )
    
    def _get_functions_data(self):
        """Retorna lista de funciones a crear."""
        return [
            # ============================================================
            # USERS - Gestión de Usuarios
            # ============================================================
            {
                'permission_django': 'users.view',
                'code': 'USR_VIEW',
                'module': 'MOD_Users',
                'name': 'Ver Usuarios',
                'description': 'Permite ver lista y detalles de usuarios del sistema',
                'status': 'activo',
            },
            {
                'permission_django': 'users.create',
                'code': 'USR_CREATE',
                'module': 'MOD_Users',
                'name': 'Crear Usuarios',
                'description': 'Permite crear nuevos usuarios en el sistema',
                'status': 'activo',
            },
            {
                'permission_django': 'users.edit',
                'code': 'USR_EDIT',
                'module': 'MOD_Users',
                'name': 'Editar Usuarios',
                'description': 'Permite modificar datos de usuarios existentes',
                'status': 'activo',
            },
            {
                'permission_django': 'users.delete',
                'code': 'USR_DELETE',
                'module': 'MOD_Users',
                'name': 'Eliminar Usuarios',
                'description': 'Permite eliminar usuarios del sistema (soft delete)',
                'status': 'activo',
            },
            
            # ============================================================
            # AUTHENTICATION - Autenticación y Seguridad
            # ============================================================
            {
                'permission_django': 'authentication.login',
                'code': 'AUTH_LOGIN',
                'module': 'MOD_Auth',
                'name': 'Iniciar Sesión',
                'description': 'Permite acceder al sistema mediante credenciales',
                'status': 'activo',
            },
            {
                'permission_django': 'authentication.logout',
                'code': 'AUTH_LOGOUT',
                'module': 'MOD_Auth',
                'name': 'Cerrar Sesión',
                'description': 'Permite cerrar sesión del sistema',
                'status': 'activo',
            },
            {
                'permission_django': 'authentication.change_password',
                'code': 'AUTH_PASS',
                'module': 'MOD_Auth',
                'name': 'Cambiar Contraseña',
                'description': 'Permite cambiar su propia contraseña',
                'status': 'activo',
            },
            {
                'permission_django': 'authentication.recover_password',
                'code': 'AUTH_RECOVER',
                'module': 'MOD_Auth',
                'name': 'Recuperar Contraseña',
                'description': 'Permite solicitar recuperación de contraseña',
                'status': 'activo',
            },
            {
                'permission_django': 'authentication.set_security_answers',
                'code': 'AUTH_SEC',
                'module': 'MOD_Auth',
                'name': 'Configurar Preguntas de Seguridad',
                'description': 'Permite configurar preguntas de seguridad',
                'status': 'activo',
            },
            {
                'permission_django': 'authentication.view_sessions',
                'code': 'AUTH_VIEW_SESS',
                'module': 'MOD_Auth',
                'name': 'Ver Sesiones',
                'description': 'Permite ver sesiones activas del usuario',
                'status': 'activo',
            },
            {
                'permission_django': 'authentication.invalidate_session',
                'code': 'AUTH_INVALIDATE',
                'module': 'MOD_Auth',
                'name': 'Invalidar Sesión',
                'description': 'Permite cerrar sesiones de otros usuarios (admin)',
                'status': 'activo',
            },
            
            # ============================================================
            # REPORTS - Reportes del Sistema
            # ============================================================
            {
                'permission_django': 'reports.view',
                'code': 'RPT_VIEW',
                'module': 'MOD_Reports',
                'name': 'Ver Reportes',
                'description': 'Permite ver reportes generados del sistema',
                'status': 'activo',
            },
            {
                'permission_django': 'reports.create',
                'code': 'RPT_CREATE',
                'module': 'MOD_Reports',
                'name': 'Crear Reportes',
                'description': 'Permite crear y generar nuevos reportes',
                'status': 'activo',
            },
            {
                'permission_django': 'reports.export.csv',
                'code': 'RPT_EXP_CSV',
                'module': 'MOD_Reports',
                'name': 'Exportar Reportes a CSV',
                'description': 'Permite exportar reportes a formato CSV',
                'status': 'activo',
            },
            {
                'permission_django': 'reports.export.excel',
                'code': 'RPT_EXP_EXCEL',
                'module': 'MOD_Reports',
                'name': 'Exportar Reportes a Excel',
                'description': 'Permite exportar reportes a formato Excel',
                'status': 'activo',
            },
            
            # ============================================================
            # DASHBOARD - Dashboards y Widgets (Modelo Granular)
            # ============================================================
            {
                'permission_django': 'dashboard.create',
                'code': 'DASH_CREATE',
                'module': 'MOD_Dashboard',
                'name': 'Crear Dashboards',
                'description': 'Permite crear nuevos dashboards personalizados',
                'status': 'activo',
            },
            {
                'permission_django': 'dashboard.widget.create',
                'code': 'DASH_WIDGET_CREATE',
                'module': 'MOD_Dashboard',
                'name': 'Crear Widgets',
                'description': 'Permite crear widgets en dashboards',
                'status': 'activo',
            },
            
            # ============================================================
            # ACCESS - Control de Acceso RBAC
            # ============================================================
            {
                'permission_django': 'access.view_functions',
                'code': 'ACC_VIEW_FUNC',
                'module': 'MOD_Access',
                'name': 'Ver Funciones',
                'description': 'Permite ver catálogo de funciones RBAC',
                'status': 'activo',
            },
            {
                'permission_django': 'access.assign_functions',
                'code': 'ACC_ASSIGN',
                'module': 'MOD_Access',
                'name': 'Asignar Funciones',
                'description': 'Permite asignar funciones RBAC a usuarios',
                'status': 'activo',
            },
            {
                'permission_django': 'access.revoke_functions',
                'code': 'ACC_REVOKE',
                'module': 'MOD_Access',
                'name': 'Revocar Funciones',
                'description': 'Permite revocar funciones RBAC de usuarios',
                'status': 'activo',
            },
            
            # ============================================================
            # SESSIONS - Gestión de Sesiones
            # ============================================================
            {
                'permission_django': 'sessions.view',
                'code': 'SESS_VIEW',
                'module': 'MOD_Sessions',
                'name': 'Ver Sesiones',
                'description': 'Permite ver historial de sesiones del sistema',
                'status': 'activo',
            },
            {
                'permission_django': 'sessions.manage',
                'code': 'SESS_MANAGE',
                'module': 'MOD_Sessions',
                'name': 'Gestionar Sesiones',
                'description': 'Permite gestionar y cerrar sesiones de usuarios',
                'status': 'activo',
            },
            
            # ============================================================
            # CENTERS - Gestión de Centros
            # ============================================================
            {
                'permission_django': 'centers.view',
                'code': 'CTR_VIEW',
                'module': 'MOD_Centers',
                'name': 'Ver Centros',
                'description': 'Permite ver información de centros de atención',
                'status': 'activo',
            },
            {
                'permission_django': 'centers.create',
                'code': 'CTR_CREATE',
                'module': 'MOD_Centers',
                'name': 'Crear Centros',
                'description': 'Permite crear nuevos centros de atención',
                'status': 'activo',
            },
            {
                'permission_django': 'centers.edit',
                'code': 'CTR_EDIT',
                'module': 'MOD_Centers',
                'name': 'Editar Centros',
                'description': 'Permite modificar centros de atención',
                'status': 'activo',
            },
            
            # ============================================================
            # SERVICES - Gestión de Servicios
            # ============================================================
            {
                'permission_django': 'services.view',
                'code': 'SRV_VIEW',
                'module': 'MOD_Services',
                'name': 'Ver Servicios',
                'description': 'Permite ver catálogo de servicios disponibles',
                'status': 'activo',
            },
            {
                'permission_django': 'services.create',
                'code': 'SRV_CREATE',
                'module': 'MOD_Services',
                'name': 'Crear Servicios',
                'description': 'Permite crear nuevos servicios en el catálogo',
                'status': 'activo',
            },
            
            # ============================================================
            # FUNCIONES PLANIFICADAS (para futuro)
            # ============================================================
            {
                'permission_django': 'analytics.view',
                'code': 'ANL_VIEW',
                'module': 'MOD_Analytics',
                'name': 'Ver Analytics',
                'description': 'Permite ver dashboard de analytics y métricas',
                'status': 'planificado',
            },
            {
                'permission_django': 'notifications.manage',
                'code': 'NOT_MANAGE',
                'module': 'MOD_Notifications',
                'name': 'Gestionar Notificaciones',
                'description': 'Permite configurar sistema de notificaciones',
                'status': 'planificado',
            },
                    ]
    
    @transaction.atomic
    def _create_functions(self, functions_data, dry_run):
        """Crea o actualiza funciones."""
        created_count = 0
        updated_count = 0
        
        for data in functions_data:
            permission_django = data['permission_django']
            
            if dry_run:
                exists = Function.objects.filter(
                    permission_django=permission_django
                ).exists()
                
                if exists:
                    self.stdout.write(
                        self.style.WARNING(f'  [RUNNING] Actualizaría: {permission_django}')
                    )
                    updated_count += 1
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'  [SUCCESS] Crearía: {permission_django}')
                    )
                    created_count += 1
            else:
                function, created = Function.objects.update_or_create(
                    permission_django=permission_django,
                    defaults={
                        'code': data['code'],
                        'module': data['module'],
                        'name': data['name'],
                        'description': data['description'],
                        'status': data['status'],
                        'is_active': True,
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'  [SUCCESS] Creada: {permission_django}')
                    )
                    created_count += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  [RUNNING] Actualizada: {permission_django}')
                    )
                    updated_count += 1
        
        return created_count, updated_count
    
    def _print_summary(self, created, updated, dry_run):
        """Imprime resumen de la operación."""
        total = created + updated
        
        self.stdout.write('')
        self.stdout.write('=' * 70)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('[SEARCH] RESUMEN (DRY-RUN - No guardado)')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('[SUCCESS] RESUMEN')
            )
        
        self.stdout.write('=' * 70)
        
        self.stdout.write(f'Total procesadas: {total}')
        self.stdout.write(
            self.style.SUCCESS(f'  [SUCCESS] Creadas: {created}')
        )
        self.stdout.write(
            self.style.WARNING(f'  [RUNNING] Actualizadas: {updated}')
        )
        
        if not dry_run:
            # Estadísticas por status
            activas = Function.objects.filter(status='activo').count()
            planificadas = Function.objects.filter(status='planificado').count()
            
            self.stdout.write('')
            self.stdout.write('Funciones por status:')
            self.stdout.write(f'  [SUCCESS] Activas: {activas}')
            self.stdout.write(f'  📋 Planificadas: {planificadas}')
            
            # Funciones por módulo
            from django.db.models import Count
            modules = Function.objects.values('module').annotate(
                count=Count('id')
            ).order_by('module')
            
            self.stdout.write('')
            self.stdout.write('Funciones por módulo:')
            for module in modules:
                self.stdout.write(
                    f"  [DIR] {module['module']}: {module['count']}"
                )
        
        self.stdout.write('=' * 70)
        
        if not dry_run:
            self.stdout.write('')
            self.stdout.write(
                self.style.SUCCESS('[DONE] Funciones RBAC v6.0.0 creadas exitosamente')
            )
