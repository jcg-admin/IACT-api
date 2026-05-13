"""
Builders para el sistema de navegacion del menu principal.
"""
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class MenuValidator:
    """Valida la estructura de datos del menu."""

    # Rangos de ID por nivel (según convención del dominio IVR)
    _LEVEL1_ID_RANGE = (1, 99)
    _LEVEL2_ID_RANGE = (100, 899)
    _REQUIRED_MENU_FIELDS = ('id_menu', 'des_name', 'nivel', 'orden')

    def validate_module(self, module_data):
        required_fields = ('code', 'name', 'url_path')
        errors = []
        for field in required_fields:
            if field not in module_data or not module_data[field]:
                errors.append(f"Campo requerido faltante o vacio: '{field}'")
        return errors

    def validate_menu(self, menu_data):
        errors = []
        if not isinstance(menu_data, list):
            return ['menu_data debe ser una lista']
        for i, item in enumerate(menu_data):
            item_errors = self.validate_module(item)
            for err in item_errors:
                errors.append(f'Item {i}: {err}')
        return errors

    @staticmethod
    def validate_numeric_id(value) -> bool:
        """Verifica que value es un entero positivo."""
        if not isinstance(value, int) or isinstance(value, bool):
            return False
        lo, hi = MenuValidator._LEVEL1_ID_RANGE[0], MenuValidator._LEVEL2_ID_RANGE[1]
        return lo <= value <= hi

    @staticmethod
    def validate_level1_id(value) -> bool:
        """Nivel 1: rango 1–99."""
        if not isinstance(value, int) or isinstance(value, bool):
            return False
        lo, hi = MenuValidator._LEVEL1_ID_RANGE
        return lo <= value <= hi

    @staticmethod
    def validate_level2_id(value) -> bool:
        """Nivel 2: rango 100–899."""
        if not isinstance(value, int) or isinstance(value, bool):
            return False
        lo, hi = MenuValidator._LEVEL2_ID_RANGE
        return lo <= value <= hi

    @staticmethod
    def validate_menu_structure(menu: Dict) -> Tuple[bool, List[str]]:
        """
        Valida la estructura de un item de menú.

        Comprueba:
        - Presencia de campos requeridos.
        - Consistencia entre id_menu y nivel (ID debe estar en el rango del nivel).

        Returns:
            (is_valid, errors): bool y lista de mensajes de error.
        """
        errors = []

        for field in MenuValidator._REQUIRED_MENU_FIELDS:
            if field not in menu:
                errors.append(f"Campo requerido faltante: '{field}'")

        if errors:
            return False, errors

        id_menu = menu['id_menu']
        nivel = menu['nivel']

        if nivel == 1 and not MenuValidator.validate_level1_id(id_menu):
            errors.append(
                f"ID {id_menu} no es valido para nivel 1 (rango 1–99)"
            )
        elif nivel == 2 and not MenuValidator.validate_level2_id(id_menu):
            errors.append(
                f"ID {id_menu} no es valido para nivel 2 (rango 100–899)"
            )

        return len(errors) == 0, errors

    @staticmethod
    def validate_icon_path(path: str) -> bool:
        """Verifica que el archivo de icono existe en el sistema de archivos."""
        return Path(path).exists()


class NavigationMenuAssembler:
    """Construye la estructura de navegacion a partir de los modulos."""

    def __init__(self):
        self.validator = MenuValidator()

    def build_from_modules(self, modules_qs, user=None):
        """
        Construye el menu a partir de un queryset de modulos.

        Args:
            modules_qs: QuerySet de modulos activos.
            user: Usuario autenticado (para filtrar permisos).

        Returns:
            list: Estructura de menu serializada.
        """
        parent_modules = [m for m in modules_qs if m.parent_id is None]
        parent_modules.sort(key=lambda m: m.order)

        menu = []
        for module in parent_modules:
            children = [
                m for m in modules_qs
                if m.parent_id == module.pk
            ]
            children.sort(key=lambda m: m.order)

            item = self._serialize_module(module)
            item['children'] = [self._serialize_module(c) for c in children]
            menu.append(item)

        return menu

    def _serialize_module(self, module):
        return {
            'code': module.code,
            'name': module.name,
            'url_path': module.url_path,
            'icon': getattr(module, 'icon', None),
            'order': module.order,
            'is_active': module.is_active,
        }

    def build_flat(self, modules_qs):
        """Retorna una lista plana de todos los modulos."""
        result = []
        for module in modules_qs:
            result.append(self._serialize_module(module))
        return result
