"""
URLs para pipeline app — UC_PIP_01..04 + ivr-health.

Center, Service, CallRecord y CallNote eliminados en FASE 3.
UC_OPR/UC_SUP/UC_CLI están fuera del scope analítico de IACT-api.
"""
from django.urls import path
from .views import etl_status, etl_errors, etl_data_availability, etl_retry, ivr_health

app_name = 'pipeline'

urlpatterns = [
    # UC_PIP_01 — estado del ETL
    path('status/',            etl_status,            name='etl-status'),

    # UC_PIP_02 — errores del ETL
    path('errors/',            etl_errors,            name='etl-errors'),

    # UC_PIP_03 — disponibilidad de datos
    path('data-availability/', etl_data_availability, name='etl-data-availability'),

    # UC_PIP_04 — solicitar reintento
    path('retry/',             etl_retry,             name='etl-retry'),

    # ivr-health — MariaDB connectivity check
    path('ivr-health/',        ivr_health,            name='ivr-health'),
]
