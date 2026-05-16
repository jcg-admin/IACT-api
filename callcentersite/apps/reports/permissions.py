"""
Permissions para app reports.

Control de acceso basado en RBAC.
"""
from rest_framework.permissions import BasePermission


class CanViewReports(BasePermission):
    """
    Permiso para ver reportes.

    Requiere función 'reports.view' (RPT_VIEW).

    CORREGIDO: Cambiado de 'reports.view_report' a 'reports.view'
    para coincidir con la función definida en create_functions.py
    """

    def has_permission(self, request, view):
        """Verificar si usuario puede ver reportes."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Superuser siempre puede
        if request.user.is_superuser:
            return True

        # Verificar función RBAC (CORREGIDO)
        return request.user.has_function('reports.view')


class CanCreateReports(BasePermission):
    """
    Permiso para crear reportes.

    Requiere función 'reports.create' (RPT_CREATE).

    CORREGIDO: Cambiado de 'reports.create_report' a 'reports.create'
    para coincidir con la función definida en create_functions.py
    """

    def has_permission(self, request, view):
        """Verificar si usuario puede crear reportes."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Superuser siempre puede
        if request.user.is_superuser:
            return True

        # Verificar función RBAC (CORREGIDO)
        return request.user.has_function('reports.create')


class CanExportReports(BasePermission):
    """
    Permiso para exportar reportes.

    Requiere función 'reports.export.csv' (RPT_EXP_CSV) o 'reports.export.excel' (RPT_EXP_EXCEL).
    CNST-007: Valida límite de exportación.

    CORREGIDO: Cambiado de 'reports.export_report' a 'reports.export.csv'
    para coincidir con la función definida en create_functions.py
    """

    def has_permission(self, request, view):
        """Verificar si usuario puede exportar reportes."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Superuser siempre puede
        if request.user.is_superuser:
            return True

        # Verificar función RBAC (CORREGIDO)
        # Acepta cualquiera de los dos permisos de exportación
        return (
            request.user.has_function('reports.export.csv') or
            request.user.has_function('reports.export.excel')
        )


class IsReportOwner(BasePermission):
    """
    Permiso para acceder solo a reportes propios.

    Solo el creador puede ver/modificar su reporte.
    """

    def has_object_permission(self, request, view, obj):
        """Verificar si usuario es dueño del reporte."""
        # Superuser siempre puede
        if request.user.is_superuser:
            return True

        # Verificar ownership
        return obj.created_by == request.user


class CanAccessCallRecordData(BasePermission):
    """
    Permiso para acceder a datos de CallRecord.

    Requiere función 'reports.view_ivr'.

    MODELO GRANULAR: Para crear reportes de llamadas, el usuario
    necesita permiso explícito para ver datos de CallRecord.
    """

    def has_permission(self, request, view):
        """Verificar si usuario puede acceder a datos de llamadas."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Superuser siempre puede
        if request.user.is_superuser:
            return True

        # Verificar función RBAC
        return request.user.has_function('reports.view_ivr')
