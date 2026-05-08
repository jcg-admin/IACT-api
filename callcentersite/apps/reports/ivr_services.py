"""
Servicios de reportes IVR — capa de acceso a MariaDB.

B-01: Invoca los SPs de IACT-db via connections['ivr'].cursor().

Cada funcion corresponde a un SP desplegado y verificado en Fase 3:
  sp_rpt_clientes              -> UC_RPT_17
  sp_rpt_centros_transferencia -> UC_RPT_12
  sp_rpt_llamadas_abandonadas  -> UC_RPT_13
  sp_rpt_cMENU_ERROR           -> UC_RPT_14
  sp_rpt_centros_xsegmento     -> UC_RPT_15
  sp_rpt_menu_redirigidos      -> UC_RPT_16 (vista redirigidos)
  sp_rpt_menu_centro           -> UC_RPT_16 (vista menu_centro)
"""
from django.conf import settings
from django.db import connections, OperationalError


def _call_sp(sp_name: str, params: list) -> list[dict]:
    """
    Invokes a MariaDB stored procedure and returns a list of dicts.
    Applies IVR_QUERY_TIMEOUT_SEC timeout before each call.
    Handles SPs that return 0 rows (cursor.description is None).
    """
    timeout_sec = getattr(settings, 'IVR_QUERY_TIMEOUT_SEC', 30)
    with connections['ivr'].cursor() as cursor:
        cursor.execute(f"SET SESSION MAX_STATEMENT_TIME={timeout_sec}")
        cursor.callproc(sp_name, params)
        if cursor.description is None:
            return []
        cols = [c[0] for c in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]


def get_clients(quarter: str) -> list[dict]:
    """
    UC_RPT_17 — Clientes unicos por segmento.
    Llama: sp_rpt_clientes(p_quarter)
    Retorna: 3 filas (nacional_A, nacional_B, puebla)
    """
    return _call_sp('sp_rpt_clientes', [quarter])


def get_transfer_centers(quarter: str, segment: str = 'todas') -> list[dict]:
    """
    UC_RPT_12 — Detalle de centros de transferencia.
    Llama: sp_rpt_centros_transferencia(p_quarter, p_segmento)
    """
    return _call_sp('sp_rpt_centros_transferencia', [quarter, segment])


def get_abandoned_calls(quarter: str, segment: str = 'todas') -> list[dict]:
    """
    UC_RPT_13 — Llamadas abandonadas por menu.
    Llama: sp_rpt_llamadas_abandonadas(p_quarter, p_segmento)
    """
    return _call_sp('sp_rpt_llamadas_abandonadas', [quarter, segment])


def get_cmenu_errors(quarter: str, segment: str = 'todas') -> list[dict]:
    """
    UC_RPT_14 — Anomalias: cMenu contiene numero de telefono.
    Llama: sp_rpt_cMENU_ERROR(p_quarter, p_segmento)
    """
    return _call_sp('sp_rpt_cMENU_ERROR', [quarter, segment])


def get_centers_by_segment(quarter: str) -> list[dict]:
    """
    UC_RPT_15 — KPIs SLA por centro de transferencia y segmento.
    Llama: sp_rpt_centros_xsegmento(p_quarter)
    """
    return _call_sp('sp_rpt_centros_xsegmento', [quarter])


def get_redirected_menus(quarter: str, segment: str = 'todas') -> list[dict]:
    """
    UC_RPT_16 (vista redirigidos) — Menus que dispararon transferencia.
    Llama: sp_rpt_menu_redirigidos(p_quarter, p_segmento)
    """
    return _call_sp('sp_rpt_menu_redirigidos', [quarter, segment])


def get_center_menus(quarter: str, segment: str = 'todas') -> list[dict]:
    """
    UC_RPT_16 (vista menu_centro) — Centro -> menus que lo alimentan.
    Llama: sp_rpt_menu_centro(p_quarter, p_segmento)
    """
    return _call_sp('sp_rpt_menu_centro', [quarter, segment])


# Segmentos y quarters validos para validacion en views
VALID_SEGMENTS = {'todas', 'nacional_A', 'nacional_B', 'puebla'}


def get_available_quarters() -> set[str]:
    """
    Returns the set of quarters available in base_ivr_detalle.
    No cache (CNST-010). Lightweight: SELECT DISTINCT on indexed column.
    Returns empty set if MariaDB is unavailable.
    """
    try:
        with connections['ivr'].cursor() as cursor:
            cursor.execute(
                "SELECT DISTINCT trimestre FROM base_ivr_detalle ORDER BY trimestre"
            )
            return {row[0] for row in cursor.fetchall()}
    except OperationalError:
        return set()
