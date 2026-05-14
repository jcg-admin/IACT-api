"""Conftest para tests FASE 2."""
import pytest


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Admin con AGR-006 (user_admin_group)."""
    from apps.users.models import User
    from apps.access.models import AccessGroup, UserAccessGroup
    from django.core.management import call_command
    from io import StringIO
    call_command('create_functions', stdout=StringIO())
    call_command('create_access_groups', stdout=StringIO())
    user = User.objects.create_user(
        username='admin_f2', password='AdminPass123!',
        state='ACTIVE', first_login=False,
    )
    agr006 = AccessGroup.objects.get(code='AGR-006')
    UserAccessGroup.objects.create(user=user, access_group=agr006)
    return user


@pytest.fixture
def auth_client(api_client, admin_user):
    """APIClient autenticado como admin."""
    api_client.force_authenticate(user=admin_user)
    return api_client
