"""
Tests unitarios para modelo Report.

Cobertura:
- Creación de reportes
- Validaciones
- Soft delete
- Relaciones
- Properties
"""
import pytest
from django.contrib.auth import get_user_model
from apps.reports.models import Report

User = get_user_model()


@pytest.mark.django_db
class TestReportModel:
    """Tests para modelo Report."""
    
    def test_crear_report_basico(self):
        """Test: Crear reporte básico con datos mínimos."""
        # Arrange
        user = User.objects.create_user(username='testuser', password='test123')
        
        # Act
        report = Report.objects.create(
            name='Test Report',
            report_type='calls',
            created_by=user
        )
        
        # Assert
        assert report.id is not None
        assert report.name == 'Test Report'
        assert report.report_type == 'calls'
        assert report.created_by == user
        assert report.status == 'pending'  # Default
        assert report.total_records == 0  # Default
        assert report.filters == {}  # Default
        assert not report.is_deleted  # SoftDeleteMixin
    
    def test_report_con_filtros_json(self):
        """Test: Crear reporte con filtros JSON."""
        # Arrange
        user = User.objects.create_user(username='testuser', password='test123')
        filtros = {
            'fecha_desde': '2025-01-01',
            'fecha_hasta': '2025-01-31',
            'servicio_800': '8001234'
        }
        
        # Act
        report = Report.objects.create(
            name='Reporte con Filtros',
            report_type='calls',
            created_by=user,
            filters=filtros
        )
        
        # Assert
        assert report.filters == filtros
        assert report.filters['fecha_desde'] == '2025-01-01'
    
    def test_report_str_representation(self):
        """Test: __str__ retorna nombre y tipo."""
        # Arrange
        user = User.objects.create_user(username='testuser', password='test123')
        report = Report.objects.create(
            name='Mi Reporte',
            report_type='users',
            created_by=user
        )
        
        # Act
        result = str(report)
        
        # Assert
        assert 'Mi Reporte' in result
        assert 'Usuarios' in result  # Display del tipo
    
    def test_report_soft_delete(self):
        """Test: Soft delete marca is_deleted=True."""
        # Arrange
        user = User.objects.create_user(username='testuser', password='test123')
        report = Report.objects.create(
            name='Report to Delete',
            report_type='audit',
            created_by=user
        )
        
        # Act
        report.delete()  # Soft delete
        
        # Assert
        assert report.is_deleted is True
        assert report.deleted_at is not None
        
        # Verificar que no aparece en queryset normal
        assert Report.objects.filter(id=report.id).count() == 0
        # Pero sí con all_objects
        assert Report.all_objects.filter(id=report.id).count() == 1
    
    def test_report_tipos_validos(self):
        """Test: Solo acepta tipos válidos (calls, users, audit)."""
        # Arrange
        user = User.objects.create_user(username='testuser', password='test123')
        
        # Act & Assert - Tipos válidos
        for tipo in ['calls', 'users', 'audit']:
            report = Report.objects.create(
                name=f'Report {tipo}',
                report_type=tipo,
                created_by=user
            )
            assert report.report_type == tipo
    
    def test_report_estados_validos(self):
        """Test: Estados válidos (pending, processing, completed, failed)."""
        # Arrange
        user = User.objects.create_user(username='testuser', password='test123')
        report = Report.objects.create(
            name='Test',
            report_type='calls',
            created_by=user
        )
        
        # Act & Assert - Cambiar estados
        estados_validos = ['pending', 'processing', 'completed', 'failed']
        for estado in estados_validos:
            report.status = estado
            report.save()
            report.refresh_from_db()
            assert report.status == estado
    
    def test_report_ordering_por_created_at(self):
        """Test: Ordering por -created_at (más reciente primero)."""
        # Arrange
        user = User.objects.create_user(username='testuser', password='test123')
        report1 = Report.objects.create(
            name='Report 1',
            report_type='calls',
            created_by=user
        )
        report2 = Report.objects.create(
            name='Report 2',
            report_type='calls',
            created_by=user
        )
        
        # Act
        reports = list(Report.objects.all())
        
        # Assert - report2 debe estar primero (más reciente)
        assert reports[0].id == report2.id
        assert reports[1].id == report1.id
    
    def test_report_relacion_con_usuario(self):
        """Test: Relación con User funciona correctamente."""
        # Arrange
        user = User.objects.create_user(username='testuser', password='test123')
        report1 = Report.objects.create(
            name='Report 1',
            report_type='calls',
            created_by=user
        )
        report2 = Report.objects.create(
            name='Report 2',
            report_type='users',
            created_by=user
        )
        
        # Act
        user_reports = user.reports.all()
        
        # Assert
        assert user_reports.count() == 2
        assert report1 in user_reports
        assert report2 in user_reports
    
    def test_report_total_records_positivo(self):
        """Test: total_records acepta valores positivos."""
        # Arrange
        user = User.objects.create_user(username='testuser', password='test123')
        report = Report.objects.create(
            name='Test',
            report_type='calls',
            created_by=user,
            total_records=5000
        )
        
        # Act & Assert
        assert report.total_records == 5000
    
    def test_report_indices_creados(self):
        """Test: Verificar que índices existen en metadata."""
        # Arrange
        indexes = Report._meta.indexes
        
        # Assert - Debe tener índices definidos
        assert len(indexes) > 0
        
        # Verificar nombres de índices esperados
        index_names = [idx.name for idx in indexes]
        assert any('created_at' in name for name in index_names)
