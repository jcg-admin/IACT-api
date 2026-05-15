"""
Serializers para Módulos.

Responsabilidad: Serialización de módulos del sistema.

Serializers:
- ModuleSerializer: Módulo con información de jerarquía
- ModuleTreeSerializer: Módulo en estructura de árbol recursiva
- MyModulesSerializer: Respuesta para endpoint /my-modules/

Principios aplicados:
- SRP: Un archivo por responsabilidad (módulos)
- Clean Code: Nombres descriptivos
- DRY: Reutilización de lógica
"""

from rest_framework import serializers
from apps.access.models import Module
from drf_spectacular.utils import extend_schema_field, OpenApiTypes


class ModuleSerializer(serializers.ModelSerializer):
    """
    Serializer para módulos.
    
    Incluye información de jerarquía y estado.
    """
    
    parent_code = serializers.CharField(source='parent.code', read_only=True, allow_null=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)
    children_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = [
            'id',
            'code',
            'name',
            'parent',
            'parent_code',
            'parent_name',
            'order',
            'icon',
            'is_active',
            'children_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_children_count(self, obj):
        """Contar hijos directos activos."""
        return obj.children.filter(is_active=True).count()


class ModuleTreeSerializer(serializers.ModelSerializer):
    """
    Serializer para módulos en estructura de árbol.
    
    Incluye hijos anidados recursivamente.
    """
    
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = [
            'id',
            'code',
            'name',
            'icon',
            'order',
            'is_active',
            'children',
        ]
    
    def get_children(self, obj):
        """
        Retorna los hijos del módulo respetando el filtro de acceso.

        Si el servicio adjuntó _accessible_children (lista prefiltrada
        por UserModuleAccess del usuario), usa esa lista.
        Si no existe (uso genérico del serializer), consulta todos
        los hijos activos.
        """
        if hasattr(obj, '_accessible_children'):
            # Lista prefiltrada por ModuleAccessService.get_user_module_tree()
            # Solo contiene hijos a los que el usuario tiene acceso.
            return ModuleTreeSerializer(
                obj._accessible_children, many=True,
                context=self.context,
            ).data
        # Uso genérico (sin filtro de acceso): todos los hijos activos
        children = obj.children.filter(is_active=True).order_by('order', 'code')
        return ModuleTreeSerializer(
            children, many=True, context=self.context).data


class MyModulesSerializer(serializers.Serializer):
    """
    Serializer para respuesta de /my-modules/.
    
    Retorna módulos accesibles por el usuario en estructura de árbol.
    """
    
    modules = ModuleTreeSerializer(many=True, read_only=True)
    total_count = serializers.IntegerField(read_only=True)
    root_count = serializers.IntegerField(read_only=True)
