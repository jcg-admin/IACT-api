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

    # Assignment Factories
    UserPermissionFactory,

    # Helper Factories
    UserWithModuleAccessFactory,
    UserWithFunctionFactory,
    CompleteUserFactory,
)
# DEUDA TÉCNICA 2026-03-21: RoleFactory, AdminRoleFactory, ManagerRoleFactory,
# AnalystRoleFactory, ViewerRoleFactory, UserRoleAssignmentFactory,
# RoleFunctionAssignmentFactory, UserWithRoleFactory eliminados — DT-002.


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
# DEUDA TÉCNICA 2026-03-21: Modelos IVR no implementados.
# Ver: documentos/planes/PLAN_IVR_SIMPLIFICACION_20260321.md
# ============================================================================
# (Importaciones deshabilitadas — ivr_factories.py sin clases activas)


# ============================================================================
# PIPELINE FACTORIES (apps/pipeline/)
# DEUDA TÉCNICA 2026-03-21: ETLJob, ETLError, SchedulerConfig, DataQualityCheck
# no existen en apps.pipeline.models. Importación silenciosa.
# ============================================================================

try:
    from .pipeline_factories import (
        ETLJobFactory, PendingETLJobFactory, RunningETLJobFactory,
        SuccessETLJobFactory, FailedETLJobFactory, ETLErrorFactory,
        ValidationErrorFactory, ConnectionErrorFactory, DataQualityErrorFactory,
        SchedulerConfigFactory, DailyJobConfigFactory, HourlyJobConfigFactory,
        HealthCheckConfigFactory, DataQualityCheckFactory, PassedCheckFactory,
        FailedCheckFactory, CompleteETLRunFactory, SchedulerHistoryFactory,
    )
except ImportError:
    pass  # Modelos Pipeline no implementados aún


# ============================================================================
# REPORT FACTORIES (apps/reports/)
# DEUDA TÉCNICA 2026-03-21: Importación silenciosa hasta que modelos sean estables.
# ============================================================================

try:
    from .report_factories import (
        ReportFactory,
        QuarterlyReportFactory as QuarterlyReportReportFactory,
        TransferReportFactory as TransferReportReportFactory,
        AbandonedReportFactory as AbandonedReportReportFactory,
        ClientReportFactory as ClientReportReportFactory,
        CustomReportFactory, ReportExecutionFactory, PendingExecutionFactory,
        RunningExecutionFactory, SuccessExecutionFactory, FailedExecutionFactory,
        ReportTemplateFactory, QuarterlyTemplateFactory, TransferTemplateFactory,
        ReportScheduleFactory, QuarterlyScheduleFactory, WeeklyScheduleFactory,
        ReportCacheFactory, CompleteReportFactory, TemplateWithScheduleFactory,
    )
except ImportError:
    pass  # Modelos Report no estables aún


# ============================================================================
# DASHBOARD FACTORIES (apps/dashboard/) - FUTURO
# DEUDA TÉCNICA 2026-03-21: Importación silenciosa hasta implementación.
# ============================================================================

try:
    from .dashboard_factories import (
        DashboardConfigFactory, DefaultDashboardFactory, PublicDashboardFactory,
        WidgetConfigFactory, CallsChartWidgetFactory, TransfersChartWidgetFactory,
        AbandonmentsChartWidgetFactory, TopClientsWidgetFactory,
        MetricsSummaryWidgetFactory, SavedFilterFactory, QuarterlyFilterFactory,
        MonthlyFilterFactory, UserDashboardPreferenceFactory,
        CompleteDashboardFactory, UserWithDashboardFactory,
    )
except ImportError:
    pass  # Dashboard no implementado aún


# ============================================================================
# ALERT FACTORIES (apps/alerts/) - FUTURO
# DEUDA TÉCNICA 2026-03-21: Importación silenciosa hasta implementación.
# ============================================================================

try:
    from .alert_factories import (
        AlertRuleFactory, ThresholdAlertRuleFactory, HighAbandonmentRuleFactory,
        LowCallVolumeRuleFactory, LongQueueTimeRuleFactory, TrendAlertRuleFactory,
        AnomalyAlertRuleFactory, AlertFactory, TriggeredAlertFactory,
        ResolvedAlertFactory, CriticalAlertFactory, HighAlertFactory,
        MediumAlertFactory, LowAlertFactory, AlertNotificationFactory,
        EmailNotificationFactory, PendingNotificationFactory, SentNotificationFactory,
        DeliveredNotificationFactory, FailedNotificationFactory,
        ReadNotificationFactory, AlertHistoryFactory, TriggeredHistoryFactory,
        ResolvedHistoryFactory, AcknowledgedHistoryFactory, EscalatedHistoryFactory,
        CompleteAlertFactory, AlertLifecycleFactory, UserWithAlertsFactory,
    )
except ImportError:
    pass  # Alerts no implementado aún


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
    'UserPermissionFactory',
    'UserWithModuleAccessFactory',
    'UserWithFunctionFactory',
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
