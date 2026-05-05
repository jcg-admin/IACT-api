"""
schema.py — apps.alerts

Extensiones drf-spectacular para apps.alerts.
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
        'name': 'Alertas',
        'description': (
            'Mensajeria interna y alertas automaticas (APScheduler, CNST-004: sin Celery).'
        ),
    },
]
