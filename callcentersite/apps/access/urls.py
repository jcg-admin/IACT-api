"""
apps/access/urls.py

URLs de control de acceso — FASE 0 + FASE 1 + FASE 2.

Orden de declaración CRÍTICO:
  Las rutas FASE 2 se declaran ANTES de include(router.urls) para que
  Django las resuelva primero (first-match). El router registra las rutas
  legacy que conviven con las canónicas de FASE 2.

Hallazgo B-01 / B-02 / B-03 (FASE 2):
  Los imports de FunctionAssignView y FunctionRevokeView desde views.py
  sobreescribían los de function_assign_view.py. Las rutas FASE 2 nunca
  se agregaron a urlpatterns. El router registraba 'groups/' y
  'separation-rules/' con precedencia, bloqueando las vistas canónicas.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# ── FASE 2 — importaciones canónicas (DEBEN preceder a views.py) ──
from .access_group_view import AccessGroupListCreateView, AccessGroupDetailView
from .sod_rule_view import SoDRuleListCreateView, SoDRuleDetailView
from .function_assign_view import (
    FunctionAssignView      as FunctionAssignV2,
    FunctionRevokeView      as FunctionRevokeV2,
    AGRAssignView,
    AGRRevokeView,
    FunctionGroupFnView,
)

# ── Legacy FASE 0/1 — importaciones ──
from .views import (
    ModuleViewSet, UserModuleAccessViewSet, MyModulesView,
    AccessGroupViewSet, UserAccessGroupViewSet,
    SeparationRuleViewSet, ExceptionalPermissionViewSet,
    EffectivePermissionsView,
    FunctionListView,
    UserEffectivePermissionsAliasView,
    FunctionAssignView      as FunctionAssignLegacy,
    FunctionRevokeView      as FunctionRevokeLegacy,
    SeparationRuleValidateView,
    GrouperListView,
    GrouperAssignView,
    UserFunctionAssignView,
    UserFunctionRevokeView,
    MenuItemViewSet,
    MenuItemTransitionView,
    PermissionVerifyView,
)

router = DefaultRouter()
router.register(r'modules',          ModuleViewSet,                basename='module')
router.register(r'module-accesses',  UserModuleAccessViewSet,      basename='moduleaccess')
router.register(r'groups',           AccessGroupViewSet,           basename='accessgroup')
router.register(r'user-groups',      UserAccessGroupViewSet,       basename='useraccessgroup')
router.register(r'separation-rules', SeparationRuleViewSet,        basename='separationrule')
router.register(r'exceptional',      ExceptionalPermissionViewSet, basename='exceptional')
router.register(r'menu-items',       MenuItemViewSet,              basename='menuitem')

app_name = 'access'

urlpatterns = [
    # ==================================================================
    # FASE 2 — Rutas canónicas (declaradas ANTES del router para prioridad)
    # ==================================================================

    # UC_PERM_05 — Gestionar Grupos de Funciones (AGR custom)
    # B-03: usa prefijo 'access-groups/' para evitar conflicto con router 'groups/'
    path('access-groups/',
         AccessGroupListCreateView.as_view(), name='access-group-list-create'),
    path('access-groups/<int:agr_id>/',
         AccessGroupDetailView.as_view(), name='access-group-detail'),
    path('access-groups/<int:agr_id>/functions/',
         FunctionGroupFnView.as_view(), name='access-group-functions'),

    # UC_ACC_05 — Reglas SoD
    # B-03: usa prefijo 'sod-rules/' para evitar conflicto con router 'separation-rules/'
    path('sod-rules/',
         SoDRuleListCreateView.as_view(), name='sod-rule-list-create'),
    path('sod-rules/<int:rule_id>/',
         SoDRuleDetailView.as_view(), name='sod-rule-detail'),

    # UC_ACC_01 / UC_ACC_02 — Asignar / Revocar funciones (canónico)
    path('users/<int:user_id>/functions/assign/',
         FunctionAssignV2.as_view(), name='function-assign-v2'),
    path('users/<int:user_id>/functions/revoke/',
         FunctionRevokeV2.as_view(), name='function-revoke-v2'),

    # UC_ACC_04 / UC_PERM_01 / UC_PERM_02 — Asignar / Revocar AGR
    path('users/<int:user_id>/agr/',
         AGRAssignView.as_view(), name='agr-assign'),
    path('users/<int:user_id>/agr/<int:agr_id>/',
         AGRRevokeView.as_view(), name='agr-revoke'),

    # ==================================================================
    # FASE 1 + FASE 0 — Rutas canónicas explícitas
    # ==================================================================

    # FASE 1 UC_PERM_07 — verificación de permiso con PrecedenceEvaluator
    path('permissions/verify/',
         PermissionVerifyView.as_view(), name='permission-verify'),

    # UC_ACC_03 / UC_PERM_07 — permisos efectivos
    path('users/<int:user_id>/effective-permissions/',
         EffectivePermissionsView.as_view(), name='effective-permissions'),

    # Función catalog
    path('functions/',
         FunctionListView.as_view(), name='function-list'),
    path('permissions/<int:user_id>/',
         UserEffectivePermissionsAliasView.as_view(), name='user-permissions'),

    # Legacy IACT-ui compatibility (accessService.js contratos)
    path('functions/assign',
         FunctionAssignLegacy.as_view(), name='function-assign'),
    path('functions/revoke',
         FunctionRevokeLegacy.as_view(), name='function-revoke'),
    path('validate-sod',
         SeparationRuleValidateView.as_view(), name='validate-separation'),
    path('groupers/',
         GrouperListView.as_view(), name='grouper-list'),
    path('groupers/assign',
         GrouperAssignView.as_view(), name='grouper-assign'),

    # G-003: UC_ACC_01/02 legacy
    path('users/<int:user_id>/functions/',
         UserFunctionAssignView.as_view(), name='user-function-assign'),
    path('users/<int:user_id>/functions/<int:function_id>/',
         UserFunctionRevokeView.as_view(), name='user-function-revoke'),

    # Modulo lifecycle
    path('my-modules/',
         MyModulesView.as_view(), name='my-modules'),
    path('menu-items/<int:pk>/transition/',
         MenuItemTransitionView.as_view(), name='menuitem-transition'),

    # ==================================================================
    # Router legacy (al final — prioridad mínima)
    # ==================================================================
    path('', include(router.urls)),
]
