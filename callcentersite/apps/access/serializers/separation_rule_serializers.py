"""
Serializers para SeparationRule.
C-002.

El ViewSet legacy (SeparationRuleViewSet) fue eliminado en STD_008 FASE 1
(2026-05-13). SeparationRuleSerializer permanece — es el serializer de
request usado en separation_rule_view.py (vistas canónicas FASE 2/3).

Endpoints canónicos:
  GET/POST  /api/access/separation-rules/         → SeparationRuleListCreateView
  GET/PATCH/DELETE /api/access/separation-rules/{id}/ → SeparationRuleDetailView
  POST      /api/access/separation-rules/validate → SeparationRuleValidateView

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
    Serializer de SeparationRule.

    Usado por las vistas canónicas (separation_rule_view.py) como
    serializer de validación de request en POST/PATCH.
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
