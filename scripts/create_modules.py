"""
Script para inicializar modulos del sistema IACT.

Uso:
    python manage.py shell < scripts/create_modules.py
"""
from apps.access.models import Module

print("Inicializando modulos del sistema IACT...")
print("="*80)

# Crear modulo padre: Reportes
reportes = Module.objects.create(
    code='MOD_REPORTES',
    name='Reportes',
    description='Modulo principal de reportes del sistema',
    parent=None,
    order=1,
    icon=None,
    url_path='/reportes',
    is_active=True,
)
print(f"Creado: {reportes.code} - {reportes.name}")

# Crear submodulos de Reportes
reporte_diario = Module.objects.create(
    code='MOD_REPORTES_DIARIO',
    name='Reporte Diario',
    description='Reporte de actividad diaria',
    parent=reportes,
    order=1,
    icon=None,
    url_path='/reportes/diario',
    is_active=True,
)
print(f"  Creado: {reporte_diario.code} - {reporte_diario.name}")

reporte_acumulado = Module.objects.create(
    code='MOD_REPORTES_ACUMULADO',
    name='Reporte Acumulado',
    description='Reporte acumulado de periodo',
    parent=reportes,
    order=2,
    icon=None,
    url_path='/reportes/acumulado',
    is_active=True,
)
print(f"  Creado: {reporte_acumulado.code} - {reporte_acumulado.name}")

# Crear modulo padre: OnBoarding
onboarding = Module.objects.create(
    code='MOD_ONBOARDING',
    name='OnBoarding',
    description='Modulo de onboarding de asesores',
    parent=None,
    order=2,
    icon=None,
    url_path='/onboarding',
    is_active=True,
)
print(f"Creado: {onboarding.code} - {onboarding.name}")

# Crear submodulos de OnBoarding
matriz_asesor = Module.objects.create(
    code='MOD_ONBOARDING_MATRIZ',
    name='Matriz de Asesores',
    description='Matriz de desempeno de asesores',
    parent=onboarding,
    order=1,
    icon=None,
    url_path='/onboarding/matriz-asesores',
    is_active=True,
)
print(f"  Creado: {matriz_asesor.code} - {matriz_asesor.name}")

# Verificar jerarquia
print("\n" + "="*80)
print("JERARQUIA CREADA:")
print("="*80)

for module in Module.objects.filter(parent__isnull=True).order_by('order'):
    print(f"\n[{module.code}] {module.name}")
    print(f"   URL: {module.url_path}")
    print(f"   Nivel: {module.get_level()}")
    
    for child in module.children.all().order_by('order'):
        print(f"   - [{child.code}] {child.name}")
        print(f"      URL: {child.url_path}")
        print(f"      Nivel: {child.get_level()}")

print(f"\nTotal modulos creados: {Module.objects.count()}")
print("Inicializacion completada")
