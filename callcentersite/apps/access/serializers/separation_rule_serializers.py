"""
Serializers para SeparationRule.
C-002.

FunctionSelector.jsx consume conflictos con estructura:
  { rule, ruleDesc, setA: [codes], setB: [codes], message }

El endpoint check retorna:
  { tiene_conflicto, regla }

El endpoint list retorna:
  [{ id, name, function_a, function_a_code, function_b, function_b_code,
     justificacion, estado, creado_por }]
"""
from rest_framework import serializers
from apps.access.models import SeparationRule


class SeparationRuleSerializer(serializers.ModelSerializer):
    function_a_code = serializers.CharField(
        source='function_a.code', read_only=True)
    function_b_code = serializers.CharField(
        source='function_b.code', read_only=True)
    function_a_name = serializers.CharField(
        source='function_a.name', read_only=True)
    function_b_name = serializers.CharField(
        source='function_b.name', read_only=True)

    class Meta:
        model = SeparationRule
        fields = [
            'id', 'name',
            'function_a', 'function_a_code', 'function_a_name',
            'function_b', 'function_b_code', 'function_b_name',
            'justificacion', 'estado', 'creado_por',
        ]
        read_only_fields = ['creado_por']


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
