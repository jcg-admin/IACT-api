"""
Tests para el modelo MenuItem (T-102).

Cobertura:
- Campos y defaults
- Invariante I-1: 1 Function = 0..1 MenuItem (OneToOneField)
- Relación parent/children
- Lifecycle choices
- __str__
"""
import pytest
from unittest.mock import MagicMock, patch
from apps.access.models import MenuItem


class TestMenuItemFields:
    """Campos y defaults del modelo."""

    def test_status_choices(self):
        choices = [c[0] for c in MenuItem.STATUS_CHOICES]
        assert choices == ['DRAFT', 'ACTIVE', 'DEPRECATED', 'ARCHIVED']

    def test_default_status_es_draft(self):
        field = MenuItem._meta.get_field('status')
        assert field.default == MenuItem.STATUS_DRAFT

    def test_default_order_es_cero(self):
        field = MenuItem._meta.get_field('order')
        assert field.default == 0

    def test_icon_blank_default(self):
        field = MenuItem._meta.get_field('icon')
        assert field.blank is True
        assert field.default == ''

    def test_route_blank_default(self):
        field = MenuItem._meta.get_field('route')
        assert field.blank is True
        assert field.default == ''

    def test_deprecated_at_nullable(self):
        field = MenuItem._meta.get_field('deprecated_at')
        assert field.null is True
        assert field.blank is True

    def test_archived_at_nullable(self):
        field = MenuItem._meta.get_field('archived_at')
        assert field.null is True
        assert field.blank is True

    def test_parent_nullable(self):
        field = MenuItem._meta.get_field('parent')
        assert field.null is True
        assert field.blank is True

    def test_function_es_onetoone(self):
        from django.db.models import OneToOneField
        field = MenuItem._meta.get_field('function')
        assert isinstance(field, OneToOneField)

    def test_function_related_name(self):
        field = MenuItem._meta.get_field('function')
        assert field.related_query_name() == 'menu_item'

    def test_ordering_por_order(self):
        assert MenuItem._meta.ordering == ['order']

    def test_db_table(self):
        assert MenuItem._meta.db_table == 'access_menu_item'

    def test_app_label(self):
        assert MenuItem._meta.app_label == 'access'


class TestMenuItemStr:
    """__str__ del modelo."""

    def test_str_incluye_label_y_status(self):
        item = MenuItem.__new__(MenuItem)
        item.display_label = 'Reportes'
        item.status = 'ACTIVE'
        assert str(item) == 'Reportes [ACTIVE]'

    def test_str_con_status_draft(self):
        item = MenuItem.__new__(MenuItem)
        item.display_label = 'Dashboard'
        item.status = 'DRAFT'
        assert str(item) == 'Dashboard [DRAFT]'


class TestMenuItemStatusConstants:
    """Constantes de estado."""

    def test_status_draft(self):
        assert MenuItem.STATUS_DRAFT == 'DRAFT'

    def test_status_active(self):
        assert MenuItem.STATUS_ACTIVE == 'ACTIVE'

    def test_status_deprecated(self):
        assert MenuItem.STATUS_DEPRECATED == 'DEPRECATED'

    def test_status_archived(self):
        assert MenuItem.STATUS_ARCHIVED == 'ARCHIVED'


class TestMenuItemInvarianteI1:
    """Invariante I-1: 1 Function = 0..1 MenuItem."""

    def test_function_onetoone_no_puede_duplicarse(self):
        """OneToOneField garantiza que Function no puede tener dos MenuItem."""
        from django.db.models import OneToOneField
        field = MenuItem._meta.get_field('function')
        assert isinstance(field, OneToOneField), \
            "function debe ser OneToOneField — invariante I-1 de CNST-032"

    def test_on_delete_protect(self):
        """Eliminar Function no debe eliminar MenuItem — debe bloquearse."""
        from django.db.models import PROTECT
        field = MenuItem._meta.get_field('function')
        assert field.remote_field.on_delete == PROTECT
