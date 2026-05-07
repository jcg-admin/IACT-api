"""
Control de acceso basado en funciones para la app Dashboard.

Verifica ownership y funciones asignadas al usuario, no roles.

Decoradores para vistas basadas en funciones (FBV):
- require_dashboard_owner
- require_dashboard_view
- require_widget_owner
- require_widget_view
- require_filter_owner
- require_authenticated

Funciones helper:
- check_dashboard_access
- check_widget_access
- check_filter_access
- get_user_dashboards
- get_user_widgets

FASE 8: Implementación de RBAC.
"""

from functools import wraps
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

from apps.dashboard.models import (
    DashboardConfig,
    WidgetConfig,
    SavedFilter,
    UserDashboardPreference
)
from apps.dashboard.permissions import (
    can_view_dashboard,
    can_edit_dashboard,
    can_delete_dashboard,
    can_view_widget,
    can_edit_widget,
    can_delete_widget,
    can_view_filter,
    can_edit_filter
)


# ==============================================================================
# DECORADORES PARA DASHBOARDS
# ==============================================================================

def require_dashboard_owner(view_func):
    """
    Decorador que requiere que el usuario sea propietario del dashboard.
    
    Uso:
        @require_dashboard_owner
        def my_view(request, dashboard_id):
            # Solo ejecuta si usuario es propietario
            ...
    
    Args:
        view_func: Vista a decorar
    
    Returns:
        Función decorada
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, dashboard_id=None, *args, **kwargs):
        # Obtener dashboard
        dashboard = get_object_or_404(
            DashboardConfig,
            id=dashboard_id,
            deleted_at__isnull=True
        )
        
        # Verificar permisos de edición (solo propietario)
        if not can_edit_dashboard(request.user, dashboard):
            return JsonResponse({
                'status': 'error',
                'message': 'No tienes permisos para editar este dashboard'
            }, status=403)
        
        # Agregar dashboard al request para acceso en la vista
        request.dashboard = dashboard
        
        return view_func(request, dashboard_id=dashboard_id, *args, **kwargs)
    
    return wrapper


def require_dashboard_view(view_func):
    """
    Decorador que requiere que el usuario pueda ver el dashboard.
    
    Permite:
    - Propietario del dashboard
    - Dashboards públicos
    - Administradores
    
    Uso:
        @require_dashboard_view
        def my_view(request, dashboard_id):
            # Solo ejecuta si usuario puede ver
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, dashboard_id=None, *args, **kwargs):
        # Obtener dashboard
        dashboard = get_object_or_404(
            DashboardConfig,
            id=dashboard_id,
            deleted_at__isnull=True
        )
        
        # Verificar permisos de visualización
        if not can_view_dashboard(request.user, dashboard):
            return JsonResponse({
                'status': 'error',
                'message': 'No tienes permisos para ver este dashboard'
            }, status=403)
        
        # Agregar dashboard al request
        request.dashboard = dashboard
        
        return view_func(request, dashboard_id=dashboard_id, *args, **kwargs)
    
    return wrapper


# ==============================================================================
# DECORADORES PARA WIDGETS
# ==============================================================================

def require_widget_owner(view_func):
    """
    Decorador que requiere que el usuario sea propietario del widget.
    
    Verifica ownership a través del dashboard padre.
    
    Uso:
        @require_widget_owner
        def my_view(request, widget_id):
            # Solo ejecuta si usuario es propietario
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, widget_id=None, *args, **kwargs):
        # Obtener widget con dashboard relacionado
        widget = get_object_or_404(
            WidgetConfig.objects.select_related('dashboard'),
            id=widget_id
        )
        
        # Verificar permisos de edición
        if not can_edit_widget(request.user, widget):
            return JsonResponse({
                'status': 'error',
                'message': 'No tienes permisos para editar este widget'
            }, status=403)
        
        # Agregar widget al request
        request.widget = widget
        request.dashboard = widget.dashboard
        
        return view_func(request, widget_id=widget_id, *args, **kwargs)
    
    return wrapper


def require_widget_view(view_func):
    """
    Decorador que requiere que el usuario pueda ver el widget.
    
    Permite:
    - Propietario del dashboard padre
    - Dashboard padre público
    - Administradores
    
    Uso:
        @require_widget_view
        def my_view(request, widget_id):
            # Solo ejecuta si usuario puede ver
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, widget_id=None, *args, **kwargs):
        # Obtener widget con dashboard relacionado
        widget = get_object_or_404(
            WidgetConfig.objects.select_related('dashboard'),
            id=widget_id
        )
        
        # Verificar permisos de visualización
        if not can_view_widget(request.user, widget):
            return JsonResponse({
                'status': 'error',
                'message': 'No tienes permisos para ver este widget'
            }, status=403)
        
        # Agregar widget al request
        request.widget = widget
        request.dashboard = widget.dashboard
        
        return view_func(request, widget_id=widget_id, *args, **kwargs)
    
    return wrapper


# ==============================================================================
# DECORADORES PARA FILTERS
# ==============================================================================

def require_filter_owner(view_func):
    """
    Decorador que requiere que el usuario sea propietario del filtro.
    
    Uso:
        @require_filter_owner
        def my_view(request, filter_id):
            # Solo ejecuta si usuario es propietario
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, filter_id=None, *args, **kwargs):
        # Obtener filtro
        saved_filter = get_object_or_404(
            SavedFilter,
            id=filter_id,
            deleted_at__isnull=True
        )
        
        # Verificar permisos de edición
        if not can_edit_filter(request.user, saved_filter):
            return JsonResponse({
                'status': 'error',
                'message': 'No tienes permisos para editar este filtro'
            }, status=403)
        
        # Agregar filtro al request
        request.saved_filter = saved_filter
        
        return view_func(request, filter_id=filter_id, *args, **kwargs)
    
    return wrapper


def require_filter_view(view_func):
    """
    Decorador que requiere que el usuario pueda ver el filtro.
    
    Permite:
    - Propietario del filtro
    - Filtros públicos
    - Administradores
    
    Uso:
        @require_filter_view
        def my_view(request, filter_id):
            # Solo ejecuta si usuario puede ver
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, filter_id=None, *args, **kwargs):
        # Obtener filtro
        saved_filter = get_object_or_404(
            SavedFilter,
            id=filter_id,
            deleted_at__isnull=True
        )
        
        # Verificar permisos de visualización
        if not can_view_filter(request.user, saved_filter):
            return JsonResponse({
                'status': 'error',
                'message': 'No tienes permisos para ver este filtro'
            }, status=403)
        
        # Agregar filtro al request
        request.saved_filter = saved_filter
        
        return view_func(request, filter_id=filter_id, *args, **kwargs)
    
    return wrapper


# ==============================================================================
# FUNCIONES HELPER
# ==============================================================================

def check_dashboard_access(user, dashboard_id, permission='view'):
    """
    Verificar acceso de usuario a dashboard.
    
    Args:
        user: Usuario a verificar
        dashboard_id: ID del dashboard
        permission: Tipo de permiso ('view', 'edit', 'delete')
    
    Returns:
        tuple: (has_access: bool, dashboard: DashboardConfig|None, error_msg: str|None)
    
    Examples:
        >>> has_access, dashboard, error = check_dashboard_access(user, 123, 'edit')
        >>> if has_access:
        >>>     # Proceder con la operación
    """
    try:
        dashboard = DashboardConfig.objects.get(
            id=dashboard_id,
            deleted_at__isnull=True
        )
    except DashboardConfig.DoesNotExist:
        return False, None, 'Dashboard no encontrado'
    
    # Verificar según tipo de permiso
    if permission == 'view':
        has_access = can_view_dashboard(user, dashboard)
        error_msg = 'No tienes permisos para ver este dashboard'
    elif permission == 'edit':
        has_access = can_edit_dashboard(user, dashboard)
        error_msg = 'No tienes permisos para editar este dashboard'
    elif permission == 'delete':
        has_access = can_delete_dashboard(user, dashboard)
        error_msg = 'No tienes permisos para eliminar este dashboard'
    else:
        return False, dashboard, f'Permiso inválido: {permission}'
    
    if has_access:
        return True, dashboard, None
    else:
        return False, dashboard, error_msg


def check_widget_access(user, widget_id, permission='view'):
    """
    Verificar acceso de usuario a widget.
    
    Args:
        user: Usuario a verificar
        widget_id: ID del widget
        permission: Tipo de permiso ('view', 'edit', 'delete')
    
    Returns:
        tuple: (has_access: bool, widget: WidgetConfig|None, error_msg: str|None)
    """
    try:
        widget = WidgetConfig.objects.select_related('dashboard').get(
            id=widget_id
        )
    except WidgetConfig.DoesNotExist:
        return False, None, 'Widget no encontrado'
    
    # Verificar según tipo de permiso
    if permission == 'view':
        has_access = can_view_widget(user, widget)
        error_msg = 'No tienes permisos para ver este widget'
    elif permission in ['edit', 'delete']:
        has_access = can_edit_widget(user, widget)
        error_msg = 'No tienes permisos para modificar este widget'
    else:
        return False, widget, f'Permiso inválido: {permission}'
    
    if has_access:
        return True, widget, None
    else:
        return False, widget, error_msg


def check_filter_access(user, filter_id, permission='view'):
    """
    Verificar acceso de usuario a filtro guardado.
    
    Args:
        user: Usuario a verificar
        filter_id: ID del filtro
        permission: Tipo de permiso ('view', 'edit')
    
    Returns:
        tuple: (has_access: bool, saved_filter: SavedFilter|None, error_msg: str|None)
    """
    try:
        saved_filter = SavedFilter.objects.get(
            id=filter_id,
            deleted_at__isnull=True
        )
    except SavedFilter.DoesNotExist:
        return False, None, 'Filtro no encontrado'
    
    # Verificar según tipo de permiso
    if permission == 'view':
        has_access = can_view_filter(user, saved_filter)
        error_msg = 'No tienes permisos para ver este filtro'
    elif permission == 'edit':
        has_access = can_edit_filter(user, saved_filter)
        error_msg = 'No tienes permisos para editar este filtro'
    else:
        return False, saved_filter, f'Permiso inválido: {permission}'
    
    if has_access:
        return True, saved_filter, None
    else:
        return False, saved_filter, error_msg


def get_user_dashboards(user, include_public=True):
    """
    Obtener dashboards accesibles por el usuario.
    
    Args:
        user: Usuario
        include_public: Si incluir dashboards públicos de otros usuarios
    
    Returns:
        QuerySet: Dashboards accesibles
    
    Examples:
        >>> dashboards = get_user_dashboards(request.user)
        >>> for dashboard in dashboards:
        >>>     print(dashboard.config_name)
    """
    # Admin ve todos
    if user.is_staff or user.is_superuser:
        return DashboardConfig.objects.filter(
            deleted_at__isnull=True
        ).select_related('user').prefetch_related('widgets')
    
    # Dashboards propios
    queryset = DashboardConfig.objects.filter(
        user=user,
        deleted_at__isnull=True
    )
    
    # Agregar públicos si se solicita
    if include_public:
        public_dashboards = DashboardConfig.objects.filter(
            is_public=True,
            deleted_at__isnull=True
        ).exclude(user=user)
        
        queryset = queryset | public_dashboards
    
    return queryset.select_related('user').prefetch_related('widgets').distinct()


def get_user_widgets(user, dashboard=None):
    """
    Obtener widgets accesibles por el usuario.
    
    Args:
        user: Usuario
        dashboard: Dashboard específico (opcional)
    
    Returns:
        QuerySet: Widgets accesibles
    
    Examples:
        >>> widgets = get_user_widgets(request.user)
        >>> widgets = get_user_widgets(request.user, dashboard=my_dashboard)
    """
    # Base queryset
    queryset = WidgetConfig.objects.select_related('dashboard', 'dashboard__user')
    
    # Filtrar por dashboard específico si se proporciona
    if dashboard:
        queryset = queryset.filter(dashboard=dashboard)
    
    # Admin ve todos
    if user.is_staff or user.is_superuser:
        return queryset
    
    # Widgets de dashboards propios o públicos
    accessible_widgets = queryset.filter(
        dashboard__user=user
    ) | queryset.filter(
        dashboard__is_public=True
    )
    
    return accessible_widgets.distinct()


def get_user_filters(user, include_public=True):
    """
    Obtener filtros accesibles por el usuario.
    
    Args:
        user: Usuario
        include_public: Si incluir filtros públicos de otros usuarios
    
    Returns:
        QuerySet: Filtros accesibles
    """
    # Admin ve todos
    if user.is_staff or user.is_superuser:
        return SavedFilter.objects.filter(
            deleted_at__isnull=True
        ).select_related('user')
    
    # Filtros propios
    queryset = SavedFilter.objects.filter(
        user=user,
        deleted_at__isnull=True
    )
    
    # Agregar públicos si se solicita
    if include_public:
        public_filters = SavedFilter.objects.filter(
            is_public=True,
            deleted_at__isnull=True
        ).exclude(user=user)
        
        queryset = queryset | public_filters
    
    return queryset.select_related('user').distinct()


# ==============================================================================
# DECORADOR GENÉRICO DE AUTENTICACIÓN
# ==============================================================================

def require_authenticated(view_func):
    """
    Decorador simple que requiere autenticación.
    
    Retorna JSON en lugar de redirigir al login.
    Útil para APIs.
    
    Uso:
        @require_authenticated
        def my_api_view(request):
            # Solo ejecuta si usuario está autenticado
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 'error',
                'message': 'Autenticación requerida'
            }, status=401)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
