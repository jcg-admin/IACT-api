"""Navigation API views."""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.navigation.builders import NavigationBuilder


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_navigation_view(request):
    """
    Return the navigation menu for the authenticated user.

    GET /api/navigation/
    """
    navigation = NavigationBuilder.for_user(request.user)
    return Response({'navigation': navigation}, status=status.HTTP_200_OK)
