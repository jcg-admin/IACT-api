"""
spectacular_hooks.py — config

Hook de postprocesamiento para drf-spectacular.
Aplica el principio Open/Closed al schema OpenAPI de IACT.

  CERRADO (base.py):
    SPECTACULAR_SETTINGS tiene solo configuracion global inmutable —
    titulo, version, componentes. No se toca al añadir nuevas apps.

  ABIERTO (schema.py de cada app):
    Cada app declara SPECTACULAR_TAGS con la descripcion de sus endpoints.
    El hook collect_app_tags() los agrega automaticamente al schema.

  Contrato del schema.py de cada app:
    SPECTACULAR_TAGS = [
        {
            'name': 'Usuarios',
            'description': 'Gestion de cuentas de usuario del sistema IACT.',
        },
    ]
    Solo se requiere el campo 'name'. 'description' es recomendado.
"""
import importlib
import logging

from django.apps import apps

logger = logging.getLogger(__name__)


def collect_app_tags(result, generator, **kwargs):
    """
    Agrega al schema los tags declarados en el schema.py de cada app.

    Registrado en SPECTACULAR_SETTINGS['POSTPROCESSING_HOOKS'].
    Si una app no tiene schema.py o no declara SPECTACULAR_TAGS,
    se ignora silenciosamente.
    """
    collected = []

    for app_config in apps.get_app_configs():
        if not app_config.name.startswith('apps.'):
            continue  # solo apps propias del proyecto

        try:
            module = importlib.import_module(f'{app_config.name}.schema')
        except ModuleNotFoundError:
            continue

        tags = getattr(module, 'SPECTACULAR_TAGS', None)
        if not tags:
            continue

        if not isinstance(tags, list):
            logger.warning(
                'SPECTACULAR_TAGS en %s.schema debe ser una lista, se ignora.',
                app_config.name,
            )
            continue

        collected.extend(tags)

    if collected:
        existing_names = {t['name'] for t in result.get('tags', [])}
        for tag in collected:
            if tag.get('name') and tag['name'] not in existing_names:
                result.setdefault('tags', []).append(tag)
                existing_names.add(tag['name'])

    return result
