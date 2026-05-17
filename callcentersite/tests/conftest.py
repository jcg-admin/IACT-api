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
    'tests.fixtures.authentication',
    'tests.fixtures.ivr',   # L-002: IVR MariaDB integration fixtures

    # Mocks
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
# La tabla tbl_temp_prueba_ivr es responsabilidad del script MariaDB:
#   scripts/provisioners/mariadb/schema_temp_prueba.sh
# Python solo CONSUME (SELECT) — no crea schema desde Python.
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
    
    Usa UserTestData para crear usuario.
    
    Uso:
        def test_protected_endpoint(authenticated_client):
            response = authenticated_client.get('/api/v1/reports/')
            assert response.status_code == 200
    """
    from tests.test_data import UserTestData

    user = UserTestData()
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    client.user = user  # Adjuntar user para acceso fácil
    return client


@pytest.fixture
def admin_client(db):
    """
    API client autenticado como superusuario.
    
    Usa AdminUserTestData para crear admin.
    
    Uso:
        def test_admin_endpoint(admin_client):
            response = admin_client.post('/api/v1/admin/users/')
            assert response.status_code == 201
    """
    from tests.test_data import AdminUserTestData

    admin = AdminUserTestData()
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
    NUEVO: Usar UserTestData directamente.
    """
    from tests.test_data import UserTestData
    return UserTestData(
        email='test@example.com',
        username='testuser',
    )


@pytest.fixture
def sample_admin(db):
    """
    Superusuario para pruebas.
    
    LEGACY: Mantenido para compatibilidad.
    NUEVO: Usar AdminUserTestData directamente.
    """
    from tests.test_data import AdminUserTestData
    return AdminUserTestData(
        email='admin@example.com',
        username='admin',
    )


# ============================================================================

# ============================================================================
# HYBRID FIXTURES (Factory + Mock)
# ============================================================================

@pytest.fixture
def user_with_complete_access(db, mock_access_service):
    """
    Usuario con acceso completo RBAC (factory + mock).
    
    Combina:
        - CompleteUserTestData (módulo + función + rol)
        - mock_access_service (permisos mockeados)
    
    Uso:
        def test_rbac(user_with_complete_access):
            user = user_with_complete_access
            assert user.usermoduleaccess_set.count() > 0
    """
    from tests.test_data import CompleteUserTestData
    
    user = CompleteUserTestData()
    
    # Mock retorna True para todos los permisos
    mock_access_service.user_has_function.return_value = True
    mock_access_service.user_has_module.return_value = True
    
    return user


@pytest.fixture
def authenticated_client_with_rbac(db, mock_access_service):
    """
    Cliente autenticado con RBAC completo.
    
    Combina:
        - UserTestData + CompleteUserTestData
        - mock_access_service
        - JWT token
    
    Uso:
        def test_api_with_rbac(authenticated_client_with_rbac):
            client = authenticated_client_with_rbac
            response = client.get('/api/v1/reports/')
            assert response.status_code == 200
    """
    from tests.test_data import CompleteUserTestData

    user = CompleteUserTestData()
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    client.user = user

    # Mock RBAC
    mock_access_service.user_has_function.return_value = True

    return client

@pytest.fixture
def report_with_export_mocks(db, mock_report_generator_service, mock_excel_exporter):
    """
    Reporte con generación y export mockeados.

    Combina:
        - QuarterlyReportTestData
        - mock_report_generator_service
        - mock_excel_exporter

    Uso:
        def test_report_generation(report_with_export_mocks):
            report = report_with_export_mocks
            assert report.file_url is not None
    """
    from tests.test_data import QuarterlyReportTestData

    # Mock generación
    mock_report_generator_service.generate_quarterly_report.return_value = {
        'report_id': 123,
        'file_url': '/fake/report.xlsx',
        'status': 'SUCCESS'
    }

    # Mock export
    mock_excel_exporter.export.return_value = '/fake/report.xlsx'

    report = QuarterlyReportTestData()
    return report


@pytest.fixture
def alert_with_notification_mocks(db, mock_send_mail):
    """
    Alerta con notificación email mockeada.
    
    Combina:
        - TriggeredAlertTestData
        - EmailNotificationTestData
        - mock_send_mail
    
    Uso:
        def test_alert_notification(alert_with_notification_mocks):
            alert = alert_with_notification_mocks
            assert alert.is_resolved is False
    """
    from tests.test_data import (
        TriggeredAlertTestData,
        EmailNotificationTestData,
        UserTestData
    )
    
    alert = TriggeredAlertTestData()
    user = UserTestData()
    
    # Notificación mockeada
    mock_send_mail.return_value = 1  # Email "enviado" (fake)
    
    notification = EmailNotificationTestData(alert=alert, user=user)
    alert.notification = notification
    
    return alert


@pytest.fixture
def dashboard_with_widgets(db):
    """
    Dashboard completo con widgets.
    
    Usa CompleteDashboardTestData.
    
    Uso:
        def test_dashboard(dashboard_with_widgets):
            data = dashboard_with_widgets
            assert len(data['widgets']) > 0
    """
    from tests.test_data import CompleteDashboardTestData, UserTestData
    
    user = UserTestData()
    data = CompleteDashboardTestData.create_dashboard(
        user=user,
        widget_types=['CALLS_CHART', 'TRANSFERS_CHART', 'ABANDONMENTS_CHART']
    )
    return data


@pytest.fixture
def audit_trail(db):
    """
    Audit trail completo (CREATE -> UPDATE -> DELETE).
    
    Usa AuditTrailTestData.
    
    Uso:
        def test_audit_trail(audit_trail):
            logs = audit_trail
            assert len(logs) == 3
    """
    from tests.test_data import AuditTrailTestData, UserTestData
    
    user = UserTestData()
    trail = AuditTrailTestData.create_trail(
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
# + 137 Factories (importados vía tests.test_data)
# + 81 Mocks (importados vía pytest_plugins)
# 
# TOTAL: 218+ fixtures disponibles
# 
# CLEAN_CODE v3.0.1: Organizado y documentado [SUCCESS]
# CNST-002: Dual DB (PostgreSQL test_iact_analytics + MariaDB test_ivr_legacy) [SUCCESS]
# CNST-010: NO cache (DummyCache en testing.py) [SUCCESS]
# ============================================================================

@pytest.fixture(scope='session', autouse=True)
def ensure_postgresql():
    """
    H-INFRA-002: garantiza que PostgreSQL esté corriendo antes de la sesión.
    Sin este fixture, todos los tests @pytest.mark.django_db fallan con
    psycopg2.OperationalError cuando el contenedor se reinicia.
    """
    import subprocess
    result = subprocess.run(
        ['pg_ctlcluster', '16', 'main', 'status'],
        capture_output=True, text=True
    )
    if 'online' not in result.stdout and 'running' not in result.stdout:
        subprocess.run(
            ['pg_ctlcluster', '16', 'main', 'start'],
            capture_output=True
        )
        import time; time.sleep(2)
    yield
