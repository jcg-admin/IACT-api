"""
TestData classes — tests/test_data/

All classes follow TestData naming (CLEAN_CODE_NAMING_PRINCIPLES).
Center, Service, CallRecord, CallNote, ETLExecution eliminados en FASE 3.
"""
from .user_test_data import UserTestData, AdminUserTestData
from .authentication_test_data import (
    LoginAttemptTestData,
    SecurityQuestionTestData,
    UserSecurityAnswerTestData,
    SessionLogTestData,
)
from .access_test_data import (
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
    AccessGroupTestData,
    UserAccessGroupTestData,
    SeparationRuleTestData,
    ExceptionalPermissionTestData,
    ApprovedExceptionalPermissionTestData,
    ExpiredExceptionalPermissionTestData,
    UserFunctionAssignmentTestData,
    UserModuleAccessTestData,
)
from .audit_test_data import (
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
    from .report_test_data import (
        ReportTestData,
        QuarterlyReportTestData,
        ReportExecutionTestData,
    )
except ImportError:
    pass

try:
    from .dashboard_test_data import (
        DashboardConfigTestData,
        CompleteDashboardTestData,
    )
except ImportError:
    pass

try:
    from .alert_test_data import (
        AlertTestData,
        EmailNotificationTestData,
        CompleteAlertTestData,
    )
except ImportError:
    pass
