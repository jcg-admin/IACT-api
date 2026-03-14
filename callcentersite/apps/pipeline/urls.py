"""
URLs para apps/pipeline/.

CLEAN_CODE v3.0.1: Incluye ViewSets + custom views.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.pipeline.views import etl_status
from apps.pipeline.viewsets import (
    CenterViewSet,
    ServiceViewSet,
    CallRecordViewSet,
    CallNoteViewSet,  # FASE 0.2
)

app_name = 'pipeline'

# DRF Router para ViewSets
router = DefaultRouter()
router.register(r'centers', CenterViewSet, basename='center')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'calls', CallRecordViewSet, basename='callrecord')
router.register(r'call-notes', CallNoteViewSet, basename='callnote')  # FASE 0.2

urlpatterns = [
    # ViewSets (DRF Router)
    path('', include(router.urls)),
    
    # Custom views
    path('status/', etl_status, name='etl_status'),
]


# ============================================================================
# ENDPOINTS DISPONIBLES
# 
# ViewSets (CRUD + custom actions):
#   /api/v1/pipeline/centers/
#   /api/v1/pipeline/services/
#   /api/v1/pipeline/calls/
#   /api/v1/pipeline/call-notes/                # FASE 0.2
# 
# Custom Views:
#   /api/v1/pipeline/status/
# ============================================================================
