"""
apps/authentication/menu_view.py

MenuView — UC_PERM_08: Generar Menú Dinámico.

Fuente: uc-perm-08/implementacion-tecnica.rst § 11
        uc-perm-08/datos-involucrados.rst § 7.3, § 7.4

Endpoint: GET /api/me/menu/
Requiere: autenticación JWT (cualquier usuario autenticado).
Sin RBAC adicional: el menú muestra solo las funciones que el usuario tiene.

Componentes:
  FunctionRegistry — lista Function con menu_visible=True
  MenuBuilder      — construye árbol Domain→Section→Action
  MenuCache        — cache 300s, key=menu:{user_id}:{locale}
  MenuInvalidator  — listener de eventos (post_save en UserAccessGroup)
"""
from django.core.cache import cache
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


MENU_CACHE_TTL   = 300   # CA-09: 300s
SUPPORTED_LOCALES = {'es', 'en'}
DEFAULT_LOCALE    = 'es'

MENU_CACHE_PREFIX = 'menu'


def _cache_key(user_id: int, locale: str) -> str:
    return f'{MENU_CACHE_PREFIX}:{user_id}:{locale}'


# ---------------------------------------------------------------------------
# FunctionRegistry
# ---------------------------------------------------------------------------
class FunctionRegistry:
    """
    Lista todas las Functions con menu_visible=True.
    Fuente de verdad para el árbol de menú.
    """
    @staticmethod
    def list() -> list[dict]:
        from apps.access.models import Function
        return list(
            Function.objects.filter(
                menu_visible=True,
                is_active=True,
            ).values(
                'pk', 'code',
                'menu_domain', 'menu_section', 'menu_action',
                'menu_label_es', 'menu_label_en',
                'menu_icon', 'menu_order',
            )
        )


# ---------------------------------------------------------------------------
# MenuBuilder
# ---------------------------------------------------------------------------
class MenuBuilder:
    """
    Construye el árbol Domain→Section→Action.
    Fuente: uc-perm-08/implementacion-tecnica.rst § 11.3

    CA-11: orden estable (ordenar por menu_order).
    CA-12: domains vacíos suprimidos.
    """

    @classmethod
    def build(cls, user_id: int, locale: str) -> dict:
        """
        Retorna:
        {
          domains: [{code, label, order, sections: [{code, label, icon, order, actions: [...]}]}],
          user_id: int,
          locale_used: str,
          generated_at: str,
          cache: bool,
        }
        """
        # 1. Cache lookup (CA-09)
        key = _cache_key(user_id, locale)
        cached = cache.get(key)
        if cached:
            cached['cache'] = True
            return cached

        # 2. FunctionRegistry
        entries = FunctionRegistry.list()

        # 3. Bulk check (UC_PERM_07)
        if not entries:
            result = cls._empty_result(user_id, locale)
            cache.set(key, result, timeout=MENU_CACHE_TTL)
            return result

        from apps.access.services.permission_service import PermissionService
        codes = [e['code'] for e in entries]
        try:
            perm_results = PermissionService.check_bulk(user_id, codes)
        except Exception:
            perm_results = {code: type('R', (), {'allowed': False})() for code in codes}

        allowed_codes = {code for code, r in perm_results.items() if r.allowed}

        # CA-03: Function REVOKED no aparece → ya filtrado por PermissionService
        # CA-05: menu_visible=False → ya filtrado por FunctionRegistry

        # 4. Construir árbol
        domains_map: dict = {}
        for entry in entries:
            if entry['code'] not in allowed_codes:
                continue

            d = entry['menu_domain'] or 'general'
            s = entry['menu_section'] or 'default'
            label = entry['menu_label_es'] if locale == 'es' else entry['menu_label_en']
            label = label or entry['code']

            if d not in domains_map:
                domains_map[d] = {'sections': {}}

            if s not in domains_map[d]['sections']:
                domains_map[d]['sections'][s] = {
                    'code': s, 'icon': entry['menu_icon'],
                    'order': entry['menu_order'], 'actions': [],
                }

            domains_map[d]['sections'][s]['actions'].append({
                'code':          entry['menu_action'] or entry['code'],
                'label':         label,
                'function_code': entry['code'],
                'order':         entry['menu_order'],
            })

        # CA-11: orden estable; CA-12: suprimir vacíos
        domains = []
        for d_code, d_data in sorted(domains_map.items()):
            sections = []
            for s_data in sorted(d_data['sections'].values(), key=lambda x: x['order']):
                if s_data['actions']:
                    s_data['actions'] = sorted(s_data['actions'], key=lambda a: a['order'])
                    sections.append(s_data)
            if sections:
                domains.append({
                    'code':     d_code,
                    'label':    d_code,
                    'order':    0,
                    'sections': sections,
                })

        result = {
            'domains':           domains,
            'user_id':           user_id,
            'locale_used':       locale,
            'generated_at':      timezone.now().isoformat(),
            'allowed_codes_count': len(allowed_codes),
            'cache':             False,
        }
        cache.set(key, result, timeout=MENU_CACHE_TTL)
        return result

    @staticmethod
    def _empty_result(user_id: int, locale: str) -> dict:
        """CA-02: User sin funciones → domains: []."""
        return {
            'domains':           [],
            'user_id':           user_id,
            'locale_used':       locale,
            'generated_at':      timezone.now().isoformat(),
            'allowed_codes_count': 0,
            'cache':             False,
        }

    @staticmethod
    def invalidate(user_id: int) -> None:
        """CA-10: invalidar cache de menú del usuario."""
        for locale in SUPPORTED_LOCALES:
            cache.delete(_cache_key(user_id, locale))


# ---------------------------------------------------------------------------
# MenuView
# ---------------------------------------------------------------------------
@extend_schema(
    summary='UC_PERM_08 — Menú dinámico del usuario',
    description=(
        'Retorna el árbol de navegación del usuario autenticado basado en sus '
        'permisos efectivos (UC_PERM_07 bulk check).\n\n'
        '**CA-01**: domains con múltiples secciones.\n'
        '**CA-02**: sin funciones → domains:[].\n'
        '**CA-03**: Function REVOKED no aparece (UC_PERM_07).\n'
        '**CA-05**: menu_visible=False → no aparece.\n'
        '**CA-06**: default locale=es.\n'
        '**CA-07**: ?locale=en → labels en inglés.\n'
        '**CA-08**: locale no soportado → fallback es.\n'
        '**CA-09**: segunda llamada dentro de TTL → cache=true.\n'
        '**CA-10**: invalidate post UC_ACC_01.\n'
        '**CA-11**: orden estable por menu_order.\n'
        '**CA-12**: domains vacíos suprimidos.\n'
        '**CA-15**: sin AuditEvent (P-51 read-no-audit).'
    ),
    parameters=[
        OpenApiParameter('locale', str, location='query',
                         description='Locale para labels (es|en). Default: es.',
                         enum=['es', 'en']),
    ],
    responses={
        200: OpenApiResponse(description='Árbol de navegación del usuario.'),
        401: OpenApiResponse(description='Sin autenticación.'),
    },
    tags=['Autenticacion'],
)
class MenuView(APIView):
    """
    GET /api/me/menu/

    UC_PERM_08 — Menú dinámico.
    CNST-010: permission_classes=[IsAuthenticated] explícito.
    CA-15: P-51 read-no-audit — CERO AuditEvents.
    """
    permission_classes = [IsAuthenticated]   # sin HasFunction adicional — es el propio menú

    def get(self, request):
        # CA-06..08: resolver locale
        locale_param = request.query_params.get('locale', DEFAULT_LOCALE).lower()
        locale = locale_param if locale_param in SUPPORTED_LOCALES else DEFAULT_LOCALE

        try:
            result = MenuBuilder.build(user_id=request.user.pk, locale=locale)
        except Exception:
            return Response(
                {'error': 'SERVICE_UNAVAILABLE', 'message': 'Error al construir el menú.'},
                status=503,
            )

        return Response(result)
