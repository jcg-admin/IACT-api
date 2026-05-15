"""
tests/unit/config/test_required_function_catalog.py

DT-REQUIRED-FUNCTION-001 — Regresión de required_function.

Verifica que toda vista con atributo required_function usa un código
que existe en el catálogo de funciones (Function). Detectó 4 vistas
con LOG-001 incorrecto en FASES 4/5.
"""
import importlib
import inspect
import pytest
from django.urls import get_resolver
from rest_framework.views import APIView


def _extract_views_with_required_function():
    """Recorre todas las URLs registradas y extrae las vistas con required_function."""
    resolver = get_resolver()
    results = []

    def _walk(r, prefix=''):
        for p in r.url_patterns:
            try:
                if hasattr(p, 'url_patterns'):
                    _walk(p, prefix + str(p.pattern))
                else:
                    callback = p.callback
                    # Desempaquetar as_view()
                    view_class = getattr(callback, 'view_class', None)
                    if view_class is None:
                        view_class = getattr(callback, 'cls', None)
                    if view_class and hasattr(view_class, 'required_function'):
                        rf = view_class.required_function
                        if rf:  # no vacío ni None
                            results.append({
                                'view': view_class.__name__,
                                'required_function': rf,
                                'url': prefix + str(p.pattern),
                            })
            except Exception:
                pass

    _walk(resolver)
    return results


@pytest.fixture(autouse=True)
def setup_function_catalog(db):
    """Poblar el catálogo de funciones antes de cada test."""
    from django.core.management import call_command
    from io import StringIO
    call_command('create_functions', stdout=StringIO())
    call_command('create_access_groups', stdout=StringIO())


@pytest.mark.django_db
class TestRequiredFunctionCatalog:

    def test_todas_las_vistas_usan_codigo_valido(self):
        """Toda vista con required_function usa un código existente en el catálogo."""
        from apps.access.models import Function

        valid_codes = set(Function.objects.values_list('code', flat=True))
        views = _extract_views_with_required_function()

        violations = []
        for v in views:
            rf = v['required_function']
            if rf not in valid_codes:
                violations.append(
                    f"{v['view']}.required_function = '{rf}' "
                    f"— código NO existe en catálogo. URL: {v['url']}"
                )

        assert violations == [], (
            f"DT-REQUIRED-FUNCTION-001: {len(violations)} vista(s) con "
            "required_function inválido:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_required_function_no_vacio(self):
        """Toda vista con required_function tiene un valor no vacío."""
        views = _extract_views_with_required_function()
        empty = [
            f"{v['view']}: required_function = '{v['required_function']}'"
            for v in views
            if not v['required_function'] or not v['required_function'].strip()
        ]
        assert empty == [], (
            "Vistas con required_function vacío:\n"
            + "\n".join(f"  - {e}" for e in empty)
        )

    def test_al_menos_N_vistas_con_required_function(self):
        """Sanity check: hay al menos 30 vistas con required_function registradas."""
        views = _extract_views_with_required_function()
        assert len(views) >= 30, (
            f"Solo {len(views)} vistas con required_function — "
            "el descubrimiento de URLs puede estar fallando."
        )
