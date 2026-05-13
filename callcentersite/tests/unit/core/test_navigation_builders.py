"""
Tests para MenuValidator y NavigationMenuAssembler.

Cobertura MenuValidator:
- validate_numeric_id: validacion de IDs genericos
- validate_level1_id / validate_level2_id: rangos por nivel
- validate_menu_structure: campos requeridos y consistencia ID/nivel
- validate_icon_path: existencia de archivo de icono

Cobertura NavigationMenuAssembler:
- build_from_modules: árbol jerárquico de módulos
- build_flat: lista plana de módulos
- _serialize_module: estructura del item de menú
"""

import pytest
from unittest.mock import patch, Mock
from apps.core.navigation.builders import MenuValidator, NavigationMenuAssembler


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
# TESTS NavigationMenuAssembler
# ============================================================================

class TestNavigationMenuAssembler:
    """Tests para NavigationMenuAssembler (build_from_modules, build_flat, _serialize_module)."""

    @pytest.fixture
    def assembler(self):
        return NavigationMenuAssembler()

    def _make_module(self, pk, code, name, url_path, order,
                     parent_id=None, is_active=True, icon=None):
        """Crea un Mock de Module con los campos que usa NavigationMenuAssembler."""
        m = Mock()
        m.pk = pk
        m.code = code
        m.name = name
        m.url_path = url_path
        m.icon = icon
        m.order = order
        m.is_active = is_active
        m.parent_id = parent_id
        return m

    # ── build_from_modules ────────────────────────────────────────────────

    def test_build_from_modules_empty_queryset(self, assembler):
        """Lista vacía retorna lista vacía."""
        assert assembler.build_from_modules([]) == []

    def test_build_from_modules_single_root_module(self, assembler):
        """Módulo raíz sin hijos retorna un item con children vacío."""
        module = self._make_module(1, 'MOD_A', 'Módulo A', '/a/', order=1)
        result = assembler.build_from_modules([module])

        assert len(result) == 1
        item = result[0]
        assert item['code'] == 'MOD_A'
        assert item['name'] == 'Módulo A'
        assert item['url_path'] == '/a/'
        assert item['children'] == []

    def test_build_from_modules_parent_with_child(self, assembler):
        """Módulo hijo se anida bajo su padre, no aparece en la raíz."""
        parent = self._make_module(1, 'MOD_PARENT', 'Padre', '/parent/', order=1)
        child  = self._make_module(2, 'MOD_CHILD',  'Hijo',  '/child/',  order=1,
                                   parent_id=1)
        result = assembler.build_from_modules([parent, child])

        assert len(result) == 1                           # solo el padre en raíz
        assert len(result[0]['children']) == 1
        assert result[0]['children'][0]['code'] == 'MOD_CHILD'

    def test_build_from_modules_orders_parents(self, assembler):
        """Los módulos raíz se ordenan por el campo 'order' ascendente."""
        m1 = self._make_module(1, 'MOD_B', 'B', '/b/', order=2)
        m2 = self._make_module(2, 'MOD_A', 'A', '/a/', order=1)
        result = assembler.build_from_modules([m1, m2])

        assert result[0]['code'] == 'MOD_A'   # order=1 primero
        assert result[1]['code'] == 'MOD_B'   # order=2 segundo

    def test_build_from_modules_orders_children(self, assembler):
        """Los hijos de un módulo también se ordenan por 'order'."""
        parent = self._make_module(1, 'MOD_P', 'P', '/p/', order=1)
        c1     = self._make_module(2, 'MOD_C2', 'C2', '/c2/', order=2, parent_id=1)
        c2     = self._make_module(3, 'MOD_C1', 'C1', '/c1/', order=1, parent_id=1)
        result = assembler.build_from_modules([parent, c1, c2])

        children = result[0]['children']
        assert children[0]['code'] == 'MOD_C1'   # order=1
        assert children[1]['code'] == 'MOD_C2'   # order=2

    # ── build_flat ────────────────────────────────────────────────────────

    def test_build_flat_empty_queryset(self, assembler):
        """Lista vacía retorna lista vacía."""
        assert assembler.build_flat([]) == []

    def test_build_flat_returns_all_modules(self, assembler):
        """Retorna todos los módulos sin jerarquía."""
        modules = [
            self._make_module(1, 'MOD_A', 'A', '/a/', order=1),
            self._make_module(2, 'MOD_B', 'B', '/b/', order=2),
        ]
        result = assembler.build_flat(modules)

        assert len(result) == 2
        codes = {item['code'] for item in result}
        assert codes == {'MOD_A', 'MOD_B'}

    def test_build_flat_does_not_add_children_key(self, assembler):
        """build_flat usa _serialize_module — sin clave 'children'."""
        module = self._make_module(1, 'MOD_A', 'A', '/a/', order=1)
        result = assembler.build_flat([module])

        assert 'children' not in result[0]

    # ── _serialize_module ─────────────────────────────────────────────────

    def test_serialize_module_all_fields(self, assembler):
        """_serialize_module retorna los 6 campos esperados."""
        module = self._make_module(1, 'MOD_X', 'X', '/x/', order=5, icon='icon.svg')
        result = assembler._serialize_module(module)

        assert result == {
            'code':      'MOD_X',
            'name':      'X',
            'url_path':  '/x/',
            'icon':      'icon.svg',
            'order':     5,
            'is_active': True,
        }

    def test_serialize_module_icon_none_when_absent(self, assembler):
        """icon es None si el módulo no tiene atributo 'icon'."""
        module = Mock(spec=['code', 'name', 'url_path', 'order', 'is_active'])
        module.code = 'MOD_Y'
        module.name = 'Y'
        module.url_path = '/y/'
        module.order = 1
        module.is_active = True
        result = assembler._serialize_module(module)

        assert result['icon'] is None
