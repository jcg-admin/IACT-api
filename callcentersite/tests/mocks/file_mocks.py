"""
Mocks para generación y almacenamiento de archivos.

CONTEXTO: Simulamos generación de archivos (Excel, CSV, PDF) sin crear
archivos reales en disco.

CLEAN_CODE v3.0.1: Nombres auto-documentados.
"""

import pytest
from unittest.mock import MagicMock, Mock, mock_open, patch
from io import BytesIO, StringIO
import os


# ============================================================================
# EXCEL EXPORTER MOCKS
# ============================================================================

@pytest.fixture
def mock_excel_exporter(mocker):
    """
    Mock de ExcelExporter (export a .xlsx).
    
    Simula export sin crear archivo real.
    
    Uso:
        def test_export_excel(mock_excel_exporter):
            exporter = ExcelExporter()
            file_path = exporter.export(data)
            assert file_path.endswith('.xlsx')
    
    Métodos mockeados:
        - export(data, output_path)
        - export_with_formatting(data, output_path, styles)
        - add_chart(workbook, data, chart_type)
    """
    from apps.reports.exporters import ExcelExporter
    
    mock_exporter = MagicMock(spec=ExcelExporter)
    
    # Mock export() retorna path fake
    mock_exporter.export.return_value = '/fake/path/report.xlsx'
    
    # Mock export_with_formatting()
    mock_exporter.export_with_formatting.return_value = '/fake/path/report_styled.xlsx'
    
    # Mock add_chart()
    mock_exporter.add_chart.return_value = True
    
    mocker.patch(
        'apps.reports.exporters.ExcelExporter',
        return_value=mock_exporter
    )
    
    return mock_exporter


@pytest.fixture
def mock_excel_file_content(mocker):
    """
    Mock que simula contenido de archivo Excel.
    
    Retorna BytesIO con contenido fake.
    
    Uso:
        def test_read_excel(mock_excel_file_content):
            content = mock_excel_file_content
            # Procesar content como Excel
    """
    # Contenido fake de Excel (binario)
    fake_content = b'PK\x03\x04\x14\x00\x00\x00\x08\x00'  # Header ZIP (Excel es ZIP)
    
    return BytesIO(fake_content)


# ============================================================================
# CSV EXPORTER MOCKS
# ============================================================================

@pytest.fixture
def mock_csv_exporter(mocker):
    """
    Mock de CSVExporter (export a .csv).
    
    Uso:
        def test_export_csv(mock_csv_exporter):
            exporter = CSVExporter()
            file_path = exporter.export(data)
            assert file_path.endswith('.csv')
    
    Métodos mockeados:
        - export(data, output_path, delimiter)
        - export_with_headers(data, output_path, headers)
    """
    from apps.reports.exporters import CSVExporter
    
    mock_exporter = MagicMock(spec=CSVExporter)
    
    # Mock export() retorna path fake
    mock_exporter.export.return_value = '/fake/path/report.csv'
    
    # Mock export_with_headers()
    mock_exporter.export_with_headers.return_value = '/fake/path/report_headers.csv'
    
    mocker.patch(
        'apps.reports.exporters.CSVExporter',
        return_value=mock_exporter
    )
    
    return mock_exporter


@pytest.fixture
def mock_csv_file_content(mocker):
    """
    Mock que simula contenido de archivo CSV.
    
    Retorna StringIO con contenido fake.
    
    Uso:
        def test_read_csv(mock_csv_file_content):
            content = mock_csv_file_content
            # Procesar content como CSV
    """
    fake_content = """year,quarter,total_calls,unique_clients
2025,1,10000,5000
2025,2,12000,6000"""
    
    return StringIO(fake_content)


# ============================================================================
# PDF EXPORTER MOCKS
# ============================================================================

@pytest.fixture
def mock_pdf_exporter(mocker):
    """
    Mock de PDFExporter (export a .pdf).
    
    Uso:
        def test_export_pdf(mock_pdf_exporter):
            exporter = PDFExporter()
            file_path = exporter.export(data)
            assert file_path.endswith('.pdf')
    
    Métodos mockeados:
        - export(data, output_path, template)
        - export_with_charts(data, output_path, charts)
    """
    from apps.reports.exporters import PDFExporter
    
    mock_exporter = MagicMock(spec=PDFExporter)
    
    # Mock export() retorna path fake
    mock_exporter.export.return_value = '/fake/path/report.pdf'
    
    # Mock export_with_charts()
    mock_exporter.export_with_charts.return_value = '/fake/path/report_charts.pdf'
    
    mocker.patch(
        'apps.reports.exporters.PDFExporter',
        return_value=mock_exporter
    )
    
    return mock_exporter


@pytest.fixture
def mock_pdf_file_content(mocker):
    """
    Mock que simula contenido de archivo PDF.
    
    Retorna BytesIO con contenido fake.
    """
    # Header PDF
    fake_content = b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n'
    
    return BytesIO(fake_content)


# ============================================================================
# FILE STORAGE MOCKS
# ============================================================================

@pytest.fixture
def mock_file_storage(mocker):
    """
    Mock de file storage (django.core.files.storage).
    
    Simula guardado/lectura sin tocar disco.
    
    Uso:
        def test_save_file(mock_file_storage):
            from django.core.files.storage import default_storage
            path = default_storage.save('report.xlsx', file_content)
            assert path == '/fake/path/report.xlsx'
    
    Métodos mockeados:
        - save(name, content)
        - delete(name)
        - exists(name)
        - url(name)
        - size(name)
        - open(name, mode)
    """
    mock_storage = MagicMock()
    
    # Mock save() retorna path fake
    mock_storage.save.return_value = '/fake/path/file.xlsx'
    
    # Mock delete() retorna True
    mock_storage.delete.return_value = True
    
    # Mock exists() retorna True por defecto
    mock_storage.exists.return_value = True
    
    # Mock url() retorna URL fake
    mock_storage.url.return_value = 'http://example.com/media/file.xlsx'
    
    # Mock size() retorna tamaño fake
    mock_storage.size.return_value = 102400  # 100 KB
    
    # Mock open() retorna BytesIO fake
    mock_storage.open.return_value = BytesIO(b'fake file content')
    
    mocker.patch(
        'django.core.files.storage.default_storage',
        mock_storage
    )
    
    return mock_storage


@pytest.fixture
def mock_file_storage_error(mocker):
    """
    Mock de file storage que falla al guardar.
    
    Uso:
        def test_save_file_error(mock_file_storage_error):
            with pytest.raises(Exception, match="Storage error"):
                default_storage.save('file.xlsx', content)
    """
    mock_storage = MagicMock()
    
    # save() lanza error
    mock_storage.save.side_effect = Exception("Storage error: Disk full")
    
    mocker.patch(
        'django.core.files.storage.default_storage',
        mock_storage
    )
    
    return mock_storage


# ============================================================================
# FILE OPERATIONS MOCKS
# ============================================================================

@pytest.fixture
def mock_open_file(mocker):
    """
    Mock de open() para archivos.
    
    Simula lectura/escritura sin tocar disco.
    
    Uso:
        def test_read_file(mock_open_file):
            with open('/fake/path/file.txt', 'r') as f:
                content = f.read()
            assert content == 'fake file content'
    """
    fake_content = 'fake file content'
    m = mock_open(read_data=fake_content)
    mocker.patch('builtins.open', m)
    
    return m


@pytest.fixture
def mock_open_binary_file(mocker):
    """
    Mock de open() para archivos binarios.
    
    Uso:
        def test_read_binary(mock_open_binary_file):
            with open('/fake/path/file.xlsx', 'rb') as f:
                content = f.read()
    """
    fake_content = b'fake binary content'
    m = mock_open(read_data=fake_content)
    mocker.patch('builtins.open', m)
    
    return m


@pytest.fixture
def mock_os_path(mocker):
    """
    Mock de os.path para tests.
    
    Útil para simular existencia de archivos.
    
    Uso:
        def test_file_exists(mock_os_path):
            mock_os_path.exists.return_value = True
            assert os.path.exists('/fake/path/file.txt')
    """
    mock_path = MagicMock()
    
    # exists() retorna True por defecto
    mock_path.exists.return_value = True
    
    # isfile() retorna True
    mock_path.isfile.return_value = True
    
    # isdir() retorna False
    mock_path.isdir.return_value = False
    
    # getsize() retorna tamaño fake
    mock_path.getsize.return_value = 102400
    
    mocker.patch('os.path', mock_path)
    
    return mock_path


@pytest.fixture
def mock_os_remove(mocker):
    """
    Mock de os.remove() para tests.
    
    Simula eliminación sin tocar disco.
    
    Uso:
        def test_delete_file(mock_os_remove):
            os.remove('/fake/path/file.txt')
            mock_os_remove.assert_called_once()
    """
    mock_remove = MagicMock()
    mocker.patch('os.remove', mock_remove)
    
    return mock_remove


@pytest.fixture
def mock_tempfile(mocker):
    """
    Mock de tempfile para tests.
    
    Simula creación de archivos temporales.
    
    Uso:
        def test_temp_file(mock_tempfile):
            with tempfile.NamedTemporaryFile() as tmp:
                assert tmp.name == '/tmp/fake_temp_file'
    """
    import tempfile
    
    mock_temp = MagicMock()
    mock_temp.name = '/tmp/fake_temp_file'
    mock_temp.__enter__ = MagicMock(return_value=mock_temp)
    mock_temp.__exit__ = MagicMock()
    
    mocker.patch('tempfile.NamedTemporaryFile', return_value=mock_temp)
    
    return mock_temp


# ============================================================================
# LIMIT VALIDATION MOCKS
# ============================================================================

@pytest.fixture
def mock_file_size_validator(mocker):
    """
    Mock de validador de tamaño de archivo.
    
    CNST-007: Export máximo 100K rows.
    
    Uso:
        def test_file_size(mock_file_size_validator):
            # Valida que archivo no exceda límite
            is_valid = validate_file_size(file_path)
    """
    mock_validator = MagicMock()
    
    # Por defecto: archivo válido
    mock_validator.validate.return_value = True
    
    # validate_row_count() verifica límite CNST-007
    mock_validator.validate_row_count.return_value = True
    
    return mock_validator


@pytest.fixture
def mock_row_count_validator(mocker):
    """
    Mock de validador de número de filas.
    
    CNST-007: Export máximo 100K rows.
    
    Uso:
        def test_row_count(mock_row_count_validator):
            is_valid = validate_row_count(100000)  # OK
            assert is_valid is True
            
            is_valid = validate_row_count(150000)  # FAIL
            assert is_valid is False
    """
    def mock_validate(row_count):
        return row_count <= 100000  # CNST-007 limit
    
    mock_validator = MagicMock()
    mock_validator.validate.side_effect = mock_validate
    
    return mock_validator


# ============================================================================
# HELPER MOCKS
# ============================================================================

@pytest.fixture
def mock_file_cleanup(mocker):
    """
    Mock de cleanup de archivos temporales.
    
    Uso:
        def test_cleanup(mock_file_cleanup):
            cleanup_old_files()
            mock_file_cleanup.assert_called_once()
    """
    mock_cleanup = MagicMock()
    mocker.patch('apps.reports.utils.cleanup_old_files', mock_cleanup)
    
    return mock_cleanup


@pytest.fixture
def mock_file_metadata(mocker):
    """
    Mock que retorna metadata de archivo.
    
    Uso:
        def test_metadata(mock_file_metadata):
            metadata = get_file_metadata('/fake/path/file.xlsx')
            assert metadata['size'] == 102400
    """
    return {
        'name': 'report.xlsx',
        'size': 102400,
        'created_at': '2025-01-20T10:00:00',
        'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }


# ============================================================================
# TOTAL MOCKS: 17
# 
# Exporter Mocks (6):
#   - mock_excel_exporter
#   - mock_excel_file_content
#   - mock_csv_exporter
#   - mock_csv_file_content
#   - mock_pdf_exporter
#   - mock_pdf_file_content
# 
# Storage Mocks (2):
#   - mock_file_storage
#   - mock_file_storage_error
# 
# File Operations Mocks (5):
#   - mock_open_file
#   - mock_open_binary_file
#   - mock_os_path
#   - mock_os_remove
#   - mock_tempfile
# 
# Validation Mocks (2):
#   - mock_file_size_validator
#   - mock_row_count_validator (CNST-007)
# 
# Helper Mocks (2):
#   - mock_file_cleanup
#   - mock_file_metadata
# 
# CNST-007: Export máximo 100K rows [SUCCESS]
# CLEAN_CODE v3.0.1: Nombres auto-documentados [SUCCESS]
# ============================================================================
