"""
Serializer para Function.

accessService.getAllFunctions() espera:
  [{ id, code, name, description, category, permission_django, is_active }]

FunctionSelector.jsx usa: func.id, func.code, func.name,
  func.description, func.category
"""
from rest_framework import serializers
from apps.access.models import Function


class FunctionSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    module_code = serializers.CharField(
        source='module.code', read_only=True)

    class Meta:
        model = Function
        fields = [
            'id', 'code', 'name', 'description',
            'permission_django', 'is_active', 'status',
            'category', 'module_code',
        ]

    def get_category(self, obj):
        """
        Mapea el codigo del modulo a la categoria que espera FunctionSelector.
        FunctionSelector usa: PIPELINE, USUARIO, AUDITORIA, ACCESO,
        CONFIGURACION, DASHBOARD.
        """
        code_upper = obj.module.code.upper() if obj.module else ''
        mapping = {
            'PIPELINE': 'PIPELINE',
            'USERS':    'USUARIO',
            'USER':     'USUARIO',
            'AUDIT':    'AUDITORIA',
            'ACCESS':   'ACCESO',
            'CONFIG':   'CONFIGURACION',
            'DASHBOARD':'DASHBOARD',
            'ALERTS':   'CONFIGURACION',
            'LOGS':     'AUDITORIA',
            'REPORTS':  'DASHBOARD',
        }
        for key, val in mapping.items():
            if key in code_upper:
                return val
        return 'CONFIGURACION'
