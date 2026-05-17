"""
schema.py — apps.pipeline

Extensiones drf-spectacular para apps.pipeline.
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
        'name': 'Estado del Pipeline',
        'description': (
            'Estado, errores, disponibilidad de datos, reintento y rendimiento '
            'del pipeline ETL. Lee directamente de job_execution_log y '
            'v_etl_rendimiento en MariaDB ivr_legacy. '
            'UC_PIP_01..04. CNST-003: dual DB, CNST-004: sin Celery.'
        ),
    },
]
