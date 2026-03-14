"""
Filtros para apps/access/.

Django-filter filtros para ViewSets de RBAC.

FASE A DT-002: Todos los filtros fueron eliminados con UserServiceAccess.
"""

# ====================================================================================
# REMOVED - FASE A DT-002 (2026-01-21)
# ====================================================================================
#
# UserServiceAccessFilter (eliminado):
#   - Filtros para UserServiceAccess
#   - 10 filtros (user, service, is_active, granted_at, etc)
#
# Razón: UserServiceAccess eliminado, reemplazado por RBAC puro
# Ver: apps/access/models.py
#
# Si necesitas filtros para Module o Function, créalos aquí:
#   - ModuleFilter
#   - FunctionFilter
#   - UserModuleAccessFilter
#   - UserFunctionAssignmentFilter
# ====================================================================================

