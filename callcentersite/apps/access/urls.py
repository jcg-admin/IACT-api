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
    # Endpoints compatibilidad IACT-ui (Fase C)
    FunctionListView,
    UserEffectivePermissionsAliasView,
    FunctionAssignView,
    FunctionRevokeView,
    SeparationRuleValidateView,
    GrouperListView,
    GrouperAssignView,
    # Fase G — endpoints DRF con auditoría (UC_ACC_01/02)
    UserFunctionAssignView,
    UserFunctionRevokeView,
    # v3.1.0 — T-102
    MenuItemViewSet,
    # v3.1.0 — T-104
    MenuItemTransitionView,
)

router = DefaultRouter()
router.register(r'modules',           ModuleViewSet,            basename='module')
router.register(r'module-accesses',   UserModuleAccessViewSet,  basename='moduleaccess')
router.register(r'groups',            AccessGroupViewSet,       basename='accessgroup')
router.register(r'user-groups',       UserAccessGroupViewSet,   basename='useraccessgroup')
router.register(r'separation-rules',   SeparationRuleViewSet,    basename='separationrule')
router.register(r'exceptional',       ExceptionalPermissionViewSet, basename='exceptional')
router.register(r'menu-items',        MenuItemViewSet,           basename='menuitem')

app_name = 'access'

urlpatterns = [
    path('', include(router.urls)),
    path('my-modules/', MyModulesView.as_view(), name='my-modules'),

    # v3.1.0 T-104 — lifecycle de MenuItem
    path('menu-items/<int:pk>/transition/',
         MenuItemTransitionView.as_view(),
         name='menuitem-transition'),

    # UC_ACC_03 / UC_PERM_07 — permisos efectivos (endpoint DRF)
    path('users/<int:user_id>/effective-permissions/',
         EffectivePermissionsView.as_view(),
         name='effective-permissions'),

    # ── Endpoints para compatibilidad con IACT-ui accessService.js ──

    # accessService.getAllFunctions()
    path('functions/',
         FunctionListView.as_view(), name='function-list'),

    # accessService.getUserPermissions(userId)
    path('permissions/<int:user_id>/',
         UserEffectivePermissionsAliasView.as_view(), name='user-permissions'),

    # accessService.assignFunction()
    path('functions/assign',
         FunctionAssignView.as_view(), name='function-assign'),

    # accessService.revokeFunction()
    path('functions/revoke',
         FunctionRevokeView.as_view(), name='function-revoke'),

    # accessService.validateSoD() — URL del contrato frontend (string opaco)
    path('validate-sod',
         SeparationRuleValidateView.as_view(), name='validate-separation'),

    # accessService.getGroupers()
    path('groupers/',
         GrouperListView.as_view(), name='grouper-list'),

    # accessService.assignGrouper()
    path('groupers/assign',
         GrouperAssignView.as_view(), name='grouper-assign'),

    # G-003: UC_ACC_01/02 — asignar/revocar función con auditoría
    path('users/<int:user_id>/functions/',
         UserFunctionAssignView.as_view(), name='user-function-assign'),
    path('users/<int:user_id>/functions/<int:function_id>/',
         UserFunctionRevokeView.as_view(), name='user-function-revoke'),
]
