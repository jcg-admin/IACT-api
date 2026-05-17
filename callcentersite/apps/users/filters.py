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
    Filtros para User.

    Filtros disponibles:
    - username (icontains)
    - email (icontains)
    - is_active (exact)
    - is_staff (exact)
    - date_joined (gte, lte)
    """

    username = django_filters.CharFilter(lookup_expr='icontains')
    email = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = User
        fields = {
            'is_active': ['exact'],
            'is_staff': ['exact'],
            'date_joined': ['gte', 'lte'],
        }
