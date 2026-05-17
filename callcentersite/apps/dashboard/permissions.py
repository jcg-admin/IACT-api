"""
Permissions para la app Dashboard.

Sistema de permisos basado en roles (RBAC) para:
- Dashboards: creación, lectura, actualización, eliminación
- Widgets: gestión completa
- Filtros: públicos y privados
- Preferencias: solo propias

Funciones implementadas:
- can_view_dashboard
- can_edit_dashboard
- can_delete_dashboard
- can_create_dashboard
- can_view_widget
- can_edit_widget
- can_delete_widget
- can_view_filter
- can_edit_filter
- can_manage_preferences

FASE 5: Implementación de permissions.
"""

from rest_framework.permissions import BasePermission


# ==============================================================================
# PERMISSION FUNCTIONS - Dashboard
# ==============================================================================

def can_view_dashboard(user, dashboard):
    """
    Verificar si usuario puede ver un dashboard.

    Reglas:
    - Propietario: Siempre puede ver
    - Dashboard público: Todos pueden ver
    - Admin: Puede ver todos
    - Otros: No pueden ver

    Args:
        user: Usuario solicitante
        dashboard: Instancia de DashboardConfig

    Returns:
        Boolean
    """
    # Usuario no autenticado
    if not user or not user.is_authenticated:
        return False

    # Admin puede ver todos
    if user.is_staff or user.is_superuser:
        return True

    # Propietario puede ver
    if dashboard.user == user:
        return True

    # Dashboard público puede ser visto por todos
    if dashboard.is_public:
        return True

    return False


def can_edit_dashboard(user, dashboard):
    """
    Verificar si usuario puede editar un dashboard.

    Reglas:
    - Propietario: Puede editar
    - Admin: Puede editar todos
    - Otros: No pueden editar

    Args:
        user: Usuario solicitante
        dashboard: Instancia de DashboardConfig

    Returns:
        Boolean
    """
    if not user or not user.is_authenticated:
        return False

    # Admin puede editar todos
    if user.is_staff or user.is_superuser:
        return True

    # Solo propietario puede editar
    if dashboard.user == user:
        return True

    return False


def can_delete_dashboard(user, dashboard):
    """
    Verificar si usuario puede eliminar un dashboard.

    Reglas:
    - Propietario: Puede eliminar
    - Admin: Puede eliminar todos
    - Otros: No pueden eliminar

    Args:
        user: Usuario solicitante
        dashboard: Instancia de DashboardConfig

    Returns:
        Boolean
    """
    if not user or not user.is_authenticated:
        return False

    # Admin puede eliminar todos
    if user.is_staff or user.is_superuser:
        return True

    # Solo propietario puede eliminar
    if dashboard.user == user:
        return True

    return False


def can_create_dashboard(user):
    """
    Verificar si usuario puede crear un dashboard.

    Reglas:
    - Usuario autenticado: Puede crear
    - No autenticado: No puede crear

    Args:
        user: Usuario solicitante

    Returns:
        Boolean
    """
    return user and user.is_authenticated


# ==============================================================================
# PERMISSION FUNCTIONS - Widget
# ==============================================================================

def can_view_widget(user, widget):
    """
    Verificar si usuario puede ver un widget.

    Reglas:
    - Propietario del dashboard: Puede ver
    - Dashboard público: Puede ver
    - Admin: Puede ver todos
    - Otros: No pueden ver

    Args:
        user: Usuario solicitante
        widget: Instancia de WidgetConfig

    Returns:
        Boolean
    """
    # Delega al permiso del dashboard padre
    return can_view_dashboard(user, widget.dashboard)


def can_edit_widget(user, widget):
    """
    Verificar si usuario puede editar un widget.

    Reglas:
    - Propietario del dashboard: Puede editar
    - Admin: Puede editar todos
    - Otros: No pueden editar

    Args:
        user: Usuario solicitante
        widget: Instancia de WidgetConfig

    Returns:
        Boolean
    """
    # Delega al permiso del dashboard padre
    return can_edit_dashboard(user, widget.dashboard)


def can_delete_widget(user, widget):
    """
    Verificar si usuario puede eliminar un widget.

    Reglas:
    - Propietario del dashboard: Puede eliminar
    - Admin: Puede eliminar todos
    - Otros: No pueden eliminar

    Args:
        user: Usuario solicitante
        widget: Instancia de WidgetConfig

    Returns:
        Boolean
    """
    # Delega al permiso del dashboard padre
    return can_edit_dashboard(user, widget.dashboard)


# ==============================================================================
# PERMISSION FUNCTIONS - SavedFilter
# ==============================================================================

def can_view_filter(user, saved_filter):
    """
    Verificar si usuario puede ver un filtro guardado.

    Reglas:
    - Propietario: Puede ver
    - Filtro público: Todos pueden ver
    - Admin: Puede ver todos
    - Otros: No pueden ver

    Args:
        user: Usuario solicitante
        saved_filter: Instancia de SavedFilter

    Returns:
        Boolean
    """
    if not user or not user.is_authenticated:
        return False

    # Admin puede ver todos
    if user.is_staff or user.is_superuser:
        return True

    # Propietario puede ver
    if saved_filter.user == user:
        return True

    # Filtro público puede ser visto por todos
    if saved_filter.is_public:
        return True

    return False


def can_edit_filter(user, saved_filter):
    """
    Verificar si usuario puede editar un filtro guardado.

    Reglas:
    - Propietario: Puede editar
    - Admin: Puede editar todos
    - Otros: No pueden editar

    Args:
        user: Usuario solicitante
        saved_filter: Instancia de SavedFilter

    Returns:
        Boolean
    """
    if not user or not user.is_authenticated:
        return False

    # Admin puede editar todos
    if user.is_staff or user.is_superuser:
        return True

    # Solo propietario puede editar
    if saved_filter.user == user:
        return True

    return False


# ==============================================================================
# PERMISSION FUNCTIONS - UserDashboardPreference
# ==============================================================================

def can_manage_preferences(user, preference):
    """
    Verificar si usuario puede gestionar preferencias.

    Reglas:
    - Propietario: Puede gestionar sus propias preferencias
    - Admin: Puede gestionar todas
    - Otros: No pueden gestionar

    Args:
        user: Usuario solicitante
        preference: Instancia de UserDashboardPreference

    Returns:
        Boolean
    """
    if not user or not user.is_authenticated:
        return False

    # Admin puede gestionar todas
    if user.is_staff or user.is_superuser:
        return True

    # Solo propietario puede gestionar sus preferencias
    if preference.user == user:
        return True

    return False


# ==============================================================================
# DRF PERMISSION CLASSES
# ==============================================================================

class IsDashboardOwnerOrReadOnly(BasePermission):
    """
    Permiso DRF: Propietario puede editar, otros solo leer si es público.

    Uso en ViewSets de Dashboard.
    """

    def has_object_permission(self, request, view, obj):
        """
        Verificar permisos a nivel de objeto.

        Args:
            request: Request HTTP
            view: Vista actual
            obj: Objeto DashboardConfig

        Returns:
            Boolean
        """
        # GET, HEAD, OPTIONS permitidos si puede ver
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return can_view_dashboard(request.user, obj)

        # POST, PUT, PATCH, DELETE solo para propietario
        return can_edit_dashboard(request.user, obj)


class IsWidgetOwnerOrReadOnly(BasePermission):
    """
    Permiso DRF: Propietario del dashboard puede editar widget.

    Uso en ViewSets de Widget.
    """

    def has_object_permission(self, request, view, obj):
        """
        Verificar permisos a nivel de objeto.

        Args:
            request: Request HTTP
            view: Vista actual
            obj: Objeto WidgetConfig

        Returns:
            Boolean
        """
        # GET, HEAD, OPTIONS permitidos si puede ver
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return can_view_widget(request.user, obj)

        # POST, PUT, PATCH, DELETE solo para propietario del dashboard
        return can_edit_widget(request.user, obj)


class IsFilterOwnerOrReadOnly(BasePermission):
    """
    Permiso DRF: Propietario puede editar filtro, otros solo leer si es público.

    Uso en ViewSets de SavedFilter.
    """

    def has_object_permission(self, request, view, obj):
        """
        Verificar permisos a nivel de objeto.

        Args:
            request: Request HTTP
            view: Vista actual
            obj: Objeto SavedFilter

        Returns:
            Boolean
        """
        # GET, HEAD, OPTIONS permitidos si puede ver
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return can_view_filter(request.user, obj)

        # POST, PUT, PATCH, DELETE solo para propietario
        return can_edit_filter(request.user, obj)


class IsPreferenceOwner(BasePermission):
    """
    Permiso DRF: Solo propietario puede gestionar sus preferencias.

    Uso en ViewSets de UserDashboardPreference.
    """

    def has_object_permission(self, request, view, obj):
        """
        Verificar permisos a nivel de objeto.

        Args:
            request: Request HTTP
            view: Vista actual
            obj: Objeto UserDashboardPreference

        Returns:
            Boolean
        """
        # Solo propietario puede gestionar
        return can_manage_preferences(request.user, obj)


# ==============================================================================
# RBAC PERMISSION CLASSES (MODELO GRANULAR)
# ==============================================================================

class CanCreateDashboard(BasePermission):
    """
    Permiso RBAC para crear dashboards.

    Requiere función 'dashboard.create' (DASH_CREATE).

    MODELO GRANULAR: Control basado en funciones RBAC, no solo autenticación.
    """

    def has_permission(self, request, view):
        """Verificar si usuario puede crear dashboards."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Superuser siempre puede
        if request.user.is_superuser:
            return True

        # Verificar función RBAC
        return request.user.has_function('dashboard.create')


class CanCreateWidget(BasePermission):
    """
    Permiso RBAC para crear widgets.

    Requiere función 'dashboard.widget.create' (DASH_WIDGET_CREATE).

    MODELO GRANULAR: Control basado en funciones RBAC.
    """

    def has_permission(self, request, view):
        """Verificar si usuario puede crear widgets."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Superuser siempre puede
        if request.user.is_superuser:
            return True

        # Verificar función RBAC
        return request.user.has_function('dashboard.widget.create')
