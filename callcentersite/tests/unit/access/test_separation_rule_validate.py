"""
tests/unit/access/test_separation_rule_validate.py

N-004 — Tests del endpoint de validación de conflictos de separación.
POST /api/access/separation-rules/validate

Reemplaza test_separation_rule_viewset.py (STD_008 FASE 1, 2026-05-13):
  El endpoint GET /check/ del ViewSet deprecated fue eliminado.
  El endpoint canónico es POST /api/access/separation-rules/validate.

Estructura de respuesta:
  { conflicts: [{ rule, ruleDesc, setA, setB, message }] }
  Lista vacía → sin conflictos.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.access.models import SeparationRule, UserFunctionAssignment
from tests.test_data.access_test_data import (
    FunctionTestData,
    SeparationRuleTestData,
)
from tests.test_data.user_test_data import AdminUserTestData, UserTestData


@pytest.fixture
def admin_client(db):
    """APIClient autenticado como superusuario — bypassa restricciones RBAC."""
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def target_user(db):
    """Usuario objetivo al que se le evaluará la asignación."""
    return UserTestData()


def _validate_url():
    return reverse('access:separation-rule-validate')


@pytest.mark.django_db
class TestSeparationRuleValidateEndpoint:
    """N-004: POST /api/access/separation-rules/validate"""

    def test_detecta_conflicto_cuando_usuario_tiene_funcion_de_set_a(
            self, admin_client, target_user):
        """
        Usuario ya tiene función del set_a de una regla ENABLED.
        Proponer función del set_b → conflicts no vacío.
        """
        client, _ = admin_client
        fa = FunctionTestData()
        fb = FunctionTestData()
        rule = SeparationRuleTestData()
        rule.functions_set_a.set([fa])
        rule.functions_set_b.set([fb])

        # El usuario objetivo ya tiene la función del set_a
        UserFunctionAssignment.objects.create(
            user=target_user, function=fa, state='ACTIVE', assigned_by=None)

        response = client.post(
            _validate_url(),
            {'userId': target_user.pk, 'functionId': fb.pk},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['conflicts']) == 1
        assert response.data['conflicts'][0]['rule'] == rule.code

    def test_detecta_conflicto_en_orden_inverso(self, admin_client, target_user):
        """
        Usuario ya tiene función del set_b.
        Proponer función del set_a → conflicto igualmente detectado.
        """
        client, _ = admin_client
        fa = FunctionTestData()
        fb = FunctionTestData()
        rule = SeparationRuleTestData()
        rule.functions_set_a.set([fa])
        rule.functions_set_b.set([fb])

        UserFunctionAssignment.objects.create(
            user=target_user, function=fb, state='ACTIVE', assigned_by=None)

        response = client.post(
            _validate_url(),
            {'userId': target_user.pk, 'functionId': fa.pk},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['conflicts']) == 1

    def test_sin_conflicto_cuando_no_hay_regla(self, admin_client, target_user):
        """Sin reglas de separación → lista vacía."""
        client, _ = admin_client
        fa = FunctionTestData()
        fb = FunctionTestData()
        # Ninguna SeparationRule creada

        UserFunctionAssignment.objects.create(
            user=target_user, function=fa, state='ACTIVE', assigned_by=None)

        response = client.post(
            _validate_url(),
            {'userId': target_user.pk, 'functionId': fb.pk},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['conflicts'] == []

    def test_regla_disabled_no_genera_conflicto(self, admin_client, target_user):
        """state=DISABLED → la regla no participa en la validación."""
        client, _ = admin_client
        fa = FunctionTestData()
        fb = FunctionTestData()
        rule = SeparationRuleTestData(state=SeparationRule.STATE_DISABLED)
        rule.functions_set_a.set([fa])
        rule.functions_set_b.set([fb])

        UserFunctionAssignment.objects.create(
            user=target_user, function=fa, state='ACTIVE', assigned_by=None)

        response = client.post(
            _validate_url(),
            {'userId': target_user.pk, 'functionId': fb.pk},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['conflicts'] == []

    def test_sin_conflicto_cuando_usuario_no_tiene_funciones(
            self, admin_client, target_user):
        """Usuario sin asignaciones activas → ningún conflicto posible."""
        client, _ = admin_client
        fa = FunctionTestData()
        fb = FunctionTestData()
        rule = SeparationRuleTestData()
        rule.functions_set_a.set([fa])
        rule.functions_set_b.set([fb])
        # No se crean asignaciones para target_user

        response = client.post(
            _validate_url(),
            {'userId': target_user.pk, 'functionId': fb.pk},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['conflicts'] == []

    def test_asignacion_revocada_no_participa(self, admin_client, target_user):
        """Asignaciones con state=REVOKED no se consideran activas."""
        client, _ = admin_client
        fa = FunctionTestData()
        fb = FunctionTestData()
        rule = SeparationRuleTestData()
        rule.functions_set_a.set([fa])
        rule.functions_set_b.set([fb])

        UserFunctionAssignment.objects.create(
            user=target_user, function=fa, state='REVOKED', assigned_by=None)

        response = client.post(
            _validate_url(),
            {'userId': target_user.pk, 'functionId': fb.pk},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['conflicts'] == []

    def test_requiere_userId_y_functionId(self, admin_client):
        """Payload incompleto → 400."""
        client, _ = admin_client
        response = client.post(
            _validate_url(),
            {'userId': 1},
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_usuario_inexistente_retorna_404(self, admin_client):
        """userId que no existe en BD → 404."""
        client, _ = admin_client
        fn = FunctionTestData()
        response = client.post(
            _validate_url(),
            {'userId': 999999, 'functionId': fn.pk},
            format='json',
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_estructura_de_conflicto_contiene_campos_requeridos(
            self, admin_client, target_user):
        """Cada item de conflicts tiene rule, ruleDesc, setA, setB, message."""
        client, _ = admin_client
        fa = FunctionTestData()
        fb = FunctionTestData()
        rule = SeparationRuleTestData()
        rule.functions_set_a.set([fa])
        rule.functions_set_b.set([fb])

        UserFunctionAssignment.objects.create(
            user=target_user, function=fa, state='ACTIVE', assigned_by=None)

        response = client.post(
            _validate_url(),
            {'userId': target_user.pk, 'functionId': fb.pk},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        conflict = response.data['conflicts'][0]
        assert 'rule'     in conflict
        assert 'ruleDesc' in conflict
        assert 'setA'     in conflict
        assert 'setB'     in conflict
        assert 'message'  in conflict
