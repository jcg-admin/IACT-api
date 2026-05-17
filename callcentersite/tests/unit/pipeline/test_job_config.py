"""
tests/unit/pipeline/test_job_config.py

TDD — UC_PIP_05: Gestionar configuracion del job ETL.

Endpoints:
  GET  /api/pipeline/job-config/           — listar configuraciones (PIP-001)
  GET  /api/pipeline/job-config/{name}/    — detalle de un job    (PIP-001)
  PATCH /api/pipeline/job-config/{name}/   — habilitar/deshabilitar (PIP-005)

Funcion RBAC:
  PIP-001  view_pipeline_status  — lectura
  PIP-005  manage_pipeline_config — escritura (nuevo)

Reglas de negocio:
  BR-ETL-01: solo is_enabled y notas son modificables via API.
              timeout_seconds, ventana_inicio/fin requieren despliegue DB.
  BR-ETL-02: solo el job 'etl_diario' y 'etl_historico' son gestionables.
  BR-ETL-03: el campo actualizado_en se actualiza automaticamente en MariaDB.
"""
import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.test_data.user_test_data import AdminUserTestData, UserTestData


# ────────────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────────────

@pytest.fixture
def client_pip(db):
    """Cliente con PIP-001 (lectura) y PIP-005 (escritura)."""
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def client_sin_pip(db):
    """Cliente sin permisos de pipeline."""
    client = APIClient()
    user = UserTestData()
    client.force_authenticate(user=user)
    return client


JOB_ROWS = [
    {
        'job_name':        'etl_diario',
        'is_enabled':      True,
        'timeout_seconds': 1800,
        'ventana_inicio':  '02:00:00',
        'ventana_fin':     '04:00:00',
        'min_intervalo_h': 6,
        'notas':           'ETL nocturno automatico.',
        'actualizado_en':  '2026-05-10T15:23:58',
    },
    {
        'job_name':        'etl_historico',
        'is_enabled':      False,
        'timeout_seconds': 7200,
        'ventana_inicio':  '02:00:00',
        'ventana_fin':     '04:00:00',
        'min_intervalo_h': 24,
        'notas':           'Carga historica manual.',
        'actualizado_en':  '2026-05-10T05:31:33',
    },
]


def _mock_ivr_cursor(rows, columns=None):
    """Devuelve un mock de cursor con los rows dados."""
    cur = MagicMock()
    cur.__enter__ = lambda s: s
    cur.__exit__ = MagicMock(return_value=False)
    if columns is None and rows:
        columns = list(rows[0].keys())
    cur.description = [(c, None, None, None, None, None, None) for c in (columns or [])]
    cur.fetchall.return_value = [tuple(r.values()) for r in rows]
    cur.fetchone.return_value = tuple(rows[0].values()) if rows else None
    return cur


# ────────────────────────────────────────────────────────────────────
# RED — GET /api/pipeline/job-config/
# ────────────────────────────────────────────────────────────────────

class TestJobConfigList:
    """UC_PIP_05 — listar configuraciones de jobs ETL."""

    def test_it01_lista_todos_los_jobs(self, client_pip):
        """CA-01: retorna lista con is_enabled, timeout_seconds, ventana."""
        url = reverse('pipeline:job-config-list')
        with patch('apps.pipeline.job_config_views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = \
                _mock_ivr_cursor(JOB_ROWS)
            response = client_pip.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert 'jobs' in data
        assert len(data['jobs']) == 2
        job = data['jobs'][0]
        assert job['job_name'] == 'etl_diario'
        assert job['is_enabled'] is True
        assert 'timeout_seconds' in job
        assert 'ventana_inicio' in job

    def test_it02_retorna_estado_general(self, client_pip):
        """CA-02: incluye cuantos jobs estan habilitados."""
        url = reverse('pipeline:job-config-list')
        with patch('apps.pipeline.job_config_views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = \
                _mock_ivr_cursor(JOB_ROWS)
            response = client_pip.get(url)

        data = response.data
        assert 'resumen' in data
        assert data['resumen']['total'] == 2
        assert data['resumen']['habilitados'] == 1
        assert data['resumen']['deshabilitados'] == 1

    def test_sec01_sin_permiso_retorna_403(self, client_sin_pip):
        """SEC-01: sin PIP-001 → 403."""
        url = reverse('pipeline:job-config-list')
        response = client_sin_pip.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_it03_mariadb_no_disponible_retorna_503(self, client_pip):
        """CA-03: MariaDB caída → 503."""
        url = reverse('pipeline:job-config-list')
        from django.db import OperationalError
        with patch('apps.pipeline.job_config_views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.side_effect = OperationalError('timeout')
            response = client_pip.get(url)
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


# ────────────────────────────────────────────────────────────────────
# RED — GET /api/pipeline/job-config/{job_name}/
# ────────────────────────────────────────────────────────────────────

class TestJobConfigDetail:
    """UC_PIP_05 — detalle de un job específico."""

    def test_it01_detalle_job_existente(self, client_pip):
        """CA-01: job_name existente → 200 con todos los campos."""
        url = reverse('pipeline:job-config-detail', kwargs={'job_name': 'etl_diario'})
        with patch('apps.pipeline.job_config_views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = \
                _mock_ivr_cursor([JOB_ROWS[0]])
            response = client_pip.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['job_name'] == 'etl_diario'
        assert response.data['is_enabled'] is True
        assert response.data['timeout_seconds'] == 1800

    def test_it02_job_inexistente_retorna_404(self, client_pip):
        """CA-02: job_name desconocido → 404."""
        url = reverse('pipeline:job-config-detail', kwargs={'job_name': 'no_existe'})
        with patch('apps.pipeline.job_config_views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = \
                _mock_ivr_cursor([])
            response = client_pip.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ────────────────────────────────────────────────────────────────────
# RED — PATCH /api/pipeline/job-config/{job_name}/
# ────────────────────────────────────────────────────────────────────

class TestJobConfigUpdate:
    """UC_PIP_05 — habilitar/deshabilitar job ETL (BR-ETL-01)."""

    def test_it01_deshabilitar_job_retorna_200(self, client_pip):
        """CA-01: PATCH is_enabled=false → 200, campo actualizado."""
        url = reverse('pipeline:job-config-detail', kwargs={'job_name': 'etl_diario'})
        with patch('apps.pipeline.job_config_views.connections') as mock_conn:
            cur = _mock_ivr_cursor([JOB_ROWS[0]])
            cur.rowcount = 1
            mock_conn.__getitem__.return_value.cursor.return_value = cur
            response = client_pip.patch(url, {'is_enabled': False}, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'actualizado_en' in response.data

    def test_it02_habilitar_job_retorna_200(self, client_pip):
        """CA-02: PATCH is_enabled=true sobre job deshabilitado → 200."""
        url = reverse('pipeline:job-config-detail', kwargs={'job_name': 'etl_historico'})
        with patch('apps.pipeline.job_config_views.connections') as mock_conn:
            cur = _mock_ivr_cursor([JOB_ROWS[1]])
            cur.rowcount = 1
            mock_conn.__getitem__.return_value.cursor.return_value = cur
            response = client_pip.patch(url, {'is_enabled': True}, format='json')

        assert response.status_code == status.HTTP_200_OK

    def test_it03_patch_notas_permitido(self, client_pip):
        """CA-03: PATCH notas → 200 (BR-ETL-01 permite notas)."""
        url = reverse('pipeline:job-config-detail', kwargs={'job_name': 'etl_diario'})
        with patch('apps.pipeline.job_config_views.connections') as mock_conn:
            cur = _mock_ivr_cursor([JOB_ROWS[0]])
            cur.rowcount = 1
            mock_conn.__getitem__.return_value.cursor.return_value = cur
            response = client_pip.patch(url, {'notas': 'Deshabilitado por mantenimiento'}, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_it04_patch_timeout_rechazado(self, client_pip):
        """CA-04: PATCH timeout_seconds → 400 (BR-ETL-01 — solo via DB)."""
        url = reverse('pipeline:job-config-detail', kwargs={'job_name': 'etl_diario'})
        response = client_pip.patch(url, {'timeout_seconds': 3600}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_it05_patch_sin_campos_validos_retorna_400(self, client_pip):
        """CA-05: PATCH sin is_enabled ni notas → 400."""
        url = reverse('pipeline:job-config-detail', kwargs={'job_name': 'etl_diario'})
        response = client_pip.patch(url, {}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_sec01_sin_permiso_escritura_retorna_403(self, client_sin_pip):
        """SEC-01: sin PIP-005 → 403."""
        url = reverse('pipeline:job-config-detail', kwargs={'job_name': 'etl_diario'})
        response = client_sin_pip.patch(url, {'is_enabled': False}, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_it06_audit_emitido_al_cambiar_estado(self, client_pip):
        """CA-06: cambio de is_enabled emite evento de auditoría."""
        url = reverse('pipeline:job-config-detail', kwargs={'job_name': 'etl_diario'})
        with patch('apps.pipeline.job_config_views.connections') as mock_conn, \
             patch('apps.pipeline.job_config_views.AuditLogService') as mock_audit:
            cur = _mock_ivr_cursor([JOB_ROWS[0]])
            cur.rowcount = 1
            mock_conn.__getitem__.return_value.cursor.return_value = cur
            response = client_pip.patch(url, {'is_enabled': False}, format='json')

        assert response.status_code == status.HTTP_200_OK
        mock_audit.emit.assert_called_once()
        call_kwargs = mock_audit.emit.call_args[1]
        assert call_kwargs['event_type'] == 'JOB_CONFIG_UPDATED'
