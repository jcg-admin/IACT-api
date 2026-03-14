"""
Serializers para CallNote (Notas de llamadas).

Responsabilidad: Serialización de notas sobre llamadas procesadas.

Serializers:
- CallNoteSerializer: Nota completa con información de usuario

Principios aplicados:
- SRP: Responsabilidad única (notas de llamadas)
- Clean Code: Campos enriched (username, full_name)
- FASE 0.2: Sistema de notas para llamadas procesadas
"""

from rest_framework import serializers
from apps.pipeline.models import CallNote


class CallNoteSerializer(serializers.ModelSerializer):
    """
    Serializer para CallNote.
    
    Permite crear/editar notas sobre CallRecords.
    El usuario se asigna automáticamente desde request.user.
    
    FASE 0.2: Sistema de notas para llamadas procesadas.
    """
    
    user_username = serializers.CharField(
        source='user.username',
        read_only=True
    )
    user_full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CallNote
        fields = [
            'id',
            'call_record',
            'user',
            'user_username',
            'user_full_name',
            'note',
            'is_important',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_user_full_name(self, obj):
        """
        Obtener nombre completo del usuario.
        
        Returns:
            str: first_name + last_name o username si no tiene nombre
        """
        if obj.user.first_name and obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return obj.user.username
