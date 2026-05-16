"""
Mixins para ViewSets DRF.

CLEAN_CODE v3.0.1: Nombres auto-documentados.
SOLID: SRP - Cada mixin una responsabilidad.
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response


# ============================================================================
# SOFT DELETE MIXIN
# ============================================================================

class SoftDeleteViewSetMixin:
    """
    Mixin para ViewSets con soft delete.

    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo agrega acciones soft delete.

    Agrega acciones custom:
    - POST /resource/{id}/restore/ - Restaura eliminado
    - DELETE /resource/{id}/hard-delete/ - Elimina físicamente

    Requiere que el modelo tenga:
    - is_deleted (BooleanField)
    - restore() (method)
    - hard_delete() (method, opcional)

    Uso:
        class ReportViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
            pass

        # Endpoints adicionales:
        POST /api/reports/1/restore/
        DELETE /api/reports/1/hard-delete/

    Examples:
        # Restaurar:
        POST /api/reports/1/restore/
        -> 200 OK {report_data}

        # Hard delete:
        DELETE /api/reports/1/hard-delete/
        -> 204 No Content
    """

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """
        Restaura registro eliminado (soft delete).

        Args:
            request: HttpRequest
            pk: Primary key

        Returns:
            Response con objeto restaurado o error
        """
        obj = self.get_object()

        # Verificar que modelo soporte soft delete
        if not hasattr(obj, 'is_deleted'):
            return Response(
                {'error': 'Model does not support soft delete'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar que esté eliminado
        if not obj.is_deleted:
            return Response(
                {'error': 'Object is not deleted'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Restaurar
        obj.restore()

        # Serializar y retornar
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    @action(detail=True, methods=['delete'])
    def hard_delete(self, request, pk=None):
        """
        Elimina físicamente (hard delete).

        Args:
            request: HttpRequest
            pk: Primary key

        Returns:
            Response 204 No Content
        """
        obj = self.get_object()

        # Si tiene método hard_delete, usarlo
        if hasattr(obj, 'hard_delete'):
            obj.hard_delete()
        else:
            # Fallback a delete normal
            obj.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================================================
# SERVICE FILTER MIXIN
# ============================================================================

# ====================================================================================
# REMOVED - FASE A DT-002 (2026-01-21)
# ====================================================================================
#
# ServiceFilterMixin (eliminado):
#   - Filtraba queryset por UserServiceAccess del usuario
#   - Usaba service_field para filtrar FK a Service
#
# Razón: UserServiceAccess eliminado, reemplazado por RBAC puro
# Reemplazo: Implementar filtrado custom en ViewSet si es necesario
# ====================================================================================


# ============================================================================
# AUDIT MIXINS
# ============================================================================


class AuditCreateMixin:
    """
    Mixin para setear created_by al crear.

    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo setea created_by.

    Requiere que el modelo tenga campo created_by.

    Uso:
        class ReportViewSet(AuditCreateMixin, viewsets.ModelViewSet):
            pass

    Examples:
        POST /api/reports/ {name: "Q1 Report"}
        -> created_by se setea automáticamente a request.user
    """

    def perform_create(self, serializer):
        """
        Setea created_by al crear.

        Args:
            serializer: Serializer con datos validados
        """
        serializer.save(created_by=self.request.user)


class AuditUpdateMixin:
    """
    Mixin para setear updated_by al actualizar.

    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo setea updated_by.

    Requiere que el modelo tenga campo updated_by.

    Uso:
        class ReportViewSet(AuditUpdateMixin, viewsets.ModelViewSet):
            pass

    Examples:
        PUT /api/reports/1/ {name: "Q1 Report Updated"}
        -> updated_by se setea automáticamente a request.user
    """

    def perform_update(self, serializer):
        """
        Setea updated_by al actualizar.

        Args:
            serializer: Serializer con datos validados
        """
        serializer.save(updated_by=self.request.user)


class AuditMixin(AuditCreateMixin, AuditUpdateMixin):
    """
    Mixin combinado para created_by y updated_by.

    CLEAN_CODE v3.0.1: Nombre auto-documentado.
    SOLID SRP: Combina create y update audit.

    Uso:
        class ReportViewSet(AuditMixin, viewsets.ModelViewSet):
            pass

        # Equivalente a:
        class ReportViewSet(AuditCreateMixin, AuditUpdateMixin, viewsets.ModelViewSet):
            pass
    """
    pass


# ============================================================================
# PAGINATION MIXIN
# ============================================================================

class PaginationControlMixin:
    """
    Mixin para controlar paginación dinámicamente.

    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo controla paginación.

    Permite al cliente desactivar paginación con query param.

    Uso:
        class ReportViewSet(PaginationControlMixin, viewsets.ModelViewSet):
            pass

        # Con paginación (default):
        GET /api/reports/
        -> {count: 100, next: ..., results: [...]}

        # Sin paginación:
        GET /api/reports/?paginate=false
        -> [...]

    Query Params:
        paginate (str): 'true' (default) o 'false'

    Examples:
        # Export sin paginación:
        GET /api/reports/?paginate=false&format=csv
        -> Todos los registros en CSV
    """

    def paginate_queryset(self, queryset):
        """
        Pagina queryset según query param.

        Args:
            queryset: QuerySet a paginar

        Returns:
            QuerySet paginado o None (sin paginación)
        """
        # Obtener query param
        paginate = self.request.query_params.get('paginate', 'true')

        # Si paginate=false, no paginar
        if paginate.lower() == 'false':
            return None

        # Paginar normalmente
        return super().paginate_queryset(queryset)


# ============================================================================
# EXPORT MIXIN
# ============================================================================

class ExportMixin:
    """
    Mixin para exportar datos.

    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo agrega acción export.

    Agrega action custom:
    - GET /resource/export/?format=csv - Exporta a CSV

    Uso:
        class ReportViewSet(ExportMixin, viewsets.ModelViewSet):
            export_fields = ['id', 'name', 'created_at']

    Configuración:
        export_fields (list): Campos a exportar

    Examples:
        GET /api/reports/export/?format=csv
        -> CSV con todos los reports
    """

    export_fields = []  # Override en subclass

    @action(detail=False, methods=['get'])
    def export(self, request):
        """
        Exporta datos a CSV.

        Args:
            request: HttpRequest

        Returns:
            HttpResponse con CSV
        """
        import csv
        from django.http import HttpResponse

        # Obtener queryset filtrado
        queryset = self.filter_queryset(self.get_queryset())

        # Crear response CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="export.csv"'

        # Escribir CSV
        writer = csv.writer(response)

        # Header
        fields = self.export_fields or ['id']
        writer.writerow(fields)

        # Rows
        for obj in queryset:
            row = [getattr(obj, field, '') for field in fields]
            writer.writerow(row)

        return response


# ============================================================================
# RESUMEN MIXINS
#
# Total: 8 mixins
#
# Soft Delete:
#   [SUCCESS] SoftDeleteViewSetMixin - Acciones restore/hard-delete
#
# Service Filter:
#   [SUCCESS] ServiceFilterMixin - Filtra por servicios del usuario
#
# Audit:
#   [SUCCESS] AuditCreateMixin - Setea created_by
#   [SUCCESS] AuditUpdateMixin - Setea updated_by
#   [SUCCESS] AuditMixin - Combinado (create + update)
#
# Pagination:
#   [SUCCESS] PaginationControlMixin - Control dinámico paginación
#
# Export:
#   [SUCCESS] ExportMixin - Exportar a CSV
#
# Principios SOLID Aplicados:
#   [SUCCESS] SRP: Cada mixin una responsabilidad
#   [SUCCESS] DRY: _get_user_services() helper
#   [SUCCESS] Clean Naming: Nombres auto-documentados
#   [SUCCESS] Documentation: Docstrings + ejemplos
#   [SUCCESS] Composable: Mixins combinables
# ============================================================================
