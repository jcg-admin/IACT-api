"""
Factory classes — tests/factories/

All classes follow TestData naming (CLEAN_CODE_NAMING_PRINCIPLES).
Center, Service, CallRecord, CallNote, ETLExecution eliminados en FASE 3.
"""
from .user_factory import UserTestData, AdminUserTestData
from .authentication_factories import (
    LoginAttemptTestData,
    SecurityQuestionTestData,
    UserSecurityAnswerTestData,
    SessionLogTestData,
)
from .access_factories import (
    ModuleTestData,
    ModuleWithParentTestData,
    FunctionTestData,
    FunctionCreateTestData,
    FunctionViewTestData,
    FunctionEditTestData,
    FunctionDeleteTestData,
    UserPermissionTestData,
    UserWithModuleAccessTestData,
    UserWithFunctionTestData,
    CompleteUserTestData,
)
from .audit_factories import (
    AuditLogTestData,
    CreateAuditLogTestData,
    UpdateAuditLogTestData,
    DeleteAuditLogTestData,
    AccessDeniedAuditLogTestData,
    UserSessionTestData,
    AuditTrailTestData,
    SessionHistoryTestData,
)

try:
    from .report_factories import ReportTestData, ReportExecutionTestData
except ImportError:
    pass

try:
    from .dashboard_factories import DashboardConfigTestData, CompleteDashboardTestData
except ImportError:
    pass

try:
    from .alert_factories import AlertTestData, CompleteAlertTestData
except ImportError:
    pass
