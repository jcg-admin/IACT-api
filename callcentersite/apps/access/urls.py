"""
URLs para access app.
B-05: AccessGroup, SeparationRule, ExceptionalPermission endpoints.
B-07: EffectivePermissions endpoint.
"""
from django.urls import path, include
from django.db import models
from rest_framework.routers import DefaultRouter
from .views import (
    ModuleViewSet, UserModuleAccessViewSet, MyModulesView,
    AccessGroupViewSet, UserAccessGroupViewSet,
    SeparationRuleViewSet, ExceptionalPermissionViewSet,
    EffectivePermissionsView,
)

router = DefaultRouter()
router.register(r'modules',           ModuleViewSet,            basename='module')
router.register(r'module-accesses',   UserModuleAccessViewSet,  basename='moduleaccess')
router.register(r'groups',            AccessGroupViewSet,       basename='accessgroup')
router.register(r'user-groups',       UserAccessGroupViewSet,   basename='useraccessgroup')
router.register(r'separation-rules',   SeparationRuleViewSet,    basename='separationrule')
router.register(r'exceptional',       ExceptionalPermissionViewSet, basename='exceptional')

app_name = 'access'

urlpatterns = [
    path('', include(router.urls)),
    path('my-modules/', MyModulesView.as_view(), name='my-modules'),
    # UC_ACC_03 / UC_PERM_07 — permisos efectivos de un usuario
    path('users/<int:user_id>/effective-permissions/',
         EffectivePermissionsView.as_view(),
         name='effective-permissions'),
]
