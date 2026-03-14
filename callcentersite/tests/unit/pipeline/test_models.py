import pytest
from datetime import date, datetime
from apps.pipeline.models import ETLExecution


@pytest.mark.unit
@pytest.mark.django_db
class TestETLExecution:
    """Tests ETLExecution."""
    
    def test_create_etl_execution(self):
        """Crear ejecucion ETL."""
        execution = ETLExecution.objects.create(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 2),
            status='RUNNING',
        )
        
        assert execution.id is not None
        assert execution.status == 'RUNNING'
        assert execution.records_extracted == 0
        assert execution.records_loaded == 0
        assert execution.started_at is not None
    
    def test_etl_execution_str(self):
        """__str__ muestra rango y status."""
        execution = ETLExecution.objects.create(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 2),
            status='SUCCESS',
        )
        
        str_repr = str(execution)
        assert '2026-01-01' in str_repr
        assert '2026-01-02' in str_repr
        assert 'SUCCESS' in str_repr
    
    def test_etl_execution_ordering(self):
        """ETL ordenado por started_at DESC (mas reciente primero)."""
        exec1 = ETLExecution.objects.create(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 2),
        )
        exec2 = ETLExecution.objects.create(
            start_date=date(2026, 1, 3),
            end_date=date(2026, 1, 4),
        )
        
        executions = list(ETLExecution.objects.all())
        
        # Mas reciente primero
        assert executions[0].id == exec2.id
        assert executions[1].id == exec1.id
    
    def test_etl_execution_status_choices(self):
        """Status tiene choices correctos."""
        choices = dict(ETLExecution._meta.get_field('status').choices)
        
        assert 'PENDING' in choices
        assert 'RUNNING' in choices
        assert 'SUCCESS' in choices
        assert 'FAILED' in choices
    
    def test_etl_execution_completed_at_nullable(self):
        """completed_at es nullable."""
        execution = ETLExecution.objects.create(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 2),
            status='RUNNING',
        )
        
        assert execution.completed_at is None
    
    def test_etl_execution_error_message_blank(self):
        """error_message puede estar vacio."""
        execution = ETLExecution.objects.create(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 2),
            status='SUCCESS',
        )
        
        assert execution.error_message == ''
