"""
schema.py — apps.logs

Extensiones drf-spectacular para apps.logs.

OCP: punto de extensión de la app para el schema OpenAPI.
Añadir aquí SPECTACULAR_TAGS sin modificar config/settings/base.py.
"""

# ─────────────────────────────────────────────────────────────────────
# SPECTACULAR_TAGS
# Recogidas automáticamente por config.spectacular_hooks.collect_app_tags
# ─────────────────────────────────────────────────────────────────────
SPECTACULAR_TAGS = [
    {
        'name': 'Registros del Sistema',
        'description': (
            'Logs del sistema: tail de Django y ETL, búsqueda, exportación, '
            'infraestructura, salud, métricas técnicas y eventos del pipeline analítico. '
            'UC_LOG_01..08. Fuente: archivos de log del sistema y MariaDB ivr_legacy.'
        ),
    },
]
