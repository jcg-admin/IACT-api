"""
Filtros para apps/users/.

Django-filter filtros para UserViewSet.
"""

import django_filters
from django.contrib.auth import get_user_model

# [SUCCESS] BEST PRACTICE: Use get_user_model() instead of direct import
# https://docs.djangoproject.com/en/stable/topics/auth/customizing/#referencing-the-user-model
User = get_user_model()


class UserFilter(django_filters.FilterSet):
    """
    Filtros para User (UC_USR_04 / FR-009.02).

    Filtros disponibles:
    - username (icontains)
    - email (icontains)
    - state (exact + in) — ACTIVE/INACTIVE/BLOCKED/ELIMINATED
    - is_active (exact) — legacy boolean
    - is_staff (exact)
    - role / agr_code — usuarios miembros de un AccessGroup
    - date_joined (gte, lte)
    """

    username = django_filters.CharFilter(lookup_expr='icontains')
    email = django_filters.CharFilter(lookup_expr='icontains')

    state = django_filters.CharFilter(field_name='state', lookup_expr='iexact')
    role = django_filters.CharFilter(method='filter_by_role')
    agr_code = django_filters.CharFilter(method='filter_by_role')

    class Meta:
        model = User
        fields = {
            'is_active': ['exact'],
            'is_staff': ['exact'],
            'date_joined': ['gte', 'lte'],
        }

    @staticmethod
    def filter_by_role(queryset, name, value):
        """FR-009.02: filtra usuarios por code de AccessGroup (rol)."""
        if not value:
            return queryset
        from apps.access.models import UserAccessGroup
        user_ids = UserAccessGroup.objects.filter(
            access_group__code__iexact=value,
        ).values_list('user_id', flat=True)
        return queryset.filter(pk__in=user_ids)
