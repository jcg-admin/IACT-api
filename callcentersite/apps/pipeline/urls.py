"""
URLs para pipeline app.
B-02 (ya corregido): status lee de MariaDB.
B-04: errores, disponibilidad y reintento.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import CenterViewSet, ServiceViewSet, CallRecordViewSet, CallNoteViewSet
from .views import etl_status, etl_errors, etl_data_availability, etl_retry, ivr_health

router = DefaultRouter()
router.register(r'centers',    CenterViewSet,     basename='center')
router.register(r'services',   ServiceViewSet,    basename='service')
router.register(r'calls',      CallRecordViewSet, basename='callrecord')
router.register(r'call-notes', CallNoteViewSet,   basename='callnote')

app_name = 'pipeline'

urlpatterns = [
    path('', include(router.urls)),

    # UC_PIP_01 — estado del ETL (B-02 corregido)
    path('status/',            etl_status,            name='etl-status'),

    # UC_PIP_02 — errores del ETL (B-04)
    path('errors/',            etl_errors,            name='etl-errors'),

    # UC_PIP_03 — disponibilidad de datos (B-04)
    path('data-availability/', etl_data_availability, name='etl-data-availability'),

    # UC_PIP_04 — solicitar reintento (B-04)
    path('retry/',             etl_retry,             name='etl-retry'),

    # I-003 — IVR MariaDB health check
    path('ivr-health/',        ivr_health,            name='ivr-health'),
]
