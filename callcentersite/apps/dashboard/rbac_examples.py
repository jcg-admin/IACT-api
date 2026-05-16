"""
Ejemplos de uso del sistema RBAC de Dashboard.

Este archivo contiene ejemplos de cómo usar los decoradores y helpers
del sistema RBAC en vistas basadas en funciones (FBV).

FASE 8: Ejemplos de uso de RBAC.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from apps.dashboard.rbac import (
    require_dashboard_owner,
    require_dashboard_view,
    require_widget_owner,
    require_widget_view,
    require_authenticated,
    check_dashboard_access,
    check_widget_access,
    get_user_dashboards,
    get_user_widgets
)
from apps.dashboard.services import DashboardService, WidgetService


# ==============================================================================
# EJEMPLO 1: DECORADOR PARA DASHBOARD OWNER
# ==============================================================================

@require_dashboard_owner
@require_http_methods(["POST"])
def update_dashboard_settings(request, dashboard_id):
    """
    Actualizar configuración del dashboard.

    Solo el propietario puede actualizar.
    El dashboard está disponible en request.dashboard
    """
    dashboard = request.dashboard  # Agregado por el decorador

    # Actualizar configuración
    if 'config_name' in request.POST:
        dashboard.config_name = request.POST['config_name']

    if 'description' in request.POST:
        dashboard.description = request.POST['description']

    dashboard.save()

    return JsonResponse({
        'status': 'success',
        'message': 'Dashboard actualizado',
        'dashboard_id': dashboard.id
    })


# ==============================================================================
# EJEMPLO 2: DECORADOR PARA DASHBOARD VIEW
# ==============================================================================

@require_dashboard_view
@require_http_methods(["GET"])
def get_dashboard_statistics(request, dashboard_id):
    """
    Obtener estadísticas del dashboard.

    Cualquier usuario con permisos de visualización puede ver.
    """
    dashboard = request.dashboard  # Agregado por el decorador

    # Calcular estadísticas
    stats = {
        'total_widgets': dashboard.widgets.count(),
        'visible_widgets': dashboard.widgets.filter(is_visible=True).count(),
        'is_default': dashboard.is_default,
        'is_public': dashboard.is_public,
        'owner': dashboard.user.username
    }

    return JsonResponse({
        'status': 'success',
        'dashboard_id': dashboard.id,
        'statistics': stats
    })


# ==============================================================================
# EJEMPLO 3: DECORADOR PARA WIDGET OWNER
# ==============================================================================

@require_widget_owner
@require_http_methods(["POST"])
def refresh_widget_data(request, widget_id):
    """
    Refrescar datos del widget.

    Solo el propietario del dashboard puede refrescar.
    """
    widget = request.widget  # Agregado por el decorador

    # Refrescar cache
    WidgetService.refresh_widget_cache(widget.id)

    return JsonResponse({
        'status': 'success',
        'message': 'Cache del widget refrescado',
        'widget_id': widget.id
    })


# ==============================================================================
# EJEMPLO 4: DECORADOR PARA WIDGET VIEW
# ==============================================================================

@require_widget_view
@require_http_methods(["GET"])
def get_widget_details(request, widget_id):
    """
    Obtener detalles del widget.

    Cualquier usuario con permisos de visualización puede ver.
    """
    widget = request.widget  # Agregado por el decorador

    details = {
        'widget_id': widget.id,
        'widget_name': widget.widget_name,
        'widget_type': widget.widget_type,
        'dashboard_id': widget.dashboard.id,
        'dashboard_name': widget.dashboard.config_name,
        'is_visible': widget.is_visible
    }

    return JsonResponse({
        'status': 'success',
        'widget': details
    })


# ==============================================================================
# EJEMPLO 5: USAR CHECK_DASHBOARD_ACCESS
# ==============================================================================

@require_authenticated
@require_http_methods(["POST"])
def clone_dashboard_manual(request, dashboard_id):
    """
    Clonar dashboard usando check_dashboard_access.

    Este ejemplo muestra cómo usar la función helper
    en lugar del decorador.
    """
    # Verificar acceso manualmente
    has_access, dashboard, error = check_dashboard_access(
        request.user,
        dashboard_id,
        permission='view'  # Solo necesita ver para clonar
    )

    if not has_access:
        return JsonResponse({
            'status': 'error',
            'message': error
        }, status=403)

    # Clonar dashboard
    try:
        cloned = DashboardService.clone_dashboard(
            dashboard.id,
            request.user
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Dashboard clonado',
            'cloned_dashboard_id': cloned.id
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


# ==============================================================================
# EJEMPLO 6: USAR GET_USER_DASHBOARDS
# ==============================================================================

@require_authenticated
@require_http_methods(["GET"])
def list_my_dashboards(request):
    """
    Listar dashboards del usuario.

    Muestra cómo usar get_user_dashboards helper.
    """
    # Obtener dashboards accesibles
    dashboards = get_user_dashboards(request.user)

    # Serializar
    dashboard_list = []
    for dashboard in dashboards:
        dashboard_list.append({
            'id': dashboard.id,
            'name': dashboard.config_name,
            'description': dashboard.description,
            'is_default': dashboard.is_default,
            'is_public': dashboard.is_public,
            'is_owner': dashboard.user == request.user,
            'widget_count': dashboard.widgets.count()
        })

    return JsonResponse({
        'status': 'success',
        'total': len(dashboard_list),
        'dashboards': dashboard_list
    })


# ==============================================================================
# EJEMPLO 7: USAR GET_USER_WIDGETS
# ==============================================================================

@require_authenticated
@require_http_methods(["GET"])
def list_dashboard_widgets(request, dashboard_id):
    """
    Listar widgets de un dashboard.

    Muestra cómo usar get_user_widgets con dashboard específico.
    """
    # Verificar acceso al dashboard
    has_access, dashboard, error = check_dashboard_access(
        request.user,
        dashboard_id,
        permission='view'
    )

    if not has_access:
        return JsonResponse({
            'status': 'error',
            'message': error
        }, status=403)

    # Obtener widgets del dashboard
    widgets = get_user_widgets(request.user, dashboard=dashboard)

    # Serializar
    widget_list = []
    for widget in widgets:
        widget_list.append({
            'id': widget.id,
            'name': widget.widget_name,
            'type': widget.widget_type,
            'is_visible': widget.is_visible,
            'position_x': widget.position_x,
            'position_y': widget.position_y
        })

    return JsonResponse({
        'status': 'success',
        'dashboard_id': dashboard.id,
        'total': len(widget_list),
        'widgets': widget_list
    })


# ==============================================================================
# EJEMPLO 8: COMBINACIÓN DE DECORADORES
# ==============================================================================

@require_dashboard_owner
@require_http_methods(["DELETE"])
def delete_dashboard_with_confirmation(request, dashboard_id):
    """
    Eliminar dashboard con confirmación.

    Combina decorador de permisos con validación adicional.
    """
    dashboard = request.dashboard

    # Validar confirmación
    confirmation = request.POST.get('confirm', '').lower()
    if confirmation != 'yes':
        return JsonResponse({
            'status': 'error',
            'message': 'Se requiere confirmación para eliminar'
        }, status=400)

    # Eliminar dashboard
    try:
        DashboardService.delete_dashboard(dashboard.id, request.user)

        return JsonResponse({
            'status': 'success',
            'message': 'Dashboard eliminado exitosamente'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


# ==============================================================================
# EJEMPLO 9: MANEJO DE MÚLTIPLES PERMISOS
# ==============================================================================

@require_authenticated
@require_http_methods(["POST"])
def batch_update_widgets(request):
    """
    Actualizar múltiples widgets en batch.

    Valida permisos para cada widget individualmente.
    """
    widget_ids = request.POST.getlist('widget_ids[]')

    if not widget_ids:
        return JsonResponse({
            'status': 'error',
            'message': 'No se proporcionaron IDs de widgets'
        }, status=400)

    updated = []
    errors = []

    for widget_id in widget_ids:
        # Verificar acceso a cada widget
        has_access, widget, error = check_widget_access(
            request.user,
            widget_id,
            permission='edit'
        )

        if not has_access:
            errors.append({
                'widget_id': widget_id,
                'error': error
            })
            continue

        # Actualizar widget
        try:
            widget.is_visible = request.POST.get('is_visible', 'true') == 'true'
            widget.save()
            updated.append(widget.id)
        except Exception as e:
            errors.append({
                'widget_id': widget_id,
                'error': str(e)
            })

    return JsonResponse({
        'status': 'success',
        'updated': len(updated),
        'widget_ids': updated,
        'errors': errors
    })
