"""
User views for the IACT API.
Includes avatar management and user profile endpoints.
"""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.validators import validate_avatar

User = get_user_model()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_avatar_view(request):
    """
    Upload or replace the authenticated user's avatar.

    POST /api/users/avatar/upload/
    Body: multipart/form-data with field 'avatar'
    """
    if 'avatar' not in request.FILES:
        return Response(
            {'detail': 'No se proporcionó ningún archivo. Use el campo "avatar".'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    image_file = request.FILES['avatar']

    try:
        validate_avatar(image_file)
    except Exception as exc:
        errors = exc.messages if hasattr(exc, 'messages') else [str(exc)]
        return Response({'detail': errors}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    if user.avatar:
        user.delete_avatar()

    user.avatar = image_file
    user.save(update_fields=['avatar'])

    return Response(
        {
            'detail': 'Avatar actualizado correctamente.',
            'avatar_url': user.get_avatar_url(),
        },
        status=status.HTTP_200_OK,
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_avatar_view(request):
    """
    Delete the authenticated user's avatar.

    DELETE /api/users/avatar/delete/
    """
    user = request.user

    if not user.avatar:
        return Response(
            {'detail': 'El usuario no tiene avatar.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    user.delete_avatar()

    return Response(
        {'detail': 'Avatar eliminado correctamente.'},
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile_view(request):
    """
    Return the authenticated user's profile data.

    GET /api/users/profile/
    """
    user = request.user

    data = {
        'id': user.pk,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.get_full_name(),
        'employee_id': user.employee_id,
        'department': user.department,
        'phone': user.phone,
        'avatar_url': user.get_avatar_url(),
        'is_active': user.is_active,
        'must_change_password': user.must_change_password,
        'date_joined': user.date_joined,
        'last_login': user.last_login,
        'functions': user.get_functions(),
    }

    return Response(data, status=status.HTTP_200_OK)
