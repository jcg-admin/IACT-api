"""
Vistas para la gestion de usuarios, avatares y perfiles.
"""
import logging
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_avatar_view(request):
    """
    Sube o reemplaza el avatar del usuario autenticado.

    POST /api/users/avatar/upload/
    Content-Type: multipart/form-data
    Body: { avatar: <file> }
    """
    if 'avatar' not in request.FILES:
        return Response(
            {'error': 'Se requiere el campo "avatar"'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    file = request.FILES['avatar']
    allowed_extensions = getattr(settings, 'ALLOWED_IMAGE_EXTENSIONS', ['jpg', 'jpeg', 'png', 'gif', 'webp'])
    max_size = getattr(settings, 'MAX_AVATAR_SIZE', 2 * 1024 * 1024)

    ext = file.name.rsplit('.', 1)[-1].lower() if '.' in file.name else ''
    if ext not in allowed_extensions:
        return Response(
            {'error': f'Extension no permitida. Permitidas: {", ".join(allowed_extensions)}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if file.size > max_size:
        mb = max_size // (1024 * 1024)
        return Response(
            {'error': f'El archivo excede el tamanio maximo de {mb}MB'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = request.user
    if user.avatar:
        try:
            user.avatar.delete(save=False)
        except Exception as exc:
            # El archivo puede no existir en storage (borrado externo o CDN).
            # No es error fatal — continuar con la subida del nuevo avatar.
            logger.warning("avatar.delete() falló para user=%s: %s", user.pk, exc)

    user.avatar = file
    user.save(update_fields=['avatar'])

    return Response(
        {'avatar_url': user.get_avatar_url()},
        status=status.HTTP_200_OK,
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_avatar_view(request):
    """
    Elimina el avatar del usuario autenticado.

    DELETE /api/users/avatar/
    """
    user = request.user
    if not user.avatar:
        return Response(
            {'error': 'El usuario no tiene avatar'},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        user.avatar.delete(save=False)
    except Exception as exc:
        # El archivo puede haberse borrado del storage externamente.
        logger.warning("avatar.delete() falló para user=%s: %s", user.pk, exc)

    user.avatar = None
    user.save(update_fields=['avatar'])

    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile_view(request):
    """
    Retorna el perfil completo del usuario autenticado.

    GET /api/users/profile/
    """
    user = request.user
    data = {
        'id': user.pk,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.get_full_name(),
        'email': user.email,
        'phone': getattr(user, 'phone', ''),
        'avatar_url': user.get_avatar_url(),
        'is_active': user.is_active,
        'is_staff': user.is_staff,
        'date_joined': user.date_joined,
        'last_login': user.last_login,
        'functions': user.get_functions(),
    }
    return Response(data, status=status.HTTP_200_OK)
