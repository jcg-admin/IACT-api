from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.conf import settings
import os
import logging

User = get_user_model()
from apps.users.serializers import UserSerializer, UserCreateSerializer

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestion usuarios.
    
    CRUD completo:
    - list: Listar usuarios
    - create: Crear usuario
    - retrieve: Detalle usuario
    - update: Actualizar usuario
    - destroy: Eliminar usuario
    
    CNST-005: Permisos IsAuthenticated.
    """
    
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Seleccionar serializer segun accion.
        
        - create: UserCreateSerializer (con password)
        - otros: UserSerializer (sin password)
        
        Returns:
            Serializer class
        """
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer


# =========================================================================
# AVATAR MANAGEMENT
# =========================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_avatar_view(request):
    """
    POST /api/users/upload-avatar/
    
    Sube o actualiza imagen de perfil del usuario autenticado.
    """
    user = request.user
    
    if 'avatar' not in request.FILES:
        return Response(
            {'error': 'No se envio ningun archivo'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    avatar_file = request.FILES['avatar']
    
    # Validar extension
    allowed_extensions = getattr(
        settings,
        'ALLOWED_IMAGE_EXTENSIONS',
        ['.jpg', '.jpeg', '.png', '.gif']
    )
    
    ext = os.path.splitext(avatar_file.name)[1].lower()
    if ext not in allowed_extensions:
        return Response(
            {
                'error': f"Extension no permitida. Use: {', '.join(allowed_extensions)}"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar tamaño
    max_size = getattr(settings, 'MAX_AVATAR_SIZE', 2 * 1024 * 1024)
    
    if avatar_file.size > max_size:
        max_mb = max_size / (1024 * 1024)
        return Response(
            {'error': f"Archivo muy grande. Maximo {max_mb}MB"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Eliminar avatar anterior si existe
    if user.avatar:
        try:
            old_avatar_path = user.avatar.path
            if os.path.exists(old_avatar_path):
                os.remove(old_avatar_path)
                logger.info(f"Avatar anterior eliminado: {old_avatar_path}")
        except Exception as e:
            logger.warning(f"Error eliminando avatar anterior: {e}")
    
    # Guardar nuevo avatar
    try:
        user.avatar = avatar_file
        user.save()
        
        logger.info(f"Avatar actualizado para usuario {user.username}")
        
        return Response(
            {
                'success': True,
                'avatar_url': user.get_avatar_url(),
                'message': 'Avatar actualizado correctamente'
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        logger.error(f"Error guardando avatar para {user.username}: {e}")
        return Response(
            {'error': 'Error guardando avatar'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_avatar_view(request):
    """
    DELETE /api/users/delete-avatar/
    
    Elimina avatar del usuario y establece el icono por defecto.
    """
    user = request.user
    
    try:
        deleted = user.delete_avatar()
        
        if deleted:
            logger.info(f"Avatar eliminado para usuario {user.username}")
            message = 'Avatar eliminado correctamente'
        else:
            logger.info(f"Usuario {user.username} no tenia avatar")
            message = 'No habia avatar para eliminar'
        
        return Response(
            {
                'success': True,
                'avatar_url': user.get_avatar_url(),
                'message': message
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        logger.error(f"Error eliminando avatar para {user.username}: {e}")
        return Response(
            {'error': 'Error eliminando avatar'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile_view(request):
    """
    GET /api/users/profile/
    
    Retorna perfil completo del usuario autenticado.
    """
    user = request.user
    
    try:
        functions = user.get_functions()
        
        profile_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name(),
            'avatar_url': user.get_avatar_url(),
            'position': user.position,
            'phone': user.phone,
            'employee_id': user.employee_id,
            'is_active': user.is_active,
            'created_at': user.date_joined.isoformat() if user.date_joined else None,
            'functions': functions,
        }
        
        logger.info(f"Perfil consultado por usuario {user.username}")
        
        return Response(profile_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error obteniendo perfil de {user.username}: {e}")
        return Response(
            {'error': 'Error obteniendo perfil'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_profile_view(request):
    """
    PUT /api/users/profile/
    
    Actualiza datos del perfil del usuario autenticado.
    """
    user = request.user
    
    allowed_fields = ['first_name', 'last_name', 'phone', 'position']
    
    try:
        updated_fields = []
        
        for field in allowed_fields:
            if field in request.data:
                setattr(user, field, request.data[field])
                updated_fields.append(field)
        
        if updated_fields:
            user.save()
            logger.info(f"Perfil actualizado para {user.username}: {', '.join(updated_fields)}")
            message = f"Perfil actualizado: {', '.join(updated_fields)}"
        else:
            message = 'No se enviaron campos para actualizar'
        
        profile_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name(),
            'avatar_url': user.get_avatar_url(),
            'position': user.position,
            'phone': user.phone,
            'employee_id': user.employee_id,
        }
        
        return Response(
            {
                'success': True,
                'message': message,
                'profile': profile_data
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        logger.error(f"Error actualizando perfil de {user.username}: {e}")
        return Response(
            {'error': 'Error actualizando perfil'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
