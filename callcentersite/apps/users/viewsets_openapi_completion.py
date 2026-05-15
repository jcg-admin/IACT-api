"""
# Código para completar decoradores de ProfileViewSet y SettingsViewSet

# ProfileViewSet - update_profile
@extend_schema(
    summary="Actualizar perfil",
    description="Actualiza bio y/o department del perfil del usuario autenticado.",
    tags=['Perfil'],
    request=UserProfileSerializer,
    responses={200: UserProfileSerializer},
)

# ProfileViewSet - upload_avatar
@extend_schema(
    summary="Subir avatar",
    description="Sube una imagen de avatar. Formatos permitidos: jpg, png, gif. Máximo 2MB.",
    tags=['Perfil'],
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'avatar': {
                    'type': 'string',
                    'format': 'binary',
                }
            }
        }
    },
    responses={
        200: OpenApiResponse(description="Avatar subido exitosamente"),
        400: OpenApiResponse(description="Formato o tamaño inválido"),
    },
)

# ProfileViewSet - remove_avatar
@extend_schema(
    summary="Eliminar avatar",
    description="Elimina el avatar del usuario autenticado.",
    tags=['Perfil'],
    request=None,
    responses={200: OpenApiResponse(description="Avatar eliminado exitosamente")},
)

# SettingsViewSet - settings (GET)
@extend_schema(
    summary="Obtener configuración",
    description="Retorna la configuración del usuario autenticado.",
    tags=['Configuración'],
    responses={200: UserSettingsSerializer},
)

# SettingsViewSet - update_settings
@extend_schema(
    summary="Actualizar configuración",
    description="Actualiza la configuración del usuario autenticado.",
    tags=['Configuración'],
    request=UserSettingsSerializer,
    responses={200: UserSettingsSerializer},
)

# SessionHistoryViewSet
@extend_schema_view(
    list=extend_schema(
        summary="Lista sesiones",
        description="Retorna historial de sesiones del usuario autenticado. Admin ve todas si especifica user_id.",
        tags=['Sesiones'],
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID de usuario (solo admin)',
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Detalle de sesión",
        description="Retorna detalles de una sesión específica.",
        tags=['Sesiones'],
    ),
)
"""
# Este archivo es una referencia de decoradores, no un módulo ejecutable.
