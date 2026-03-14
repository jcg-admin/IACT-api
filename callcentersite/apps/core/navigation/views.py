"""
Navigation Views - API para menus dinamicos

Endpoint:
- GET /api/navigation/menu/ - Menu del usuario con IDs numericos
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import logging

from .builders import MenuBuilder, MenuSerializer

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_menu_view(request):
    """
    GET /api/navigation/menu/
    
    Retorna menu personalizado del usuario segun sus permisos RBAC.
    Todos los id_menu son numericos.
    
    Headers:
        Authorization: Bearer {token}
    
    Response 200:
        {
            "menu": [
                {
                    "id_menu": 5,
                    "des_name": "Reportes",
                    "icon": "/static/icons/menu/reports.png",
                    "nivel": 1,
                    "orden": 50,
                    "submenus": [...]
                }
            ],
            "user": {
                "username": "jperez",
                "full_name": "Juan Perez"
            }
        }
    """
    try:
        user = request.user
        
        # Construir menu
        builder = MenuBuilder()
        raw_menu = builder.build_user_menu(user)
        
        # Serializar para API
        serialized_menu = [
            MenuSerializer.serialize_menu(menu)
            for menu in raw_menu
        ]
        
        logger.info(f"Menu generado para usuario {user.username}: {len(serialized_menu)} items")
        
        return Response(
            {
                'menu': serialized_menu,
                'user': {
                    'username': user.username,
                    'full_name': user.get_full_name() or user.username,
                }
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        logger.error(f"Error generando menu para {request.user.username}: {e}")
        return Response(
            {'error': 'Error generando menu'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
