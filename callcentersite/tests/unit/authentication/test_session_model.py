"""
tests/unit/fase1/test_session_model.py

Prerequisito de UC_AUTH_01 (BR-005 sesión única, CA-02).
Verifica el modelo Session canónico.

Hallazgo F1-H-002: SessionLog tenía estructura incorrecta para UC_AUTH_01.
El modelo canónico requiere state ACTIVE/CLOSED/EXPIRED, close_reason,
expires_at y client_info.
"""
import pytest
from datetime import timedelta
from django.utils import timezone


@pytest.mark.django_db
class TestSessionModel:
    """Session — modelo-dominio-iact.rst § 4.1."""

    def test_session_state_choices(self):
        """Session.state tiene ACTIVE, CLOSED, EXPIRED."""
        from apps.authentication.models import Session
        choices = [c[0] for c in Session._meta.get_field('state').choices]
        assert 'ACTIVE'  in choices
        assert 'CLOSED'  in choices
        assert 'EXPIRED' in choices

    def test_session_created_with_active_state(self, db):
        """Session creada con state=ACTIVE y expires_at=now+15min."""
        from apps.authentication.models import Session
        from apps.users.models import User

        user = User.objects.create_user(username='s_alice', password='Pass123!')
        session = Session.objects.create(
            user=user,
            state='ACTIVE',
            expires_at=timezone.now() + timedelta(minutes=15),
        )
        assert session.state == 'ACTIVE'
        assert session.session_id is not None  # UUID
        assert session.started_at is not None
        assert session.close_reason == ''

    def test_session_close_superseded(self, db):
        """BR-005: sesión previa transita ACTIVE → CLOSED con SUPERSEDED."""
        from apps.authentication.models import Session
        from apps.users.models import User

        user = User.objects.create_user(username='s_bob', password='Pass123!')
        session = Session.objects.create(
            user=user, state='ACTIVE',
            expires_at=timezone.now() + timedelta(minutes=15),
        )
        session.close(reason='SUPERSEDED')
        session.refresh_from_db()
        assert session.state == 'CLOSED'
        assert session.close_reason == 'SUPERSEDED'
        assert session.closed_at is not None

    def test_session_uniqueness_per_user(self, db):
        """BR-005: un usuario no debería tener 2 Sessions ACTIVE simultáneas."""
        from apps.authentication.models import Session
        from apps.users.models import User

        user = User.objects.create_user(username='s_carol', password='Pass123!')
        s1 = Session.objects.create(
            user=user, state='ACTIVE',
            expires_at=timezone.now() + timedelta(minutes=15),
        )
        # Simular login en otro dispositivo: cierra la anterior
        s1.close(reason='SUPERSEDED')
        s2 = Session.objects.create(
            user=user, state='ACTIVE',
            expires_at=timezone.now() + timedelta(minutes=15),
        )
        active = Session.objects.filter(user=user, state='ACTIVE').count()
        assert active == 1

    def test_session_client_info(self, db):
        """Session.client_info almacena datos del dispositivo."""
        from apps.authentication.models import Session
        from apps.users.models import User

        user = User.objects.create_user(username='s_dan', password='Pass123!')
        session = Session.objects.create(
            user=user, state='ACTIVE',
            expires_at=timezone.now() + timedelta(minutes=15),
            client_info={'device': 'iPhone 15', 'platform': 'iOS'},
        )
        session.refresh_from_db()
        assert session.client_info['device'] == 'iPhone 15'
