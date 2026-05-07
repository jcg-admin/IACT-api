"""
schema.py — apps.reports

Extensiones drf-spectacular para apps.reports.
Importado desde AppConfig.ready().

OCP: punto de extension de la app para el schema OpenAPI.
Anadir aqui OpenApiViewExtension, OpenApiSerializerExtension y
SPECTACULAR_TAGS sin modificar config/settings/base.py.
"""

# ─────────────────────────────────────────────────────────────────────
# SPECTACULAR_TAGS
# Recogidas automaticamente por config.spectacular_hooks.collect_app_tags
# ─────────────────────────────────────────────────────────────────────
SPECTACULAR_TAGS = [
    {
        'name': 'Reportes de Llamadas',
        'description': (
            'Reportes generados invocando SPs de MariaDB ivr_legacy: clientes, '
            'centros de transferencia, llamadas abandonadas, menus IVR. '
            'UC_RPT_12..17. CNST-003: READ-ONLY sobre ivr_legacy.'
        ),
    },
    {
        'name': 'Reportes',
        'description': (
            'Gestion, programacion y exportacion de reportes analiticos. UC_RPT_01..11.'
        ),
    },
]
