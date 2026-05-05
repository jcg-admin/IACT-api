"""
tests/unit/config/test_spectacular_hooks.py

TDD — Principio Open/Closed aplicado a drf-spectacular.

Cubre:
  1. collect_app_tags — comportamiento del hook (unitario, sin BD)
  2. Contratos de SPECTACULAR_TAGS en cada apps/*/schema.py
  3. Integracion: POSTPROCESSING_HOOKS referencia al hook correcto

RED → GREEN → REFACTOR:
  Estos tests se escribieron para describir el comportamiento esperado
  del patron OCP implementado en:
    config/spectacular_hooks.py
    apps/*/schema.py
    config/settings/base.py  (POSTPROCESSING_HOOKS)
"""

import importlib
import types
import pytest


# =============================================================================
# 1. TESTS UNITARIOS DEL HOOK collect_app_tags
# =============================================================================

class TestCollectAppTagsHook:
    """
    Tests unitarios de config.spectacular_hooks.collect_app_tags.

    No requieren BD. El hook se prueba con mocks de la app registry
    de Django para aislar el comportamiento sin depender de la DB.
    """

    def _run_hook(self, app_configs, result=None):
        """Ejecuta el hook con una lista de AppConfig mockeados."""
        from config.spectacular_hooks import collect_app_tags

        if result is None:
            result = {}

        class MockGenerator:
            pass

        with pytest.MonkeyPatch.context() as mp:
            from django import apps as django_apps

            mp.setattr(
                django_apps.registry.Apps,
                'get_app_configs',
                lambda self: app_configs,
            )
            return collect_app_tags(result, MockGenerator())

    def _make_app_config(self, name, schema_module=None):
        """Crea un AppConfig mock con nombre y schema.py opcionales."""
        cfg = types.SimpleNamespace(name=name)

        if schema_module is not None:
            fake = types.ModuleType(f'{name}.schema')
            for attr, val in schema_module.items():
                setattr(fake, attr, val)
            import sys
            sys.modules[f'{name}.schema'] = fake

        return cfg

    # --- Comportamiento nominal ---

    def test_agrega_tags_de_app_propia(self):
        """Tags de una app 'apps.*' se añaden al schema."""
        from config.spectacular_hooks import collect_app_tags

        # Preparar schema.py simulado
        import sys
        fake = types.ModuleType('apps.testapp.schema')
        fake.SPECTACULAR_TAGS = [
            {'name': 'TestTag', 'description': 'Descripcion de prueba.'}
        ]
        sys.modules['apps.testapp.schema'] = fake

        try:
            app_cfg = types.SimpleNamespace(name='apps.testapp')
            result = {}

            with pytest.MonkeyPatch.context() as mp:
                from django.apps import apps as django_apps_registry
                mp.setattr(django_apps_registry, 'get_app_configs', lambda: [app_cfg])
                collect_app_tags(result, None)

            assert 'tags' in result
            assert any(t['name'] == 'TestTag' for t in result['tags'])
        finally:
            del sys.modules['apps.testapp.schema']

    def test_ignora_apps_externas(self):
        """Apps sin prefijo 'apps.' (django.contrib, etc.) se ignoran."""
        from config.spectacular_hooks import collect_app_tags
        import sys

        fake = types.ModuleType('django.contrib.auth.schema')
        fake.SPECTACULAR_TAGS = [{'name': 'NoDeberiaSalir'}]
        sys.modules['django.contrib.auth.schema'] = fake

        try:
            app_cfg = types.SimpleNamespace(name='django.contrib.auth')
            result = {}

            with pytest.MonkeyPatch.context() as mp:
                from django.apps import apps as django_apps_registry
                mp.setattr(django_apps_registry, 'get_app_configs', lambda: [app_cfg])
                collect_app_tags(result, None)

            assert 'tags' not in result or not any(
                t.get('name') == 'NoDeberiaSalir' for t in result.get('tags', [])
            )
        finally:
            del sys.modules['django.contrib.auth.schema']

    def test_ignora_app_sin_schema_py(self):
        """Apps sin schema.py no producen error y no añaden tags."""
        from config.spectacular_hooks import collect_app_tags

        app_cfg = types.SimpleNamespace(name='apps.sinschema')
        result = {}

        with pytest.MonkeyPatch.context() as mp:
            from django.apps import apps as django_apps_registry
            mp.setattr(django_apps_registry, 'get_app_configs', lambda: [app_cfg])
            collect_app_tags(result, None)

        assert 'tags' not in result

    def test_ignora_schema_sin_spectacular_tags(self):
        """schema.py sin SPECTACULAR_TAGS se ignora silenciosamente."""
        from config.spectacular_hooks import collect_app_tags
        import sys

        fake = types.ModuleType('apps.notagsapp.schema')
        # Sin SPECTACULAR_TAGS
        sys.modules['apps.notagsapp.schema'] = fake

        try:
            app_cfg = types.SimpleNamespace(name='apps.notagsapp')
            result = {}

            with pytest.MonkeyPatch.context() as mp:
                from django.apps import apps as django_apps_registry
                mp.setattr(django_apps_registry, 'get_app_configs', lambda: [app_cfg])
                collect_app_tags(result, None)

            assert 'tags' not in result
        finally:
            del sys.modules['apps.notagsapp.schema']

    def test_no_duplica_tags_por_nombre(self):
        """Un tag cuyo 'name' ya existe en result['tags'] no se añade de nuevo."""
        from config.spectacular_hooks import collect_app_tags
        import sys

        fake = types.ModuleType('apps.dupapp.schema')
        fake.SPECTACULAR_TAGS = [{'name': 'TagExistente', 'description': 'Nueva desc.'}]
        sys.modules['apps.dupapp.schema'] = fake

        try:
            app_cfg = types.SimpleNamespace(name='apps.dupapp')
            result = {'tags': [{'name': 'TagExistente', 'description': 'Original.'}]}

            with pytest.MonkeyPatch.context() as mp:
                from django.apps import apps as django_apps_registry
                mp.setattr(django_apps_registry, 'get_app_configs', lambda: [app_cfg])
                collect_app_tags(result, None)

            tags_con_nombre = [t for t in result['tags'] if t['name'] == 'TagExistente']
            assert len(tags_con_nombre) == 1, 'No debe haber duplicados'
        finally:
            del sys.modules['apps.dupapp.schema']

    def test_respeta_tags_preexistentes_en_result(self):
        """Tags ya presentes en result['tags'] no se pierden."""
        from config.spectacular_hooks import collect_app_tags
        import sys

        fake = types.ModuleType('apps.newapp.schema')
        fake.SPECTACULAR_TAGS = [{'name': 'NuevoTag'}]
        sys.modules['apps.newapp.schema'] = fake

        try:
            app_cfg = types.SimpleNamespace(name='apps.newapp')
            result = {'tags': [{'name': 'TagPrevio'}]}

            with pytest.MonkeyPatch.context() as mp:
                from django.apps import apps as django_apps_registry
                mp.setattr(django_apps_registry, 'get_app_configs', lambda: [app_cfg])
                collect_app_tags(result, None)

            nombres = {t['name'] for t in result['tags']}
            assert 'TagPrevio' in nombres
            assert 'NuevoTag' in nombres
        finally:
            del sys.modules['apps.newapp.schema']

    def test_spectacular_tags_no_lista_se_ignora(self):
        """
        SPECTACULAR_TAGS que no es list se ignora sin lanzar excepcion.

        El hook usa logging.warning (no stdlib warnings.warn),
        por lo que se verifica que: no lanza excepcion y no añade tags.
        """
        from config.spectacular_hooks import collect_app_tags
        import sys

        fake = types.ModuleType('apps.malapp.schema')
        fake.SPECTACULAR_TAGS = 'no soy una lista'
        sys.modules['apps.malapp.schema'] = fake

        try:
            app_cfg = types.SimpleNamespace(name='apps.malapp')
            result = {}

            with pytest.MonkeyPatch.context() as mp:
                from django.apps import apps as django_apps_registry
                mp.setattr(django_apps_registry, 'get_app_configs', lambda: [app_cfg])

                # No debe lanzar excepcion (hook robusto ante tipos incorrectos)
                collect_app_tags(result, None)

            assert 'tags' not in result, (
                'SPECTACULAR_TAGS invalido no debe añadir tags al schema'
            )
        finally:
            del sys.modules['apps.malapp.schema']

    def test_retorna_el_result_modificado(self):
        """El hook retorna el dict result (por convencion de drf-spectacular hooks)."""
        from config.spectacular_hooks import collect_app_tags

        result = {}

        with pytest.MonkeyPatch.context() as mp:
            from django.apps import apps as django_apps_registry
            mp.setattr(django_apps_registry, 'get_app_configs', lambda: [])
            returned = collect_app_tags(result, None)

        assert returned is result


# =============================================================================
# 2. CONTRATO DE SPECTACULAR_TAGS POR APP
# =============================================================================

APPS_CON_SCHEMA = [
    'apps.users',
    'apps.authentication',
    'apps.access',
    'apps.audit',
    'apps.pipeline',
    'apps.reports',
    'apps.alerts',
    'apps.dashboard',
]


class TestSpectacularTagsContrato:
    """
    Verifica que SPECTACULAR_TAGS en cada schema.py cumple el contrato:
      - Es una lista no vacía
      - Cada elemento es un dict con clave 'name'
      - 'name' es un string no vacío
      - No hay nombres duplicados dentro de la misma app
    """

    @pytest.mark.parametrize('app_name', APPS_CON_SCHEMA)
    def test_spectacular_tags_es_lista(self, app_name):
        """SPECTACULAR_TAGS debe ser una lista."""
        module = importlib.import_module(f'{app_name}.schema')
        tags = getattr(module, 'SPECTACULAR_TAGS', None)
        assert isinstance(tags, list), (
            f'{app_name}.schema.SPECTACULAR_TAGS debe ser una lista, '
            f'es {type(tags).__name__}'
        )

    @pytest.mark.parametrize('app_name', APPS_CON_SCHEMA)
    def test_spectacular_tags_no_esta_vacia(self, app_name):
        """SPECTACULAR_TAGS no debe ser una lista vacía."""
        module = importlib.import_module(f'{app_name}.schema')
        tags = getattr(module, 'SPECTACULAR_TAGS', [])
        assert len(tags) > 0, f'{app_name}.schema.SPECTACULAR_TAGS no puede ser vacía'

    @pytest.mark.parametrize('app_name', APPS_CON_SCHEMA)
    def test_cada_tag_tiene_name(self, app_name):
        """Cada tag debe tener la clave 'name'."""
        module = importlib.import_module(f'{app_name}.schema')
        for i, tag in enumerate(getattr(module, 'SPECTACULAR_TAGS', [])):
            assert 'name' in tag, (
                f'{app_name}.schema.SPECTACULAR_TAGS[{i}] no tiene clave "name"'
            )

    @pytest.mark.parametrize('app_name', APPS_CON_SCHEMA)
    def test_name_es_string_no_vacio(self, app_name):
        """El valor de 'name' debe ser un string no vacío."""
        module = importlib.import_module(f'{app_name}.schema')
        for i, tag in enumerate(getattr(module, 'SPECTACULAR_TAGS', [])):
            name = tag.get('name', '')
            assert isinstance(name, str) and name.strip(), (
                f'{app_name}.schema.SPECTACULAR_TAGS[{i}]["name"] '
                f'debe ser un string no vacío'
            )

    @pytest.mark.parametrize('app_name', APPS_CON_SCHEMA)
    def test_no_hay_nombres_duplicados_en_la_misma_app(self, app_name):
        """No debe haber dos tags con el mismo nombre en la misma app."""
        module = importlib.import_module(f'{app_name}.schema')
        tags = getattr(module, 'SPECTACULAR_TAGS', [])
        nombres = [t['name'] for t in tags if 'name' in t]
        assert len(nombres) == len(set(nombres)), (
            f'{app_name}.schema.SPECTACULAR_TAGS tiene nombres duplicados: '
            f'{[n for n in nombres if nombres.count(n) > 1]}'
        )


# =============================================================================
# 3. INTEGRACION: POSTPROCESSING_HOOKS apunta al hook correcto
# =============================================================================

class TestPostprocessingHooksIntegracion:
    """
    Verifica que SPECTACULAR_SETTINGS['POSTPROCESSING_HOOKS'] contiene
    la referencia al hook y que el hook es importable.
    """

    def test_postprocessing_hooks_contiene_collect_app_tags(self):
        """SPECTACULAR_SETTINGS debe incluir collect_app_tags."""
        from django.conf import settings
        hooks = settings.SPECTACULAR_SETTINGS.get('POSTPROCESSING_HOOKS', [])
        assert 'config.spectacular_hooks.collect_app_tags' in hooks, (
            'config.spectacular_hooks.collect_app_tags debe estar en '
            'SPECTACULAR_SETTINGS["POSTPROCESSING_HOOKS"]'
        )

    def test_hook_es_importable(self):
        """El modulo config.spectacular_hooks debe ser importable."""
        module = importlib.import_module('config.spectacular_hooks')
        assert hasattr(module, 'collect_app_tags'), (
            'config.spectacular_hooks debe exportar collect_app_tags'
        )

    def test_collect_app_tags_es_callable(self):
        """collect_app_tags debe ser una funcion callable."""
        from config.spectacular_hooks import collect_app_tags
        assert callable(collect_app_tags)

    def test_collect_app_tags_firma_compatible_con_spectacular(self):
        """collect_app_tags debe aceptar (result, generator, **kwargs) sin error."""
        from config.spectacular_hooks import collect_app_tags
        import inspect
        sig = inspect.signature(collect_app_tags)
        params = list(sig.parameters.keys())
        assert 'result' in params, 'El hook debe aceptar el parametro "result"'
        assert 'generator' in params, 'El hook debe aceptar el parametro "generator"'

    def test_base_py_no_contiene_tags_hardcodeados(self):
        """
        OCP: base.py no debe contener una clave 'TAGS' en SPECTACULAR_SETTINGS.
        Los tags viven exclusivamente en los schema.py de cada app.
        """
        from django.conf import settings
        assert 'TAGS' not in settings.SPECTACULAR_SETTINGS, (
            'SPECTACULAR_SETTINGS no debe contener "TAGS" hardcodeados. '
            'Los tags deben declararse en apps/*/schema.py via SPECTACULAR_TAGS.'
        )

    def test_todas_las_apps_propias_tienen_schema_py(self):
        """
        Todas las apps del proyecto (prefijo 'apps.') deben tener schema.py.
        Garantiza que ninguna app nueva quede sin documentar.
        """
        from django.apps import apps

        apps_sin_schema = []
        for app_config in apps.get_app_configs():
            if not app_config.name.startswith('apps.'):
                continue
            try:
                importlib.import_module(f'{app_config.name}.schema')
            except ModuleNotFoundError:
                apps_sin_schema.append(app_config.name)

        assert not apps_sin_schema, (
            f'Las siguientes apps no tienen schema.py: {apps_sin_schema}. '
            f'Crear el archivo con SPECTACULAR_TAGS = [] como minimo.'
        )
