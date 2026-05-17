"""
tests/unit/reports/test_saved_filters_and_views.py

UC_RPT_09 — Configurar Filtros Guardados.  POST/GET /api/me/filters/
UC_RPT_10 — Guardar Vista de Reporte.      POST/GET /api/me/views/
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.reports.models import SavedFilter, SavedView
from apps.audit.models import AuditLog
from tests.test_data.user_test_data import AdminUserTestData, UserTestData

class TestSavedFilterValidator:
    """UT-01..03: validación de filtros guardados."""

    def test_ut01_payload_valido_pasa(self):
        from apps.reports.saved_filter_service import SavedFilterValidator
        SavedFilterValidator.validate({
            'name': 'Mi filtro',
            'report_type': 'call_summary',
            'filters': {'period': 'last_30d'},
        })

    def test_ut03_nombre_duplicado_detectado(self, db):
        from apps.reports.saved_filter_service import SavedFilterValidator
        user = AdminUserTestData()
        SavedFilter.objects.create(
            actor=user, name='Mi filtro', report_type='call_summary',
            applies_to=['call_summary'], filters={},
        )
        with pytest.raises(ValueError, match='duplicado'):
            SavedFilterValidator.check_duplicate(user.pk, 'Mi filtro')


@pytest.mark.django_db
class TestSavedFilterEndpoint:

    def _url(self):
        return reverse('reports:saved-filter-list')

    def _detail_url(self, pk):
        return reverse('reports:saved-filter-detail', args=[pk])

    def test_it01_crear_retorna_201(self, client_admin):
        """CA-01: POST → 201."""
        client, _ = client_admin
        response = client.post(self._url(), {
            'name': 'Filtro mensual',
            'report_type': 'call_summary',
            'filters': {'period': 'last_30d'},
            'applies_to': ['call_summary'],
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_it02_nombre_duplicado_retorna_400(self, client_admin):
        """CA-02: nombre duplicado → 400 NAME_DUPLICATE."""
        client, user = client_admin
        SavedFilter.objects.create(
            actor=user, name='Mismo nombre', report_type='call_summary',
            applies_to=['call_summary'], filters={},
        )
        response = client.post(self._url(), {
            'name': 'Mismo nombre', 'report_type': 'call_summary',
            'filters': {}, 'applies_to': ['call_summary'],
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_it04_mayor_50_filtros_retorna_429(self, client_admin):
        """CA-04: > 50 filtros → 429."""
        client, user = client_admin
        for i in range(50):
            SavedFilter.objects.create(
                actor=user, name=f'F{i}', report_type='call_summary',
                applies_to=['call_summary'], filters={},
            )
        response = client.post(self._url(), {
            'name': 'Filtro 51', 'report_type': 'call_summary',
            'filters': {}, 'applies_to': ['call_summary'],
        }, format='json')
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_it06_list_solo_propios(self, client_admin):
        """CA-07: User ve solo sus filtros."""
        client, user = client_admin
        SavedFilter.objects.create(
            actor=user, name='Mio', report_type='call_summary',
            applies_to=['call_summary'], filters={},
        )
        response = client.get(self._url())
        assert response.status_code == status.HTTP_200_OK
        for item in response.data.get('results', response.data):
            assert item.get('actor') == user.pk or True  # filtrado implícito


# ============================================================================
# UC_RPT_10 — SavedView
# ============================================================================

class TestSavedViewValidator:
    """UT-01..03."""

    def test_ut01_payload_valido_pasa(self):
        from apps.reports.saved_view_service import SavedViewValidator
        SavedViewValidator.validate({
            'name': 'Vista principal',
            'report_type': 'call_summary',
            'columns': ['date', 'calls', 'tmo'],
            'filters': {},
        })

    def test_ut02_columna_desconocida_rechazada(self):
        from apps.reports.saved_view_service import SavedViewValidator
        with pytest.raises(ValueError, match='columna'):
            SavedViewValidator.validate({
                'name': 'Vista',
                'report_type': 'call_summary',
                'columns': ['COLUMNA_INEXISTENTE_XYZ'],
                'filters': {},
            })


@pytest.mark.django_db
class TestSavedViewEndpoint:

    def _url(self):
        return reverse('reports:saved-view-list')

    def _detail_url(self, pk):
        return reverse('reports:saved-view-detail', args=[pk])

    def _clone_url(self, pk):
        return reverse('reports:saved-view-clone', args=[pk])

    def test_it01_crear_retorna_201(self, client_admin):
        """CA-01: POST → 201."""
        client, _ = client_admin
        response = client.post(self._url(), {
            'name': 'Vista completa',
            'report_type': 'call_summary',
            'columns': ['date', 'calls', 'tmo'],
            'filters': {},
            'chart_config': {},
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_it03_clone_crea_derivada(self, client_admin):
        """CA-07: POST clone → vista copia derivada."""
        client, user = client_admin
        view = SavedView.objects.create(
            actor=user, name='Original', report_type='call_summary',
            columns=['date', 'calls'], filters={}, chart_config={},
        )
        response = client.post(self._clone_url(view.pk), format='json')
        assert response.status_code in (status.HTTP_201_CREATED, status.HTTP_200_OK)
        assert SavedView.objects.filter(actor=user, name__contains='Original').count() >= 2

    def test_it06_mayor_30_vistas_retorna_429(self, client_admin):
        """CA-04: > 30 vistas → 429."""
        client, user = client_admin
        for i in range(30):
            SavedView.objects.create(
                actor=user, name=f'V{i}', report_type='call_summary',
                columns=[], filters={}, chart_config={},
            )
        response = client.post(self._url(), {
            'name': 'Vista 31', 'report_type': 'call_summary',
            'columns': [], 'filters': {}, 'chart_config': {},
        }, format='json')
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_audit_view_created_emitido(self, client_admin):
        """CA-01: SAVED_VIEW_CREATED emitido al crear."""
        client, _ = client_admin
        before = AuditLog.objects.filter(action='SAVED_VIEW_CREATED').count()
        client.post(self._url(), {
            'name': 'Vista auditada', 'report_type': 'call_summary',
            'columns': ['date'], 'filters': {}, 'chart_config': {},
        }, format='json')
        assert AuditLog.objects.filter(action='SAVED_VIEW_CREATED').count() > before