"""
schema.py — apps.users

Extensiones drf-spectacular para apps.users.
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
        'name': 'Usuarios',
        'description': (
            'CRUD de cuentas de usuario. Incluye activacion, desactivacion y consulta del usuario autenticado (me).'
        ),
    },
    {
        'name': 'Perfil',
        'description': (
            'Perfil de usuario: bio, departamento y avatar.'
        ),
    },
    {
        'name': 'Configuracion',
        'description': (
            'Preferencias del usuario: idioma, zona horaria, notificaciones.'
        ),
    },
    {
        'name': 'Sesiones',
        'description': (
            'Historial de sesiones (lectura). Admin puede ver sesiones de cualquier usuario.'
        ),
    },
]
