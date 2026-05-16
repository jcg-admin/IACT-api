"""
apps/users/profile_view.py

GET/PATCH /api/users/profile/  — perfil del usuario autenticado.
GET/PATCH /api/users/settings/ — configuraciones del usuario autenticado.

Los modelos UserProfile y UserSettings fueron integrados directamente en User
(FASE 4). Estos endpoints exponen los campos disponibles en el modelo User.
"""
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class UserProfileSerializer(serializers.Serializer):
    """
    Campos de perfil expuestos via GET/PATCH /api/users/profile/.
    Basado en los campos reales del modelo User (no UserProfile eliminado).
    """
    username    = serializers.CharField(read_only=True)
    email       = serializers.EmailField(read_only=True)
    first_name  = serializers.CharField(required=False, allow_blank=True)
    last_name   = serializers.CharField(required=False, allow_blank=True)
    avatar_url  = serializers.SerializerMethodField()

    def get_avatar_url(self, obj):
        if obj.avatar and hasattr(obj.avatar, 'url'):
            try:
                return obj.avatar.url
            except Exception:
                return None
        return None


class UserSettingsSerializer(serializers.Serializer):
    """
    Campos de configuración expuestos via GET/PATCH /api/users/settings/.
    Valores por defecto — la persistencia real requiere campos en User.
    """
    language              = serializers.ChoiceField(
        choices=['es', 'en'], default='es', required=False)
    theme                 = serializers.ChoiceField(
        choices=['light', 'dark', 'system'], default='light', required=False)
    timezone              = serializers.CharField(default='America/Mexico_City', required=False)
    notifications_enabled = serializers.BooleanField(default=True, required=False)

    def validate_timezone(self, value):
        import zoneinfo
        try:
            zoneinfo.ZoneInfo(value)
        except (zoneinfo.ZoneInfoNotFoundError, KeyError, Exception):
            raise serializers.ValidationError(
                f"Timezone inválido: '{value}'. Use el formato 'Continent/City'."
            )
        return value


class ProfileView(APIView):
    """
    GET /api/users/profile/  — retorna perfil del usuario autenticado.
    PATCH /api/users/profile/ — actualiza campos de perfil.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = request.user
        for field in ('first_name', 'last_name'):
            if field in serializer.validated_data:
                setattr(user, field, serializer.validated_data[field])
        user.save(update_fields=['first_name', 'last_name'])
        return Response(UserProfileSerializer(user).data)


class SettingsView(APIView):
    """
    GET /api/users/settings/  — retorna configuraciones del usuario autenticado.
    PATCH /api/users/settings/ — actualiza configuraciones.
    """
    permission_classes = [IsAuthenticated]

    # Clave usada para persistir settings en cache con TTL largo
    _CACHE_TTL = 86_400 * 7  # 7 días

    def _cache_key(self, user):
        return f'user_settings:{user.pk}'

    def _get_settings(self, user):
        from django.core.cache import cache
        defaults = {
            'language': 'es',
            'theme': 'light',
            'timezone': 'America/Mexico_City',
            'notifications_enabled': True,
        }
        stored = cache.get(self._cache_key(user)) or {}
        return {**defaults, **stored}

    def _save_settings(self, user, data):
        from django.core.cache import cache
        current = self._get_settings(user)
        current.update(data)
        cache.set(self._cache_key(user), current, self._CACHE_TTL)
        return current

    def get(self, request):
        settings = self._get_settings(request.user)
        return Response(settings)

    def patch(self, request):
        serializer = UserSettingsSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        settings = self._save_settings(request.user, serializer.validated_data)
        return Response(settings)


class AvatarUploadView(APIView):
    """
    POST   /api/users/profile/avatar/ — sube avatar.
    DELETE /api/users/profile/avatar/ — elimina avatar.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.users.serializers import AvatarUploadSerializer
        serializer = AvatarUploadSerializer(
            request.user, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        from apps.users.services.profile_service import ProfileService
        user = ProfileService().upload_avatar(
            user_id=request.user.pk,
            avatar_file=serializer.validated_data['avatar'],
            uploaded_by=request.user,
        )
        return Response(UserProfileSerializer(user).data)

    def delete(self, request):
        user = request.user
        if user.avatar:
            try:
                user.avatar.delete(save=True)
            except Exception:
                user.avatar = None
                user.save(update_fields=['avatar'])
        return Response(UserProfileSerializer(user).data)
