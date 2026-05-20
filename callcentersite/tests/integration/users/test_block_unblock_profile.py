"""
Tests de integracion para UC_USR_05 (block), UC_USR_06 (unblock),
UC_USR_07 (editar perfil propio).

Cubre las CAs minimas declaradas en la iniciativa
``implementar-uc-usr-05-06-07-api``:

- CA-01 block transiciona state=BLOCKED + is_active=False + audit
- CA-02 unblock revierte solo si state=BLOCKED
- CA-03 self-block prohibido
- CA-04 idempotencia (BLOCKED->block / ACTIVE->unblock = noop)
- CA-05 patch /me/profile/ emite USER_PROFILE_UPDATED solo si cambia
- CA-06 alias /me/profile/ funcional
"""
import uuid

import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditLog

User = get_user_model()


@pytest.mark.django_db
class TestUserBlockUnblock:
    """UC_USR_05 / UC_USR_06."""

    def _make_user(self, **overrides):
        u = uuid.uuid4().hex[:6]
        defaults = {
            'username': f'usr_{u}',
            'email': f'usr_{u}@test.com',
            'password': 'Pass1234',
        }
        defaults.update(overrides)
        return User.objects.create_user(**defaults)

    def test_block_user_transiciona_a_blocked(self, admin_client):
        """CA-01: POST block -> state=BLOCKED + is_active=False + audit."""
        target = self._make_user()
        response = admin_client.post(f'/api/users/{target.pk}/block/')

        assert response.status_code == 200
        target.refresh_from_db()
        assert target.state == 'BLOCKED'
        assert target.is_active is False
        assert AuditLog.objects.filter(
            action='USER_BLOCKED',
            resource=f'User:{target.pk}',
        ).exists()

    def test_unblock_user_revierte_a_active(self, admin_client):
        """CA-02: unblock sobre BLOCKED -> ACTIVE + is_active=True."""
        target = self._make_user()
        target.state = 'BLOCKED'
        target.is_active = False
        target.save()

        response = admin_client.post(f'/api/users/{target.pk}/unblock/')

        assert response.status_code == 200
        target.refresh_from_db()
        assert target.state == 'ACTIVE'
        assert target.is_active is True
        assert AuditLog.objects.filter(
            action='USER_UNBLOCKED',
            resource=f'User:{target.pk}',
        ).exists()

    def test_self_block_prohibido(self, admin_client, admin_user):
        """CA-03: bloquearse a si mismo retorna 400."""
        response = admin_client.post(f'/api/users/{admin_user.pk}/block/')
        assert response.status_code == 400
        assert response.data.get('error') == 'SELF_BLOCK_FORBIDDEN'

    def test_block_idempotente(self, admin_client):
        """CA-04: block sobre BLOCKED no re-emite audit."""
        target = self._make_user()
        target.state = 'BLOCKED'
        target.save()
        before = AuditLog.objects.filter(action='USER_BLOCKED').count()

        response = admin_client.post(f'/api/users/{target.pk}/block/')

        assert response.status_code == 200
        after = AuditLog.objects.filter(action='USER_BLOCKED').count()
        assert after == before

    def test_unblock_sobre_active_es_noop(self, admin_client):
        """CA-04: unblock sobre ACTIVE no re-emite audit."""
        target = self._make_user()
        before = AuditLog.objects.filter(action='USER_UNBLOCKED').count()

        response = admin_client.post(f'/api/users/{target.pk}/unblock/')

        assert response.status_code == 200
        after = AuditLog.objects.filter(action='USER_UNBLOCKED').count()
        assert after == before


@pytest.mark.django_db
class TestEditOwnProfile:
    """UC_USR_07."""

    def test_patch_me_profile_emite_audit_si_cambia(self, api_client):
        """CA-05: PATCH /me/profile/ con cambio -> USER_PROFILE_UPDATED."""
        user = User.objects.create_user(
            username='u_self_07',
            email='u_self_07@test.com',
            password='Pass1234',
            first_name='Old',
        )
        api_client.force_authenticate(user=user)
        before = AuditLog.objects.filter(action='USER_PROFILE_UPDATED').count()

        response = api_client.patch(
            '/api/users/me/profile/',
            {'first_name': 'New'},
            format='json',
        )

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.first_name == 'New'
        after = AuditLog.objects.filter(action='USER_PROFILE_UPDATED').count()
        assert after == before + 1

    def test_patch_me_profile_no_audit_si_no_cambia(self, api_client):
        """CA-05: PATCH sin cambio efectivo no emite audit."""
        user = User.objects.create_user(
            username='u_self_07b',
            email='u_self_07b@test.com',
            password='Pass1234',
            first_name='Same',
        )
        api_client.force_authenticate(user=user)
        before = AuditLog.objects.filter(action='USER_PROFILE_UPDATED').count()

        response = api_client.patch(
            '/api/users/me/profile/',
            {'first_name': 'Same'},
            format='json',
        )

        assert response.status_code == 200
        after = AuditLog.objects.filter(action='USER_PROFILE_UPDATED').count()
        assert after == before

    def test_alias_profile_y_me_profile_son_equivalentes(self, api_client):
        """CA-06: ambos paths retornan el mismo perfil."""
        user = User.objects.create_user(
            username='u_self_07c',
            email='u_self_07c@test.com',
            password='Pass1234',
        )
        api_client.force_authenticate(user=user)

        a = api_client.get('/api/users/profile/').data
        b = api_client.get('/api/users/me/profile/').data
        assert a == b
