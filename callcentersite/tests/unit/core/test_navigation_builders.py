"""
Tests para MenuValidator.

Cobertura:
- validate_numeric_id: validacion de IDs genericos
- validate_level1_id / validate_level2_id: rangos por nivel
- validate_menu_structure: campos requeridos y consistencia ID/nivel
- validate_icon_path: existencia de archivo de icono

TestMenuBuilder, TestMenuSerializer, TestMenuBuilderIntegration eliminados:
pertenecen a T-102 (MenuItem) — se crearán cuando la funcionalidad esté implementada.
"""

import pytest
from unittest.mock import patch
from apps.core.navigation.builders import MenuValidator, MenuBuilder


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
