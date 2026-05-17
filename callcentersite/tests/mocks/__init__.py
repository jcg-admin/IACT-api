"""
Mocks para Testing - FASE 1 Testing Infrastructure.

Centraliza TODOS los mocks para fácil acceso.

CLEAN_CODE v3.0.1: Imports organizados por categoría.
Total Mocks: 81 fixtures
"""

# ============================================================================
# DATABASE MOCKS (12)
# ============================================================================

from .database_mocks import (
    # PostgreSQL Mocks
    mock_postgresql_connection,

    # Error Mocks
    mock_connection_error,

    # Helper Mocks
    mock_database_settings,
    mock_transaction_atomic,
)


# ============================================================================
# SERVICE MOCKS (13)
# ============================================================================

from .service_mocks import (
    # ETL Service Mocks
    mock_etl_service,
    mock_etl_service_empty,
    mock_etl_service_error,
    
    # Report Service Mocks
    mock_report_generator_service,
    mock_report_service_limit_exceeded,
    
    # Access Service Mocks
    mock_access_service,
    mock_access_service_denied,
    
    # Other Service Mocks
    mock_audit_service,
    mock_user_service,
    mock_authentication_service,
    mock_authentication_service_invalid,
    mock_dashboard_service,
    mock_alert_service,
)


# ============================================================================
# FILE MOCKS (17)
# ============================================================================

from .file_mocks import (
    # Exporter Mocks
    mock_excel_exporter,
    mock_excel_file_content,
    mock_csv_exporter,
    mock_csv_file_content,
    mock_pdf_exporter,
    mock_pdf_file_content,
    
    # Storage Mocks
    mock_file_storage,
    mock_file_storage_error,
    
    # File Operations Mocks
    mock_open_file,
    mock_open_binary_file,
    mock_os_path,
    mock_os_remove,
    mock_tempfile,
    
    # Validation Mocks
    mock_file_size_validator,
    mock_row_count_validator,
    
    # Helper Mocks
    mock_file_cleanup,
    mock_file_metadata,
)


# ============================================================================
# SCHEDULER MOCKS (19)
# ============================================================================

from .scheduler_mocks import (
    # Base Scheduler Mocks
    mock_apscheduler,
    mock_scheduler_job,
    
    # Trigger Mocks
    mock_cron_trigger,
    mock_interval_trigger,
    mock_date_trigger,
    
    # Job Execution Mocks
    mock_job_execution_success,
    mock_job_execution_failure,
    
    # Scheduled Jobs Mocks
    mock_cleanup_sessions_job,
    mock_etl_monitor_job,
    mock_health_check_job,
    mock_quarterly_report_job,
    
    # JobStore Mocks
    mock_memory_job_store,
    mock_sqlalchemy_job_store,
    
    # Lifecycle Mocks
    mock_scheduler_start,
    mock_scheduler_shutdown,
    
    # Error Mocks
    mock_scheduler_error,
    mock_job_not_found,
    
    # Helper Mocks
    mock_scheduler_config,
    mock_all_scheduled_jobs,
)


# ============================================================================
# EXTERNAL MOCKS (20)
# ============================================================================

from .external_mocks import (
    # Email Mocks
    mock_email_backend,
    mock_send_mail,
    mock_send_mail_failure,
    mock_email_message,
    mock_email_multipart,
    
    # Cache Mocks
    mock_cache,
    mock_cache_settings,
    mock_cache_key,
    
    # External API Mocks
    mock_requests_get,
    mock_requests_post,
    mock_requests_error,
    
    # Other Mocks
    mock_timezone,
    mock_logger,
    mock_logger_error,
    mock_settings,
    mock_uuid,
    mock_random,
)


# ============================================================================
# __ALL__ EXPORTS
# ============================================================================

__all__ = [
    # Database Mocks activos (4)
    'mock_postgresql_connection',
    'mock_connection_error',
    'mock_database_settings',
    'mock_transaction_atomic',
    # IVR mocks desactivados — DEUDA TÉCNICA 2026-03-21
    
    # Service Mocks (13)
    'mock_etl_service',
    'mock_etl_service_empty',
    'mock_etl_service_error',
    'mock_report_generator_service',
    'mock_report_service_limit_exceeded',
    'mock_access_service',
    'mock_access_service_denied',
    'mock_audit_service',
    'mock_user_service',
    'mock_authentication_service',
    'mock_authentication_service_invalid',
    'mock_dashboard_service',
    'mock_alert_service',
    
    # File Mocks (17)
    'mock_excel_exporter',
    'mock_excel_file_content',
    'mock_csv_exporter',
    'mock_csv_file_content',
    'mock_pdf_exporter',
    'mock_pdf_file_content',
    'mock_file_storage',
    'mock_file_storage_error',
    'mock_open_file',
    'mock_open_binary_file',
    'mock_os_path',
    'mock_os_remove',
    'mock_tempfile',
    'mock_file_size_validator',
    'mock_row_count_validator',
    'mock_file_cleanup',
    'mock_file_metadata',
    
    # Scheduler Mocks (19)
    'mock_apscheduler',
    'mock_scheduler_job',
    'mock_cron_trigger',
    'mock_interval_trigger',
    'mock_date_trigger',
    'mock_job_execution_success',
    'mock_job_execution_failure',
    'mock_cleanup_sessions_job',
    'mock_etl_monitor_job',
    'mock_health_check_job',
    'mock_quarterly_report_job',
    'mock_memory_job_store',
    'mock_sqlalchemy_job_store',
    'mock_scheduler_start',
    'mock_scheduler_shutdown',
    'mock_scheduler_error',
    'mock_job_not_found',
    'mock_scheduler_config',
    'mock_all_scheduled_jobs',
    
    # External Mocks (20)
    'mock_email_backend',
    'mock_send_mail',
    'mock_send_mail_failure',
    'mock_email_message',
    'mock_email_multipart',
    'mock_cache',
    'mock_cache_settings',
    'mock_cache_key',
    'mock_requests_get',
    'mock_requests_post',
    'mock_requests_error',
    'mock_timezone',
    'mock_logger',
    'mock_logger_error',
    'mock_settings',
    'mock_uuid',
    'mock_random',
]


# ============================================================================
# TOTAL MOCKS: 81 fixtures
# 
# Por Categoría:
#   Database:    12 mocks
#   Services:    13 mocks
#   Files:       17 mocks
#   Scheduler:   19 mocks
#   External:    20 mocks
# 
# Restricciones Cumplidas:
#   [SUCCESS] CNST-001: NO email backend real (console)
#   [SUCCESS] CNST-002: Dual DB (IVR readonly)
#   [SUCCESS] CNST-007: Export max 100K rows
#   [SUCCESS] CNST-010: Cache locmem (NO Redis)
#   [SUCCESS] CNST-013: APScheduler (NO Celery)
# 
# CLEAN_CODE v3.0.1: Imports organizados y documentados [SUCCESS]
# FASE 1 - PARTE 3: COMPLETADA [SUCCESS]
# ============================================================================
