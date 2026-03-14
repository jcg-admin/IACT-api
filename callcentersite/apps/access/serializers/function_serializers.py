"""
Serializers para Funciones RBAC v6.0.0.

Responsabilidad: Serialización de funciones del sistema RBAC.

Serializers:
- FunctionSerializer: Función completa con todos los campos
- FunctionListSerializer: Función simplificada para listados

Principios aplicados:
- SRP: Responsabilidad única (funciones RBAC)
- RBAC v6.0.0: Uso de permission_django (namespaces)
- Clean Code: Nombres descriptivos y documentación

RBAC v6.0.0:
- permission_django: Namespace Django (PK funcional)
- Status: activo, planificado, deprecado
- Validaciones integradas
"""

from rest_framework import serializers
from apps.access.models import Function


class FunctionSerializer(serializers.ModelSerializer):
    """
    Serializer para funciones RBAC v6.0.0.
    
    RBAC v6.0.0: Usa permission_django (namespaces) como identificador.
    
    Read-only fields:
    - id, created_at, updated_at
    
    Fields:
    - permission_django: Namespace Django (PK funcional)
    - code: Código legacy (para compatibilidad)
    - module: Módulo al que pertenece
    - name: Nombre descriptivo
    - description: Descripción de la función
    - status: activo, planificado, deprecado
    - is_active: Activo/inactivo
    
    Examples:
        >>> func = Function.objects.get(permission_django='users.view')
        >>> serializer = FunctionSerializer(func)
        >>> serializer.data['permission_django']
        'users.view'
        >>> serializer.data['status']
        'activo'
    """
    
    class Meta:
        model = Function
        fields = [
            'id',
            'permission_django',
            'code',
            'module',
            'name',
            'description',
            'status',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FunctionListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listado de funciones.
    
    Solo incluye campos esenciales para listas.
    Optimizado para performance en listados grandes.
    """
    
    class Meta:
        model = Function
        # CLEAN CODE: Explicit is better than implicit (PEP 20)
        fields = (
            'id',
            'permission_django',
            'code',
            'name',
            'module',
            'status',
            'is_active',
        )
        # List views are typically read-only
        read_only_fields = fields
