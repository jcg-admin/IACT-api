"""
apps/access/urls.py

URLs de control de acceso — FASE 0 + FASE 1 + FASE 2 + FASE 3.

Orden de declaración CRÍTICO:
  Las rutas FASE 2/3 se declaran ANTES de include(router.urls) para que
  Django las resuelva primero (first-match). El router registra las rutas
  legacy que conviven con las canónicas.

Hallazgo B-01 / B-02 / B-03 (FASE 2):
  Los imports de FunctionAssignView y FunctionRevokeView desde views.py
  sobreescribían los de function_assign_view.py. Las rutas FASE 2 nunca
  se agregaron a urlpatterns. El router registraba 'groups/' y
  'separation-rules/' con precedencia, bloqueando las vistas canónicas.

STD_008 FASE 3 (2026-05-13):
  sod-rules/ → separation-rules/ (canonical — IACT-ui espera esta URL)
  sod-rule-* names → separation-rule-* names
  separation-rules/validate agregado (canonical — accessGateway.validateSeparationRules)
  router.register separation-rules eliminado (evitar colisión operationId drf-spectacular)
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# ── FASE 2/3 — importaciones canónicas (DEBEN preceder a views.py) ──
from .access_group_view import AccessGroupListCreateView, AccessGroupDetailView
from .separation_rule_view import SeparationRuleListCreateView, SeparationRuleDetailView
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
    ExceptionalPermissionViewSet,
    EffectivePermissionsView,
    FunctionListView,
    UserEffectivePermissionsAliasView,
    FunctionAssignView      as FunctionAssignLegacy,
    FunctionRevokeView      as FunctionRevokeLegacy,
    SeparationRuleValidateView,
    SeparationRuleValidateLegacyView,
    GrouperListView,
    GrouperAssignView,
    UserFunctionAssignView,
    UserFunctionRevokeView,
    MenuItemViewSet,
    MenuItemTransitionView,
    PermissionVerifyView,
)
from apps.audit.access_audit_views import (
    AccessAuditListView, AccessAuditDetailView, AccessAuditAggregationsView,
)
from .exceptional_permission_views import (
    ExceptionalGrantView   as _ExceptionalGrantView,
    ExceptionalPreviewView as _ExceptionalPreviewView,
    ExceptionalRevokeView  as _ExceptionalRevokeView,
)

# STD_008 FASE 3: SeparationRuleViewSet eliminado del router para evitar
# colisión de operationId con las rutas explícitas de separation-rules/.
# El ViewSet queda en views.py marcado deprecated hasta su eliminación definitiva.
router = DefaultRouter()
router.register(r'modules',          ModuleViewSet,                basename='module')
router.register(r'module-accesses',  UserModuleAccessViewSet,      basename='moduleaccess')
router.register(r'groups',           AccessGroupViewSet,           basename='accessgroup')
router.register(r'user-groups',      UserAccessGroupViewSet,       basename='useraccessgroup')
router.register(r'exceptional',      ExceptionalPermissionViewSet, basename='exceptional')
router.register(r'menu-items',       MenuItemViewSet,              basename='menuitem')

app_name = 'access'

urlpatterns = [
    # ==================================================================
    # FASE 2/3 — Rutas canónicas (declaradas ANTES del router)
    # ==================================================================

    # UC_PERM_05 — Gestionar Grupos de Funciones (AGR custom)
    path('access-groups/',
         AccessGroupListCreateView.as_view(), name='access-group-list-create'),
    path('access-groups/<int:agr_id>/',
         AccessGroupDetailView.as_view(), name='access-group-detail'),
    path('access-groups/<int:agr_id>/functions/',
         FunctionGroupFnView.as_view(), name='access-group-functions'),

    # UC_ACC_05 — Reglas de Separación de Funciones
    # STD_008 FASE 3: separation-rules/ (IACT-ui ya usaba esta URL)
    path('separation-rules/',
         SeparationRuleListCreateView.as_view(), name='separation-rule-list-create'),
    path('separation-rules/<int:rule_id>/',
         SeparationRuleDetailView.as_view(), name='separation-rule-detail'),

    # UC_ACC_01 — Validar conflictos antes de asignar (canonical)
    # accessGateway.validateSeparationRules() → POST /access/separation-rules/validate
    # NOTA: declarado ANTES de separation-rules/<int:rule_id>/ — no hay conflicto porque
    # 'validate' no es un entero, por lo que <int:rule_id> no lo captura.
    path('separation-rules/validate',
         SeparationRuleValidateView.as_view(), name='separation-rule-validate'),

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

    # Legacy IACT-ui compatibility (accessService.js contratos heredados)
    path('functions/assign',
         FunctionAssignLegacy.as_view(), name='function-assign'),
    path('functions/revoke',
         FunctionRevokeLegacy.as_view(), name='function-revoke'),
    # validate-sod: legacy endpoint sin consumidor activo en IACT-ui.
    # El frontend ya migró a separation-rules/validate.
    # Se mantiene para backward compat hasta deprecación formal.
    path('validate-sod',
         SeparationRuleValidateLegacyView.as_view(), name='validate-separation'),
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
    # UC_ACC_09 — Auditar cambios de acceso (FASE 5)
    path('audit/',                      AccessAuditListView.as_view(),         name='access-audit-list'),
    path('audit/<int:event_id>/',       AccessAuditDetailView.as_view(),       name='access-audit-detail'),
    path('audit/aggregations/',         AccessAuditAggregationsView.as_view(), name='access-audit-aggregations'),
    # UC_ACC_08, UC_PERM_03, UC_PERM_04 — Permisos Excepcionales (FASE 4)
    # ==================================================================
    path('users/<int:user_id>/exceptional-permissions/',
         _ExceptionalGrantView.as_view(),   name='exceptional-grant'),
    path('users/<int:user_id>/exceptional-permissions/preview/',
         _ExceptionalPreviewView.as_view(), name='exceptional-preview'),
    path('users/<int:user_id>/exceptional-permissions/<int:permission_id>/',
         _ExceptionalRevokeView.as_view(),  name='exceptional-revoke'),

    # ==================================================================
    # Router legacy (al final — prioridad mínima)
    # ==================================================================
    path('', include(router.urls)),
]
