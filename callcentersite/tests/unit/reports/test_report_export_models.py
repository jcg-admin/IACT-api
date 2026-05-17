"""Tests modelos Report y ExportJob."""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()
from apps.reports.models import ExportJob, Report, ExportJob


@pytest.mark.django_db
class TestReportModel:
    """Tests modelo Report."""
    
    def test_create_report(self):
        """Test crear report."""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        report = Report.objects.create(
            name='Test Report',
            report_type='calls',
            created_by=user,
            total_records=100
        )
        
        assert report.id is not None
        assert report.name == 'Test Report'
        assert report.report_type == 'calls'
        assert report.created_by == user
        assert report.total_records == 100
        assert report.status in ('pending', 'queued')
    
    def test_report_str(self):
        """Test __str__ method."""
        user = User.objects.create_user(username='test', password='pass')
        report = Report.objects.create(
            name='My Report',
            report_type='users',
            created_by=user
        )
        
        assert str(report) == 'My Report (Usuarios)'
    
    def test_report_filters_json(self):
        """Test filtros JSON."""
        user = User.objects.create_user(username='test', password='pass')
        filters = {'days': 7, 'status': 'active'}
        
        report = Report.objects.create(
            name='Filtered Report',
            report_type='calls',
            created_by=user,
            filters=filters
        )
        
        assert report.filters == filters
        assert report.filters['days'] == 7


@pytest.mark.django_db
class TestExportJobModel:
    """Tests modelo ExportJob."""
    
    def test_create_export_job(self):
        """Test crear export job."""
        user = User.objects.create_user(username='test', password='pass')
        report = Report.objects.create(
            name='Test Report',
            report_type='calls',
            created_by=user
        )
        
        job = ExportJob.objects.create(
            report=report,
            format='csv',
            total_records=500
        )
        
        assert job.id is not None
        assert job.report == report
        assert job.format == 'csv'
        assert job.total_records == 500
        assert job.exported_records == 0
        assert job.status in ('pending', 'queued')
    
    def test_export_job_str(self):
        """Test __str__ method — formato canónico ExportJob(report_type/format/status)."""
        user = User.objects.create_user(username='test', password='pass')
        report = Report.objects.create(
            name='My Report',
            report_type='users',
            created_by=user
        )
        job = ExportJob.objects.create(
            report=report,
            report_type='users',
            format='excel',
            total_records=100
        )
        # __str__ usa report_type/format/status (campos directos, sin FK nullable)
        result = str(job)
        assert 'users' in result
        assert 'excel' in result
        assert 'ExportJob(' in result
    
    def test_progress_percentage(self):
        """Test calcular porcentaje de progreso."""
        user = User.objects.create_user(username='test', password='pass')
        report = Report.objects.create(
            name='Progress Report',
            report_type='calls',
            created_by=user
        )
        job = ExportJob.objects.create(
            report=report,
            format='csv',
            total_records=1000,
            exported_records=250
        )
        
        assert job.progress_percentage == 25.0
