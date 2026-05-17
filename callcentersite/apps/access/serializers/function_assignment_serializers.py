"""
Serializers para Asignación de Funciones RBAC v6.0.0.

Responsabilidad: Serialización de asignaciones de funciones a usuarios.

Serializers:
- UserFunctionAssignmentSerializer: Asignación completa con info enriched
- AssignFunctionSerializer: Input para asignar función a usuario
- RevokeFunctionSerializer: Input para revocar función de usuario
- MyFunctionsSerializer: Respuesta para endpoint /my-functions/

Principios aplicados:
- SRP: Responsabilidad única (asignaciones de funciones)
- RBAC v6.0.0: Gestión con namespaces
- Validation: Prevención de duplicados
- Clean Code: Campos enriched
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from apps.access.models import Function, UserFunctionAssignment

User = get_user_model()


class UserFunctionAssignmentSerializer(serializers.ModelSerializer):
    """
    Serializer para asignaciones de funciones a usuarios.

    RBAC v6.0.0: Gestión de asignaciones con namespaces.

    Incluye información enriquecida:
    - user_username: Username del usuario
    - user_full_name: Nombre completo del usuario
    - function_namespace: Namespace de la función (permission_django)
    - function_name: Nombre de la función
    - function_module: Módulo de la función
    - assigned_by_username: Username de quien asignó

    Read-only fields:
    - id, assigned_at
    - Relaciones enriched (user_username, etc)

    Examples:
        >>> assignment = UserFunctionAssignment.objects.first()
        >>> serializer = UserFunctionAssignmentSerializer(assignment)
        >>> serializer.data['function_namespace']
        'users.view'
        >>> serializer.data['is_active']
        True
    """

    user_username = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    function_namespace = serializers.CharField(
        source='function.permission_django',
        read_only=True
    )
    function_name = serializers.CharField(source='function.name', read_only=True)
    function_module = serializers.CharField(source='function.module', read_only=True)
    assigned_by_username = serializers.CharField(
        source='assigned_by.username',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = UserFunctionAssignment
        fields = [
            'id',
            'user',
            'user_username',
            'user_full_name',
            'function',
            'function_namespace',
            'function_name',
            'function_module',
            'assigned_at',
            'assigned_by',
            'assigned_by_username',
            'reason',
            'is_active',
        ]
        read_only_fields = [
            'id',
            'assigned_at',
            'assigned_by',
        ]


class AssignFunctionSerializer(serializers.Serializer):
    """
    Serializer para asignar función a usuario.

    Input:
    - user: ID del usuario (required)
    - function: ID de la función (required)
    - reason: Razón de la asignación (optional)

    Validations:
    - Usuario debe existir
    - Función debe existir y estar activa (status='activo')
    - No debe existir asignación activa duplicada

    Process:
    - Valida inputs
    - Crea UserFunctionAssignment
    - assigned_by se obtiene del request.user (en la view)

    Examples:
        >>> data = {
        ...     'user': 1,
        ...     'function': 2,
        ...     'reason': 'Usuario de soporte'
        ... }
        >>> serializer = AssignFunctionSerializer(data=data)
        >>> serializer.is_valid()
        True
    """

    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=True,
        help_text='ID del usuario'
    )
    function = serializers.PrimaryKeyRelatedField(
        queryset=Function.objects.filter(is_active=True, status='activo'),
        required=True,
        help_text='ID de la función (solo funciones activas)'
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        help_text='Razón de la asignación'
    )

    def validate(self, attrs):
        """
        Valida que no exista asignación activa duplicada.

        Previene duplicados de la misma función al mismo usuario.
        """
        user = attrs['user']
        function = attrs['function']

        # Verificar si ya existe asignación activa
        exists = UserFunctionAssignment.objects.filter(
            user=user,
            function=function,
            is_active=True
        ).exists()

        if exists:
            raise serializers.ValidationError({
                'function': f'Usuario ya tiene asignada la función {function.permission_django}'
            })

        return attrs


class RevokeFunctionSerializer(serializers.Serializer):
    """
    Serializer para revocar función de usuario.

    Input:
    - assignment: ID de la asignación (required)

    Validations:
    - Asignación debe existir
    - Asignación debe estar activa (is_active=True)

    Process:
    - Valida que assignment existe y está activa
    - Marca is_active=False (en la view)

    Examples:
        >>> data = {'assignment': 1}
        >>> serializer = RevokeFunctionSerializer(data=data)
        >>> serializer.is_valid()
        True
    """

    assignment = serializers.PrimaryKeyRelatedField(
        queryset=UserFunctionAssignment.objects.filter(is_active=True),
        required=True,
        help_text='ID de la asignación a revocar (solo asignaciones activas)'
    )


class MyFunctionsSerializer(serializers.Serializer):
    """
    Serializer para respuesta de /my-functions/.

    Retorna funciones del usuario autenticado.

    Fields:
    - functions: Lista de namespaces (permission_django)
    - count: Total de funciones activas
    - user: Datos básicos del usuario

    Examples:
        >>> data = {
        ...     'functions': ['users.view', 'calls.view'],
        ...     'count': 2,
        ...     'user': {'id': 1, 'username': 'john'}
        ... }
        >>> serializer = MyFunctionsSerializer(data)
        >>> serializer.data['functions']
        ['users.view', 'calls.view']
    """

    functions = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
        help_text='Lista de namespaces de funciones (permission_django)'
    )
    count = serializers.IntegerField(
        read_only=True,
        help_text='Total de funciones activas asignadas'
    )
    user = serializers.DictField(
        read_only=True,
        help_text='Datos básicos del usuario (id, username, full_name)'
    )
