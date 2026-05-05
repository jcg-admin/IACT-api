"""
schema.py — apps.authentication

Extensiones drf-spectacular para apps.authentication.
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
        'name': 'Autenticacion',
        'description': (
            'Login JWT, logout, cambio y recuperacion de contrasena. Cumple CNST-002 (sesiones en BD).'
        ),
    },
]
