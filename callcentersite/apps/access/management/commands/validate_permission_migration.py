"""
Comando para validar la migración de permisos.

Verifica que:
- No existen funciones CALL_*
- No existe módulo MOD_Calls
- Existen funciones PIPELINE_CALLREC_*
- Existe módulo MOD_IVR
- No hay asignaciones activas a CALL_*

Uso:
    python manage.py validate_permission_migration
"""
from django.core.management.base import BaseCommand
from apps.access.models import Function, Module, UserFunctionAssignment


class Command(BaseCommand):
    help = 'Valida la migración de permisos'
    
    def handle(self, *args, **options):
        """Ejecutar validación."""
        self.stdout.write('=' * 70)
        self.stdout.write(
            self.style.SUCCESS('[SEARCH] VALIDACIÓN DE MIGRACIÓN DE PERMISOS')
        )
        self.stdout.write('=' * 70)
        self.stdout.write('')
        
        errors = []
        warnings = []
        success = []
        
        # ================================================================
        # 1. Verificar que NO existen funciones CALL_*
        # ================================================================
        self.stdout.write('1. Verificando funciones obsoletas CALL_*...')
        old_functions = Function.objects.filter(code__startswith='CALL_')
        if old_functions.exists():
            errors.append(
                f'[ERROR] Todavía existen {old_functions.count()} funciones CALL_*'
            )
            for func in old_functions:
                errors.append(f'   - {func.code}')
        else:
            success.append('[SUCCESS] No existen funciones CALL_* (correcto)')
        self.stdout.write('')
        
        # ================================================================
        # 2. Verificar que NO existe módulo MOD_Calls
        # ================================================================
        self.stdout.write('2. Verificando módulos obsoletos MOD_Calls*...')
        old_modules = Module.objects.filter(code__startswith='MOD_Calls')
        if old_modules.exists():
            errors.append(
                f'[ERROR] Todavía existen {old_modules.count()} módulos MOD_Calls*'
            )
            for mod in old_modules:
                errors.append(f'   - {mod.code}')
        else:
            success.append('[SUCCESS] No existen módulos MOD_Calls* (correcto)')
        self.stdout.write('')
        
        # ================================================================
        # 3. Verificar que EXISTEN funciones PIPELINE_CALLREC_*
        # ================================================================
        self.stdout.write('3. Verificando funciones nuevas PIPELINE_CALLREC_*...')
        expected_pipeline_functions = [
            'PIPELINE_CALLREC_VIEW',
            'PIPELINE_CALLREC_CREATE',
            'PIPELINE_CALLREC_EDIT',
            'PIPELINE_CALLREC_DELETE',
            'PIPELINE_CALLREC_STATS',
            'PIPELINE_CALLREC_EXPORT',
        ]
        
        for func_code in expected_pipeline_functions:
            try:
                func = Function.objects.get(code=func_code)
                success.append(f'[SUCCESS] {func_code} existe')
            except Function.DoesNotExist:
                errors.append(f'[ERROR] {func_code} NO existe')
        self.stdout.write('')
        
        # ================================================================
        # 4. Verificar que EXISTE módulo MOD_IVR
        # ================================================================
        self.stdout.write('4. Verificando módulo MOD_IVR...')
        try:
            ivr_module = Module.objects.get(code='MOD_IVR')
            success.append('[SUCCESS] MOD_IVR existe')
        except Module.DoesNotExist:
            warnings.append('[WARN] MOD_IVR NO existe (opcional)')
        self.stdout.write('')
        
        # ================================================================
        # 5. Verificar funciones IVR_CALLLOG_*
        # ================================================================
        self.stdout.write('5. Verificando funciones IVR_CALLLOG_*...')
        expected_ivr_functions = [
            'IVR_CALLLOG_VIEW',
            'IVR_CALLLOG_STATS',
        ]
        
        for func_code in expected_ivr_functions:
            try:
                func = Function.objects.get(code=func_code)
                success.append(f'[SUCCESS] {func_code} existe')
            except Function.DoesNotExist:
                warnings.append(f'[WARN] {func_code} NO existe (opcional)')
        self.stdout.write('')
        
        # ================================================================
        # 6. Verificar funciones DASH_*
        # ================================================================
        self.stdout.write('6. Verificando funciones DASH_*...')
        expected_dash_functions = [
            'DASH_CREATE',
            'DASH_WIDGET_CREATE',
        ]
        
        for func_code in expected_dash_functions:
            try:
                func = Function.objects.get(code=func_code)
                success.append(f'[SUCCESS] {func_code} existe')
            except Function.DoesNotExist:
                warnings.append(f'[WARN] {func_code} NO existe (opcional)')
        self.stdout.write('')
        
        # ================================================================
        # 7. Verificar asignaciones huérfanas
        # ================================================================
        self.stdout.write('7. Verificando asignaciones activas a CALL_*...')
        orphan_assignments = UserFunctionAssignment.objects.filter(
            function__code__startswith='CALL_',
            deleted_at__isnull=True
        )
        if orphan_assignments.exists():
            errors.append(
                f'[ERROR] {orphan_assignments.count()} asignaciones activas a '
                'funciones CALL_* no migradas'
            )
            for assignment in orphan_assignments[:5]:
                errors.append(
                    f'   - {assignment.user.username}: {assignment.function.code}'
                )
            if orphan_assignments.count() > 5:
                errors.append(f'   ... y {orphan_assignments.count() - 5} más')
        else:
            success.append('[SUCCESS] No hay asignaciones activas a CALL_* (correcto)')
        self.stdout.write('')
        
        # ================================================================
        # RESUMEN
        # ================================================================
        self.stdout.write('=' * 70)
        self.stdout.write('📊 RESUMEN DE VALIDACIÓN')
        self.stdout.write('=' * 70)
        self.stdout.write('')
        
        # Mostrar éxitos
        if success:
            self.stdout.write(self.style.SUCCESS('[SUCCESS] ÉXITOS:'))
            for msg in success:
                self.stdout.write(f'  {msg}')
            self.stdout.write('')
        
        # Mostrar advertencias
        if warnings:
            self.stdout.write(self.style.WARNING('[WARN] ADVERTENCIAS:'))
            for msg in warnings:
                self.stdout.write(f'  {msg}')
            self.stdout.write('')
        
        # Mostrar errores
        if errors:
            self.stdout.write(self.style.ERROR('[ERROR] ERRORES:'))
            for msg in errors:
                self.stdout.write(f'  {msg}')
            self.stdout.write('')
        
        # Resultado final
        if errors:
            self.stdout.write(
                self.style.ERROR('[ERROR] VALIDACIÓN FALLIDA - Corregir errores')
            )
            return False
        elif warnings:
            self.stdout.write(
                self.style.WARNING('[WARN] VALIDACIÓN CON ADVERTENCIAS')
            )
            return True
        else:
            self.stdout.write(
                self.style.SUCCESS('[SUCCESS] VALIDACIÓN EXITOSA - Todo correcto')
            )
            return True
