"""
Tests app ivr_legacy existe.
"""
import pytest


def test_ivr_legacy_app_importable():
    """App ivr_legacy debe ser importable."""
    from apps import ivr_legacy
    assert ivr_legacy is not None


def test_ivr_models_importable():
    """Modelos ivr_legacy deben ser importables."""
    from apps.ivr import models
    assert hasattr(models, '__file__')
