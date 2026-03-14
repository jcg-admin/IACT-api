"""
Builders para el sistema de navegacion del menu principal.
"""


class MenuValidator:
    """Valida la estructura de datos del menu."""

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


class MenuBuilder:
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
