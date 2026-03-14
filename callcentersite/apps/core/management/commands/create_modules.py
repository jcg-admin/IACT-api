"""
Management command: create_modules v3.0.0

Genera la estructura completa de modulos del sistema IACT incluyendo:
- Modulos de negocio (use cases)
- Sistema de navegacion (menus con iconos)
- Metadata completa
- IDs numericos para todos los menus

Uso:
    python manage.py create_modules [opciones]

Opciones:
    --dry-run       Muestra lo que haria sin crear archivos
    --force         Sobrescribe archivos existentes
    --module=NAME   Crea solo un modulo especifico
    --verbose       Muestra informacion detallada
    --skip-nav      No genera archivos de navegacion

Version: 3.0.0
Basado en: UC v4.1.0, RBAC v5.2.1
Fecha: 2026-01-16
Cambios v3: IDs numericos para menus
"""

from django.core.management.base import BaseCommand, CommandError
from pathlib import Path
from typing import Dict, List, Optional
import json


class Command(BaseCommand):
    """Management command para generar estructura completa de modulos IACT."""
    
    help = 'Genera estructura de modulos + navegacion (UC v4.1.0) con IDs numericos'
    
    # =========================================================================
    # CONFIGURACION GLOBAL
    # =========================================================================
    
    VERSION_INFO = {
        'command_version': '3.0.0',
        'uc_version': '4.1.0',
        'rbac_version': '5.2.1',
        'total_uc': 47,
        'total_functions': 42,
        'total_modules': 8,
        'changelog': 'v3.0.0: IDs numericos para todos los menus',
    }
    
    # =========================================================================
    # ESQUEMA DE IDS NUMERICOS
    # =========================================================================
    # NIVEL 1: 1-99
    # NIVEL 2: 100-999 (primer digito = modulo padre)
    #   - Auth (1): 101-199
    #   - Users (2): 201-299
    #   - Access (3): 301-399
    #   - Pipeline (4): 401-499
    #   - Reports (5): 501-599
    #   - Alerts (6): 601-699
    #   - Audit (7): 701-799
    #   - Logs (8): 801-899
    # =========================================================================
    
    MODULES_CONFIG = {
        'auth': {
            'name': 'MOD_Auth',
            'app': 'authentication',
            'description': 'Autenticacion y gestion de sesiones',
            'uc_count': 5,
            'functions_count': 4,
            'status': 'implemented',
            'menu_config': {
                'nivel': 1,
                'id_menu': 1,
                'des_name': 'Autenticacion',
                'icon': '/static/icons/menu/auth.png',
                'orden': 10,
            },
            'use_cases': [
                {
                    'id': 'UC_AUTH_01',
                    'title': 'Iniciar Sesion',
                    'functions': ['AUTH-001: manage_sessions'],
                    'groups': ['AGR-001', 'AGR-006', 'AGR-010'],
                    'cnst': ['CNST-002', 'CNST-005'],
                    'menu': {
                        'id_menu': 101,
                        'des_name': 'Iniciar Sesion',
                        'endpoint': '/api/auth/login/',
                        'method': 'POST',
                        'icon': '/static/icons/submenu/login.png',
                        'orden': 1,
                    },
                },
                {
                    'id': 'UC_AUTH_02',
                    'title': 'Cerrar Sesion',
                    'functions': ['AUTH-002: close_user_session'],
                    'groups': ['AGR-001', 'AGR-010'],
                    'cnst': ['CNST-002'],
                    'menu': {
                        'id_menu': 102,
                        'des_name': 'Cerrar Sesion',
                        'endpoint': '/api/auth/logout/',
                        'method': 'POST',
                        'icon': '/static/icons/submenu/logout.png',
                        'orden': 2,
                    },
                },
                {
                    'id': 'UC_AUTH_03',
                    'title': 'Recuperar Contraseña',
                    'functions': ['AUTH-003: reset_password'],
                    'groups': ['AGR-010'],
                    'cnst': ['CNST-001', 'CNST-002'],
                    'menu': {
                        'id_menu': 103,
                        'des_name': 'Recuperar Contraseña',
                        'endpoint': '/api/auth/reset-password/',
                        'method': 'POST',
                        'icon': '/static/icons/submenu/reset_password.png',
                        'orden': 3,
                    },
                },
                {
                    'id': 'UC_AUTH_04',
                    'title': 'Cambiar Contraseña',
                    'functions': ['AUTH-001: manage_sessions'],
                    'groups': ['AGR-001'],
                    'cnst': ['CNST-002', 'CNST-009'],
                    'menu': {
                        'id_menu': 104,
                        'des_name': 'Cambiar Contraseña',
                        'endpoint': '/api/auth/change-password/',
                        'method': 'PUT',
                        'icon': '/static/icons/submenu/change_password.png',
                        'orden': 4,
                    },
                },
                {
                    'id': 'UC_AUTH_05',
                    'title': 'Gestionar Sesiones',
                    'functions': ['AUTH-004: view_active_sessions'],
                    'groups': ['AGR-006', 'AGR-010'],
                    'cnst': ['CNST-002', 'CNST-009'],
                    'menu': {
                        'id_menu': 105,
                        'des_name': 'Sesiones Activas',
                        'endpoint': '/api/auth/sessions/',
                        'method': 'GET',
                        'icon': '/static/icons/submenu/sessions.png',
                        'orden': 5,
                    },
                },
            ],
        },
        
        'users': {
            'name': 'MOD_Users',
            'app': 'users',
            'description': 'Gestion de identidades de usuarios',
            'uc_count': 4,
            'functions_count': 9,
            'status': 'implemented',
            'menu_config': {
                'nivel': 1,
                'id_menu': 2,
                'des_name': 'Usuarios',
                'icon': '/static/icons/menu/users.png',
                'orden': 20,
            },
            'use_cases': [
                {
                    'id': 'UC_USR_01',
                    'title': 'Crear Usuario',
                    'functions': ['USR-001: create_users', 'USR-002: update_users'],
                    'groups': ['AGR-006'],
                    'cnst': ['CNST-002', 'CNST-009'],
                    'menu': {
                        'id_menu': 201,
                        'des_name': 'Crear Usuario',
                        'endpoint': '/api/users/create/',
                        'method': 'POST',
                        'icon': '/static/icons/submenu/create_user.png',
                        'orden': 1,
                    },
                },
                {
                    'id': 'UC_USR_02',
                    'title': 'Consultar Usuarios',
                    'functions': ['USR-004: list_users', 'USR-005: search_users', 'USR-009: view_users'],
                    'groups': ['AGR-002', 'AGR-006'],
                    'cnst': [],
                    'menu': {
                        'id_menu': 202,
                        'des_name': 'Consultar Usuarios',
                        'endpoint': '/api/users/',
                        'method': 'GET',
                        'icon': '/static/icons/submenu/list_users.png',
                        'orden': 2,
                    },
                },
                {
                    'id': 'UC_USR_03',
                    'title': 'Modificar Usuario',
                    'functions': ['USR-002: update_users', 'USR-006: block_users', 
                                  'USR-007: unblock_users', 'USR-008: reactivate_users'],
                    'groups': ['AGR-006'],
                    'cnst': ['CNST-009'],
                    'menu': {
                        'id_menu': 203,
                        'des_name': 'Modificar Usuario',
                        'endpoint': '/api/users/{id}/',
                        'method': 'PUT',
                        'icon': '/static/icons/submenu/update_user.png',
                        'orden': 3,
                    },
                },
                {
                    'id': 'UC_USR_04',
                    'title': 'Eliminar Usuario',
                    'functions': ['USR-003: delete_users'],
                    'groups': ['AGR-006'],
                    'cnst': ['CNST-009'],
                    'menu': {
                        'id_menu': 204,
                        'des_name': 'Eliminar Usuario',
                        'endpoint': '/api/users/{id}/',
                        'method': 'DELETE',
                        'icon': '/static/icons/submenu/delete_user.png',
                        'orden': 4,
                    },
                },
            ],
        },
        
        'access': {
            'name': 'MOD_Access',
            'app': 'access',
            'description': 'Control de acceso RBAC',
            'uc_count': 7,
            'functions_count': 5,
            'status': 'implemented',
            'menu_config': {
                'nivel': 1,
                'id_menu': 3,
                'des_name': 'Permisos',
                'icon': '/static/icons/menu/access.png',
                'orden': 30,
            },
            'use_cases': [
                {
                    'id': 'UC_ACC_01',
                    'title': 'Asignar Funciones',
                    'functions': ['ACC-001: assign_functions'],
                    'groups': ['AGR-007'],
                    'cnst': ['CNST-005', 'CNST-009', 'CNST-010'],
                    'menu': {
                        'id_menu': 301,
                        'des_name': 'Asignar Funciones',
                        'endpoint': '/api/access/assign-functions/',
                        'method': 'POST',
                        'icon': '/static/icons/submenu/assign_functions.png',
                        'orden': 1,
                    },
                },
                {
                    'id': 'UC_ACC_02',
                    'title': 'Revocar Funciones',
                    'functions': ['ACC-002: revoke_functions'],
                    'groups': ['AGR-007'],
                    'cnst': ['CNST-005', 'CNST-009', 'CNST-010'],
                    'menu': {
                        'id_menu': 302,
                        'des_name': 'Revocar Funciones',
                        'endpoint': '/api/access/revoke-functions/',
                        'method': 'POST',
                        'icon': '/static/icons/submenu/revoke_functions.png',
                        'orden': 2,
                    },
                },
                {
                    'id': 'UC_ACC_03',
                    'title': 'Consultar Permisos',
                    'functions': ['ACC-003: view_assignments'],
                    'groups': ['AGR-007'],
                    'cnst': [],
                    'menu': {
                        'id_menu': 303,
                        'des_name': 'Ver Permisos',
                        'endpoint': '/api/access/permissions/',
                        'method': 'GET',
                        'icon': '/static/icons/submenu/view_permissions.png',
                        'orden': 3,
                    },
                },
                {
                    'id': 'UC_ACC_04',
                    'title': 'Asignar Agrupador',
                    'functions': ['ACC-004: assign_function_groups'],
                    'groups': ['AGR-007'],
                    'cnst': ['CNST-005', 'CNST-009', 'CNST-010'],
                    'menu': {
                        'id_menu': 304,
                        'des_name': 'Asignar Grupos',
                        'endpoint': '/api/access/assign-groups/',
                        'method': 'POST',
                        'icon': '/static/icons/submenu/assign_groups.png',
                        'orden': 4,
                    },
                },
                {
                    'id': 'UC_ACC_05',
                    'title': 'Gestionar SoD',
                    'functions': ['ACC-005: manage_separation_rules'],
                    'groups': ['AGR-007'],
                    'cnst': ['CNST-005', 'CNST-009', 'CNST-010'],
                    'menu': {
                        'id_menu': 305,
                        'des_name': 'Reglas SoD',
                        'endpoint': '/api/access/sod-rules/',
                        'method': 'GET',
                        'icon': '/static/icons/submenu/sod_rules.png',
                        'orden': 5,
                    },
                },
                {
                    'id': 'UC_ACC_08',
                    'title': 'Permiso Temporal',
                    'functions': ['ACC-001: assign_functions'],
                    'groups': ['AGR-007'],
                    'cnst': ['CNST-005', 'CNST-009'],
                    'menu': {
                        'id_menu': 306,
                        'des_name': 'Permiso Temporal',
                        'endpoint': '/api/access/temporary-permission/',
                        'method': 'POST',
                        'icon': '/static/icons/submenu/temp_permission.png',
                        'orden': 6,
                    },
                },
                {
                    'id': 'UC_ACC_09',
                    'title': 'Auditar Cambios Acceso',
                    'functions': ['(lectura)'],
                    'groups': ['AGR-008'],
                    'cnst': ['CNST-009'],
                    'menu': {
                        'id_menu': 307,
                        'des_name': 'Auditoria Accesos',
                        'endpoint': '/api/access/audit/',
                        'method': 'GET',
                        'icon': '/static/icons/submenu/audit_access.png',
                        'orden': 7,
                    },
                },
            ],
        },
        
        'pipeline': {
            'name': 'MOD_Pipeline',
            'app': 'pipeline',
            'description': 'Supervision de procesos ETL',
            'uc_count': 4,
            'functions_count': 4,
            'status': 'implemented',
            'menu_config': {
                'nivel': 1,
                'id_menu': 4,
                'des_name': 'ETL Pipeline',
                'icon': '/static/icons/menu/pipeline.png',
                'orden': 40,
            },
            'use_cases': [
                {
                    'id': 'UC_PIP_01',
                    'title': 'Supervisar ETL',
                    'functions': ['PIP-001: view_pipeline_status'],
                    'groups': ['AGR-009'],
                    'cnst': ['CNST-003', 'CNST-009'],
                    'menu': {
                        'id_menu': 401,
                        'des_name': 'Estado ETL',
                        'endpoint': '/api/pipeline/status/',
                        'method': 'GET',
                        'icon': '/static/icons/submenu/pipeline_status.png',
                        'orden': 1,
                    },
                },
                {
                    'id': 'UC_PIP_02',
                    'title': 'Consultar Errores ETL',
                    'functions': ['PIP-002: view_pipeline_errors'],
                    'groups': ['AGR-009'],
                    'cnst': ['CNST-003', 'CNST-009'],
                    'menu': {
                        'id_menu': 402,
                        'des_name': 'Errores ETL',
                        'endpoint': '/api/pipeline/errors/',
                        'method': 'GET',
                        'icon': '/static/icons/submenu/pipeline_errors.png',
                        'orden': 2,
                    },
                },
                {
                    'id': 'UC_PIP_03',
                    'title': 'Consultar Disponibilidad',
                    'functions': ['PIP-003: view_data_availability'],
                    'groups': ['AGR-009'],
                    'cnst': ['CNST-003'],
                    'menu': {
                        'id_menu': 403,
                        'des_name': 'Disponibilidad Datos',
                        'endpoint': '/api/pipeline/availability/',
                        'method': 'GET',
                        'icon': '/static/icons/submenu/data_availability.png',
                        'orden': 3,
                    },
                },
                {
                    'id': 'UC_PIP_04',
                    'title': 'Solicitar Reintento',
                    'functions': ['PIP-004: request_pipeline_retry'],
                    'groups': ['AGR-009'],
                    'cnst': ['CNST-003', 'CNST-009'],
                    'menu': {
                        'id_menu': 404,
                        'des_name': 'Reintentar ETL',
                        'endpoint': '/api/pipeline/retry/',
                        'method': 'POST',
                        'icon': '/static/icons/submenu/pipeline_retry.png',
                        'orden': 4,
                    },
                },
            ],
        },
        
        'reports': {
            'name': 'MOD_Reports',
            'app': 'reports',
            'description': 'Reportes, dashboards y visualizaciones',
            'uc_count': 14,
            'functions_count': 8,
            'status': 'implemented',
            'menu_config': {
                'nivel': 1,
                'id_menu': 5,
                'des_name': 'Reportes',
                'icon': '/static/icons/menu/reports.png',
                'orden': 50,
            },
            'use_cases': [
                {
                    'id': 'UC_RPT_01',
                    'title': 'Consultar Reporte Trimestral',
                    'functions': ['RPT-001: view_reports'],
                    'groups': ['AGR-002', 'AGR-003', 'AGR-004'],
                    'cnst': ['CNST-003', 'CNST-006'],
                    'menu': {
                        'id_menu': 501,
                        'des_name': 'Reporte Trimestral',
                        'endpoint': '/api/reports/quarterly/',
                        'method': 'GET',
                        'icon': '/static/icons/submenu/quarterly_report.png',
                        'orden': 1,
                    },
                },
                {
                    'id': 'UC_RPT_02',
                    'title': 'Consultar Problemas Menu',
                    'functions': ['RPT-001: view_reports'],
                    'groups': ['AGR-002', 'AGR-003', 'AGR-004'],
                    'cnst': ['CNST-003', 'CNST-006'],
                    'menu': {
                        'id_menu': 502,
                        'des_name': 'Problemas de Menu',
                        'endpoint': '/api/reports/menu-problems/',
                        'method': 'GET',
                        'icon': '/static/icons/submenu/menu_problems.png',
                        'orden': 2,
                    },
                },
                {
                    'id': 'UC_RPT_03',
                    'title': 'Consultar Transferencias',
                    'functions': ['RPT-001: view_reports'],
                    'groups': ['AGR-002', 'AGR-003', 'AGR-004'],
                    'cnst': ['CNST-003', 'CNST-006'],
                    'menu': {
                        'id_menu': 503,
                        'des_name': 'Transferencias',
                        'endpoint': '/api/reports/transfers/',
                        'method': 'GET',
                        'icon': '/static/icons/submenu/transfers.png',
                        'orden': 3,
                    },
                },
                {
                    'id': 'UC_RPT_04',
                    'title': 'Filtrar Por Fecha',
                    'functions': ['RPT-003: filter_reports'],
                    'groups': ['AGR-002', 'AGR-003', 'AGR-004'],
                    'cnst': ['CNST-006'],
                    'menu': None,
                },
                {
                    'id': 'UC_RPT_05',
                    'title': 'Filtrar Por Centro',
                    'functions': ['RPT-003: filter_reports'],
                    'groups': ['AGR-002', 'AGR-003', 'AGR-004'],
                    'cnst': [],
                    'menu': None,
                },
                {
                    'id': 'UC_RPT_06',
                    'title': 'Exportar CSV',
                    'functions': ['RPT-004: export_csv'],
                    'groups': ['AGR-003', 'AGR-004'],
                    'cnst': ['CNST-001', 'CNST-007', 'CNST-009'],
                    'menu': {
                        'id_menu': 504,
                        'des_name': 'Exportar CSV',
                        'endpoint': '/api/reports/export/csv/',
                        'method': 'POST',
                        'icon': '/static/icons/submenu/export_csv.png',
                        'orden': 4,
                    },
                },
                {
                    'id': 'UC_RPT_07',
                    'title': 'Exportar Excel',
                    'functions': ['RPT-005: export_excel'],
                    'groups': ['AGR-003', 'AGR-004'],
                    'cnst': ['CNST-001', 'CNST-007', 'CNST-009'],
                    'menu': {
                        'id_menu': 505,
                        'des_name': 'Exportar Excel',
                        'endpoint': '/api/reports/export/excel/',
                        'method': 'POST',
                        'icon': '/static/icons/submenu/export_excel.png',
                        'orden': 5,
                    },
                },
                {
                    'id': 'UC_RPT_08',
                    'title': 'Exportar PDF',
                    'functions': ['RPT-006: export_pdf'],
                    'groups': ['AGR-003', 'AGR-004'],
                    'cnst': ['CNST-001', 'CNST-007', 'CNST-009'],
                    'menu': {
                        'id_menu': 506,
                        'des_name': 'Exportar PDF',
                        'endpoint': '/api/reports/export/pdf/',
                        'method': 'POST',
                        'icon': '/static/icons/submenu/export_pdf.png',
                        'orden': 6,
                    },
                },
                {
                    'id': 'UC_RPT_09',
                    'title': 'Ver Dashboard',
                    'functions': ['RPT-002: view_dashboard'],
                    'groups': ['AGR-001', 'AGR-002', 'AGR-003'],
                    'cnst': ['CNST-003'],
                    'menu': {
                        'id_menu': 507,
                        'des_name': 'Dashboard Principal',
                        'endpoint': '/api/reports/dashboard/',
                        'method': 'GET',
                        'icon': '/static/icons/submenu/dashboard.png',
                        'orden': 7,
                    },
                },
                {
                    'id': 'UC_RPT_10',
                    'title': 'Ver KPIs',
                    'functions': ['RPT-007: view_kpis'],
                    'groups': ['AGR-002', 'AGR-003', 'AGR-004'],
                    'cnst': ['CNST-003'],
                    'menu': {
                        'id_menu': 508,
                        'des_name': 'Indicadores KPI',
                        'endpoint': '/api/reports/kpis/',
                        'method': 'GET',
                        'icon': '/static/icons/submenu/kpis.png',
                        'orden': 8,
                    },
                },
                {
                    'id': 'UC_RPT_11',
                    'title': 'Ver Tendencias',
                    'functions': ['RPT-008: view_charts'],
                    'groups': ['AGR-002', 'AGR-003', 'AGR-004'],
                    'cnst': ['CNST-003'],
                    'menu': {
                        'id_menu': 509,
                        'des_name': 'Graficos Tendencias',
                        'endpoint': '/api/reports/charts/trends/',
                        'method': 'GET',
                        'icon': '/static/icons/submenu/trends.png',
                        'orden': 9,
                    },
                },
                {
                    'id': 'UC_RPT_12',
                    'title': 'Ver Grafico Hora',
                    'functions': ['RPT-008: view_charts'],
                    'groups': ['AGR-002', 'AGR-003', 'AGR-004'],
                    'cnst': ['CNST-003'],
                    'menu': {
                        'id_menu': 510,
                        'des_name': 'Grafico por Hora',
                        'endpoint': '/api/reports/charts/hourly/',
                        'method': 'GET',
                        'icon': '/static/icons/submenu/chart_hourly.png',
                        'orden': 10,
                    },
                },
                {
                    'id': 'UC_RPT_13',
                    'title': 'Ver Grafico Dia',
                    'functions': ['RPT-008: view_charts'],
                    'groups': ['AGR-002', 'AGR-003', 'AGR-004'],
                    'cnst': ['CNST-003'],
                    'menu': {
                        'id_menu': 511,
                        'des_name': 'Grafico por Dia',
                        'endpoint': '/api/reports/charts/daily/',
                        'method': 'GET',
                        'icon': '/static/icons/submenu/chart_daily.png',
                        'orden': 11,
                    },
                },
                {
                    'id': 'UC_RPT_14',
                    'title': 'Ver Distribucion Centro',
                    'functions': ['RPT-008: view_charts'],
                    'groups': ['AGR-002', 'AGR-003', 'AGR-004'],
                    'cnst': ['CNST-003'],
                    'menu': {
                        'id_menu': 512,
                        'des_name': 'Distribucion por Centro',
                        'endpoint': '/api/reports/charts/center-distribution/',
                        'method': 'GET',
                        'icon': '/static/icons/submenu/center_distribution.png',
                        'orden': 12,
                    },
                },
            ],
        },
        
        'alerts': {
            'name': 'MOD_Alerts',
            'app': 'alerts',
            'description': 'Sistema de alertas internas',
            'uc_count': 5,
            'functions_count': 6,
            'status': 'pending',
            'menu_config': {
                'nivel': 1,
                'id_menu': 6,
                'des_name': 'Alertas',
                'icon': '/static/icons/menu/alerts.png',
                'orden': 60,
            },
            'use_cases': [
                {
                    'id': 'UC_ALR_01',
                    'title': 'Configurar Alerta',
                    'functions': ['ALR-002: configure_alerts'],
                    'groups': ['AGR-003', 'AGR-005'],
                    'cnst': ['CNST-001', 'CNST-004', 'CNST-009'],
                    'menu': {
                        'id_menu': 601,
                        'des_name': 'Configurar Alerta',
                        'endpoint': '/api/alerts/configure/',
                        'method': 'POST',
                        'icon': '/static/icons/submenu/configure_alert.png',
                        'orden': 1,
                    },
                },
                {
                    'id': 'UC_ALR_02',
                    'title': 'Consultar Alertas',
                    'functions': ['ALR-001: view_alerts'],
                    'groups': ['AGR-003', 'AGR-005'],
                    'cnst': ['CNST-001'],
                    'menu': {
                        'id_menu': 602,
                        'des_name': 'Consultar Alertas',
                        'endpoint': '/api/alerts/',
                        'method': 'GET',
                        'icon': '/static/icons/submenu/view_alerts.png',
                        'orden': 2,
                    },
                },
                {
                    'id': 'UC_ALR_03',
                    'title': 'Pausar Alerta',
                    'functions': ['ALR-004: pause_alerts'],
                    'groups': ['AGR-005'],
                    'cnst': ['CNST-009'],
                    'menu': {
                        'id_menu': 603,
                        'des_name': 'Pausar Alerta',
                        'endpoint': '/api/alerts/{id}/pause/',
                        'method': 'PUT',
                        'icon': '/static/icons/submenu/pause_alert.png',
                        'orden': 3,
                    },
                },
                {
                    'id': 'UC_ALR_04',
                    'title': 'Eliminar Alerta',
                    'functions': ['ALR-005: delete_alerts'],
                    'groups': ['AGR-005'],
                    'cnst': ['CNST-009'],
                    'menu': {
                        'id_menu': 604,
                        'des_name': 'Eliminar Alerta',
                        'endpoint': '/api/alerts/{id}/',
                        'method': 'DELETE',
                        'icon': '/static/icons/submenu/delete_alert.png',
                        'orden': 4,
                    },
                },
                {
                    'id': 'UC_ALR_05',
                    'title': 'Gestionar Destinatarios',
                    'functions': ['ALR-003: configure_team_alerts', 'ALR-006: view_alert_history'],
                    'groups': ['AGR-005'],
                    'cnst': ['CNST-001', 'CNST-004'],
                    'menu': {
                        'id_menu': 605,
                        'des_name': 'Gestionar Destinatarios',
                        'endpoint': '/api/alerts/{id}/recipients/',
                        'method': 'PUT',
                        'icon': '/static/icons/submenu/manage_recipients.png',
                        'orden': 5,
                    },
                },
            ],
        },
        
        'audit': {
            'name': 'MOD_Audit',
            'app': 'audit',
            'description': 'Auditoria y compliance',
            'uc_count': 4,
            'functions_count': 4,
            'status': 'implemented',
            'menu_config': {
                'nivel': 1,
                'id_menu': 7,
                'des_name': 'Auditoria',
                'icon': '/static/icons/menu/audit.png',
                'orden': 70,
            },
            'use_cases': [
                {
                    'id': 'UC_AUD_01',
                    'title': 'Consultar Auditoria',
                    'functions': ['AUD-001: view_audit_log', 'AUD-002: search_audit_log'],
                    'groups': ['AGR-008'],
                    'cnst': ['CNST-008', 'CNST-009'],
                    'menu': {
                        'id_menu': 701,
                        'des_name': 'Registro de Auditoria',
                        'endpoint': '/api/audit/log/',
                        'method': 'GET',
                        'icon': '/static/icons/submenu/audit_log.png',
                        'orden': 1,
                    },
                },
                {
                    'id': 'UC_AUD_02',
                    'title': 'Generar Reporte Compliance',
                    'functions': ['AUD-004: generate_compliance_report'],
                    'groups': ['AGR-008'],
                    'cnst': ['CNST-008', 'CNST-009'],
                    'menu': {
                        'id_menu': 702,
                        'des_name': 'Reporte Compliance',
                        'endpoint': '/api/audit/compliance-report/',
                        'method': 'POST',
                        'icon': '/static/icons/submenu/compliance_report.png',
                        'orden': 2,
                    },
                },
                {
                    'id': 'UC_AUD_03',
                    'title': 'Exportar Auditoria',
                    'functions': ['AUD-003: export_audit_log'],
                    'groups': ['AGR-008'],
                    'cnst': ['CNST-001', 'CNST-008', 'CNST-009'],
                    'menu': {
                        'id_menu': 703,
                        'des_name': 'Exportar Auditoria',
                        'endpoint': '/api/audit/export/',
                        'method': 'POST',
                        'icon': '/static/icons/submenu/export_audit.png',
                        'orden': 3,
                    },
                },
                {
                    'id': 'UC_AUD_04',
                    'title': 'Registrar Evento',
                    'functions': ['(sistema)'],
                    'groups': ['Sistema'],
                    'cnst': ['CNST-009'],
                    'menu': None,
                },
            ],
        },
        
        'logs': {
            'name': 'MOD_Logs',
            'app': 'logs',
            'description': 'Logs tecnicos del sistema',
            'uc_count': 4,
            'functions_count': 2,
            'status': 'pending',
            'menu_config': {
                'nivel': 1,
                'id_menu': 8,
                'des_name': 'Logs del Sistema',
                'icon': '/static/icons/menu/logs.png',
                'orden': 80,
            },
            'use_cases': [
                {
                    'id': 'UC_LOG_01',
                    'title': 'Consultar Logs',
                    'functions': ['LOG-001: view_technical_logs'],
                    'groups': ['AGR-010'],
                    'cnst': ['CNST-008'],
                    'menu': {
                        'id_menu': 801,
                        'des_name': 'Consultar Logs',
                        'endpoint': '/api/logs/',
                        'method': 'GET',
                        'icon': '/static/icons/submenu/view_logs.png',
                        'orden': 1,
                    },
                },
                {
                    'id': 'UC_LOG_02',
                    'title': 'Filtrar Logs',
                    'functions': ['LOG-001: view_technical_logs'],
                    'groups': ['AGR-010'],
                    'cnst': ['CNST-008'],
                    'menu': None,
                },
                {
                    'id': 'UC_LOG_03',
                    'title': 'Exportar Logs',
                    'functions': ['LOG-002: export_logs'],
                    'groups': ['AGR-010'],
                    'cnst': ['CNST-001', 'CNST-008'],
                    'menu': {
                        'id_menu': 802,
                        'des_name': 'Exportar Logs',
                        'endpoint': '/api/logs/export/',
                        'method': 'POST',
                        'icon': '/static/icons/submenu/export_logs.png',
                        'orden': 2,
                    },
                },
                {
                    'id': 'UC_LOG_04',
                    'title': 'Configurar Retencion',
                    'functions': ['(admin)'],
                    'groups': ['AGR-009'],
                    'cnst': ['CNST-008'],
                    'menu': {
                        'id_menu': 803,
                        'des_name': 'Configurar Retencion',
                        'endpoint': '/api/logs/retention/',
                        'method': 'PUT',
                        'icon': '/static/icons/submenu/log_retention.png',
                        'orden': 3,
                    },
                },
            ],
        },
    }
    
    def add_arguments(self, parser):
        """Define argumentos del command."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra lo que haria sin crear archivos',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Sobrescribe archivos existentes',
        )
        parser.add_argument(
            '--module',
            type=str,
            help='Crea solo un modulo especifico',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Muestra informacion detallada',
        )
        parser.add_argument(
            '--skip-nav',
            action='store_true',
            help='No genera archivos de navegacion',
        )
    
    def handle(self, *args, **options):
        """Ejecuta el command."""
        self.dry_run = options['dry_run']
        self.force = options['force']
        self.module_filter = options.get('module')
        self.verbose = options['verbose']
        self.skip_nav = options['skip_nav']
        
        self.stdout.write('=' * 70)
        self.stdout.write('  GENERADOR DE MODULOS IACT v3.0.0 - IDs NUMERICOS')
        self.stdout.write('=' * 70)
        self.stdout.write(f"  UC v{self.VERSION_INFO['uc_version']} | "
                         f"RBAC v{self.VERSION_INFO['rbac_version']} | "
                         f"{self.VERSION_INFO['total_uc']} Casos de Uso")
        self.stdout.write('=' * 70)
        self.stdout.write('')
        
        if self.dry_run:
            self.stdout.write('[DRY-RUN] No se crearan archivos\n')
        
        # Filtrar modulos
        modules_to_create = self.MODULES_CONFIG
        if self.module_filter:
            if self.module_filter not in self.MODULES_CONFIG:
                raise CommandError(f"Modulo '{self.module_filter}' no existe")
            modules_to_create = {self.module_filter: self.MODULES_CONFIG[self.module_filter]}
        
        # Crear estructura
        total_created = 0
        total_skipped = 0
        
        for module_key, module_config in modules_to_create.items():
            created, skipped = self._create_module(module_key, module_config)
            total_created += created
            total_skipped += skipped
        
        # Metadata global
        self._create_metadata_file()
        
        # Estructura de iconos
        if not self.skip_nav:
            self._create_icon_structure()
        
        # Resumen
        self.stdout.write('')
        self.stdout.write('=' * 70)
        self.stdout.write('  RESUMEN')
        self.stdout.write('=' * 70)
        self.stdout.write(f"  Modulos procesados: {len(modules_to_create)}")
        self.stdout.write(f"  Archivos creados: {total_created}")
        self.stdout.write(f"  Archivos omitidos: {total_skipped}")
        self.stdout.write('=' * 70)
        
        if not self.dry_run:
            self.stdout.write('\nEstructura de modulos creada exitosamente')
        else:
            self.stdout.write('\nEjecuta sin --dry-run para crear los archivos')
    
    def _create_module(self, module_key: str, module_config: Dict) -> tuple:
        """Crea la estructura de un modulo."""
        created = 0
        skipped = 0
        
        module_name = module_config['name']
        status = module_config['status']
        status_icon = '[OK]' if status == 'implemented' else '[PENDING]'
        
        self.stdout.write(f"\n{status_icon} {module_name} ({module_config['app']})")
        self.stdout.write(f"   {module_config['description']}")
        self.stdout.write(f"   UC: {module_config['uc_count']} | Funciones: {module_config['functions_count']}")
        self.stdout.write(f"   ID Menu: {module_config['menu_config']['id_menu']}")
        
        # Directorio base
        base_path = Path('modules') / module_key
        if self._create_directory(base_path):
            created += 1
        else:
            skipped += 1
        
        # __init__.py
        init_path = base_path / '__init__.py'
        init_content = self._generate_module_init(module_key, module_config)
        if self._create_file(init_path, init_content):
            created += 1
        else:
            skipped += 1
        
        # README.md
        readme_path = base_path / 'README.md'
        readme_content = self._generate_module_readme(module_key, module_config)
        if self._create_file(readme_path, readme_content):
            created += 1
        else:
            skipped += 1
        
        # Navegacion
        if not self.skip_nav:
            nav_created, nav_skipped = self._create_navigation_metadata(base_path, module_config)
            created += nav_created
            skipped += nav_skipped
        
        # UC
        for uc in module_config['use_cases']:
            uc_created, uc_skipped = self._create_use_case_module(base_path, uc, module_config)
            created += uc_created
            skipped += uc_skipped
        
        return created, skipped
    
    def _create_navigation_metadata(self, base_path: Path, module_config: Dict) -> tuple:
        """Crea metadata de navegacion del modulo."""
        created = 0
        skipped = 0
        
        nav_path = base_path / 'navigation'
        if self._create_directory(nav_path):
            created += 1
        else:
            skipped += 1
        
        # menu_metadata.json
        metadata_path = nav_path / 'menu_metadata.json'
        metadata_content = self._generate_navigation_metadata(module_config)
        if self._create_file(metadata_path, metadata_content):
            created += 1
        else:
            skipped += 1
        
        return created, skipped
    
    def _generate_navigation_metadata(self, module_config: Dict) -> str:
        """Genera el archivo menu_metadata.json."""
        menu_config = module_config['menu_config']
        
        # Construir submenus solo de UC que tienen menu
        submenus = []
        for uc in module_config['use_cases']:
            if uc.get('menu'):
                menu_item = uc['menu'].copy()
                menu_item['required_functions'] = uc['functions']
                submenus.append(menu_item)
        
        metadata = {
            'module': module_config['name'],
            'app': module_config['app'],
            'menu_tree': [
                {
                    'nivel': menu_config['nivel'],
                    'id_menu': menu_config['id_menu'],
                    'des_name': menu_config['des_name'],
                    'icon': menu_config['icon'],
                    'orden': menu_config['orden'],
                    'required_functions': [],
                    'submenus': submenus
                }
            ]
        }
        
        return json.dumps(metadata, indent=2, ensure_ascii=False)
    
    def _create_use_case_module(self, base_path: Path, uc: Dict, module_config: Dict) -> tuple:
        """Crea el submodulo de un caso de uso."""
        created = 0
        skipped = 0
        
        uc_dir_name = uc['id'].lower()
        uc_path = base_path / uc_dir_name
        
        if self.verbose:
            menu_id = uc.get('menu', {}).get('id_menu', 'N/A') if uc.get('menu') else 'N/A'
            self.stdout.write(f"      -> {uc['id']}: {uc['title']} (Menu ID: {menu_id})")
        
        if self._create_directory(uc_path):
            created += 1
        else:
            skipped += 1
        
        # __init__.py
        uc_init_path = uc_path / '__init__.py'
        uc_init_content = self._generate_uc_init(uc, module_config)
        if self._create_file(uc_init_path, uc_init_content):
            created += 1
        else:
            skipped += 1
        
        # metadata.json
        metadata_path = uc_path / 'metadata.json'
        metadata_content = self._generate_uc_metadata(uc, module_config)
        if self._create_file(metadata_path, metadata_content):
            created += 1
        else:
            skipped += 1
        
        return created, skipped
    
    def _create_icon_structure(self):
        """Crea estructura de directorios para iconos."""
        self.stdout.write('\nCreando estructura de iconos...')
        
        icon_dirs = [
            Path('static/icons/menu'),
            Path('static/icons/submenu'),
            Path('static/icons/defaults'),
            Path('media/profiles'),
        ]
        
        for icon_dir in icon_dirs:
            self._create_directory(icon_dir)
        
        # Crear archivo .gitkeep para mantener directorios vacios
        for icon_dir in icon_dirs:
            gitkeep_path = icon_dir / '.gitkeep'
            if not gitkeep_path.exists() and not self.dry_run:
                gitkeep_path.touch()
    
    def _create_directory(self, path: Path) -> bool:
        """Crea un directorio."""
        if self.dry_run:
            if self.verbose:
                self.stdout.write(f"   [DRY-RUN] Crearia directorio: {path}")
            return True
        
        if path.exists():
            if self.verbose:
                self.stdout.write(f"   [SKIP] Directorio existe: {path}")
            return False
        
        path.mkdir(parents=True, exist_ok=True)
        if self.verbose:
            self.stdout.write(f"   [CREATE] {path}/")
        return True
    
    def _create_file(self, path: Path, content: str) -> bool:
        """Crea un archivo con contenido."""
        if self.dry_run:
            if self.verbose:
                self.stdout.write(f"   [DRY-RUN] Crearia archivo: {path}")
            return True
        
        if path.exists() and not self.force:
            if self.verbose:
                self.stdout.write(f"   [SKIP] Archivo existe: {path}")
            return False
        
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        
        if self.verbose:
            self.stdout.write(f"   [CREATE] {path}")
        return True
    
    def _generate_module_init(self, module_key: str, module_config: Dict) -> str:
        """Genera el __init__.py del modulo."""
        return f'''"""
{module_config['name']} - {module_config['description']}

App Django: apps/{module_config['app']}/
Casos de Uso: {module_config['uc_count']}
Funciones RBAC: {module_config['functions_count']}
Estado: {module_config['status']}
ID Menu: {module_config['menu_config']['id_menu']}

Version: UC v{self.VERSION_INFO['uc_version']}
"""

__version__ = "{self.VERSION_INFO['uc_version']}"

MODULE_INFO = {{
    'key': '{module_key}',
    'name': '{module_config['name']}',
    'app': '{module_config['app']}',
    'description': '{module_config['description']}',
    'uc_count': {module_config['uc_count']},
    'functions_count': {module_config['functions_count']},
    'status': '{module_config['status']}',
    'menu_id': {module_config['menu_config']['id_menu']},
}}
'''
    
    def _generate_module_readme(self, module_key: str, module_config: Dict) -> str:
        """Genera el README.md del modulo."""
        uc_list = '\n'.join([
            f"- {uc['id']}: {uc['title']}" + 
            (f" (Menu ID: {uc['menu']['id_menu']})" if uc.get('menu') else " (sin menu)")
            for uc in module_config['use_cases']
        ])
        
        return f'''# {module_config['name']} - {module_config['description']}

## Informacion General

- App Django: apps/{module_config['app']}/
- Casos de Uso: {module_config['uc_count']}
- Funciones RBAC: {module_config['functions_count']}
- Estado: {module_config['status']}
- ID Menu Nivel 1: {module_config['menu_config']['id_menu']}

## Casos de Uso

{uc_list}

## Version

- UC: v{self.VERSION_INFO['uc_version']}
- RBAC: v{self.VERSION_INFO['rbac_version']}

---

Generado automaticamente por create_modules command v{self.VERSION_INFO['command_version']}
'''
    
    def _generate_uc_init(self, uc: Dict, module_config: Dict) -> str:
        """Genera el __init__.py del UC."""
        functions_str = ', '.join([f'"{f}"' for f in uc['functions']])
        groups_str = ', '.join([f'"{g}"' for g in uc['groups']])
        cnst_str = ', '.join([f'"{c}"' for c in uc['cnst']])
        menu_id = uc.get('menu', {}).get('id_menu', None) if uc.get('menu') else None
        
        return f'''"""
{uc['id']}: {uc['title']}

Modulo: {module_config['name']}
App: apps/{module_config['app']}/
Menu ID: {menu_id if menu_id else 'N/A (sin menu)'}

Funciones RBAC: {', '.join(uc['functions'])}
Grupos: {', '.join(uc['groups'])}
CNST: {', '.join(uc['cnst']) if uc['cnst'] else 'Ninguna'}
"""

UC_INFO = {{
    'id': '{uc['id']}',
    'title': '{uc['title']}',
    'module': '{module_config['name']}',
    'app': '{module_config['app']}',
    'menu_id': {menu_id if menu_id else 'None'},
    'functions': [{functions_str}],
    'groups': [{groups_str}],
    'cnst': [{cnst_str}],
}}
'''
    
    def _generate_uc_metadata(self, uc: Dict, module_config: Dict) -> str:
        """Genera el metadata.json del UC."""
        metadata = {
            'uc_id': uc['id'],
            'title': uc['title'],
            'module': {
                'name': module_config['name'],
                'app': module_config['app'],
            },
            'rbac': {
                'functions': uc['functions'],
                'groups': uc['groups'],
            },
            'constraints': uc['cnst'],
            'navigation': uc.get('menu'),
            'version': {
                'uc': self.VERSION_INFO['uc_version'],
                'rbac': self.VERSION_INFO['rbac_version'],
            },
        }
        return json.dumps(metadata, indent=2, ensure_ascii=False)
    
    def _create_metadata_file(self):
        """Crea archivo de metadata general."""
        metadata_path = Path('modules') / 'MODULES_METADATA.json'
        
        metadata = {
            'version': self.VERSION_INFO,
            'id_schema': {
                'description': 'Esquema de IDs numericos',
                'nivel_1': '1-99 (menus principales)',
                'nivel_2': '100-999 (submenus, primer digito = modulo padre)',
                'ranges': {
                    'auth': {'menu': 1, 'submenus': '101-199'},
                    'users': {'menu': 2, 'submenus': '201-299'},
                    'access': {'menu': 3, 'submenus': '301-399'},
                    'pipeline': {'menu': 4, 'submenus': '401-499'},
                    'reports': {'menu': 5, 'submenus': '501-599'},
                    'alerts': {'menu': 6, 'submenus': '601-699'},
                    'audit': {'menu': 7, 'submenus': '701-799'},
                    'logs': {'menu': 8, 'submenus': '801-899'},
                }
            },
            'modules': {},
        }
        
        for module_key, module_config in self.MODULES_CONFIG.items():
            metadata['modules'][module_key] = {
                'name': module_config['name'],
                'app': module_config['app'],
                'description': module_config['description'],
                'uc_count': module_config['uc_count'],
                'functions_count': module_config['functions_count'],
                'status': module_config['status'],
                'menu_id': module_config['menu_config']['id_menu'],
                'menu_config': module_config['menu_config'],
                'use_cases': [
                    {
                        'id': uc['id'],
                        'title': uc['title'],
                        'has_menu': uc.get('menu') is not None,
                        'menu_id': uc['menu']['id_menu'] if uc.get('menu') else None,
                    }
                    for uc in module_config['use_cases']
                ],
            }
        
        content = json.dumps(metadata, indent=2, ensure_ascii=False)
        self._create_file(metadata_path, content)
