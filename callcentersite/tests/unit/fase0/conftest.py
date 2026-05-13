"""Conftest aislado para tests de FASE 0 — sin dependencias de mocks globales."""
import pytest


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()
