"""
schema.py — apps.audit

Extensiones drf-spectacular para apps.audit.
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
        'name': 'Auditoria',
        'description': (
            'Logs de auditoria inmutables (CNST-009). Solo lectura. Registra login, logout, creacion, modificacion y eliminacion de recursos.'
        ),
    },
]
