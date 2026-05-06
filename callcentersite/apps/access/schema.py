"""
schema.py — apps.access

Extensiones drf-spectacular para apps.access.
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
        'name': 'Acceso',
        'description': (
            'Control de acceso RBAC v6.0.0: asignacion y revocacion de modulos y funciones por usuario.'
        ),
    },
]
