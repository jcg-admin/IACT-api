"""
Tests para MenuItemViewSet y MenuItemTransitionView (T-102 / T-104).

Cobertura:
- MenuItemSerializer: campos presentes
- MenuItemViewSet: queryset apunta a MenuItem
- MenuItemTransitionView: acepta status válido, rechaza inválido
- Rutas registradas correctamente
"""
import pytest
from unittest.mock import MagicMock, patch
from django.urls import reverse

from apps.access.models import MenuItem
from apps.access.serializers import MenuItemSerializer, MenuItemTreeSerializer
from apps.access.views import MenuItemViewSet, MenuItemTransitionView
from apps.access.services.menu_lifecycle_service import (
    MenuLifecycleService,
    InvalidTransitionError,
)


# ---------------------------------------------------------------------------
# Serializer
# ---------------------------------------------------------------------------

class TestMenuItemSerializer:

    def test_campos_requeridos_presentes(self):
        fields = set(MenuItemSerializer().fields.keys())
        required = {
            'id', 'function', 'display_label', 'icon',
            'route', 'order', 'parent', 'status',
            'created_at', 'updated_at',
        }
        assert required.issubset(fields)

    def test_function_code_es_read_only(self):
        field = MenuItemSerializer().fields['function_code']
        assert field.read_only is True

    def test_campos_read_only(self):
        serializer = MenuItemSerializer()
        read_only = {
            name for name, f in serializer.fields.items()
            if f.read_only
        }
        assert 'created_at' in read_only
        assert 'updated_at' in read_only

    def test_tree_serializer_tiene_children(self):
        fields = set(MenuItemTreeSerializer().fields.keys())
        assert 'children' in fields

    def test_tree_serializer_no_expone_status(self):
        """TreeSerializer solo expone items ACTIVE — no necesita status."""
        fields = set(MenuItemTreeSerializer().fields.keys())
        assert 'status' not in fields


# ---------------------------------------------------------------------------
# ViewSet
# ---------------------------------------------------------------------------

class TestMenuItemViewSet:

    def test_queryset_apunta_a_menuitem(self):
        assert MenuItemViewSet.queryset.model is MenuItem

    def test_serializer_class(self):
        assert MenuItemViewSet.serializer_class is MenuItemSerializer


# ---------------------------------------------------------------------------
# TransitionView
# ---------------------------------------------------------------------------

class TestMenuItemTransitionView:

    def _make_request(self, data):
        request = MagicMock()
        request.data = data
        return request

    def test_status_ausente_retorna_400(self):
        from rest_framework import status as http_status
        view = MenuItemTransitionView()
        request = self._make_request({})

        with patch('apps.access.models.MenuItem.objects') as mock_qs:
            mock_qs.get.return_value = MagicMock(spec=MenuItem)
            response = view.post(request, pk=1)

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST

    def test_transicion_valida_retorna_200(self):
        from rest_framework import status as http_status
        view = MenuItemTransitionView()
        request = self._make_request({'status': 'ACTIVE'})

        mock_item = MagicMock(spec=MenuItem)
        mock_item.pk = 1
        mock_item.status = 'ACTIVE'

        with patch('apps.access.models.MenuItem.objects') as mock_qs, \
             patch.object(MenuLifecycleService, 'transition'), \
             patch.object(MenuLifecycleService, 'get_allowed_transitions', return_value=['DEPRECATED']):
            mock_qs.get.return_value = mock_item
            response = view.post(request, pk=1)

        assert response.status_code == http_status.HTTP_200_OK
        assert 'status' in response.data
        assert 'allowed_next' in response.data

    def test_transicion_invalida_retorna_400(self):
        from rest_framework import status as http_status
        view = MenuItemTransitionView()
        request = self._make_request({'status': 'ARCHIVED'})

        mock_item = MagicMock(spec=MenuItem)
        mock_item.pk = 1
        mock_item.status = 'DRAFT'

        with patch('apps.access.models.MenuItem.objects') as mock_qs, \
             patch.object(MenuLifecycleService, 'transition',
                          side_effect=InvalidTransitionError("no permitida")):
            mock_qs.get.return_value = mock_item
            response = view.post(request, pk=1)

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST

    def test_menuitem_no_encontrado_retorna_404(self):
        from rest_framework import status as http_status
        view = MenuItemTransitionView()
        request = self._make_request({'status': 'ACTIVE'})

        with patch('apps.access.models.MenuItem.objects') as mock_qs:
            mock_qs.get.side_effect = MenuItem.DoesNotExist
            response = view.post(request, pk=999)

        assert response.status_code == http_status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# URLs
# ---------------------------------------------------------------------------

class TestMenuItemUrls:

    def test_menuitem_list_url(self):
        url = reverse('access:menuitem-list')
        assert url == '/api/access/menu-items/'

    def test_menuitem_detail_url(self):
        url = reverse('access:menuitem-detail', kwargs={'pk': 42})
        assert url == '/api/access/menu-items/42/'

    def test_menuitem_transition_url(self):
        url = reverse('access:menuitem-transition', kwargs={'pk': 1})
        assert url == '/api/access/menu-items/1/transition/'
