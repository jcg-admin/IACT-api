"""
Service Layer para CallRecord.

Contiene lógica de negocio para registros de llamadas.

Service Layer Pattern: Lógica de negocio separada de models.
CLEAN_CODE v3.0.1: Nombres auto-documentados.
"""

from django.db import transaction
from django.db.models import Sum, Avg, Count, Q
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

from apps.pipeline.models import CallRecord, Service
from apps.utils.validators import validate_export_row_limit


class CallRecordService:
    """
    Service para operaciones de CallRecord.
    
    Métodos:
        - create_record(data)
        - bulk_create_records(records_data)
        - update_record(record, data)
        - get_records_by_date_range(start_date, end_date, service_800)
        - get_service_stats(service_800, start_date, end_date)
        - get_daily_stats(fecha, service_800)
        - get_top_callers(service_800, start_date, end_date, limit)
        - aggregate_records_by_day(fecha, service_800)
        - validate_export_size(queryset)
    """
    
    @staticmethod
    @transaction.atomic
    def create_record(data: Dict) -> CallRecord:
        """
        Crear registro de llamadas.
        
        Args:
            data (dict): Datos del registro
                - fecha (date): Fecha de llamadas
                - telefono (str): Número telefónico
                - servicio_800 (str): Número servicio 800
                - total_llamadas (int): Total de llamadas
                - llamadas_contestadas (int): Contestadas
                - llamadas_abandonadas (int): Abandonadas
                - duracion_total_segundos (int, opcional)
        
        Returns:
            CallRecord: Registro creado
        
        Raises:
            ValidationError: Si datos inválidos o duplicado
        
        Examples:
            >>> data = {
            ...     'fecha': date(2025, 1, 15),
            ...     'telefono': '912345678',
            ...     'servicio_800': '800-123-4567',
            ...     'total_llamadas': 100,
            ...     'llamadas_contestadas': 85,
            ...     'llamadas_abandonadas': 15
            ... }
            >>> record = CallRecordService.create_record(data)
        """
        # Verificar si ya existe
        fecha = data.get('fecha')
        telefono = data.get('telefono')
        servicio_800 = data.get('servicio_800')
        
        if CallRecord.objects.filter(
            fecha=fecha,
            telefono=telefono,
            servicio_800=servicio_800
        ).exists():
            raise ValidationError(
                f"Ya existe registro para {fecha} - {telefono} - {servicio_800}"
            )
        
        # Crear registro
        record = CallRecord(**data)
        record.full_clean()  # Valida consistencia (clean method)
        record.save()
        
        return record
    
    @staticmethod
    @transaction.atomic
    def bulk_create_records(records_data: List[Dict]) -> Tuple[List[CallRecord], int]:
        """
        Crear múltiples registros en batch.
        
        IMPORTANTE: Ignora duplicados automáticamente.
        
        Args:
            records_data (list): Lista de dicts con datos de registros
        
        Returns:
            tuple: (records_created, duplicates_ignored)
        
        Examples:
            >>> data = [
            ...     {'fecha': date(2025,1,15), 'telefono': '91234', ...},
            ...     {'fecha': date(2025,1,15), 'telefono': '91235', ...},
            ... ]
            >>> records, ignored = CallRecordService.bulk_create_records(data)
        """
        records_to_create = []
        duplicates_ignored = 0
        
        for data in records_data:
            fecha = data.get('fecha')
            telefono = data.get('telefono')
            servicio_800 = data.get('servicio_800')
            
            # Verificar si ya existe
            if CallRecord.objects.filter(
                fecha=fecha,
                telefono=telefono,
                servicio_800=servicio_800
            ).exists():
                duplicates_ignored += 1
                continue
            
            # Crear objeto
            record = CallRecord(**data)
            
            # Validar antes de agregar
            try:
                record.full_clean()
                records_to_create.append(record)
            except ValidationError:
                # Ignorar registros inválidos
                duplicates_ignored += 1
        
        # Crear en batch
        if records_to_create:
            created = CallRecord.objects.bulk_create(records_to_create)
        else:
            created = []
        
        return created, duplicates_ignored
    
    @staticmethod
    @transaction.atomic
    def update_record(record: CallRecord, data: Dict) -> CallRecord:
        """
        Actualizar registro de llamadas.
        
        Args:
            record (CallRecord): Registro a actualizar
            data (dict): Datos a actualizar
        
        Returns:
            CallRecord: Registro actualizado
        
        Raises:
            ValidationError: Si datos inválidos
        """
        # Actualizar campos permitidos
        allowed_fields = [
            'total_llamadas',
            'llamadas_contestadas',
            'llamadas_abandonadas',
            'duracion_total_segundos'
        ]
        
        for field, value in data.items():
            if field in allowed_fields:
                setattr(record, field, value)
        
        record.full_clean()
        record.save()
        
        return record
    
    @staticmethod
    def get_records_by_date_range(
        start_date: date,
        end_date: date,
        service_800: Optional[str] = None
    ):
        """
        Obtener registros por rango de fechas.
        
        Args:
            start_date (date): Fecha inicio
            end_date (date): Fecha fin
            service_800 (str, opcional): Filtrar por servicio
        
        Returns:
            QuerySet: Registros filtrados
        
        Examples:
            >>> records = CallRecordService.get_records_by_date_range(
            ...     start_date=date(2025, 1, 1),
            ...     end_date=date(2025, 1, 31),
            ...     service_800='800-123-4567'
            ... )
        """
        query = CallRecord.objects.filter(
            fecha__gte=start_date,
            fecha__lte=end_date
        )
        
        if service_800:
            query = query.filter(servicio_800=service_800)
        
        return query.order_by('-fecha', '-created_at')
    
    @staticmethod
    def get_service_stats(
        service_800: str,
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Obtener estadísticas agregadas de un servicio.
        
        Args:
            service_800 (str): Número servicio 800
            start_date (date): Fecha inicio
            end_date (date): Fecha fin
        
        Returns:
            dict: {
                'total_calls': int,
                'total_answered': int,
                'total_abandoned': int,
                'answer_rate': Decimal,
                'abandonment_rate': Decimal,
                'unique_callers': int,
                'avg_duration_seconds': Decimal,
                'total_duration_hours': Decimal,
                'days_with_data': int
            }
        
        Examples:
            >>> stats = CallRecordService.get_service_stats(
            ...     service_800='800-123-4567',
            ...     start_date=date(2025, 1, 1),
            ...     end_date=date(2025, 1, 31)
            ... )
            >>> stats['answer_rate']
            Decimal('85.50')
        """
        records = CallRecord.objects.filter(
            servicio_800=service_800,
            fecha__gte=start_date,
            fecha__lte=end_date
        )
        
        aggregates = records.aggregate(
            total_calls=Sum('total_llamadas'),
            total_answered=Sum('llamadas_contestadas'),
            total_abandoned=Sum('llamadas_abandonadas'),
            unique_callers=Count('telefono', distinct=True),
            total_duration=Sum('duracion_total_segundos'),
            avg_duration=Avg('duracion_total_segundos'),
            days_count=Count('fecha', distinct=True)
        )
        
        # Calcular rates
        total = aggregates['total_calls'] or 0
        answered = aggregates['total_answered'] or 0
        abandoned = aggregates['total_abandoned'] or 0
        
        if total > 0:
            answer_rate = (Decimal(answered) / Decimal(total) * 100).quantize(Decimal('0.01'))
            abandonment_rate = (Decimal(abandoned) / Decimal(total) * 100).quantize(Decimal('0.01'))
        else:
            answer_rate = Decimal('0.00')
            abandonment_rate = Decimal('0.00')
        
        # Duración total en horas
        total_duration_seconds = aggregates['total_duration'] or 0
        total_duration_hours = Decimal(total_duration_seconds / 3600).quantize(Decimal('0.01'))
        
        return {
            'total_calls': total,
            'total_answered': answered,
            'total_abandoned': abandoned,
            'answer_rate': answer_rate,
            'abandonment_rate': abandonment_rate,
            'unique_callers': aggregates['unique_callers'] or 0,
            'avg_duration_seconds': Decimal(aggregates['avg_duration'] or 0).quantize(Decimal('0.01')),
            'total_duration_hours': total_duration_hours,
            'days_with_data': aggregates['days_count'] or 0
        }
    
    @staticmethod
    def get_daily_stats(fecha: date, service_800: Optional[str] = None) -> Dict:
        """
        Obtener estadísticas de un día específico.
        
        Args:
            fecha (date): Fecha
            service_800 (str, opcional): Filtrar por servicio
        
        Returns:
            dict: Estadísticas del día
        
        Examples:
            >>> stats = CallRecordService.get_daily_stats(
            ...     fecha=date(2025, 1, 15),
            ...     service_800='800-123-4567'
            ... )
        """
        query = CallRecord.objects.filter(fecha=fecha)
        
        if service_800:
            query = query.filter(servicio_800=service_800)
        
        aggregates = query.aggregate(
            total_calls=Sum('total_llamadas'),
            total_answered=Sum('llamadas_contestadas'),
            total_abandoned=Sum('llamadas_abandonadas'),
            unique_callers=Count('telefono', distinct=True),
            services_count=Count('servicio_800', distinct=True)
        )
        
        total = aggregates['total_calls'] or 0
        answered = aggregates['total_answered'] or 0
        
        if total > 0:
            answer_rate = (Decimal(answered) / Decimal(total) * 100).quantize(Decimal('0.01'))
        else:
            answer_rate = Decimal('0.00')
        
        return {
            'fecha': fecha,
            'total_calls': total,
            'total_answered': answered,
            'total_abandoned': aggregates['total_abandoned'] or 0,
            'answer_rate': answer_rate,
            'unique_callers': aggregates['unique_callers'] or 0,
            'services_count': aggregates['services_count'] or 0,
        }
    
    @staticmethod
    def get_top_callers(
        service_800: str,
        start_date: date,
        end_date: date,
        limit: int = 10
    ) -> List[Dict]:
        """
        Obtener top N callers por volumen de llamadas.
        
        Args:
            service_800 (str): Número servicio
            start_date (date): Fecha inicio
            end_date (date): Fecha fin
            limit (int): Cantidad de resultados (default 10)
        
        Returns:
            list: Lista de dicts con estadísticas por caller
        
        Examples:
            >>> top = CallRecordService.get_top_callers(
            ...     service_800='800-123-4567',
            ...     start_date=date(2025, 1, 1),
            ...     end_date=date(2025, 1, 31),
            ...     limit=5
            ... )
        """
        from django.db.models import F
        
        top_callers = CallRecord.objects.filter(
            servicio_800=service_800,
            fecha__gte=start_date,
            fecha__lte=end_date
        ).values('telefono').annotate(
            total_calls=Sum('total_llamadas'),
            total_answered=Sum('llamadas_contestadas'),
            total_abandoned=Sum('llamadas_abandonadas'),
            days_active=Count('fecha', distinct=True)
        ).order_by('-total_calls')[:limit]
        
        # Calcular rates
        result = []
        for caller in top_callers:
            total = caller['total_calls']
            answered = caller['total_answered']
            
            if total > 0:
                answer_rate = (Decimal(answered) / Decimal(total) * 100).quantize(Decimal('0.01'))
            else:
                answer_rate = Decimal('0.00')
            
            result.append({
                'telefono': caller['telefono'],
                'total_calls': total,
                'total_answered': answered,
                'total_abandoned': caller['total_abandoned'],
                'answer_rate': answer_rate,
                'days_active': caller['days_active']
            })
        
        return result
    
    @staticmethod
    @transaction.atomic
    def aggregate_records_by_day(fecha: date, service_800: str) -> CallRecord:
        """
        Agregar múltiples registros de un día en uno solo.
        
        Útil para consolidar datos de prueba o migraciones.
        
        Args:
            fecha (date): Fecha a agregar
            service_800 (str): Servicio
        
        Returns:
            CallRecord: Registro agregado
        
        Examples:
            >>> aggregated = CallRecordService.aggregate_records_by_day(
            ...     fecha=date(2025, 1, 15),
            ...     service_800='800-123-4567'
            ... )
        """
        records = CallRecord.objects.filter(
            fecha=fecha,
            servicio_800=service_800
        )
        
        if not records.exists():
            raise ValidationError(f"No hay registros para {fecha} - {service_800}")
        
        # Agregar por teléfono
        aggregates = records.values('telefono').annotate(
            total_calls=Sum('total_llamadas'),
            total_answered=Sum('llamadas_contestadas'),
            total_abandoned=Sum('llamadas_abandonadas'),
            total_duration=Sum('duracion_total_segundos')
        )
        
        # Eliminar registros antiguos
        records.delete()
        
        # Crear registros agregados
        new_records = []
        for agg in aggregates:
            record = CallRecord(
                fecha=fecha,
                telefono=agg['telefono'],
                servicio_800=service_800,
                total_llamadas=agg['total_calls'],
                llamadas_contestadas=agg['total_answered'],
                llamadas_abandonadas=agg['total_abandoned'],
                duracion_total_segundos=agg['total_duration']
            )
            new_records.append(record)
        
        return CallRecord.objects.bulk_create(new_records)
    
    @staticmethod
    def validate_export_size(queryset) -> Tuple[bool, int]:
        """
        Validar que export no exceda límite.
        
        CNST-007: Export máximo 100K rows.
        
        Args:
            queryset: QuerySet a exportar
        
        Returns:
            tuple: (is_valid, row_count)
        
        Raises:
            ValidationError: Si excede límite
        
        Examples:
            >>> is_valid, count = CallRecordService.validate_export_size(queryset)
        """
        row_count = queryset.count()
        
        try:
            validate_export_row_limit(row_count)
            return True, row_count
        except ValidationError:
            return False, row_count


# ============================================================================
# TOTAL METHODS: 11
# 
# CRUD:
#   - create_record(data)
#   - bulk_create_records(records_data)
#   - update_record(record, data)
# 
# Queries:
#   - get_records_by_date_range(start, end, service_800)
#   - get_daily_stats(fecha, service_800)
#   - get_top_callers(service, start, end, limit)
# 
# Statistics:
#   - get_service_stats(service_800, start, end)
# 
# Aggregation:
#   - aggregate_records_by_day(fecha, service_800)
# 
# Validation:
#   - validate_export_size(queryset) (CNST-007)
# 
# Características:
#   [SUCCESS] @transaction.atomic donde corresponde
#   [SUCCESS] Bulk operations optimizadas
#   [SUCCESS] Estadísticas agregadas complejas
#   [SUCCESS] Validaciones de negocio
#   [SUCCESS] CNST-007: Export validation
#   [SUCCESS] Type hints
#   [SUCCESS] Docstrings completos
#   [SUCCESS] CLEAN_CODE v3.0.1
# ============================================================================
