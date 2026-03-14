"""
Views para app reports.

Endpoints:
- ReportViewSet: CRUD reportes
- ExportJobViewSet: CRUD jobs exportación
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from .models import Report, ExportJob
from .serializers import (
    ReportSerializer,
    ReportCreateSerializer,
    ExportJobSerializer,
)
from .services import ReportService, ExportService
from .permissions import (
    CanViewReports,
    CanCreateReports,
    CanExportReports,
    IsReportOwner,
)


class ReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de reportes.
    
    Endpoints:
    - list: Listar reportes del usuario
    - create: Crear nuevo reporte
    - retrieve: Detalle de reporte
    - update: Actualizar reporte
    - destroy: Eliminar reporte (soft delete)
    - generate: Generar datos del reporte
    - export: Exportar reporte a CSV/Excel
    """
    
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated, CanViewReports]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['report_type', 'status']
    ordering_fields = ['created_at', 'name']
    search_fields = ['name']
    
    def get_queryset(self):
        """
        Filtrar reportes por usuario.
        
        Solo muestra reportes propios (excepto superuser).
        """
        user = self.request.user
        
        if user.is_superuser:
            return Report.objects.all()
        
        # Solo reportes del usuario
        return Report.objects.filter(created_by=user)
    
    def get_serializer_class(self):
        """Usar serializer apropiado según acción."""
        if self.action == 'create':
            return ReportCreateSerializer
        return ReportSerializer
    
    def get_permissions(self):
        """
        Permisos según acción y tipo de reporte.
        
        MODELO GRANULAR: Para reportes de datos sensibles, se requieren
        permisos adicionales además del permiso genérico de reportes.
        """
        if self.action == 'create':
            # Verificar tipo de reporte solicitado
            report_type = self.request.data.get('report_type')
            
            # Permisos base para crear reportes
            permissions = [IsAuthenticated(), CanCreateReports()]
            
            # Permisos adicionales según tipo de datos
            if report_type == 'calls':
                # Reportes de llamadas requieren acceso a CallRecord
                from .permissions import CanAccessCallRecordData
                permissions.append(CanAccessCallRecordData())
            
            # TODO: Agregar validaciones para otros tipos
            # elif report_type == 'users':
            #     permissions.append(CanAccessUserData())
            # elif report_type == 'audit':
            #     permissions.append(CanAccessAuditData())
            
            return permissions
            
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsReportOwner()]
        elif self.action == 'export':
            return [IsAuthenticated(), CanExportReports()]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        """Asignar usuario al crear reporte."""
        report = serializer.save(created_by=self.request.user)
        
        # Generar reporte automáticamente
        ReportService.generate_report(report)
    
    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """
        Generar datos del reporte.
        
        POST /api/v1/reports/{id}/generate/
        
        Procesa datos según filtros y actualiza total_records.
        """
        report = self.get_object()
        
        # Verificar ownership
        if report.created_by != request.user and not request.user.is_superuser:
            return Response(
                {'detail': 'No tiene permiso para generar este reporte'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generar reporte
        try:
            ReportService.generate_report(report)
            
            serializer = self.get_serializer(report)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'detail': f'Error generando reporte: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def export(self, request, pk=None):
        """
        Exportar reporte a CSV o Excel.
        
        POST /api/v1/reports/{id}/export/
        Body: {
            "format": "csv" | "excel"
        }
        
        CNST-007: Valida límite de 100K registros.
        """
        report = self.get_object()
        
        # Verificar ownership
        if report.created_by != request.user and not request.user.is_superuser:
            return Response(
                {'detail': 'No tiene permiso para exportar este reporte'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validar reporte completado
        if report.status != 'completed':
            return Response(
                {'detail': 'Solo se pueden exportar reportes completados'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener formato
        export_format = request.data.get('format', 'csv')
        if export_format not in ['csv', 'excel']:
            return Response(
                {'detail': 'Formato inválido. Use "csv" o "excel"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar CNST-007
        if report.total_records > ExportService.MAX_EXPORT_SIZE:
            return Response(
                {
                    'detail': f'CNST-007 violation: Cannot export {report.total_records:,} records. '
                             f'Maximum allowed: {ExportService.MAX_EXPORT_SIZE:,}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear ExportJob
        export_job = ExportJob.objects.create(
            report=report,
            format=export_format,
            total_records=report.total_records
        )
        
        # Exportar
        try:
            export_service = ExportService(export_job)
            file_path = export_service.export()
            
            return Response({
                'export_job_id': export_job.id,
                'file_path': file_path,
                'status': 'completed'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'detail': f'Error exportando reporte: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExportJobViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para gestión de export jobs (solo lectura).
    
    Endpoints:
    - list: Listar jobs de exportación
    - retrieve: Detalle de job
    """
    
    queryset = ExportJob.objects.all()
    serializer_class = ExportJobSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'format']
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        """
        Filtrar export jobs por usuario.
        
        Solo muestra jobs de reportes propios (excepto superuser).
        """
        user = self.request.user
        
        if user.is_superuser:
            return ExportJob.objects.all()
        
        # Solo jobs de reportes del usuario
        return ExportJob.objects.filter(report__created_by=user)
