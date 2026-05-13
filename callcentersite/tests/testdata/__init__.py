"""
TestData classes - FASE 1 Testing Infrastructure.

All classes follow TestData naming (CLEAN_CODE_NAMING_PRINCIPLES).
No *Factory suffix — TestData describes the purpose, not the pattern.

Importar todos los factories aquí para fácil acceso.

CLEAN_CODE v3.0.1: Imports organizados por app.
Total Factories: 137+
"""

# ============================================================================
# USER FACTORIES
# ============================================================================

from .user_test_data import (
    UserTestData,
    AdminUserTestData,
)


# ============================================================================
# CORE FACTORIES (apps/core/)
# ============================================================================

from .core_test_data import (
    CenterTestData,
    ServiceTestData,
    CallRecordTestData,
)


# ============================================================================
# AUTHENTICATION FACTORIES (apps/authentication/)
# ============================================================================

from .authentication_test_data import (
    LoginAttemptTestData,
    SecurityQuestionTestData,
    UserSecurityAnswerTestData,
    SessionLogTestData,
)


# ============================================================================
# ACCESS FACTORIES (apps/access/) - RBAC
# ============================================================================

from .access_test_data import (
    # Module Factories
    ModuleTestData,
    ModuleWithParentTestData,

    # Function Factories
    FunctionTestData,
    FunctionCreateTestData,
    FunctionViewTestData,
    FunctionEditTestData,
    FunctionDeleteTestData,

    # Assignment Factories
    UserPermissionTestData,

    # Helper Factories
    UserWithModuleAccessTestData,
    UserWithFunctionTestData,
    CompleteUserTestData,
)
# DEUDA TÉCNICA 2026-03-21: RoleTestData, AdminRoleTestData, ManagerRoleTestData,
# AnalystRoleTestData, ViewerRoleTestData, UserRoleAssignmentTestData,
# RoleFunctionAssignmentTestData, UserWithRoleTestData eliminados — DT-002.


# ============================================================================
# AUDIT FACTORIES (apps/audit/)
# ============================================================================

from .audit_test_data import (
    # AuditLog Factories
    AuditLogTestData,
    CreateAuditLogTestData,
    UpdateAuditLogTestData,
    DeleteAuditLogTestData,
    AccessDeniedAuditLogTestData,
    
    # SessionLog Factories
    SessionLogTestData,
    LoginSessionLogTestData,
    LogoutSessionLogTestData,
    ExpiredSessionLogTestData,
    
    # Helper Factories
    UserSessionTestData,
    AuditTrailTestData,
    SessionHistoryTestData,
)




# ============================================================================
# PIPELINE FACTORIES (apps/pipeline/)
# DEUDA TÉCNICA 2026-03-21: ETLJob, ETLError, SchedulerConfig, DataQualityCheck
# no existen en apps.pipeline.models. Importación silenciosa.
# ============================================================================

try:
    from .pipeline_test_data import (
        ETLJobTestData, PendingETLJobTestData, RunningETLJobTestData,
        SuccessETLJobTestData, FailedETLJobTestData, ETLErrorTestData,
        ValidationErrorTestData, ConnectionErrorTestData, DataQualityErrorTestData,
        SchedulerConfigTestData, DailyJobConfigTestData, HourlyJobConfigTestData,
        HealthCheckConfigTestData, DataQualityCheckTestData, PassedCheckTestData,
        FailedCheckTestData, CompleteETLRunTestData, SchedulerHistoryTestData,
    )
except ImportError:
    pass  # Modelos Pipeline no implementados aún


# ============================================================================
# REPORT FACTORIES (apps/reports/)
# DEUDA TÉCNICA 2026-03-21: Importación silenciosa hasta que modelos sean estables.
# ============================================================================

try:
    from .report_test_data import (
        ReportTestData,
        QuarterlyReportTestData as QuarterlyReportReportTestData,
        TransferReportTestData as TransferReportReportTestData,
        AbandonedReportTestData as AbandonedReportReportTestData,
        ClientReportTestData as ClientReportReportTestData,
        CustomReportTestData, ReportExecutionTestData, PendingExecutionTestData,
        RunningExecutionTestData, SuccessExecutionTestData, FailedExecutionTestData,
        ReportTemplateTestData, QuarterlyTemplateTestData, TransferTemplateTestData,
        ReportScheduleTestData, QuarterlyScheduleTestData, WeeklyScheduleTestData,
        ReportCacheTestData, CompleteReportTestData, TemplateWithScheduleTestData,
    )
except ImportError:
    pass  # Modelos Report no estables aún


# ============================================================================
# DASHBOARD FACTORIES (apps/dashboard/) - FUTURO
# DEUDA TÉCNICA 2026-03-21: Importación silenciosa hasta implementación.
# ============================================================================

try:
    from .dashboard_test_data import (
        DashboardConfigTestData, DefaultDashboardTestData, PublicDashboardTestData,
        WidgetConfigTestData, CallsChartWidgetTestData, TransfersChartWidgetTestData,
        AbandonmentsChartWidgetTestData, TopClientsWidgetTestData,
        MetricsSummaryWidgetTestData, SavedFilterTestData, QuarterlyFilterTestData,
        MonthlyFilterTestData, UserDashboardPreferenceTestData,
        CompleteDashboardTestData, UserWithDashboardTestData,
    )
except ImportError:
    pass  # Dashboard no implementado aún


# ============================================================================
# ALERT FACTORIES (apps/alerts/) - FUTURO
# DEUDA TÉCNICA 2026-03-21: Importación silenciosa hasta implementación.
# ============================================================================

try:
    from .alert_test_data import (
        AlertRuleTestData, ThresholdAlertRuleTestData, HighAbandonmentRuleTestData,
        LowCallVolumeRuleTestData, LongQueueTimeRuleTestData, TrendAlertRuleTestData,
        AnomalyAlertRuleTestData, AlertTestData, TriggeredAlertTestData,
        ResolvedAlertTestData, CriticalAlertTestData, HighAlertTestData,
        MediumAlertTestData, LowAlertTestData, AlertNotificationTestData,
        EmailNotificationTestData, PendingNotificationTestData, SentNotificationTestData,
        DeliveredNotificationTestData, FailedNotificationTestData,
        ReadNotificationTestData, AlertHistoryTestData, TriggeredHistoryTestData,
        ResolvedHistoryTestData, AcknowledgedHistoryTestData, EscalatedHistoryTestData,
        CompleteAlertTestData, AlertLifecycleTestData, UserWithAlertsTestData,
    )
except ImportError:
    pass  # Alerts no implementado aún


# ============================================================================
# __ALL__ EXPORTS
# ============================================================================

__all__ = [
    # Users
    'UserTestData',
    'AdminUserTestData',
    
    # Core
    'CenterTestData',
    'ServiceTestData',
    'CallRecordTestData',
    
    # Authentication (4)
    'LoginAttemptTestData',
    'SecurityQuestionTestData',
    'UserSecurityAnswerTestData',
    'SessionLogTestData',
    
    # Access (18)
    'ModuleTestData',
    'ModuleWithParentTestData',
    'FunctionTestData',
    'FunctionCreateTestData',
    'FunctionViewTestData',
    'FunctionEditTestData',
    'FunctionDeleteTestData',
    'UserPermissionTestData',
    'UserWithModuleAccessTestData',
    'UserWithFunctionTestData',
    'CompleteUserTestData',
    
    # Audit (13)
    'AuditLogTestData',
    'CreateAuditLogTestData',
    'UpdateAuditLogTestData',
    'DeleteAuditLogTestData',
    'AccessDeniedAuditLogTestData',
    'SessionLogTestData',
    'LoginSessionLogTestData',
    'LogoutSessionLogTestData',
    'ExpiredSessionLogTestData',
    'UserSessionTestData',
    'AuditTrailTestData',
    'SessionHistoryTestData',
    
    
    # Pipeline (16)
    'ETLJobTestData',
    'PendingETLJobTestData',
    'RunningETLJobTestData',
    'SuccessETLJobTestData',
    'FailedETLJobTestData',
    'ETLErrorTestData',
    'ValidationErrorTestData',
    'ConnectionErrorTestData',
    'DataQualityErrorTestData',
    'SchedulerConfigTestData',
    'DailyJobConfigTestData',
    'HourlyJobConfigTestData',
    'HealthCheckConfigTestData',
    'DataQualityCheckTestData',
    'PassedCheckTestData',
    'FailedCheckTestData',
    'CompleteETLRunTestData',
    'SchedulerHistoryTestData',
    
    # Reports (17)
    'ReportTestData',
    'QuarterlyReportReportTestData',
    'TransferReportReportTestData',
    'AbandonedReportReportTestData',
    'ClientReportReportTestData',
    'CustomReportTestData',
    'ReportExecutionTestData',
    'PendingExecutionTestData',
    'RunningExecutionTestData',
    'SuccessExecutionTestData',
    'FailedExecutionTestData',
    'ReportTemplateTestData',
    'QuarterlyTemplateTestData',
    'TransferTemplateTestData',
    'ReportScheduleTestData',
    'QuarterlyScheduleTestData',
    'WeeklyScheduleTestData',
    'ReportCacheTestData',
    'CompleteReportTestData',
    'TemplateWithScheduleTestData',
    
    # Dashboard (13)
    'DashboardConfigTestData',
    'DefaultDashboardTestData',
    'PublicDashboardTestData',
    'WidgetConfigTestData',
    'CallsChartWidgetTestData',
    'TransfersChartWidgetTestData',
    'AbandonmentsChartWidgetTestData',
    'TopClientsWidgetTestData',
    'MetricsSummaryWidgetTestData',
    'SavedFilterTestData',
    'QuarterlyFilterTestData',
    'MonthlyFilterTestData',
    'UserDashboardPreferenceTestData',
    'CompleteDashboardTestData',
    'UserWithDashboardTestData',
    
    # Alerts (27)
    'AlertRuleTestData',
    'ThresholdAlertRuleTestData',
    'HighAbandonmentRuleTestData',
    'LowCallVolumeRuleTestData',
    'LongQueueTimeRuleTestData',
    'TrendAlertRuleTestData',
    'AnomalyAlertRuleTestData',
    'AlertTestData',
    'TriggeredAlertTestData',
    'ResolvedAlertTestData',
    'CriticalAlertTestData',
    'HighAlertTestData',
    'MediumAlertTestData',
    'LowAlertTestData',
    'AlertNotificationTestData',
    'EmailNotificationTestData',
    'PendingNotificationTestData',
    'SentNotificationTestData',
    'DeliveredNotificationTestData',
    'FailedNotificationTestData',
    'ReadNotificationTestData',
    'AlertHistoryTestData',
    'TriggeredHistoryTestData',
    'ResolvedHistoryTestData',
    'AcknowledgedHistoryTestData',
    'EscalatedHistoryTestData',
    'CompleteAlertTestData',
    'AlertLifecycleTestData',
    'UserWithAlertsTestData',
]


# ============================================================================
# TOTAL FACTORIES: 141
# 
# Por App:
#   users:         2
#   core:          3
#   authentication:4
#   access:       18
#   audit:        13
#   ivr:          17
#   pipeline:     16
#   reports:      17
#   dashboard:    13
#   alerts:       27
# 
# CLEAN_CODE v3.0.1: Imports organizados y documentados [SUCCESS]
# FASE 1 - PARTE 6: Authentication Factories COMPLETADAS [SUCCESS]
# ============================================================================

# M-001..M-004: New access factories (Fase M)
from .access_test_data import (
    AccessGroupTestData,
    UserAccessGroupTestData,
    SeparationRuleTestData,
    ExceptionalPermissionTestData,
    ApprovedExceptionalPermissionTestData,
    ExpiredExceptionalPermissionTestData,
    UserFunctionAssignmentTestData,
    UserModuleAccessTestData,
)
