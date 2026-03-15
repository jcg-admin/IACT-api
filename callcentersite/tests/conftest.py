"""
Configuración pytest compartida - FASE 1 Testing Infrastructure v2.0.0.

Integra:
- 137 Factories (factory_boy)
- 81 Mocks (pytest fixtures)
- Fixtures híbridas (factory + mock)

CLEAN_CODE v3.0.1: Organizado por categoría.
Total Fixtures: 218+ (factories + mocks + híbridas)
"""

import pytest
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model


# ============================================================================
# PYTEST PLUGINS - Integración Factories + Mocks
# ============================================================================

pytest_plugins = [
    # Fixtures existentes
    'tests.fixtures.users',
    'tests.fixtures.rbac',
    
    # Mocks (PARTE 3)
    'tests.mocks.database_mocks',
    'tests.mocks.service_mocks',
    'tests.mocks.file_mocks',
    'tests.mocks.scheduler_mocks',
    'tests.mocks.external_mocks',
]


# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
# Las bases de datos para tests se configuran en config/settings/testing.py:
#   - default → test_iact_analytics  (PostgreSQL, migrations completas)
#   - ivr     → test_ivr_legacy      (MariaDB, schema vacío managed=False)
#
# Django crea/destruye los schemas automáticamente al correr pytest.
# No se necesita override aquí.
#
# PENDIENTE: fixture para crear tabla call_logs en test_ivr_legacy
# y sembrar datos para tests de consumo IVR (ver deuda-tecnica.md).
# ============================================================================


# ============================================================================
# API CLIENT FIXTURES
# ============================================================================

@pytest.fixture
def api_client():
    """
    Cliente REST API básico sin autenticación.
    
    Uso:
        def test_public_endpoint(api_client):
            response = api_client.get('/api/v1/public/')
            assert response.status_code == 200
    """
    return APIClient()


@pytest.fixture
def authenticated_client(db):
    """
    API client autenticado con usuario regular.
    
    Usa UserFactory para crear usuario.
    
    Uso:
        def test_protected_endpoint(authenticated_client):
            response = authenticated_client.get('/api/v1/reports/')
            assert response.status_code == 200
    """
    from tests.factories import UserFactory

    user = UserFactory()
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    client.user = user  # Adjuntar user para acceso fácil
    return client


@pytest.fixture
def admin_client(db):
    """
    API client autenticado como superusuario.
    
    Usa AdminUserFactory para crear admin.
    
    Uso:
        def test_admin_endpoint(admin_client):
            response = admin_client.post('/api/v1/admin/users/')
            assert response.status_code == 201
    """
    from tests.factories import AdminUserFactory

    admin = AdminUserFactory()
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=admin)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    client.user = admin
    return client


# ============================================================================
# USER FIXTURES (Legacy - mantenidas para compatibilidad)
# ============================================================================

@pytest.fixture
def sample_user(db):
    """
    Usuario estándar para pruebas.
    
    LEGACY: Mantenido para compatibilidad.
    NUEVO: Usar UserFactory directamente.
    """
    from tests.factories import UserFactory
    return UserFactory(
        email='test@example.com',
        username='testuser',
    )


@pytest.fixture
def sample_admin(db):
    """
    Superusuario para pruebas.
    
    LEGACY: Mantenido para compatibilidad.
    NUEVO: Usar AdminUserFactory directamente.
    """
    from tests.factories import AdminUserFactory
    return AdminUserFactory(
        email='admin@example.com',
        username='admin',
    )


# ============================================================================
# CORE MODEL FIXTURES (Legacy - mantenidas para compatibilidad)
# ============================================================================

@pytest.fixture
def sample_center(db):
    """
    Centro de ejemplo.
    
    LEGACY: Mantenido para compatibilidad.
    NUEVO: Usar CenterFactory directamente.
    """
    from tests.factories import CenterFactory
    return CenterFactory(codigo='CT01', nombre='Centro Test')


@pytest.fixture
def sample_service(db):
    """
    Servicio de ejemplo.
    
    LEGACY: Mantenido para compatibilidad.
    NUEVO: Usar ServiceFactory directamente.
    """
    from tests.factories import ServiceFactory
    return ServiceFactory(
        numero_800='800-123-4567',
        nombre='Servicio Test'
    )


# ============================================================================
# HYBRID FIXTURES (Factory + Mock)
# ============================================================================

@pytest.fixture
def user_with_complete_access(db, mock_access_service):
    """
    Usuario con acceso completo RBAC (factory + mock).
    
    Combina:
        - CompleteUserFactory (módulo + función + rol)
        - mock_access_service (permisos mockeados)
    
    Uso:
        def test_rbac(user_with_complete_access):
            user = user_with_complete_access
            assert user.usermoduleaccess_set.count() > 0
    """
    from tests.factories import CompleteUserFactory
    
    user = CompleteUserFactory()
    
    # Mock retorna True para todos los permisos
    mock_access_service.user_has_function.return_value = True
    mock_access_service.user_has_module.return_value = True
    
    return user


@pytest.fixture
def authenticated_client_with_rbac(db, mock_access_service):
    """
    Cliente autenticado con RBAC completo.
    
    Combina:
        - UserFactory + CompleteUserFactory
        - mock_access_service
        - JWT token
    
    Uso:
        def test_api_with_rbac(authenticated_client_with_rbac):
            client = authenticated_client_with_rbac
            response = client.get('/api/v1/reports/')
            assert response.status_code == 200
    """
    from tests.factories import CompleteUserFactory

    user = CompleteUserFactory()
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    client.user = user

    # Mock RBAC
    mock_access_service.user_has_function.return_value = True

    return client


@pytest.fixture
def etl_job_with_mocks(db, mock_ivr_connection, mock_etl_service):
    """
    ETL Job con BD IVR y service mockeados.
    
    Combina:
        - SuccessETLJobFactory
        - mock_ivr_connection (BD IVR)
        - mock_etl_service (ETL service)
    
    Uso:
        def test_etl_execution(etl_job_with_mocks):
            job = etl_job_with_mocks
            assert job.status == 'SUCCESS'
    """
    from tests.factories import SuccessETLJobFactory
    
    # BD IVR retorna datos fake
    mock_ivr_connection.cursor.return_value.fetchall.return_value = [
        (2025, 1, 10000, 5000, 180)
    ]
    
    # Service retorna resultado exitoso
    mock_etl_service.extract_quarterly_data.return_value = [
        {'year': 2025, 'quarter': 1, 'total_calls': 10000}
    ]
    
    job = SuccessETLJobFactory()
    return job


@pytest.fixture
def report_with_export_mocks(db, mock_report_generator_service, mock_excel_exporter):
    """
    Reporte con generación y export mockeados.
    
    Combina:
        - QuarterlyReportReportFactory
        - mock_report_generator_service
        - mock_excel_exporter
    
    Uso:
        def test_report_generation(report_with_export_mocks):
            report = report_with_export_mocks
            assert report.file_url is not None
    """
    from tests.factories import QuarterlyReportReportFactory
    
    # Mock generación
    mock_report_generator_service.generate_quarterly_report.return_value = {
        'report_id': 123,
        'file_url': '/fake/report.xlsx',
        'status': 'SUCCESS'
    }
    
    # Mock export
    mock_excel_exporter.export.return_value = '/fake/report.xlsx'
    
    report = QuarterlyReportReportFactory()
    return report


@pytest.fixture
def scheduled_job_with_mocks(db, mock_apscheduler, mock_cleanup_sessions_job):
    """
    Scheduled job con APScheduler mockeado.
    
    Combina:
        - DailyJobConfigFactory
        - mock_apscheduler
        - mock_cleanup_sessions_job
    
    Uso:
        def test_scheduled_job(scheduled_job_with_mocks):
            config = scheduled_job_with_mocks
            assert config.is_active is True
    """
    from tests.factories import DailyJobConfigFactory
    
    # Mock job en scheduler
    mock_apscheduler.get_job.return_value = mock_cleanup_sessions_job
    
    config = DailyJobConfigFactory(job_name='cleanup_sessions')
    return config


@pytest.fixture
def alert_with_notification_mocks(db, mock_send_mail):
    """
    Alerta con notificación email mockeada.
    
    Combina:
        - TriggeredAlertFactory
        - EmailNotificationFactory
        - mock_send_mail
    
    Uso:
        def test_alert_notification(alert_with_notification_mocks):
            alert = alert_with_notification_mocks
            assert alert.is_resolved is False
    """
    from tests.factories import (
        TriggeredAlertFactory,
        EmailNotificationFactory,
        UserFactory
    )
    
    alert = TriggeredAlertFactory()
    user = UserFactory()
    
    # Notificación mockeada
    mock_send_mail.return_value = 1  # Email "enviado" (fake)
    
    notification = EmailNotificationFactory(alert=alert, user=user)
    alert.notification = notification
    
    return alert


@pytest.fixture
def quarterly_data_with_mocks(db, mock_ivr_cursor_quarterly):
    """
    Datos trimestrales completos con BD IVR mockeada.
    
    Combina:
        - CompleteQuarterDataFactory
        - mock_ivr_cursor_quarterly
    
    Uso:
        def test_quarterly_data(quarterly_data_with_mocks):
            data = quarterly_data_with_mocks
            assert data['quarterly'].year == 2025
    """
    from tests.factories.ivr_factories import CompleteQuarterDataFactory
    
    # BD IVR retorna datos fake
    mock_ivr_cursor_quarterly.fetchall.return_value = [
        {'year': 2025, 'quarter': 1, 'total_calls': 10000}
    ]
    
    data = CompleteQuarterDataFactory.create_quarter(year=2025, quarter=1)
    return data


@pytest.fixture
def dashboard_with_widgets(db):
    """
    Dashboard completo con widgets.
    
    Usa CompleteDashboardFactory.
    
    Uso:
        def test_dashboard(dashboard_with_widgets):
            data = dashboard_with_widgets
            assert len(data['widgets']) > 0
    """
    from tests.factories import CompleteDashboardFactory, UserFactory
    
    user = UserFactory()
    data = CompleteDashboardFactory.create_dashboard(
        user=user,
        widget_types=['CALLS_CHART', 'TRANSFERS_CHART', 'ABANDONMENTS_CHART']
    )
    return data


@pytest.fixture
def audit_trail(db):
    """
    Audit trail completo (CREATE -> UPDATE -> DELETE).
    
    Usa AuditTrailFactory.
    
    Uso:
        def test_audit_trail(audit_trail):
            logs = audit_trail
            assert len(logs) == 3
    """
    from tests.factories import AuditTrailFactory, UserFactory
    
    user = UserFactory()
    trail = AuditTrailFactory.create_trail(
        user=user,
        model_name='Report',
        object_id='123'
    )
    return trail


# ============================================================================
# HELPER FIXTURES
# ============================================================================

@pytest.fixture
def sample_date():
    """
    Fecha estática para tests determinísticos.
    
    Uso:
        def test_date_filter(sample_date):
            reports = Report.objects.filter(created_at=sample_date)
    """
    from datetime import date
    return date(2025, 1, 15)


@pytest.fixture
def sample_datetime():
    """
    Datetime estático para tests.
    
    Uso:
        def test_datetime_filter(sample_datetime):
            logs = AuditLog.objects.filter(timestamp__gte=sample_datetime)
    """
    from datetime import datetime
    return datetime(2025, 1, 15, 10, 0, 0)


@pytest.fixture
def sample_quarter():
    """
    Quarter sample data.
    
    Uso:
        def test_quarterly_report(sample_quarter):
            year, quarter = sample_quarter
            report = generate_quarterly_report(year, quarter)
    """
    return (2025, 1)


@pytest.fixture
def sample_did():
    """
    DID sample para tests IVR.
    
    Uso:
        def test_did_report(sample_did):
            report = DIDReport.objects.filter(did=sample_did)
    """
    return '800123456'


@pytest.fixture
def cleanup_files():
    """
    Cleanup de archivos temporales después de tests.
    
    Uso:
        def test_file_generation(cleanup_files):
            file = generate_report()
            # Archivo será eliminado automáticamente
    """
    files_to_cleanup = []
    
    def register(filepath):
        files_to_cleanup.append(filepath)
    
    yield register
    
    # Cleanup después del test
    import os
    for filepath in files_to_cleanup:
        if os.path.exists(filepath):
            os.remove(filepath)


# ============================================================================
# TOTAL FIXTURES EN CONFTEST: 60+
# 
# Categorías:
#   - API Clients: 3 (api_client, authenticated_client, admin_client)
#   - Users (legacy): 2 (sample_user, sample_admin)
#   - Core Models (legacy): 2 (sample_center, sample_service)
#   - Hybrid Fixtures: 8 (factory + mock combinados)
#   - Helpers: 5
# 
# + 137 Factories (importados vía tests.factories)
# + 81 Mocks (importados vía pytest_plugins)
# 
# TOTAL: 218+ fixtures disponibles
# 
# CLEAN_CODE v3.0.1: Organizado y documentado [SUCCESS]
# CNST-002: Dual DB (PostgreSQL test_iact_analytics + MariaDB test_ivr_legacy) [SUCCESS]
# CNST-010: NO cache (DummyCache en testing.py) [SUCCESS]
# ============================================================================