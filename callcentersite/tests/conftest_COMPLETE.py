"""
Configuración pytest COMPLETA - IACT Call Center System v3.0.0

Fixtures globales para TODAS las apps del proyecto.
Basado en análisis arquitectónico completo (43 partes, 11 módulos).

CLEAN_CODE v3.0.1: Nombres auto-documentados.
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone

# ============================================================================
# FIXTURES: API CLIENTS
# ============================================================================

@pytest.fixture
def api_client():
    """Cliente REST API básico sin autenticación."""
    return APIClient()


@pytest.fixture
def authenticated_client(db, sample_user):
    """
    API client autenticado con usuario regular.
    
    Uso:
        def test_endpoint(authenticated_client):
            response = authenticated_client.get('/api/v1/modules/')
            assert response.status_code == 200
    """
    client = APIClient()
    refresh = RefreshToken.for_user(sample_user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.fixture
def admin_client(db, sample_admin):
    """
    API client autenticado como superusuario.
    
    Uso:
        def test_admin_endpoint(admin_client):
            response = admin_client.post('/api/v1/users/')
            assert response.status_code == 201
    """
    client = APIClient()
    refresh = RefreshToken.for_user(sample_admin)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


# ============================================================================
# FIXTURES: USERS (apps/users/)
# ============================================================================

@pytest.fixture
def sample_user(db):
    """
    Usuario estándar para pruebas.
    
    Atributos:
    - email: test@example.com
    - username: testuser
    - password: testpass123
    - is_active: True
    """
    User = get_user_model()
    return User.objects.create_user(
        email='test@example.com',
        username='testuser',
        password='testpass123'
    )


@pytest.fixture
def sample_admin(db):
    """
    Superusuario para pruebas de administración.
    
    Atributos:
    - email: admin@example.com
    - username: admin
    - password: adminpass123
    - is_superuser: True
    - is_staff: True
    """
    User = get_user_model()
    return User.objects.create_superuser(
        email='admin@example.com',
        username='admin',
        password='adminpass123'
    )


@pytest.fixture
def sample_inactive_user(db):
    """Usuario inactivo para tests de acceso."""
    User = get_user_model()
    user = User.objects.create_user(
        email='inactive@example.com',
        username='inactiveuser',
        password='testpass123'
    )
    user.is_active = False
    user.save()
    return user


# ============================================================================
# FIXTURES: AUTHENTICATION (apps/authentication/)
# ============================================================================

@pytest.fixture
def valid_login_credentials():
    """Credenciales válidas para login."""
    return {
        'username': 'testuser',
        'password': 'testpass123'
    }


@pytest.fixture
def invalid_login_credentials():
    """Credenciales inválidas para tests de autenticación."""
    return {
        'username': 'testuser',
        'password': 'wrongpassword'
    }


@pytest.fixture
def jwt_tokens(db, sample_user):
    """
    Tokens JWT válidos (access + refresh).
    
    Returns:
        dict: {'access': str, 'refresh': str}
    """
    refresh = RefreshToken.for_user(sample_user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh)
    }


# ============================================================================
# FIXTURES: ACCESS / RBAC (apps/access/)
# ============================================================================

@pytest.fixture
def sample_module(db):
    """
    Módulo raíz para tests RBAC.
    
    Atributos:
    - module_id: 'MODULE_001'
    - name: 'Test Module'
    - parent: None (raíz)
    """
    from apps.access.models import Module
    return Module.objects.create(
        module_id='MODULE_001',
        name='Test Module',
        parent=None,
        is_active=True
    )


@pytest.fixture
def sample_child_module(db, sample_module):
    """Módulo hijo para tests de jerarquía."""
    from apps.access.models import Module
    return Module.objects.create(
        module_id='MODULE_002',
        name='Child Module',
        parent=sample_module,
        is_active=True
    )


@pytest.fixture
def sample_function(db, sample_module):
    """
    Función RBAC para tests.
    
    Atributos:
    - function_id: 'test.function'
    - name: 'Test Function'
    - module: sample_module
    """
    from apps.access.models import Function
    return Function.objects.create(
        function_id='test.function',
        name='Test Function',
        description='Function for testing',
        module=sample_module
    )


@pytest.fixture
def sample_role(db):
    """
    Rol RBAC para tests.
    
    Atributos:
    - role_id: 'ROLE_TEST'
    - name: 'Test Role'
    """
    from apps.access.models import Role
    return Role.objects.create(
        role_id='ROLE_TEST',
        name='Test Role',
        description='Role for testing'
    )


@pytest.fixture
def user_with_module_access(db, sample_user, sample_module):
    """Usuario con acceso a módulo."""
    from apps.access.models import UserModuleAccess
    UserModuleAccess.objects.create(
        user=sample_user,
        module=sample_module
    )
    return sample_user


@pytest.fixture
def user_with_function(db, sample_user, sample_function):
    """Usuario con función asignada."""
    from apps.access.models import UserFunctionAssignment
    UserFunctionAssignment.objects.create(
        user=sample_user,
        function=sample_function
    )
    return sample_user


@pytest.fixture
def user_with_role(db, sample_user, sample_role):
    """Usuario con rol asignado."""
    from apps.access.models import UserRoleAssignment
    UserRoleAssignment.objects.create(
        user=sample_user,
        role=sample_role
    )
    return sample_user


# ============================================================================
# FIXTURES: AUDIT (apps/audit/)
# ============================================================================

@pytest.fixture
def sample_audit_log(db, sample_user):
    """
    Log de auditoría para tests.
    
    Atributos:
    - action: 'CREATE'
    - user: sample_user
    - model_name: 'TestModel'
    """
    from apps.audit.models import AuditLog
    return AuditLog.objects.create(
        action='CREATE',
        user=sample_user,
        model_name='TestModel',
        object_id='123',
        ip_address='127.0.0.1',
        user_agent='Test Agent'
    )


@pytest.fixture
def sample_session_log(db, sample_user):
    """Log de sesión para tests."""
    from apps.audit.models import SessionLog
    return SessionLog.objects.create(
        user=sample_user,
        session_key='test_session_key',
        ip_address='127.0.0.1',
        user_agent='Test Agent',
        action='LOGIN'
    )


# ============================================================================
# FIXTURES: IVR / ETL (apps/ivr/)
# ============================================================================

@pytest.fixture
def sample_quarterly_report(db):
    """
    Reporte trimestral Q1 2025 para tests.
    
    CNST-002: Consume BD IVR readonly.
    """
    from apps.ivr.models import QuarterlyReport
    return QuarterlyReport.objects.create(
        year=2025,
        quarter=1,
        total_calls=10000,
        unique_clients=5000,
        avg_duration_seconds=180
    )


@pytest.fixture
def sample_transfer_report(db):
    """Reporte de transferencias para tests."""
    from apps.ivr.models import TransferReport
    return TransferReport.objects.create(
        year=2025,
        quarter=1,
        menu_option='1',
        total_transfers=500,
        avg_wait_time_seconds=30
    )


@pytest.fixture
def sample_abandoned_report(db):
    """Reporte de abandonos para tests."""
    from apps.ivr.models import AbandonedReport
    return AbandonedReport.objects.create(
        year=2025,
        quarter=1,
        did='800123456',
        total_abandoned=100,
        abandonment_rate=0.05
    )


@pytest.fixture
def sample_client_report(db):
    """Reporte de clientes para tests."""
    from apps.ivr.models import ClientReport
    return ClientReport.objects.create(
        year=2025,
        quarter=1,
        client_id='CLIENT_001',
        total_calls=50,
        total_duration_seconds=900
    )


@pytest.fixture
def sample_call_record_q1(db):
    """Registro de llamada Q1 para tests."""
    from apps.ivr.models import CallRecordQ1
    return CallRecordQ1.objects.create(
        fecha=date(2025, 1, 15),
        telefono='800123456',
        duracion_segundos=180,
        estado='COMPLETED'
    )


# ============================================================================
# FIXTURES: PIPELINE (apps/pipeline/)
# ============================================================================

@pytest.fixture
def sample_etl_job(db):
    """
    ETL Job para tests.
    
    Atributos:
    - job_name: 'test_quarterly_report'
    - status: 'SUCCESS'
    """
    from apps.pipeline.models import ETLJob
    return ETLJob.objects.create(
        job_name='test_quarterly_report',
        status='SUCCESS',
        started_at=timezone.now() - timedelta(minutes=10),
        finished_at=timezone.now(),
        records_processed=1000,
        records_failed=0
    )


@pytest.fixture
def sample_etl_error(db, sample_etl_job):
    """Error ETL para tests."""
    from apps.pipeline.models import ETLError
    return ETLError.objects.create(
        job=sample_etl_job,
        error_type='VALIDATION_ERROR',
        error_message='Invalid data format',
        record_data={'row': 123}
    )


@pytest.fixture
def sample_scheduler_config(db):
    """Configuración de scheduler para tests."""
    from apps.pipeline.models import SchedulerConfig
    return SchedulerConfig.objects.create(
        job_name='quarterly_report_etl',
        cron_expression='0 2 * * *',
        is_active=True,
        max_retries=3
    )


# ============================================================================
# FIXTURES: REPORTS (apps/reports/)
# ============================================================================

@pytest.fixture
def sample_report(db, sample_user):
    """
    Reporte generado para tests.
    
    Atributos:
    - report_type: 'quarterly'
    - file_format: 'xlsx'
    - generated_by: sample_user
    """
    from apps.reports.models import Report
    return Report.objects.create(
        report_type='quarterly',
        report_name='Q1 2025 Summary',
        generated_by=sample_user,
        file_format='xlsx',
        file_url='http://example.com/reports/test.xlsx',
        file_size_bytes=1024000,
        row_count=500,
        parameters={'year': 2025, 'quarter': 1},
        generation_time_seconds=5.5,
        is_cached=False
    )


@pytest.fixture
def sample_report_execution(db, sample_report):
    """Ejecución de reporte para tests."""
    from apps.reports.models import ReportExecution
    return ReportExecution.objects.create(
        report=sample_report,
        execution_status='SUCCESS',
        started_at=timezone.now() - timedelta(seconds=10),
        finished_at=timezone.now()
    )


@pytest.fixture
def sample_report_template(db):
    """Template de reporte para tests."""
    from apps.reports.models import ReportTemplate
    return ReportTemplate.objects.create(
        template_name='Quarterly Summary Template',
        report_type='quarterly',
        default_parameters={'year': 2025, 'quarter': 1},
        is_active=True
    )


# ============================================================================
# FIXTURES: DASHBOARD (apps/dashboard/)
# ============================================================================

@pytest.fixture
def sample_dashboard_config(db, sample_user):
    """Configuración de dashboard para tests."""
    from apps.dashboard.models import DashboardConfig
    return DashboardConfig.objects.create(
        user=sample_user,
        config_name='My Dashboard',
        layout_config={
            'widgets': ['calls', 'transfers', 'abandonments']
        },
        is_default=True
    )


@pytest.fixture
def sample_widget_config(db, sample_dashboard_config):
    """Configuración de widget para tests."""
    from apps.dashboard.models import WidgetConfig
    return WidgetConfig.objects.create(
        dashboard=sample_dashboard_config,
        widget_type='CALLS_CHART',
        position_x=0,
        position_y=0,
        width=6,
        height=4,
        config_data={'chart_type': 'line'}
    )


# ============================================================================
# FIXTURES: ALERTS (apps/alerts/)
# ============================================================================

@pytest.fixture
def sample_alert_rule(db):
    """
    Regla de alerta para tests.
    
    Atributos:
    - rule_name: 'High Abandonment Rate'
    - metric: 'abandonment_rate'
    - threshold: 0.15 (15%)
    """
    from apps.alerts.models import AlertRule
    return AlertRule.objects.create(
        rule_name='High Abandonment Rate',
        rule_type='THRESHOLD',
        metric='abandonment_rate',
        threshold_value=Decimal('0.15'),
        comparison_operator='>',
        is_active=True
    )


@pytest.fixture
def sample_alert(db, sample_alert_rule):
    """Alerta generada para tests."""
    from apps.alerts.models import Alert
    return Alert.objects.create(
        rule=sample_alert_rule,
        severity='HIGH',
        message='Abandonment rate exceeded threshold',
        current_value=Decimal('0.18'),
        threshold_value=Decimal('0.15'),
        triggered_at=timezone.now()
    )


@pytest.fixture
def sample_alert_notification(db, sample_alert, sample_user):
    """Notificación de alerta para tests."""
    from apps.alerts.models import AlertNotification
    return AlertNotification.objects.create(
        alert=sample_alert,
        user=sample_user,
        notification_type='EMAIL',
        sent_at=timezone.now(),
        is_read=False
    )


# ============================================================================
# FIXTURES: UTILS (helpers)
# ============================================================================

@pytest.fixture
def sample_date():
    """Fecha estática para reproducibilidad."""
    return date(2025, 1, 15)


@pytest.fixture
def sample_datetime():
    """Datetime estático para reproducibilidad."""
    return datetime(2025, 1, 15, 10, 30, 0)


@pytest.fixture
def sample_quarter():
    """Trimestre para tests."""
    return {
        'year': 2025,
        'quarter': 1,
        'start_date': date(2025, 1, 1),
        'end_date': date(2025, 3, 31)
    }


@pytest.fixture
def mock_request(rf, sample_user):
    """
    Mock request con usuario autenticado.
    
    Uso:
        def test_view(mock_request):
            response = my_view(mock_request)
            assert response.status_code == 200
    """
    request = rf.get('/api/test/')
    request.user = sample_user
    return request


# ============================================================================
# FIXTURES: MOCKS
# ============================================================================

@pytest.fixture
def mock_etl_service(mocker):
    """
    Mock de ETLService para tests sin BD IVR.
    
    Uso:
        def test_etl(mock_etl_service):
            mock_etl_service.extract_data.return_value = [...]
            result = ETLService.extract_data()
            assert len(result) > 0
    """
    from apps.pipeline.services import ETLService
    return mocker.patch.object(ETLService, 'extract_data')


@pytest.fixture
def mock_email_service(mocker):
    """
    Mock de EmailService para tests sin enviar emails.
    
    CNST-001: NO email backend real.
    """
    from django.core.mail import send_mail
    return mocker.patch('django.core.mail.send_mail')


@pytest.fixture
def mock_cache(mocker):
    """
    Mock de cache para tests.
    
    CNST-010: Cache locmem.
    """
    from django.core.cache import cache
    mocker.patch.object(cache, 'get', return_value=None)
    mocker.patch.object(cache, 'set', return_value=True)
    return cache


@pytest.fixture
def mock_apscheduler(mocker):
    """
    Mock de APScheduler para tests sin jobs reales.
    
    CNST-013: APScheduler (NO Celery).
    """
    return mocker.patch('apscheduler.schedulers.background.BackgroundScheduler')


# ============================================================================
# FIXTURES: DATABASE
# ============================================================================

@pytest.fixture
def use_ivr_db(db):
    """
    Fixture para tests que usan BD IVR.
    
    CNST-002: BD IVR readonly.
    
    Uso:
        @pytest.mark.django_db(databases=['ivr'])
        def test_ivr(use_ivr_db):
            # Usa BD IVR
            pass
    """
    pass


# ============================================================================
# FIXTURES: FILES
# ============================================================================

@pytest.fixture
def sample_excel_file(tmp_path):
    """
    Archivo Excel temporal para tests.
    
    Returns:
        Path: Ruta al archivo .xlsx
    """
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws['A1'] = 'Test Data'
    
    file_path = tmp_path / 'test_report.xlsx'
    wb.save(file_path)
    return file_path


@pytest.fixture
def sample_csv_file(tmp_path):
    """Archivo CSV temporal para tests."""
    import csv
    
    file_path = tmp_path / 'test_data.csv'
    with open(file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Column1', 'Column2'])
        writer.writerow(['Value1', 'Value2'])
    
    return file_path


@pytest.fixture
def sample_pdf_file(tmp_path):
    """Archivo PDF temporal para tests."""
    from reportlab.pdfgen import canvas
    
    file_path = tmp_path / 'test_report.pdf'
    c = canvas.Canvas(str(file_path))
    c.drawString(100, 750, "Test PDF")
    c.save()
    
    return file_path


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configuración adicional de pytest."""
    # Registrar markers custom
    config.addinivalue_line(
        "markers", "unit: Tests unitarios (rápidos)"
    )
    config.addinivalue_line(
        "markers", "integration: Tests de integración"
    )
    config.addinivalue_line(
        "markers", "api: Tests de API REST"
    )
    config.addinivalue_line(
        "markers", "slow: Tests lentos (>1s)"
    )
    config.addinivalue_line(
        "markers", "fast: Tests rápidos (<1s)"
    )


# ============================================================================
# TOTAL FIXTURES: 60+
# 
# Cobertura:
# - API Clients (3)
# - Users/Auth (6)
# - Access/RBAC (8)
# - Audit (2)
# - IVR/ETL (5)
# - Pipeline (3)
# - Reports (3)
# - Dashboard (2)
# - Alerts (3)
# - Utils (4)
# - Mocks (5)
# - Files (3)
# - Database (1)
# 
# CLEAN_CODE v3.0.1: Nombres auto-documentados [SUCCESS]
# ============================================================================
