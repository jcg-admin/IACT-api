"""
tests/unit/access/test_separation_rule.py

N-001 — Tests unitarios de SeparationRule.
"""
import pytest
from django.db import IntegrityError
from django.db.models import Q

from apps.access.models import SeparationRule
from tests.test_data.access_test_data import (
    FunctionTestData,
    SeparationRuleTestData,
)


@pytest.mark.django_db
class TestSeparationRuleUniqueConstraint:
    """N-001-A: la misma dupla (function_a, function_b) no puede tener
    dos reglas activas simultáneamente."""

    def test_duplicate_pair_raises_integrity_error(self):
        fn_a = FunctionTestData()
        fn_b = FunctionTestData()
        SeparationRuleTestData(function_a=fn_a, function_b=fn_b)

        with pytest.raises(IntegrityError):
            SeparationRuleTestData(function_a=fn_a, function_b=fn_b)

    def test_reversed_pair_is_distinct_constraint(self):
        """(A, B) y (B, A) son constraints distintos en la DB.
        El modelo no normaliza el orden — la validación de negocio
        se hace en el serializer via check_conflict."""
        fn_a = FunctionTestData()
        fn_b = FunctionTestData()
        SeparationRuleTestData(function_a=fn_a, function_b=fn_b)

        # (B, A) no viola el constraint — son dos filas distintas
        rule_reversed = SeparationRuleTestData(
            function_a=fn_b, function_b=fn_a)
        assert rule_reversed.pk is not None


@pytest.mark.django_db
class TestSeparationRuleQuery:
    """N-001-B: consultas bidireccionales via Q."""

    def test_conflict_query_finds_direct_pair(self):
        fn_a = FunctionTestData()
        fn_b = FunctionTestData()
        rule = SeparationRuleTestData(function_a=fn_a, function_b=fn_b)

        found = SeparationRule.objects.filter(
            Q(function_a=fn_a, function_b=fn_b) |
            Q(function_a=fn_b, function_b=fn_a),
            status='active',
        ).first()

        assert found == rule

    def test_conflict_query_finds_reversed_pair(self):
        """La query bidireccional encuentra la regla sin importar el orden."""
        fn_a = FunctionTestData()
        fn_b = FunctionTestData()
        rule = SeparationRuleTestData(function_a=fn_a, function_b=fn_b)

        found = SeparationRule.objects.filter(
            Q(function_a=fn_b, function_b=fn_a) |
            Q(function_a=fn_a, function_b=fn_b),
            status='active',
        ).first()

        assert found == rule

    def test_inactive_rule_not_found_by_active_filter(self):
        fn_a = FunctionTestData()
        fn_b = FunctionTestData()
        SeparationRuleTestData(
            function_a=fn_a, function_b=fn_b, status='suspended')

        found = SeparationRule.objects.filter(
            Q(function_a=fn_a, function_b=fn_b) |
            Q(function_a=fn_b, function_b=fn_a),
            status='active',
        ).first()

        assert found is None
