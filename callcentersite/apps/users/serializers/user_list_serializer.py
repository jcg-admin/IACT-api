"""
apps/users/serializers/user_list_serializer.py

Serializers canónicos de UC_USR_02 — Consultar Usuarios.

Fuente: uc-usr-02/datos-involucrados.rst § 7.3 (listado) y § 7.4 (detalle)

UserListSerializer  — GET /api/users/   (CA-01: paginado, CA-02: PII restringido)
UserDetailSerializer — GET /api/users/{id}/ (CA-03: detalle con email completo)

Hallazgo F1-H-006:
  - UserListSerializer anterior exponía email completo (violación CNST-026).
  - No tenía campo 'state' ni 'last_login_at' (campos canónicos del modelo).
  - No era el serializer usado por el endpoint registrado en urls.py.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


def _mask_email(email: str) -> str:
    """
    CNST-026: enmascara email en listados.
    'ana.gomez@empresa.com' → 'a***@empresa.com'
    Formato: primer_carácter + '***' + '@' + dominio.
    """
    if not email or '@' not in email:
        return '***'
    local, domain = email.split('@', 1)
    return f'{local[0]}***@{domain}' if local else f'***@{domain}'


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer de listado — UC_USR_02 CA-01 / CA-02.

    CNST-026: email mascarado (email_masked).
    Incluye: id, username, email_masked, full_name_initials, state,
             created_at, last_login_at, active_agr_ids.
    Excluye: email completo, password_hash, first_name, last_name.

    Fuente: uc-usr-02/datos-involucrados.rst § 7.3
    """

    email_masked = serializers.SerializerMethodField(
        help_text='Email enmascarado (CNST-026). Ej: a***@empresa.com',
    )
    full_name_initials = serializers.SerializerMethodField(
        help_text='Iniciales del nombre completo. Ej: AG',
    )
    active_agr_ids = serializers.SerializerMethodField(
        help_text='IDs numéricos de AccessGroups activos del usuario.',
    )
    created_at = serializers.DateTimeField(
        source='date_joined',
        read_only=True,
        help_text='Fecha de creación de la cuenta.',
    )

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email_masked',
            'full_name_initials',
            'state',
            'created_at',
            'last_login_at',
            'active_agr_ids',
        )
        read_only_fields = fields

    def get_email_masked(self, obj) -> str:
        return _mask_email(obj.email or '')

    def get_full_name_initials(self, obj) -> str:
        """Iniciales: 'Ana Gomez' → 'AG'. Si no hay nombre, usa username[0].upper()."""
        first = (obj.first_name or '').strip()
        last  = (obj.last_name  or '').strip()
        if first and last:
            return f'{first[0].upper()}{last[0].upper()}'
        if first:
            return first[0].upper()
        return obj.username[0].upper() if obj.username else '?'

    def get_active_agr_ids(self, obj) -> list[int]:
        """IDs de AccessGroups activos. Mínimo N+1 para evitar N+1 queries."""
        try:
            from apps.access.models import UserAccessGroup
            return list(
                UserAccessGroup.objects.filter(user=obj)
                .values_list('access_group_id', flat=True)
            )
        except Exception:
            return []


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Serializer de detalle — UC_USR_02 CA-03.

    Email completo visible (invocante tiene view_users — privilegio suficiente).
    Incluye: email completo, state, first_login, Assignments activos.
    Excluye: password, password_hash.

    Fuente: uc-usr-02/datos-involucrados.rst § 7.4
    """

    full_name = serializers.CharField(
        source='get_full_name',
        read_only=True,
    )
    active_assignments = serializers.SerializerMethodField(
        help_text='Asignaciones de AccessGroup activas.',
    )
    active_sessions_count = serializers.SerializerMethodField(
        help_text='Número de sesiones ACTIVE actuales.',
    )
    created_at = serializers.DateTimeField(
        source='date_joined',
        read_only=True,
    )

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'state',
            'first_login',
            'created_at',
            'last_login_at',
            'active_assignments',
            'active_sessions_count',
        )
        read_only_fields = fields

    def get_active_assignments(self, obj) -> list[dict]:
        try:
            from apps.access.models import UserAccessGroup
            rows = (
                UserAccessGroup.objects
                .filter(user=obj)
                .select_related('access_group')
            )
            return [
                {
                    'access_group_id': row.access_group.id,
                    'access_group_name': row.access_group.name,
                    'granted_at': row.granted_at.isoformat() if hasattr(row, 'granted_at') and row.granted_at else None,
                }
                for row in rows
            ]
        except Exception:
            return []

    def get_active_sessions_count(self, obj) -> int:
        try:
            from apps.authentication.models import Session
            return Session.objects.filter(user=obj, state='ACTIVE').count()
        except Exception:
            return 0
