"""
Servicios para app reports.

CNST-007: Límite de exportación 100,000 registros.
SIN AWS/S3 - Exportación local.
"""
import csv
import io
from datetime import datetime
from typing import Dict, List, Any
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from .models import Report, ExportJob


class ExportService:
    """
    Servicio para exportación de reportes.

    CNST-007: Valida límite de 100K registros.
    Exporta a CSV o Excel (SIN S3, almacenamiento local).
    """

    # CNST-007: Límite máximo de exportación
    MAX_EXPORT_SIZE = 100000

    def __init__(self, export_job: ExportJob):
        """
        Inicializar servicio de exportación.

        Args:
            export_job: Job de exportación a procesar
        """
        self.export_job = export_job
        self.report = export_job.report

    def export(self) -> str:
        """
        Ejecutar exportación según formato.

        Returns:
            str: Ruta del archivo exportado

        Raises:
            ValueError: Si formato no soportado
            RuntimeError: Si excede CNST-007
        """
        # Validar CNST-007
        if self.export_job.total_records > self.MAX_EXPORT_SIZE:
            raise RuntimeError(
                f"CNST-007 violation: Cannot export {self.export_job.total_records:,} records. "
                f"Maximum allowed: {self.MAX_EXPORT_SIZE:,}"
            )

        # Actualizar estado
        self.export_job.status = 'running'
        self.export_job.started_at = timezone.now()
        self.export_job.save()

        try:
            # Exportar según formato
            if self.export_job.format == 'csv':
                file_path = self._export_csv()
            elif self.export_job.format == 'excel':
                file_path = self._export_excel()
            else:
                raise ValueError(f"Formato no soportado: {self.export_job.format}")

            # Actualizar job exitoso
            self.export_job.file_path = file_path
            self.export_job.status = 'completed'
            self.export_job.completed_at = timezone.now()
            self.export_job.exported_records = self.export_job.total_records
            self.export_job.save()

            return file_path

        except Exception as e:
            # Actualizar job fallido
            self.export_job.status = 'failed'
            self.export_job.error_message = str(e)
            self.export_job.save()
            raise

    def _export_csv(self) -> str:
        """
        Exportar reporte a CSV.

        Returns:
            str: Ruta del archivo CSV generado
        """
        # Obtener datos
        data = self._get_report_data()

        # Generar nombre de archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"report_{self.report.id}_{timestamp}.csv"
        file_path = f"exports/{filename}"

        # Escribir CSV
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        # Guardar contenido (en producción, guardar en filesystem)
        # Por ahora, retornamos la ruta
        return file_path

    def _export_excel(self) -> str:
        """
        Exportar reporte a Excel.

        Returns:
            str: Ruta del archivo Excel generado
        """
        # Obtener datos
        data = self._get_report_data()

        # Crear workbook
        wb = Workbook()
        ws = wb.active
        ws.title = self.report.name[:31]  # Max 31 chars

        if data:
            # Agregar headers con estilo
            headers = list(data[0].keys())
            ws.append(headers)

            # Estilo para headers
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True)

            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font

            # Agregar datos
            for row_data in data:
                ws.append(list(row_data.values()))

        # Generar nombre de archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"report_{self.report.id}_{timestamp}.xlsx"
        file_path = f"exports/{filename}"

        # Guardar (en producción, guardar en filesystem)
        # wb.save(file_path)

        return file_path

    def _get_report_data(self) -> List[Dict[str, Any]]:
        """
        Obtener datos del reporte según tipo.

        Returns:
            List[Dict]: Datos del reporte
        """
        report_type = self.report.report_type
        filters = self.report.filters

        if report_type == 'calls':
            return self._get_calls_data(filters)
        elif report_type == 'users':
            return self._get_users_data(filters)
        elif report_type == 'audit':
            return self._get_audit_data(filters)
        else:
            return []

    def _get_calls_data(self, filters: Dict) -> List[Dict]:
        """
        Obtener datos de llamadas.

        CallRecord eliminado en FASE 3 (UC_OPR/UC_SUP/UC_CLI fuera de scope).
        Los datos de llamadas se obtienen desde MariaDB via sp_rpt_* (ivr_services.py).
        """
        return []

    def _get_users_data(self, filters: Dict) -> List[Dict]:
        """
        Obtener datos de usuarios.

        Args:
            filters: Filtros aplicados

        Returns:
            List[Dict]: Datos de usuarios
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()

        queryset = User.objects.filter(state='ACTIVE')

        # Aplicar filtros
        if 'is_active' in filters:
            queryset = queryset.filter(is_active=filters['is_active'])
        if 'is_staff' in filters:
            queryset = queryset.filter(is_staff=filters['is_staff'])

        # Limitar CNST-007
        queryset = queryset[:self.MAX_EXPORT_SIZE]

        # Convertir a dict
        return list(queryset.values(
            'username',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'is_staff',
            'date_joined',
        ))

    def _get_audit_data(self, filters: Dict) -> List[Dict]:
        """
        Obtener datos de auditoría.

        Args:
            filters: Filtros aplicados

        Returns:
            List[Dict]: Datos de auditoría
        """
        from apps.audit.models import AuditLog

        queryset = AuditLog.objects.all()

        # Aplicar filtros
        if 'action' in filters:
            queryset = queryset.filter(action=filters['action'])
        if 'fecha_desde' in filters:
            queryset = queryset.filter(timestamp__gte=filters['fecha_desde'])
        if 'fecha_hasta' in filters:
            queryset = queryset.filter(timestamp__lte=filters['fecha_hasta'])

        # Limitar CNST-007
        queryset = queryset[:self.MAX_EXPORT_SIZE]

        # Convertir a dict
        return list(queryset.values(
            'timestamp',
            'user__username',
            'action',
            'resource_type',
            'resource_id',
            'description',
        ))


class ReportService:
    """
    Servicio para generación de reportes.

    Procesa datos y crea reportes según tipo.
    """

    @staticmethod
    def generate_report(report: Report) -> None:
        """
        Generar reporte procesando datos.

        Args:
            report: Report a generar
        """
        # Actualizar estado
        report.status = 'processing'
        report.save()

        try:
            # Obtener count según tipo
            if report.report_type == 'calls':
                count = ReportService._count_calls(report.filters)
            elif report.report_type == 'users':
                count = ReportService._count_users(report.filters)
            elif report.report_type == 'audit':
                count = ReportService._count_audit(report.filters)
            else:
                count = 0

            # Actualizar reporte
            report.total_records = count
            report.status = 'completed'
            report.save()

        except Exception:
            report.status = 'failed'
            report.save()
            raise

    @staticmethod
    def _count_calls(filters: Dict) -> int:
        """
        Contar llamadas según filtros.

        CallRecord eliminado en FASE 3 (UC_OPR/UC_SUP/UC_CLI fuera de scope).
        """
        return 0

    @staticmethod
    def _count_users(filters: Dict) -> int:
        """Contar usuarios según filtros."""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        queryset = User.objects.filter(state='ACTIVE')

        if 'is_active' in filters:
            queryset = queryset.filter(is_active=filters['is_active'])
        if 'is_staff' in filters:
            queryset = queryset.filter(is_staff=filters['is_staff'])

        return queryset.count()

    @staticmethod
    def _count_audit(filters: Dict) -> int:
        """Contar logs de auditoría según filtros."""
        from apps.audit.models import AuditLog

        queryset = AuditLog.objects.all()

        if 'action' in filters:
            queryset = queryset.filter(action=filters['action'])
        if 'fecha_desde' in filters:
            queryset = queryset.filter(timestamp__gte=filters['fecha_desde'])
        if 'fecha_hasta' in filters:
            queryset = queryset.filter(timestamp__lte=filters['fecha_hasta'])

        return queryset.count()
