"""
Tests para MenuBuilder y MenuValidator.

Cobertura:
- MenuValidator: validacion de IDs numericos
- MenuBuilder: construccion de menus dinamicos
- MenuSerializer: serializacion para API
- Integracion con RBAC
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json

from apps.core.navigation.builders import (
    MenuValidator,
    MenuBuilder,
    MenuSerializer,
)


# ============================================================================
# TESTS MenuValidator
# ============================================================================

class TestMenuValidator:
    """Tests para validacion de IDs de menu."""
    
    def test_validate_numeric_id_valid(self):
        """Test validar ID numerico valido."""
        assert MenuValidator.validate_numeric_id(5) is True
        assert MenuValidator.validate_numeric_id(501) is True
        assert MenuValidator.validate_numeric_id(1) is True
        assert MenuValidator.validate_numeric_id(899) is True
    
    def test_validate_numeric_id_invalid_type(self):
        """Test validar ID no numerico."""
        assert MenuValidator.validate_numeric_id("MOD_REPORTS") is False
        assert MenuValidator.validate_numeric_id(None) is False
        assert MenuValidator.validate_numeric_id([5]) is False
    
    def test_validate_numeric_id_out_of_range(self):
        """Test validar ID fuera de rango."""
        assert MenuValidator.validate_numeric_id(0) is False
        assert MenuValidator.validate_numeric_id(900) is False
        assert MenuValidator.validate_numeric_id(1000) is False
        assert MenuValidator.validate_numeric_id(-5) is False
    
    def test_validate_level1_id_valid(self):
        """Test validar ID nivel 1 valido (1-99)."""
        assert MenuValidator.validate_level1_id(1) is True
        assert MenuValidator.validate_level1_id(50) is True
        assert MenuValidator.validate_level1_id(99) is True
    
    def test_validate_level1_id_invalid(self):
        """Test validar ID nivel 1 invalido."""
        assert MenuValidator.validate_level1_id(0) is False
        assert MenuValidator.validate_level1_id(100) is False
        assert MenuValidator.validate_level1_id(501) is False
    
    def test_validate_level2_id_valid(self):
        """Test validar ID nivel 2 valido (100-899)."""
        assert MenuValidator.validate_level2_id(100) is True
        assert MenuValidator.validate_level2_id(501) is True
        assert MenuValidator.validate_level2_id(899) is True
    
    def test_validate_level2_id_invalid(self):
        """Test validar ID nivel 2 invalido."""
        assert MenuValidator.validate_level2_id(99) is False
        assert MenuValidator.validate_level2_id(900) is False
        assert MenuValidator.validate_level2_id(5) is False
    
    def test_validate_menu_structure_valid_level1(self):
        """Test validar estructura de menu nivel 1."""
        menu = {
            'id_menu': 5,
            'des_name': 'Reportes',
            'nivel': 1,
            'orden': 50,
        }
        
        is_valid, errors = MenuValidator.validate_menu_structure(menu)
        assert is_valid is True
        assert errors == []
    
    def test_validate_menu_structure_valid_level2(self):
        """Test validar estructura de menu nivel 2."""
        menu = {
            'id_menu': 501,
            'des_name': 'Dashboard',
            'nivel': 2,
            'orden': 1,
        }
        
        is_valid, errors = MenuValidator.validate_menu_structure(menu)
        assert is_valid is True
        assert errors == []
    
    def test_validate_menu_structure_missing_required_fields(self):
        """Test validar estructura sin campos requeridos."""
        menu = {
            'id_menu': 5,
            # Falta des_name, nivel, orden
        }
        
        is_valid, errors = MenuValidator.validate_menu_structure(menu)
        assert is_valid is False
        assert len(errors) > 0
        assert any('des_name' in err for err in errors)
    
    def test_validate_menu_structure_invalid_id_for_level(self):
        """Test validar ID invalido para nivel."""
        menu = {
            'id_menu': 501,  # ID nivel 2
            'des_name': 'Reportes',
            'nivel': 1,  # Pero dice ser nivel 1
            'orden': 50,
        }
        
        is_valid, errors = MenuValidator.validate_menu_structure(menu)
        assert is_valid is False
        assert any('ID 501 no es valido para nivel 1' in err for err in errors)
    
    def test_validate_icon_path_exists(self):
        """Test validar que icono existe."""
        with patch('pathlib.Path.exists', return_value=True):
            assert MenuValidator.validate_icon_path('/static/icons/menu/reports.png') is True
    
    def test_validate_icon_path_not_exists(self):
        """Test validar que icono no existe."""
        with patch('pathlib.Path.exists', return_value=False):
            assert MenuValidator.validate_icon_path('/static/icons/menu/fake.png') is False


# ============================================================================
# TESTS MenuBuilder
# ============================================================================

class TestMenuBuilder:
    """Tests para construccion de menus dinamicos."""
    
    @pytest.fixture
    def mock_user(self):
        """Usuario mock con funciones RBAC."""
        user = Mock()
        user.username = 'testuser'
        user.get_full_name.return_value = 'Test User'
        user.get_functions.return_value = [
            'RPT-001: view_reports',
            'RPT-002: view_dashboard',
        ]
        return user
    
    @pytest.fixture
    def sample_metadata(self):
        """Metadata de menu de ejemplo."""
        return {
            "module": "MOD_Reports",
            "app": "reports",
            "menu_tree": [
                {
                    "nivel": 1,
                    "id_menu": 5,
                    "des_name": "Reportes",
                    "icon": "/static/icons/menu/reports.png",
                    "orden": 50,
                    "required_functions": [],
                    "submenus": [
                        {
                            "id_menu": 501,
                            "des_name": "Dashboard",
                            "icon": "/static/icons/submenu/dashboard.png",
                            "endpoint": "/api/v1/reports/dashboard/",
                            "method": "GET",
                            "orden": 1,
                            "required_functions": ["RPT-002: view_dashboard"]
                        },
                        {
                            "id_menu": 502,
                            "des_name": "Reporte Diario",
                            "icon": "/static/icons/submenu/daily.png",
                            "endpoint": "/api/v1/reports/daily/",
                            "method": "GET",
                            "orden": 2,
                            "required_functions": ["RPT-001: view_reports"]
                        },
                        {
                            "id_menu": 503,
                            "des_name": "Exportar CSV",
                            "icon": "/static/icons/submenu/csv.png",
                            "endpoint": "/api/v1/reports/export/csv/",
                            "method": "POST",
                            "orden": 3,
                            "required_functions": ["RPT-004: export_csv"]
                        }
                    ]
                }
            ]
        }
    
    def test_builder_initialization(self):
        """Test inicializacion de MenuBuilder."""
        builder = MenuBuilder()
        assert builder is not None
    
    @patch('apps.core.navigation.builders.MenuBuilder._load_all_menu_metadata')
    def test_build_user_menu_with_permissions(self, mock_load, mock_user, sample_metadata):
        """Test construccion de menu filtrado por permisos."""
        mock_load.return_value = [sample_metadata]
        
        builder = MenuBuilder()
        menu = builder.build_user_menu(mock_user)
        
        assert len(menu) == 1
        assert menu[0]['id_menu'] == 5
        assert menu[0]['des_name'] == 'Reportes'
        
        # Solo debe incluir submenus con permisos
        submenus = menu[0]['submenus']
        assert len(submenus) == 2  # Dashboard y Reporte Diario
        
        submenu_ids = [sm['id_menu'] for sm in submenus]
        assert 501 in submenu_ids  # Dashboard (tiene permiso)
        assert 502 in submenu_ids  # Reporte Diario (tiene permiso)
        assert 503 not in submenu_ids  # Exportar CSV (NO tiene permiso)
    
    @patch('apps.core.navigation.builders.MenuBuilder._load_all_menu_metadata')
    def test_build_user_menu_no_permissions(self, mock_load, sample_metadata):
        """Test construccion de menu sin permisos."""
        mock_load.return_value = [sample_metadata]
        
        user = Mock()
        user.get_functions.return_value = []  # Sin permisos
        
        builder = MenuBuilder()
        menu = builder.build_user_menu(user)
        
        # Menu principal debe aparecer (no requiere permisos)
        assert len(menu) == 1
        assert menu[0]['id_menu'] == 5
        
        # Pero sin submenus (todos requieren permisos)
        assert len(menu[0]['submenus']) == 0
    
    @patch('apps.core.navigation.builders.MenuBuilder._load_all_menu_metadata')
    def test_build_user_menu_all_permissions(self, mock_load, sample_metadata):
        """Test construccion de menu con todos los permisos."""
        mock_load.return_value = [sample_metadata]
        
        user = Mock()
        user.get_functions.return_value = [
            'RPT-001: view_reports',
            'RPT-002: view_dashboard',
            'RPT-004: export_csv',
        ]
        
        builder = MenuBuilder()
        menu = builder.build_user_menu(user)
        
        # Todos los submenus deben aparecer
        submenus = menu[0]['submenus']
        assert len(submenus) == 3
        
        submenu_ids = [sm['id_menu'] for sm in submenus]
        assert 501 in submenu_ids
        assert 502 in submenu_ids
        assert 503 in submenu_ids
    
    def test_filter_by_permissions_empty_required(self, mock_user):
        """Test filtro con required_functions vacio."""
        builder = MenuBuilder()
        
        item = {
            'id_menu': 5,
            'required_functions': []
        }
        
        assert builder._has_permission(mock_user, item) is True
    
    def test_filter_by_permissions_user_has_permission(self, mock_user):
        """Test filtro cuando usuario tiene permiso."""
        builder = MenuBuilder()
        
        item = {
            'id_menu': 501,
            'required_functions': ['RPT-002: view_dashboard']
        }
        
        assert builder._has_permission(mock_user, item) is True
    
    def test_filter_by_permissions_user_missing_permission(self, mock_user):
        """Test filtro cuando usuario NO tiene permiso."""
        builder = MenuBuilder()
        
        item = {
            'id_menu': 503,
            'required_functions': ['RPT-004: export_csv']
        }
        
        assert builder._has_permission(mock_user, item) is False
    
    def test_personalize_menu_avatar_url(self, mock_user):
        """Test personalizacion de avatar URL."""
        mock_user.get_avatar_url.return_value = '/media/profiles/user_1/avatar.jpg'
        
        builder = MenuBuilder()
        
        menu = {
            'id_menu': 201,
            'icon': '{{user.avatar_url}}'
        }
        
        personalized = builder._personalize_menu(menu, mock_user)
        assert personalized['icon'] == '/media/profiles/user_1/avatar.jpg'
    
    def test_personalize_menu_username(self, mock_user):
        """Test personalizacion de username."""
        builder = MenuBuilder()
        
        menu = {
            'id_menu': 201,
            'des_name': 'Perfil de {{user.username}}'
        }
        
        personalized = builder._personalize_menu(menu, mock_user)
        assert personalized['des_name'] == 'Perfil de testuser'


# ============================================================================
# TESTS MenuSerializer
# ============================================================================

class TestMenuSerializer:
    """Tests para serializacion de menus."""
    
    def test_serialize_menu_level1(self):
        """Test serializar menu nivel 1."""
        menu = {
            'id_menu': 5,
            'des_name': 'Reportes',
            'icon': '/static/icons/menu/reports.png',
            'nivel': 1,
            'orden': 50,
            'submenus': []
        }
        
        serialized = MenuSerializer.serialize_menu(menu)
        
        assert serialized['id_menu'] == 5
        assert serialized['des_name'] == 'Reportes'
        assert serialized['icon'] == '/static/icons/menu/reports.png'
        assert serialized['nivel'] == 1
        assert serialized['orden'] == 50
        assert 'submenus' in serialized
    
    def test_serialize_menu_with_endpoint(self):
        """Test serializar menu con endpoint."""
        menu = {
            'id_menu': 501,
            'des_name': 'Dashboard',
            'endpoint': '/api/v1/reports/dashboard/',
            'method': 'GET'
        }
        
        serialized = MenuSerializer.serialize_menu(menu)
        
        assert 'endpoint' in serialized
        assert serialized['endpoint']['url'] == '/api/v1/reports/dashboard/'
        assert serialized['endpoint']['method'] == 'GET'
    
    def test_serialize_menu_with_submenus(self):
        """Test serializar menu con submenus."""
        menu = {
            'id_menu': 5,
            'des_name': 'Reportes',
            'submenus': [
                {
                    'id_menu': 501,
                    'des_name': 'Dashboard',
                    'endpoint': '/api/v1/reports/dashboard/',
                    'method': 'GET'
                }
            ]
        }
        
        serialized = MenuSerializer.serialize_menu(menu)
        
        assert len(serialized['submenus']) == 1
        assert serialized['submenus'][0]['id_menu'] == 501
        assert 'endpoint' in serialized['submenus'][0]
    
    def test_serialize_menu_removes_internal_fields(self):
        """Test que campos internos se eliminan."""
        menu = {
            'id_menu': 5,
            'des_name': 'Reportes',
            'required_functions': ['RPT-001: view_reports'],  # Campo interno
            'module': 'MOD_Reports'  # Campo interno
        }
        
        serialized = MenuSerializer.serialize_menu(menu)
        
        assert 'required_functions' not in serialized
        assert 'module' not in serialized
        assert 'id_menu' in serialized
        assert 'des_name' in serialized


# ============================================================================
# TESTS DE INTEGRACION
# ============================================================================

class TestMenuBuilderIntegration:
    """Tests de integracion para MenuBuilder."""
    
    @pytest.fixture
    def complex_metadata(self):
        """Metadata compleja con multiples apps."""
        return [
            {
                "module": "MOD_Auth",
                "app": "authentication",
                "menu_tree": [{
                    "nivel": 1,
                    "id_menu": 1,
                    "des_name": "Autenticacion",
                    "orden": 10,
                    "required_functions": [],
                    "submenus": [
                        {
                            "id_menu": 101,
                            "des_name": "Login",
                            "orden": 1,
                            "required_functions": []
                        }
                    ]
                }]
            },
            {
                "module": "MOD_Reports",
                "app": "reports",
                "menu_tree": [{
                    "nivel": 1,
                    "id_menu": 5,
                    "des_name": "Reportes",
                    "orden": 50,
                    "required_functions": [],
                    "submenus": [
                        {
                            "id_menu": 501,
                            "des_name": "Dashboard",
                            "orden": 1,
                            "required_functions": ["RPT-002: view_dashboard"]
                        }
                    ]
                }]
            }
        ]
    
    @patch('apps.core.navigation.builders.MenuBuilder._load_all_menu_metadata')
    def test_build_menu_multiple_apps(self, mock_load, complex_metadata):
        """Test construccion de menu con multiples apps."""
        mock_load.return_value = complex_metadata
        
        user = Mock()
        user.get_functions.return_value = ['RPT-002: view_dashboard']
        
        builder = MenuBuilder()
        menu = builder.build_user_menu(user)
        
        # Deben aparecer ambas apps
        assert len(menu) == 2
        
        menu_ids = [m['id_menu'] for m in menu]
        assert 1 in menu_ids  # Auth
        assert 5 in menu_ids  # Reports
    
    @patch('apps.core.navigation.builders.MenuBuilder._load_all_menu_metadata')
    def test_build_menu_ordered(self, mock_load, complex_metadata):
        """Test que menus se ordenan correctamente."""
        mock_load.return_value = complex_metadata
        
        user = Mock()
        user.get_functions.return_value = []
        
        builder = MenuBuilder()
        menu = builder.build_user_menu(user)
        
        # Deben estar ordenados por 'orden'
        assert menu[0]['orden'] == 10  # Auth primero
        assert menu[1]['orden'] == 50  # Reports segundo
