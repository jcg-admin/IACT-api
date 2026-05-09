from rest_framework import serializers
from apps.access.models import MenuItem


class MenuItemSerializer(serializers.ModelSerializer):
    """
    Serializer para MenuItem.

    CNST-032: MenuItem es wrapper UX sobre Function.
    El acceso lo controla Function — aquí solo se expone metadata visual.
    """

    function_code = serializers.CharField(source='function.code', read_only=True)
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = [
            'id',
            'function',
            'function_code',
            'display_label',
            'icon',
            'route',
            'order',
            'parent',
            'status',
            'deprecated_at',
            'archived_at',
            'children_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'deprecated_at', 'archived_at']

    def get_children_count(self, obj) -> int:
        return obj.children.count()


class MenuItemTreeSerializer(serializers.ModelSerializer):
    """
    Serializer anidado para representar el árbol completo de navegación.
    Solo incluye items ACTIVE.
    """

    children = serializers.SerializerMethodField()
    function_code = serializers.CharField(source='function.code', read_only=True)

    class Meta:
        model = MenuItem
        fields = [
            'id',
            'function_code',
            'display_label',
            'icon',
            'route',
            'order',
            'children',
        ]

    def get_children(self, obj):
        active_children = obj.children.filter(status=MenuItem.STATUS_ACTIVE).order_by('order')
        return MenuItemTreeSerializer(active_children, many=True).data
