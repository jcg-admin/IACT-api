"""
Comando para migrar asignaciones de funciones de usuarios.

Migra de funciones obsoletas (CALL_*) a funciones correctas (PIPELINE_CALLREC_*).

Uso:
    python manage.py migrate_call_permissions [--dry-run]
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.access.models import Function, UserFunctionAssignment
from django.utils import timezone


class Command(BaseCommand):
    help = 'Migra asignaciones de CALL_* a PIPELINE_CALLREC_*'
    
    # Mapeo de funciones antiguas a nuevas
    MIGRATION_MAP = {
        'CALL_VIEW': 'PIPELINE_CALLREC_VIEW',
        'CALL_CREATE': 'PIPELINE_CALLREC_CREATE',
        'CALL_EDIT': 'PIPELINE_CALLREC_EDIT',
        'CALL_DELETE': 'PIPELINE_CALLREC_DELETE',
        'CALL_STATS': 'PIPELINE_CALLREC_STATS',
        'CALL_EXP_CSV': 'PIPELINE_CALLREC_EXPORT',
    }
    
    def add_arguments(self, parser):
        """Agregar argumentos al comando."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar sin guardar cambios (preview)',
        )
    
    @transaction.atomic
    def handle(self, *args, **options):
        """Ejecutar migración."""
        dry_run = options.get('dry_run', False)
        
        self.stdout.write('=' * 70)
        self.stdout.write(
            self.style.SUCCESS('[RUNNING] MIGRACIÓN DE PERMISOS: CALL_* -> PIPELINE_CALLREC_*')
        )
        self.stdout.write('=' * 70)
        self.stdout.write('')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('[SEARCH] MODO DRY-RUN: No se guardarán cambios')
            )
            self.stdout.write('')
        
        # Estadísticas
        total_migrated = 0
        total_errors = 0
        users_affected = set()
        
        # Procesar cada función antigua
        for old_code, new_code in self.MIGRATION_MAP.items():
            self.stdout.write(f'Procesando: {old_code} -> {new_code}')
            
            try:
                # Obtener funciones
                try:
                    old_function = Function.objects.get(code=old_code)
                except Function.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'  [WARN] Función {old_code} no existe')
                    )
                    continue
                
                try:
                    new_function = Function.objects.get(code=new_code)
                except Function.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  [ERROR] Función {new_code} no existe. '
                            f'Ejecute create_functions.py primero.'
                        )
                    )
                    total_errors += 1
                    continue
                
                # Obtener asignaciones activas de función antigua
                old_assignments = UserFunctionAssignment.objects.filter(
                    function=old_function,
                    deleted_at__isnull=True
                )
                
                count = old_assignments.count()
                if count == 0:
                    self.stdout.write(
                        self.style.WARNING('  [WARN] Sin asignaciones activas')
                    )
                    continue
                
                self.stdout.write(f'  📊 {count} asignaciones encontradas')
                
                # Migrar cada asignación
                migrated = 0
                for assignment in old_assignments:
                    users_affected.add(assignment.user.username)
                    
                    if not dry_run:
                        # Crear nueva asignación
                        UserFunctionAssignment.objects.get_or_create(
                            user=assignment.user,
                            function=new_function,
                            defaults={
                                'assigned_by': assignment.assigned_by,
                                'assigned_at': assignment.assigned_at,
                            }
                        )
                        
                        # Soft delete de asignación antigua
                        assignment.deleted_at = timezone.now()
                        assignment.save()
                    
                    migrated += 1
                    
                    if dry_run:
                        self.stdout.write(
                            f'    [SEARCH] {assignment.user.username}: '
                            f'{old_code} -> {new_code} (dry-run)'
                        )
                    else:
                        self.stdout.write(
                            f'    [SUCCESS] {assignment.user.username}: '
                            f'{old_code} -> {new_code}'
                        )
                
                total_migrated += migrated
                self.stdout.write(
                    self.style.SUCCESS(f'  [SUCCESS] {migrated} asignaciones migradas')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  [ERROR] Error: {str(e)}')
                )
                total_errors += 1
            
            self.stdout.write('')
        
        # Resumen final
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
        
        self.stdout.write(f'Total asignaciones migradas: {total_migrated}')
        self.stdout.write(f'Usuarios afectados: {len(users_affected)}')
        self.stdout.write(f'Errores: {total_errors}')
        
        if users_affected:
            self.stdout.write('')
            self.stdout.write('Usuarios afectados:')
            for username in sorted(users_affected):
                self.stdout.write(f'  - {username}')
        
        if dry_run:
            self.stdout.write('')
            self.stdout.write(
                self.style.WARNING(
                    '[WARN] Ejecute sin --dry-run para aplicar cambios'
                )
            )
        else:
            self.stdout.write('')
            self.stdout.write(
                self.style.SUCCESS('[SUCCESS] Migración completada exitosamente')
            )
        
        self.stdout.write('')
