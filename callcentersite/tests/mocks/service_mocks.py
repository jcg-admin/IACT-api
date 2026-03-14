"""
Mocks para Services (Service Layer Pattern).

CONTEXTO: Lógica de negocio en services (NO en models).
Mockeamos services para tests unitarios sin ejecutar lógica real.

RESTRICCIONES:
- Service Layer Pattern: Lógica en services
- Mocks retornan datos fake sin ejecutar código real

CLEAN_CODE v3.0.1: Nombres auto-documentados.
"""

import pytest
from unittest.mock import MagicMock, Mock, patch
from decimal import Decimal
from datetime import datetime, timedelta


# ============================================================================
# ETL SERVICE MOCKS
# ============================================================================

@pytest.fixture
def mock_etl_service(mocker):
    """
    Mock de ETLService (extracción de datos IVR).
    
    Simula extracción sin tocar BD IVR real.
    
    Uso:
        def test_report(mock_etl_service):
            mock_etl_service.extract_quarterly_data.return_value = [...]
            # Test usa datos mock
    
    Métodos mockeados:
        - extract_quarterly_data(year, quarter)
        - extract_transfer_data(year, quarter)
        - extract_abandoned_data(year, quarter)
        - extract_client_data(year, quarter)
    """
    from apps.pipeline.services import ETLService
    
    mock_service = MagicMock(spec=ETLService)
    
    # Mock extract_quarterly_data
    mock_service.extract_quarterly_data.return_value = [
        {
            'year': 2025,
            'quarter': 1,
            'total_calls': 10000,
            'unique_clients': 5000,
            'avg_duration_seconds': 180,
            'abandonment_rate': Decimal('0.15')
        }
    ]
    
    # Mock extract_transfer_data
    mock_service.extract_transfer_data.return_value = [
        {'menu_option': '1', 'total_transfers': 500, 'avg_wait_time': 30},
        {'menu_option': '2', 'total_transfers': 300, 'avg_wait_time': 25},
    ]
    
    # Mock extract_abandoned_data
    mock_service.extract_abandoned_data.return_value = [
        {'did': '800123456', 'total_abandoned': 150, 'abandonment_rate': Decimal('0.15')}
    ]
    
    # Mock extract_client_data
    mock_service.extract_client_data.return_value = [
        {'client_id': 'CLIENT_001', 'total_calls': 100, 'total_duration': 18000}
    ]
    
    mocker.patch(
        'apps.pipeline.services.ETLService',
        return_value=mock_service
    )
    
    return mock_service


@pytest.fixture
def mock_etl_service_empty(mocker):
    """
    Mock de ETLService que retorna datos vacíos.
    
    Uso:
        def test_report_no_data(mock_etl_service_empty):
            data = ETLService.extract_quarterly_data(2025, 1)
            assert len(data) == 0
    """
    from apps.pipeline.services import ETLService
    
    mock_service = MagicMock(spec=ETLService)
    
    # Todos los métodos retornan lista vacía
    mock_service.extract_quarterly_data.return_value = []
    mock_service.extract_transfer_data.return_value = []
    mock_service.extract_abandoned_data.return_value = []
    mock_service.extract_client_data.return_value = []
    
    mocker.patch(
        'apps.pipeline.services.ETLService',
        return_value=mock_service
    )
    
    return mock_service


@pytest.fixture
def mock_etl_service_error(mocker):
    """
    Mock de ETLService que lanza error.
    
    Uso:
        def test_etl_failure(mock_etl_service_error):
            with pytest.raises(Exception, match="ETL failed"):
                ETLService.extract_quarterly_data(2025, 1)
    """
    from apps.pipeline.services import ETLService
    
    mock_service = MagicMock(spec=ETLService)
    
    # Todos los métodos lanzan error
    mock_service.extract_quarterly_data.side_effect = Exception("ETL failed: Connection timeout")
    mock_service.extract_transfer_data.side_effect = Exception("ETL failed: Connection timeout")
    
    mocker.patch(
        'apps.pipeline.services.ETLService',
        return_value=mock_service
    )
    
    return mock_service


# ============================================================================
# REPORT SERVICE MOCKS
# ============================================================================

@pytest.fixture
def mock_report_generator_service(mocker):
    """
    Mock de ReportGeneratorService (generación de reportes).
    
    Simula generación sin crear archivos reales.
    
    Uso:
        def test_generate_report(mock_report_generator_service):
            report = ReportGeneratorService.generate_quarterly_report(2025, 1, user)
            assert report['status'] == 'SUCCESS'
    
    Métodos mockeados:
        - generate_quarterly_report(year, quarter, user)
        - generate_transfer_report(year, quarter, user)
        - generate_abandoned_report(year, quarter, user)
        - generate_custom_report(parameters, user)
    """
    from apps.reports.services import ReportGeneratorService
    
    mock_service = MagicMock(spec=ReportGeneratorService)
    
    # Mock generate_quarterly_report
    mock_service.generate_quarterly_report.return_value = {
        'report_id': 123,
        'file_url': 'http://example.com/reports/quarterly_2025_Q1.xlsx',
        'file_size': 102400,
        'row_count': 1000,
        'status': 'SUCCESS',
        'generation_time': 5.2
    }
    
    # Mock generate_transfer_report
    mock_service.generate_transfer_report.return_value = {
        'report_id': 124,
        'file_url': 'http://example.com/reports/transfers_2025_Q1.xlsx',
        'status': 'SUCCESS'
    }
    
    # Mock generate_abandoned_report
    mock_service.generate_abandoned_report.return_value = {
        'report_id': 125,
        'file_url': 'http://example.com/reports/abandoned_2025_Q1.xlsx',
        'status': 'SUCCESS'
    }
    
    mocker.patch(
        'apps.reports.services.ReportGeneratorService',
        return_value=mock_service
    )
    
    return mock_service


@pytest.fixture
def mock_report_service_limit_exceeded(mocker):
    """
    Mock de ReportGeneratorService que lanza error por límite excedido.
    
    CNST-007: Export máximo 100K rows.
    
    Uso:
        def test_report_limit(mock_report_service_limit_exceeded):
            with pytest.raises(Exception, match="100000 rows"):
                ReportGeneratorService.generate_quarterly_report(2025, 1, user)
    """
    from apps.reports.services import ReportGeneratorService
    
    mock_service = MagicMock(spec=ReportGeneratorService)
    
    mock_service.generate_quarterly_report.side_effect = Exception(
        "Export limit exceeded: 150000 rows > 100000 max (CNST-007)"
    )
    
    mocker.patch(
        'apps.reports.services.ReportGeneratorService',
        return_value=mock_service
    )
    
    return mock_service


# ============================================================================
# ACCESS SERVICE MOCKS (RBAC)
# ============================================================================

@pytest.fixture
def mock_access_service(mocker):
    """
    Mock de AccessService (verificación RBAC).
    
    Simula verificación de permisos sin consultar BD.
    
    Uso:
        def test_permission(mock_access_service):
            # Por defecto, usuario tiene acceso
            assert AccessService.user_has_function(user, 'reports.view')
    
    Métodos mockeados:
        - user_has_function(user, function_id)
        - user_has_module(user, module_id)
        - user_has_role(user, role_id)
        - get_user_functions(user)
    """
    from apps.access.services import AccessService
    
    mock_service = MagicMock(spec=AccessService)
    
    # Por defecto: usuario tiene acceso
    mock_service.user_has_function.return_value = True
    mock_service.user_has_module.return_value = True
    mock_service.user_has_role.return_value = True
    
    # Mock get_user_functions
    mock_service.get_user_functions.return_value = [
        'reports.view',
        'reports.create',
        'dashboard.view',
    ]
    
    mocker.patch(
        'apps.access.services.AccessService',
        return_value=mock_service
    )
    
    return mock_service


@pytest.fixture
def mock_access_service_denied(mocker):
    """
    Mock de AccessService que deniega acceso.
    
    Uso:
        def test_permission_denied(mock_access_service_denied):
            assert not AccessService.user_has_function(user, 'reports.delete')
    """
    from apps.access.services import AccessService
    
    mock_service = MagicMock(spec=AccessService)
    
    # Usuario NO tiene acceso
    mock_service.user_has_function.return_value = False
    mock_service.user_has_module.return_value = False
    mock_service.user_has_role.return_value = False
    mock_service.get_user_functions.return_value = []
    
    mocker.patch(
        'apps.access.services.AccessService',
        return_value=mock_service
    )
    
    return mock_service


# ============================================================================
# AUDIT SERVICE MOCKS
# ============================================================================

@pytest.fixture
def mock_audit_service(mocker):
    """
    Mock de AuditService (registro de auditoría).
    
    Simula logging sin escribir BD.
    
    Uso:
        def test_audit(mock_audit_service):
            AuditService.log_action(user, 'CREATE', 'Report', 123)
            mock_audit_service.log_action.assert_called_once()
    
    Métodos mockeados:
        - log_action(user, action, model_name, object_id)
        - log_session(user, action, session_key)
        - get_user_audit_trail(user, days)
    """
    from apps.audit.services import AuditService
    
    mock_service = MagicMock(spec=AuditService)
    
    # Mock log_action (retorna AuditLog fake)
    mock_service.log_action.return_value = MagicMock(
        id=1,
        action='CREATE',
        user=None,
        model_name='Report',
        object_id='123'
    )
    
    # Mock log_session
    mock_service.log_session.return_value = MagicMock(
        id=1,
        action='LOGIN',
        user=None
    )
    
    # Mock get_user_audit_trail
    mock_service.get_user_audit_trail.return_value = []
    
    mocker.patch(
        'apps.audit.services.AuditService',
        return_value=mock_service
    )
    
    return mock_service


# ============================================================================
# USER SERVICE MOCKS
# ============================================================================

@pytest.fixture
def mock_user_service(mocker):
    """
    Mock de UserService (gestión de usuarios).
    
    Uso:
        def test_create_user(mock_user_service):
            user = UserService.create_user({'username': 'test'})
            assert user.username == 'test'
    
    Métodos mockeados:
        - create_user(data)
        - update_user(user, data)
        - deactivate_user(user)
        - change_password(user, password)
    """
    from apps.users.services import UserService
    
    mock_service = MagicMock(spec=UserService)
    
    # Mock create_user
    mock_service.create_user.return_value = MagicMock(
        id=1,
        username='test',
        email='test@example.com',
        is_active=True
    )
    
    # Mock update_user
    mock_service.update_user.return_value = MagicMock(
        id=1,
        username='test_updated'
    )
    
    # Mock deactivate_user
    mock_service.deactivate_user.return_value = True
    
    # Mock change_password
    mock_service.change_password.return_value = True
    
    mocker.patch(
        'apps.users.services.UserService',
        return_value=mock_service
    )
    
    return mock_service


# ============================================================================
# AUTHENTICATION SERVICE MOCKS
# ============================================================================

@pytest.fixture
def mock_authentication_service(mocker):
    """
    Mock de AuthenticationService (autenticación JWT).
    
    Uso:
        def test_login(mock_authentication_service):
            tokens = AuthenticationService.login('user', 'pass')
            assert 'access' in tokens
            assert 'refresh' in tokens
    
    Métodos mockeados:
        - login(username, password)
        - logout(user, session_key)
        - refresh_token(refresh_token)
        - validate_token(access_token)
    """
    from apps.authentication.services import AuthenticationService
    
    mock_service = MagicMock(spec=AuthenticationService)
    
    # Mock login (retorna tokens JWT fake)
    mock_service.login.return_value = {
        'access': 'fake_access_token_12345',
        'refresh': 'fake_refresh_token_67890',
        'user': MagicMock(id=1, username='test')
    }
    
    # Mock logout
    mock_service.logout.return_value = True
    
    # Mock refresh_token
    mock_service.refresh_token.return_value = {
        'access': 'new_fake_access_token_11111'
    }
    
    # Mock validate_token
    mock_service.validate_token.return_value = True
    
    mocker.patch(
        'apps.authentication.services.AuthenticationService',
        return_value=mock_service
    )
    
    return mock_service


@pytest.fixture
def mock_authentication_service_invalid(mocker):
    """
    Mock de AuthenticationService que falla autenticación.
    
    Uso:
        def test_login_failed(mock_authentication_service_invalid):
            with pytest.raises(Exception, match="Invalid credentials"):
                AuthenticationService.login('user', 'wrong_pass')
    """
    from apps.authentication.services import AuthenticationService
    
    mock_service = MagicMock(spec=AuthenticationService)
    
    # login() lanza error
    mock_service.login.side_effect = Exception("Invalid credentials")
    
    # validate_token retorna False
    mock_service.validate_token.return_value = False
    
    mocker.patch(
        'apps.authentication.services.AuthenticationService',
        return_value=mock_service
    )
    
    return mock_service


# ============================================================================
# DASHBOARD SERVICE MOCKS (FUTURO)
# ============================================================================

@pytest.fixture
def mock_dashboard_service(mocker):
    """
    Mock de DashboardService (gestión de dashboards).
    
    FUTURO: Cuando se implemente apps/dashboard/.
    
    Uso:
        def test_dashboard(mock_dashboard_service):
            config = DashboardService.get_user_dashboard(user)
            assert config is not None
    """
    # Importar cuando se implemente
    # from apps.dashboard.services import DashboardService
    
    mock_service = MagicMock()
    
    # Mock get_user_dashboard
    mock_service.get_user_dashboard.return_value = MagicMock(
        id=1,
        config_name='Default Dashboard',
        is_default=True
    )
    
    # Mock create_widget
    mock_service.create_widget.return_value = MagicMock(
        id=1,
        widget_type='CALLS_CHART'
    )
    
    return mock_service


# ============================================================================
# ALERT SERVICE MOCKS (FUTURO)
# ============================================================================

@pytest.fixture
def mock_alert_service(mocker):
    """
    Mock de AlertService (gestión de alertas).
    
    FUTURO: Cuando se implemente apps/alerts/.
    
    Uso:
        def test_alert(mock_alert_service):
            alert = AlertService.trigger_alert(rule, current_value)
            assert alert.severity == 'HIGH'
    """
    # Importar cuando se implemente
    # from apps.alerts.services import AlertService
    
    mock_service = MagicMock()
    
    # Mock trigger_alert
    mock_service.trigger_alert.return_value = MagicMock(
        id=1,
        severity='HIGH',
        is_resolved=False
    )
    
    # Mock resolve_alert
    mock_service.resolve_alert.return_value = True
    
    # Mock evaluate_rule
    mock_service.evaluate_rule.return_value = True  # Alerta dispara
    
    return mock_service


# ============================================================================
# TOTAL MOCKS: 13
# 
# ETL Service Mocks (3):
#   - mock_etl_service
#   - mock_etl_service_empty
#   - mock_etl_service_error
# 
# Report Service Mocks (2):
#   - mock_report_generator_service
#   - mock_report_service_limit_exceeded
# 
# Access Service Mocks (2):
#   - mock_access_service
#   - mock_access_service_denied
# 
# Other Service Mocks (6):
#   - mock_audit_service
#   - mock_user_service
#   - mock_authentication_service
#   - mock_authentication_service_invalid
#   - mock_dashboard_service (futuro)
#   - mock_alert_service (futuro)
# 
# Service Layer Pattern implementado [SUCCESS]
# CLEAN_CODE v3.0.1: Nombres auto-documentados [SUCCESS]
# ============================================================================
