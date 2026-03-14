"""
FactoryBoy factories - FASE 1 Testing Infrastructure.

Importar todos los factories aquí para fácil acceso.

CLEAN_CODE v3.0.1: Imports organizados por app.
Total Factories: 137+
"""

# ============================================================================
# USER FACTORIES
# ============================================================================

from .user_factory import (
    UserFactory,
    AdminUserFactory,
)


# ============================================================================
# CORE FACTORIES (apps/core/)
# ============================================================================

from .core import (
    CenterFactory,
    ServiceFactory,
    CallRecordFactory,
)


# ============================================================================
# AUTHENTICATION FACTORIES (apps/authentication/)
# ============================================================================

from .authentication_factories import (
    LoginAttemptFactory,
    SecurityQuestionFactory,
    UserSecurityAnswerFactory,
    SessionLogFactory,
)


# ============================================================================
# ACCESS FACTORIES (apps/access/) - RBAC
# ============================================================================

from .access_factories import (
    # Module Factories
    ModuleFactory,
    ModuleWithParentFactory,
    
    # Function Factories
    FunctionFactory,
    FunctionCreateFactory,
    FunctionViewFactory,
    FunctionEditFactory,
    FunctionDeleteFactory,
    
    # Role Factories
    RoleFactory,
    AdminRoleFactory,
    ManagerRoleFactory,
    AnalystRoleFactory,
    ViewerRoleFactory,
    
    # Assignment Factories
    UserModuleAccessFactory,
    UserFunctionAssignmentFactory,
    UserRoleAssignmentFactory,
    RoleFunctionAssignmentFactory,
    
    # Helper Factories
    UserWithModuleAccessFactory,
    UserWithFunctionFactory,
    UserWithRoleFactory,
    CompleteUserFactory,
)


# ============================================================================
# AUDIT FACTORIES (apps/audit/)
# ============================================================================

from .audit_factories import (
    # AuditLog Factories
    AuditLogFactory,
    CreateAuditLogFactory,
    UpdateAuditLogFactory,
    DeleteAuditLogFactory,
    AccessDeniedAuditLogFactory,
    
    # SessionLog Factories
    SessionLogFactory,
    LoginSessionLogFactory,
    LogoutSessionLogFactory,
    ExpiredSessionLogFactory,
    
    # Helper Factories
    UserSessionFactory,
    AuditTrailFactory,
    SessionHistoryFactory,
)


# ============================================================================
# IVR FACTORIES (apps/ivr_legacy/)
# ============================================================================

from .ivr_factories import (
    # Quarterly Factories
    QuarterlyReportFactory,
    Q1ReportFactory,
    Q2ReportFactory,
    Q3ReportFactory,
    Q4ReportFactory,
    
    # Report Factories
    TransferReportFactory,
    AbandonedReportFactory,
    ClientReportFactory,
    
    # CallRecord Factories
    CallRecordQ1Factory,
    CallRecordQ2Factory,
    CallRecordQ3Factory,
    CallRecordQ4Factory,
    
    # Stats Factories
    MonthlyStatsFactory,
    HourlyStatsFactory,
    DIDReportFactory,
    
    # Helper Factories
    CompleteQuarterDataFactory,
    YearDataFactory,
)


# ============================================================================
# PIPELINE FACTORIES (apps/pipeline/)
# ============================================================================

from .pipeline_factories import (
    # ETLJob Factories
    ETLJobFactory,
    PendingETLJobFactory,
    RunningETLJobFactory,
    SuccessETLJobFactory,
    FailedETLJobFactory,
    
    # ETLError Factories
    ETLErrorFactory,
    ValidationErrorFactory,
    ConnectionErrorFactory,
    DataQualityErrorFactory,
    
    # SchedulerConfig Factories
    SchedulerConfigFactory,
    DailyJobConfigFactory,
    HourlyJobConfigFactory,
    HealthCheckConfigFactory,
    
    # DataQualityCheck Factories
    DataQualityCheckFactory,
    PassedCheckFactory,
    FailedCheckFactory,
    
    # Helper Factories
    CompleteETLRunFactory,
    SchedulerHistoryFactory,
)


# ============================================================================
# REPORT FACTORIES (apps/reports/)
# ============================================================================

from .report_factories import (
    # Report Factories
    ReportFactory,
    QuarterlyReportFactory as QuarterlyReportReportFactory,  # Alias para evitar conflicto
    TransferReportFactory as TransferReportReportFactory,
    AbandonedReportFactory as AbandonedReportReportFactory,
    ClientReportFactory as ClientReportReportFactory,
    CustomReportFactory,
    
    # ReportExecution Factories
    ReportExecutionFactory,
    PendingExecutionFactory,
    RunningExecutionFactory,
    SuccessExecutionFactory,
    FailedExecutionFactory,
    
    # ReportTemplate Factories
    ReportTemplateFactory,
    QuarterlyTemplateFactory,
    TransferTemplateFactory,
    
    # ReportSchedule Factories
    ReportScheduleFactory,
    QuarterlyScheduleFactory,
    WeeklyScheduleFactory,
    
    # ReportCache Factories
    ReportCacheFactory,
    
    # Helper Factories
    CompleteReportFactory,
    TemplateWithScheduleFactory,
)


# ============================================================================
# DASHBOARD FACTORIES (apps/dashboard/) - FUTURO
# ============================================================================

from .dashboard_factories import (
    # DashboardConfig Factories
    DashboardConfigFactory,
    DefaultDashboardFactory,
    PublicDashboardFactory,
    
    # WidgetConfig Factories
    WidgetConfigFactory,
    CallsChartWidgetFactory,
    TransfersChartWidgetFactory,
    AbandonmentsChartWidgetFactory,
    TopClientsWidgetFactory,
    MetricsSummaryWidgetFactory,
    
    # SavedFilter Factories
    SavedFilterFactory,
    QuarterlyFilterFactory,
    MonthlyFilterFactory,
    
    # UserDashboardPreference Factories
    UserDashboardPreferenceFactory,
    
    # Helper Factories
    CompleteDashboardFactory,
    UserWithDashboardFactory,
)


# ============================================================================
# ALERT FACTORIES (apps/alerts/) - FUTURO
# ============================================================================

from .alert_factories import (
    # AlertRule Factories
    AlertRuleFactory,
    ThresholdAlertRuleFactory,
    HighAbandonmentRuleFactory,
    LowCallVolumeRuleFactory,
    LongQueueTimeRuleFactory,
    TrendAlertRuleFactory,
    AnomalyAlertRuleFactory,
    
    # Alert Factories
    AlertFactory,
    TriggeredAlertFactory,
    ResolvedAlertFactory,
    CriticalAlertFactory,
    HighAlertFactory,
    MediumAlertFactory,
    LowAlertFactory,
    
    # AlertNotification Factories
    AlertNotificationFactory,
    EmailNotificationFactory,
    PendingNotificationFactory,
    SentNotificationFactory,
    DeliveredNotificationFactory,
    FailedNotificationFactory,
    ReadNotificationFactory,
    
    # AlertHistory Factories
    AlertHistoryFactory,
    TriggeredHistoryFactory,
    ResolvedHistoryFactory,
    AcknowledgedHistoryFactory,
    EscalatedHistoryFactory,
    
    # Helper Factories
    CompleteAlertFactory,
    AlertLifecycleFactory,
    UserWithAlertsFactory,
)


# ============================================================================
# __ALL__ EXPORTS
# ============================================================================

__all__ = [
    # Users
    'UserFactory',
    'AdminUserFactory',
    
    # Core
    'CenterFactory',
    'ServiceFactory',
    'CallRecordFactory',
    
    # Authentication (4)
    'LoginAttemptFactory',
    'SecurityQuestionFactory',
    'UserSecurityAnswerFactory',
    'SessionLogFactory',
    
    # Access (18)
    'ModuleFactory',
    'ModuleWithParentFactory',
    'FunctionFactory',
    'FunctionCreateFactory',
    'FunctionViewFactory',
    'FunctionEditFactory',
    'FunctionDeleteFactory',
    'RoleFactory',
    'AdminRoleFactory',
    'ManagerRoleFactory',
    'AnalystRoleFactory',
    'ViewerRoleFactory',
    'UserModuleAccessFactory',
    'UserFunctionAssignmentFactory',
    'UserRoleAssignmentFactory',
    'RoleFunctionAssignmentFactory',
    'UserWithModuleAccessFactory',
    'UserWithFunctionFactory',
    'UserWithRoleFactory',
    'CompleteUserFactory',
    
    # Audit (13)
    'AuditLogFactory',
    'CreateAuditLogFactory',
    'UpdateAuditLogFactory',
    'DeleteAuditLogFactory',
    'AccessDeniedAuditLogFactory',
    'SessionLogFactory',
    'LoginSessionLogFactory',
    'LogoutSessionLogFactory',
    'ExpiredSessionLogFactory',
    'UserSessionFactory',
    'AuditTrailFactory',
    'SessionHistoryFactory',
    
    # IVR (17)
    'QuarterlyReportFactory',
    'Q1ReportFactory',
    'Q2ReportFactory',
    'Q3ReportFactory',
    'Q4ReportFactory',
    'TransferReportFactory',
    'AbandonedReportFactory',
    'ClientReportFactory',
    'CallRecordQ1Factory',
    'CallRecordQ2Factory',
    'CallRecordQ3Factory',
    'CallRecordQ4Factory',
    'MonthlyStatsFactory',
    'HourlyStatsFactory',
    'DIDReportFactory',
    'CompleteQuarterDataFactory',
    'YearDataFactory',
    
    # Pipeline (16)
    'ETLJobFactory',
    'PendingETLJobFactory',
    'RunningETLJobFactory',
    'SuccessETLJobFactory',
    'FailedETLJobFactory',
    'ETLErrorFactory',
    'ValidationErrorFactory',
    'ConnectionErrorFactory',
    'DataQualityErrorFactory',
    'SchedulerConfigFactory',
    'DailyJobConfigFactory',
    'HourlyJobConfigFactory',
    'HealthCheckConfigFactory',
    'DataQualityCheckFactory',
    'PassedCheckFactory',
    'FailedCheckFactory',
    'CompleteETLRunFactory',
    'SchedulerHistoryFactory',
    
    # Reports (17)
    'ReportFactory',
    'QuarterlyReportReportFactory',
    'TransferReportReportFactory',
    'AbandonedReportReportFactory',
    'ClientReportReportFactory',
    'CustomReportFactory',
    'ReportExecutionFactory',
    'PendingExecutionFactory',
    'RunningExecutionFactory',
    'SuccessExecutionFactory',
    'FailedExecutionFactory',
    'ReportTemplateFactory',
    'QuarterlyTemplateFactory',
    'TransferTemplateFactory',
    'ReportScheduleFactory',
    'QuarterlyScheduleFactory',
    'WeeklyScheduleFactory',
    'ReportCacheFactory',
    'CompleteReportFactory',
    'TemplateWithScheduleFactory',
    
    # Dashboard (13)
    'DashboardConfigFactory',
    'DefaultDashboardFactory',
    'PublicDashboardFactory',
    'WidgetConfigFactory',
    'CallsChartWidgetFactory',
    'TransfersChartWidgetFactory',
    'AbandonmentsChartWidgetFactory',
    'TopClientsWidgetFactory',
    'MetricsSummaryWidgetFactory',
    'SavedFilterFactory',
    'QuarterlyFilterFactory',
    'MonthlyFilterFactory',
    'UserDashboardPreferenceFactory',
    'CompleteDashboardFactory',
    'UserWithDashboardFactory',
    
    # Alerts (27)
    'AlertRuleFactory',
    'ThresholdAlertRuleFactory',
    'HighAbandonmentRuleFactory',
    'LowCallVolumeRuleFactory',
    'LongQueueTimeRuleFactory',
    'TrendAlertRuleFactory',
    'AnomalyAlertRuleFactory',
    'AlertFactory',
    'TriggeredAlertFactory',
    'ResolvedAlertFactory',
    'CriticalAlertFactory',
    'HighAlertFactory',
    'MediumAlertFactory',
    'LowAlertFactory',
    'AlertNotificationFactory',
    'EmailNotificationFactory',
    'PendingNotificationFactory',
    'SentNotificationFactory',
    'DeliveredNotificationFactory',
    'FailedNotificationFactory',
    'ReadNotificationFactory',
    'AlertHistoryFactory',
    'TriggeredHistoryFactory',
    'ResolvedHistoryFactory',
    'AcknowledgedHistoryFactory',
    'EscalatedHistoryFactory',
    'CompleteAlertFactory',
    'AlertLifecycleFactory',
    'UserWithAlertsFactory',
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
