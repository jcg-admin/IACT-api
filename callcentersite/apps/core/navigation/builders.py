"""
Menu Builder v4.0.0 - Sistema de Navegacion IACT con RBAC v6.0.0

Construye menus dinamicos basados en:
- Metadata de navegacion (menu_metadata.json)
- Permisos RBAC v6.0.0 del usuario (namespaces Django)
- Validacion de iconos fisicos
- IDs numericos para todos los menus

Version: 4.0.0
Fecha: 2026-01-23
Cambios v4: RBAC v6.0.0 con namespaces Django
Cambios v3: Soporte para IDs numericos
"""

from pathlib import Path
from django.conf import settings
from typing import Dict, List, Set
import json
import logging

logger = logging.getLogger(__name__)


class MenuBuilder:
    """
    Construye menus personalizados para usuarios segun sus permisos RBAC v6.0.0.
    
    Caracteristicas:
    - Filtra menus por funciones del usuario (namespaces Django)
    - Valida existencia fisica de iconos
    - Inyecta datos dinamicos (avatar del usuario)
    - Ordena menus segun metadata
    - Soporta IDs numericos para menus
    
    Version 4.0.0: RBAC v6.0.0 con namespaces
    - Usa permission_django (e.g., 'users.view')
    - Soporta formato legacy 'CODE: namespace'
    - IDs numericos (Nivel 1: 1-99, Nivel 2: 100-999)
    """
    
    ICON_DEFAULTS = {
        'menu': '/static/icons/defaults/menu_default.png',
        'submenu': '/static/icons/defaults/submenu_default.png',
        'avatar': '/static/icons/defaults/avatar_default.png',
    }
    
    def __init__(self):
        self.apps_path = Path(settings.BASE_DIR) / 'apps'
        self.static_path = Path(settings.BASE_DIR) / 'static'
        self.media_path = Path(settings.MEDIA_ROOT)
    
    def build_user_menu(self, user) -> List[Dict]:
        """
        Construye menu completo para el usuario autenticado.
        
        Args:
            user: Instancia del modelo User
        
        Returns:
            Lista de diccionarios con estructura de menu
            Todos los id_menu son numericos (int)
        """
        # 1. Cargar metadata de todos los modulos
        all_menus = self._load_all_menu_metadata()
        
        # 2. Obtener funciones RBAC del usuario
        user_functions = self._get_user_functions(user)
        
        # 3. Filtrar menus por permisos
        filtered_menus = self._filter_by_permissions(all_menus, user_functions)
        
        # 4. Validar iconos
        validated_menus = self._validate_icons(filtered_menus)
        
        # 5. Personalizar con datos del usuario
        personalized_menus = self._personalize_menu(validated_menus, user)
        
        # 6. Ordenar por campo 'orden'
        sorted_menus = sorted(personalized_menus, key=lambda x: x.get('orden', 999))
        
        return sorted_menus
    
    def _load_all_menu_metadata(self) -> List[Dict]:
        """
        Carga archivos menu_metadata.json de todos los modulos.
        
        Returns:
            Lista de menus con sus submenus
            Todos con id_menu numerico
        """
        menus = []
        
        if not self.apps_path.exists():
            logger.warning(f"Directorio apps no encontrado: {self.apps_path}")
            return menus
        
        for app_dir in self.apps_path.iterdir():
            if not app_dir.is_dir():
                continue
            
            metadata_file = app_dir / 'navigation' / 'menu_metadata.json'
            
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        menu_tree = data.get('menu_tree', [])
                        
                        # Validar que todos los IDs sean numericos
                        for menu in menu_tree:
                            self._validate_menu_ids(menu)
                        
                        menus.extend(menu_tree)
                        
                        logger.debug(f"Cargada metadata de: {app_dir.name}")
                except json.JSONDecodeError as e:
                    logger.error(f"Error al parsear {metadata_file}: {e}")
                except Exception as e:
                    logger.error(f"Error cargando metadata de {app_dir.name}: {e}")
        
        logger.info(f"Cargados {len(menus)} menus principales")
        return menus
    
    def _validate_menu_ids(self, menu: Dict):
        """
        Valida que los IDs sean numericos.
        
        Args:
            menu: Diccionario del menu
        
        Raises:
            ValueError: Si encuentra un ID no numerico
        """
        if 'id_menu' in menu:
            if not isinstance(menu['id_menu'], int):
                raise ValueError(
                    f"ID de menu debe ser numerico: {menu.get('id_menu')} "
                    f"(tipo: {type(menu['id_menu'])})"
                )
        
        # Validar submenus
        for submenu in menu.get('submenus', []):
            if 'id_menu' in submenu:
                if not isinstance(submenu['id_menu'], int):
                    raise ValueError(
                        f"ID de submenu debe ser numerico: {submenu.get('id_menu')} "
                        f"(tipo: {type(submenu['id_menu'])})"
                    )
    
    def _get_user_functions(self, user) -> Set[str]:
        """
        Obtiene conjunto de funciones RBAC del usuario.
        
        RBAC v6.0.0: Retorna namespaces Django (permission_django).
        
        Args:
            user: Instancia del modelo User
        
        Returns:
            Set con namespaces de funciones (e.g., {'users.view', 'calls.view'})
        
        Examples:
            >>> user.get_functions()
            {'users.view', 'calls.view', 'reports.view'}
        """
        functions = set()
        
        if hasattr(user, 'get_functions'):
            functions = set(user.get_functions())
        elif hasattr(user, 'user_functions'):
            functions = set(user.user_functions.values_list('name', flat=True))
        else:
            logger.warning(f"Usuario {user.username} no tiene metodo get_functions()")
        
        logger.debug(f"Usuario {user.username} tiene {len(functions)} funciones")
        return functions
    
    def _filter_by_permissions(self, menus: List[Dict], user_functions: Set[str]) -> List[Dict]:
        """
        Filtra menus y submenus segun funciones del usuario.
        
        Args:
            menus: Lista de menus completos
            user_functions: Set de funciones del usuario
        
        Returns:
            Lista de menus filtrados
        """
        filtered = []
        
        for menu in menus:
            # Verificar permisos del menu principal
            required = self._extract_function_names(menu.get('required_functions', []))
            
            # Si el menu requiere permisos y el usuario no los tiene, skip
            if required and not required.intersection(user_functions):
                logger.debug(f"Menu ID {menu.get('id_menu')} filtrado (sin permisos)")
                continue
            
            # Filtrar submenus
            if 'submenus' in menu:
                filtered_submenus = []
                
                for submenu in menu['submenus']:
                    sub_required = self._extract_function_names(
                        submenu.get('required_functions', [])
                    )
                    
                    # Si no requiere permisos O el usuario los tiene, incluir
                    if not sub_required or sub_required.intersection(user_functions):
                        submenu_copy = submenu.copy()
                        filtered_submenus.append(submenu_copy)
                    else:
                        logger.debug(f"Submenu ID {submenu.get('id_menu')} filtrado")
                
                # Ordenar submenus por 'orden'
                filtered_submenus.sort(key=lambda x: x.get('orden', 999))
                menu['submenus'] = filtered_submenus
            
            # Solo incluir menu si tiene submenus o no requiere permisos
            if not menu.get('submenus') or len(menu['submenus']) > 0:
                filtered.append(menu)
        
        logger.info(f"Filtrados {len(filtered)} menus de {len(menus)} totales")
        return filtered
    
    def _extract_function_names(self, functions: List[str]) -> Set[str]:
        """
        Extrae nombres de funciones (namespaces).
        
        RBAC v6.0.0: Soporta namespaces Django directamente.
        
        Formatos soportados:
        - Namespace directo: 'users.view' -> {'users.view'}
        - Legacy con código: 'USR_VIEW: users.view' -> {'users.view'}
        - Lista vacía: [] -> set()
        
        Args:
            functions: Lista de namespaces o formato legacy
        
        Returns:
            Set de namespaces (e.g., {'users.view', 'calls.view'})
        
        Examples:
            >>> _extract_function_names(['users.view', 'calls.view'])
            {'users.view', 'calls.view'}
            
            >>> _extract_function_names(['USR_VIEW: users.view'])
            {'users.view'}
        """
        names = set()
        
        for func in functions:
            if ':' in func:
                # Formato legacy: 'USR_VIEW: users.view'
                parts = func.split(':', 1)
                if len(parts) == 2:
                    namespace = parts[1].strip()
                    names.add(namespace)
            else:
                # Formato v6.0.0: 'users.view'
                names.add(func.strip())
        
        return names
    
    def _validate_icons(self, menus: List[Dict]) -> List[Dict]:
        """
        Valida existencia fisica de archivos de iconos.
        Si un icono no existe, lo reemplaza por el default.
        
        Args:
            menus: Lista de menus con rutas de iconos
        
        Returns:
            Lista de menus con iconos validados
        """
        for menu in menus:
            # Validar icono del menu principal
            menu['icon'] = self._validate_icon_path(
                menu.get('icon'),
                default=self.ICON_DEFAULTS['menu']
            )
            
            # Validar iconos de submenus
            for submenu in menu.get('submenus', []):
                submenu['icon'] = self._validate_icon_path(
                    submenu.get('icon'),
                    default=self.ICON_DEFAULTS['submenu']
                )
        
        return menus
    
    def _validate_icon_path(self, icon_path: str, default: str) -> str:
        """
        Verifica que el archivo de icono exista fisicamente.
        
        Args:
            icon_path: Ruta del icono (ej: '/static/icons/menu/reports.png')
            default: Ruta del icono por defecto
        
        Returns:
            Ruta validada o default si no existe
        """
        if not icon_path:
            return default
        
        # Si es una variable de template (ej: '{{user.avatar_url}}'), no validar
        if '{{' in icon_path and '}}' in icon_path:
            return icon_path
        
        # Convertir ruta web a ruta fisica
        file_path = None
        
        if icon_path.startswith('/static/'):
            relative_path = icon_path.replace('/static/', '')
            file_path = self.static_path / relative_path
        elif icon_path.startswith('/media/'):
            relative_path = icon_path.replace('/media/', '')
            file_path = self.media_path / relative_path
        else:
            logger.warning(f"Ruta de icono invalida: {icon_path}")
            return default
        
        # Verificar existencia
        if file_path and file_path.exists():
            return icon_path
        else:
            logger.debug(f"Icono no encontrado: {icon_path} -> usando default")
            return default
    
    def _personalize_menu(self, menus: List[Dict], user) -> List[Dict]:
        """
        Inyecta datos dinamicos del usuario (ej: avatar).
        
        Args:
            menus: Lista de menus
            user: Instancia del modelo User
        
        Returns:
            Lista de menus personalizados
        """
        # Obtener URL del avatar del usuario
        if hasattr(user, 'get_avatar_url'):
            avatar_url = user.get_avatar_url()
        else:
            avatar_url = self.ICON_DEFAULTS['avatar']
        
        # Reemplazar variables de template
        for menu in menus:
            menu['icon'] = self._replace_template_vars(menu['icon'], user, avatar_url)
            
            for submenu in menu.get('submenus', []):
                submenu['icon'] = self._replace_template_vars(submenu['icon'], user, avatar_url)
        
        return menus
    
    def _replace_template_vars(self, text: str, user, avatar_url: str) -> str:
        """
        Reemplaza variables de template en texto.
        
        Args:
            text: Texto con posibles variables (ej: '{{user.avatar_url}}')
            user: Instancia del modelo User
            avatar_url: URL del avatar del usuario
        
        Returns:
            Texto con variables reemplazadas
        """
        if not text:
            return text
        
        replacements = {
            '{{user.avatar_url}}': avatar_url,
            '{{user.username}}': user.username,
            '{{user.first_name}}': user.first_name,
            '{{user.last_name}}': user.last_name,
        }
        
        result = text
        for var, value in replacements.items():
            if var in result:
                result = result.replace(var, value)
        
        return result


class MenuSerializer:
    """
    Serializa menus para respuestas de API.
    Asegura que todos los IDs sean numericos.
    """
    
    @staticmethod
    def serialize_menu(menu: Dict) -> Dict:
        """
        Serializa un menu para respuesta JSON.
        
        Args:
            menu: Diccionario con datos del menu
        
        Returns:
            Diccionario serializado para API con id_menu numerico
        """
        return {
            'id_menu': int(menu.get('id_menu')),  # Asegurar que sea int
            'des_name': menu.get('des_name'),
            'icon': menu.get('icon'),
            'nivel': menu.get('nivel'),
            'orden': menu.get('orden'),
            'submenus': [
                MenuSerializer.serialize_submenu(submenu)
                for submenu in menu.get('submenus', [])
            ]
        }
    
    @staticmethod
    def serialize_submenu(submenu: Dict) -> Dict:
        """
        Serializa un submenu para respuesta JSON.
        
        Args:
            submenu: Diccionario con datos del submenu
        
        Returns:
            Diccionario serializado para API con id_menu numerico
        """
        endpoint = submenu.get('endpoint', {})
        
        return {
            'id_menu': int(submenu.get('id_menu')),  # Asegurar que sea int
            'des_name': submenu.get('des_name'),
            'icon': submenu.get('icon'),
            'nivel': 2,
            'orden': submenu.get('orden'),
            'endpoint': {
                'url': endpoint if isinstance(endpoint, str) else endpoint.get('url'),
                'method': submenu.get('method', 'GET'),
            }
        }


class MenuValidator:
    """
    Valida estructura de menus y esquema de IDs.
    """
    
    # Esquema de IDs numericos
    ID_SCHEMA = {
        'nivel_1_range': (1, 99),
        'nivel_2_ranges': {
            1: (101, 199),  # Auth
            2: (201, 299),  # Users
            3: (301, 399),  # Access
            4: (401, 499),  # Pipeline
            5: (501, 599),  # Reports
            6: (601, 699),  # Alerts
            7: (701, 799),  # Audit
            8: (801, 899),  # Logs
        }
    }
    
    @classmethod
    def validate_menu_structure(cls, menu: Dict) -> bool:
        """
        Valida estructura y IDs de un menu.
        
        Args:
            menu: Diccionario del menu
        
        Returns:
            True si es valido
        
        Raises:
            ValueError: Si encuentra errores de validacion
        """
        # Validar ID del menu principal
        menu_id = menu.get('id_menu')
        if not isinstance(menu_id, int):
            raise ValueError(f"ID de menu debe ser numerico: {menu_id}")
        
        min_id, max_id = cls.ID_SCHEMA['nivel_1_range']
        if not (min_id <= menu_id <= max_id):
            raise ValueError(
                f"ID de menu nivel 1 fuera de rango: {menu_id} "
                f"(rango permitido: {min_id}-{max_id})"
            )
        
        # Validar IDs de submenus
        if 'submenus' in menu:
            expected_range = cls.ID_SCHEMA['nivel_2_ranges'].get(menu_id)
            if not expected_range:
                logger.warning(f"No hay rango definido para submenus de menu {menu_id}")
            else:
                min_sub, max_sub = expected_range
                
                for submenu in menu['submenus']:
                    submenu_id = submenu.get('id_menu')
                    if not isinstance(submenu_id, int):
                        raise ValueError(f"ID de submenu debe ser numerico: {submenu_id}")
                    
                    if not (min_sub <= submenu_id <= max_sub):
                        raise ValueError(
                            f"ID de submenu fuera de rango: {submenu_id} "
                            f"(rango permitido para menu {menu_id}: {min_sub}-{max_sub})"
                        )
        
        return True
