"""
tests/unit/access/test_separation_rule.py

N-001 — Tests unitarios de SeparationRule (modelo v5.4.0).

El modelo v5.4.0 usa ManyToManyField para los dos conjuntos de funciones
en conflicto. El modelo v5.2.1 usaba FKs binarios (function_a, function_b);
esos campos ya no existen.

Hallazgo FASE 1 (2026-05-13):
  Los tests originales usaban SeparationRuleTestData(functions_set_a=...) y
  Q(functions_set_a=..., status='active') — campos inexistentes en v5.4.0.
  Reescritos para el modelo actual.
"""
import pytest
from django.db import IntegrityError

from apps.access.models import SeparationRule
from tests.test_data.access_test_data import (
    FunctionTestData,
    SeparationRuleTestData,
)


@pytest.mark.django_db
class TestSeparationRuleCodeConstraint:
    """N-001-A: el campo code tiene unique=True."""

    def test_duplicate_code_raises_integrity_error(self):
        SeparationRuleTestData(code='UNIQ-001')
        with pytest.raises(Exception):
            with __import__("django.db", fromlist=["transaction"]).db.transaction.atomic():
                SeparationRuleTestData(code='UNIQ-001')

    def test_distinct_codes_coexist(self):
        r1 = SeparationRuleTestData(code='UNIQ-001')
        r2 = SeparationRuleTestData(code='UNIQ-002')
        assert r1.pk != r2.pk


@pytest.mark.django_db
class TestSeparationRuleIsViolatedBy:
    """N-001-B: SeparationRule.is_violated_by() detecta violaciones M2M."""

    def _make_rule(self):
        fa = FunctionTestData()
        fb = FunctionTestData()
        rule = SeparationRuleTestData()
        rule.functions_set_a.set([fa])
        rule.functions_set_b.set([fb])
        return rule, fa, fb

    def test_violated_when_user_has_functions_from_both_sets(self):
        """Usuario con funciones de set_a Y set_b → violación."""
        rule, fa, fb = self._make_rule()
        assert rule.is_violated_by({fa.code, fb.code}) is True

    def test_not_violated_when_user_only_has_set_a(self):
        """Usuario con funciones solo de set_a → sin violación."""
        rule, fa, fb = self._make_rule()
        assert rule.is_violated_by({fa.code}) is False

    def test_not_violated_when_user_only_has_set_b(self):
        """Usuario con funciones solo de set_b → sin violación."""
        rule, fa, fb = self._make_rule()
        assert rule.is_violated_by({fb.code}) is False

    def test_not_violated_when_no_overlap(self):
        """Funciones que no pertenecen a ningún conjunto → sin violación."""
        rule, fa, fb = self._make_rule()
        other = FunctionTestData()
        assert rule.is_violated_by({other.code}) is False

    def test_not_violated_when_rule_disabled(self):
        """state=DISABLED desactiva la regla — nunca viola."""
        rule, fa, fb = self._make_rule()
        rule.state = SeparationRule.STATE_DISABLED
        rule.save(update_fields=['state'])
        assert rule.is_violated_by({fa.code, fb.code}) is False


@pytest.mark.django_db
class TestSeparationRuleFindConflict:
    """N-001-C: SeparationRule.find_conflict() retorna el par conflictivo."""

    def _make_rule(self):
        fa = FunctionTestData()
        fb = FunctionTestData()
        rule = SeparationRuleTestData()
        rule.functions_set_a.set([fa])
        rule.functions_set_b.set([fb])
        return rule, fa, fb

    def test_returns_conflict_pair_when_violated(self):
        rule, fa, fb = self._make_rule()
        result = rule.find_conflict({fa.code, fb.code})
        assert result is not None
        assert set(result) == {fa.code, fb.code}

    def test_returns_none_when_not_violated(self):
        rule, fa, fb = self._make_rule()
        # Solo set_a — no hay violación
        result = rule.find_conflict({fa.code})
        assert result is None

    def test_returns_none_when_rule_disabled(self):
        rule, fa, fb = self._make_rule()
        rule.state = SeparationRule.STATE_DISABLED
        rule.save(update_fields=['state'])
        result = rule.find_conflict({fa.code, fb.code})
        assert result is None

    def test_symmetric_detection(self):
        """El conflicto se detecta sin importar el orden de los códigos."""
        rule, fa, fb = self._make_rule()
        result_ab = rule.find_conflict({fa.code, fb.code})
        result_ba = rule.find_conflict({fb.code, fa.code})
        assert result_ab is not None
        assert result_ba is not None
        assert set(result_ab) == set(result_ba)
