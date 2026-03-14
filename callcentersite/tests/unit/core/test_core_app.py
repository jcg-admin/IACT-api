"""
Tests app core existe.
"""
import pytest


def test_core_app_importable():
    """App core debe ser importable."""
    from apps import core
    assert core is not None


def test_core_models_importable():
    """Modelos core deben ser importables."""
    from apps.core import models
    assert hasattr(models, '__file__')
