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
        'name': 'RBAC',
        'description': (
            'Control de acceso basado en funciones: AccessGroup, SeparationRule, '
            'ExceptionalPermission. Endpoints compatibles con accessService.js de IACT-ui. '
            'UC_ACC_01..09, UC_PERM_01..10, UC_ADM_01..03.'
        ),
    },
]
