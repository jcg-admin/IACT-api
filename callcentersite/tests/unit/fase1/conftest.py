"""Conftest para tests FASE 1."""
import pytest


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()
