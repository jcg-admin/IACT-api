"""
tests/unit/fase1/test_user_model_fields.py

Prerequisito de UC_AUTH_01, UC_AUTH_04, UC_USR_03.
Verifica que User tiene los campos canónicos del modelo-dominio-iact.rst.

Hallazgo F1-H-001: User.state, User.first_login, User.password_expires_at
y User.last_login_at no existían en el modelo.
"""
import pytest
from django.utils import timezone
from datetime import timedelta


@pytest.mark.django_db
class TestUserStateField:
    """User.state — enum ACTIVE/INACTIVE/BLOCKED (modelo-dominio § 4.1)."""

    def test_user_state_choices_exist(self):
        """User.state debe tener choices ACTIVE, INACTIVE, BLOCKED."""
        from apps.users.models import User
        field = User._meta.get_field('state')
        choices = [c[0] for c in field.choices]
        assert 'ACTIVE'   in choices
        assert 'INACTIVE' in choices
        assert 'BLOCKED'  in choices

    def test_user_created_with_active_state_by_default(self):
        """Usuarios creados con state=ACTIVE por defecto."""
        from apps.users.models import User
        user = User.objects.create_user(username='alice', password='Pass123!')
        assert user.state == 'ACTIVE'

    def test_user_state_inactive(self):
        """User puede tener state=INACTIVE (BR-009 baja lógica)."""
        from apps.users.models import User
        user = User.objects.create_user(
            username='bob', password='Pass123!', state='INACTIVE'
        )
        assert user.state == 'INACTIVE'

    def test_user_state_blocked(self):
        """User puede tener state=BLOCKED (BR-015: 5 intentos fallidos)."""
        from apps.users.models import User
        user = User.objects.create_user(
            username='carol', password='Pass123!', state='BLOCKED'
        )
        assert user.state == 'BLOCKED'


@pytest.mark.django_db
class TestUserFirstLoginField:
    """User.first_login — UC_AUTH_01 FA-01, UC_AUTH_04."""

    def test_user_first_login_true_by_default(self):
        """Nuevos usuarios tienen first_login=True (UC_USR_01 CA-01)."""
        from apps.users.models import User
        user = User.objects.create_user(username='dan', password='Pass123!')
        assert user.first_login is True

    def test_user_first_login_set_to_false(self):
        """first_login se puede poner en False (UC_AUTH_04 exitoso)."""
        from apps.users.models import User
        user = User.objects.create_user(
            username='eve', password='Pass123!', first_login=False
        )
        assert user.first_login is False


@pytest.mark.django_db
class TestUserPasswordExpiresAt:
    """User.password_expires_at — UC_AUTH_01 FA-02."""

    def test_password_expires_at_nullable(self):
        """password_expires_at es nullable — sin expiración si None."""
        from apps.users.models import User
        user = User.objects.create_user(username='frank', password='Pass123!')
        assert user.password_expires_at is None

    def test_password_expires_at_can_be_set(self):
        """password_expires_at puede configurarse."""
        from apps.users.models import User
        expires = timezone.now() + timedelta(days=90)
        user = User.objects.create_user(
            username='grace', password='Pass123!',
            password_expires_at=expires,
        )
        user.refresh_from_db()
        assert user.password_expires_at is not None


@pytest.mark.django_db
class TestUserLastLoginAt:
    """User.last_login_at — UC_AUTH_01 paso 14."""

    def test_last_login_at_nullable(self):
        """last_login_at es None antes del primer login."""
        from apps.users.models import User
        user = User.objects.create_user(username='henry', password='Pass123!')
        assert user.last_login_at is None

    def test_last_login_at_can_be_updated(self):
        """last_login_at se puede actualizar."""
        from apps.users.models import User
        user = User.objects.create_user(username='ivan', password='Pass123!')
        now = timezone.now()
        user.last_login_at = now
        user.save(update_fields=['last_login_at'])
        user.refresh_from_db()
        assert user.last_login_at is not None
