"""
Serializers para SeparationRule.
C-002.

FunctionSelector.jsx consume conflictos con estructura:
  { rule, ruleDesc, setA: [codes], setB: [codes], message }

El endpoint check retorna:
  { tiene_conflicto, regla }

El endpoint list (legacy ViewSet) retorna:
  [{ id, code, name, state,
     functions_set_a_codes, functions_set_b_codes,
     created_by, created_at }]

Hallazgo H-001 (STD_008 FASE 1, 2026-05-13):
  El serializer referenciaba function_a/function_b/justification/status
  que no existen en SeparationRule desde FASE 0 (modelo v5.4.0 usa
  functions_set_a/functions_set_b M2M y state en vez de status).
  Corregido para eliminar FieldError e ImproperlyConfigured en runtime.
"""
from rest_framework import serializers
from apps.access.models import SeparationRule


class SeparationRuleSerializer(serializers.ModelSerializer):
    """
    Serializer del ViewSet legacy de SeparationRule.

    El ViewSet está marcado como deprecated — supersedido por
    SeparationRuleListCreateView / SeparationRuleDetailView (FASE 2).
    """
    functions_set_a_codes = serializers.SerializerMethodField(
        help_text='Códigos de función del conjunto A.')
    functions_set_b_codes = serializers.SerializerMethodField(
        help_text='Códigos de función del conjunto B.')

    def get_functions_set_a_codes(self, obj) -> list[str]:
        return list(obj.functions_set_a.values_list('code', flat=True))

    def get_functions_set_b_codes(self, obj) -> list[str]:
        return list(obj.functions_set_b.values_list('code', flat=True))

    class Meta:
        model = SeparationRule
        fields = [
            'id', 'code', 'name', 'description', 'state',
            'functions_set_a_codes', 'functions_set_b_codes',
            'created_by', 'created_at',
        ]
        read_only_fields = ['created_by', 'created_at']


class SeparationRuleCheckSerializer(serializers.Serializer):
    """
    Respuesta del endpoint check.
    Estructura que consume FunctionSelector.jsx y SoDValidator.jsx:
      tiene_conflicto: bool
      regla: str | null
      conflicts: [{ rule, ruleDesc, setA, setB, message }]
    """
    tiene_conflicto = serializers.BooleanField()
    regla           = serializers.CharField(allow_null=True)
    conflicts       = serializers.ListField(child=serializers.DictField())
