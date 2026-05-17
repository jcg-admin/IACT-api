"""
Vistas para el sistema de navegacion.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .builders import NavigationMenuAssembler
from drf_spectacular.utils import extend_schema


@extend_schema(tags=['navegacion'], responses={200: None})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def navigation_menu_view(request):
    """
    Retorna la estructura de navegacion para el usuario autenticado.
    """
    try:
        from apps.access.models import Module
        modules = Module.objects.filter(is_active=True).select_related('parent')
        builder = NavigationMenuAssembler()
        menu = builder.build_from_modules(modules, user=request.user)
        return Response({'menu': menu})
    except Exception as exc:
        return Response({'error': str(exc)}, status=500)


@extend_schema(tags=['navegacion'], responses={200: None})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def navigation_modules_view(request):
    """
    Retorna la lista plana de todos los modulos activos.
    """
    try:
        from apps.access.models import Module
        modules = Module.objects.filter(is_active=True).order_by('order')
        builder = NavigationMenuAssembler()
        flat = builder.build_flat(modules)
        return Response({'modules': flat})
    except Exception as exc:
        return Response({'error': str(exc)}, status=500)
