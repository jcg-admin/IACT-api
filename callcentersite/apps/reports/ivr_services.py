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
from django.db import connections, OperationalError


def _call_sp(sp_name: str, params: list) -> list[dict]:
    """
    Invoca un SP de MariaDB y retorna lista de dicts.
    Maneja el caso de SP que retorna 0 filas (cursor.description is None).
    """
    with connections['ivr'].cursor() as cursor:
        cursor.callproc(sp_name, params)
        if cursor.description is None:
            return []
        cols = [c[0] for c in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]


def get_clientes(quarter: str) -> list[dict]:
    """
    UC_RPT_17 — Clientes unicos por segmento.
    Llama: sp_rpt_clientes(p_quarter)
    Retorna: 3 filas (nacional_A, nacional_B, puebla)
    """
    return _call_sp('sp_rpt_clientes', [quarter])


def get_centros_transferencia(quarter: str, segmento: str = 'todas') -> list[dict]:
    """
    UC_RPT_12 — Detalle de centros de transferencia.
    Llama: sp_rpt_centros_transferencia(p_quarter, p_segmento)
    """
    return _call_sp('sp_rpt_centros_transferencia', [quarter, segmento])


def get_llamadas_abandonadas(quarter: str, segmento: str = 'todas') -> list[dict]:
    """
    UC_RPT_13 — Llamadas abandonadas por menu.
    Llama: sp_rpt_llamadas_abandonadas(p_quarter, p_segmento)
    """
    return _call_sp('sp_rpt_llamadas_abandonadas', [quarter, segmento])


def get_cmenu_error(quarter: str, segmento: str = 'todas') -> list[dict]:
    """
    UC_RPT_14 — Anomalias: cMenu contiene numero de telefono.
    Llama: sp_rpt_cMENU_ERROR(p_quarter, p_segmento)
    """
    return _call_sp('sp_rpt_cMENU_ERROR', [quarter, segmento])


def get_centros_xsegmento(quarter: str) -> list[dict]:
    """
    UC_RPT_15 — KPIs SLA por centro de transferencia y segmento.
    Llama: sp_rpt_centros_xsegmento(p_quarter)
    """
    return _call_sp('sp_rpt_centros_xsegmento', [quarter])


def get_menu_redirigidos(quarter: str, segmento: str = 'todas') -> list[dict]:
    """
    UC_RPT_16 (vista redirigidos) — Menus que dispararon transferencia.
    Llama: sp_rpt_menu_redirigidos(p_quarter, p_segmento)
    """
    return _call_sp('sp_rpt_menu_redirigidos', [quarter, segmento])


def get_menu_centro(quarter: str, segmento: str = 'todas') -> list[dict]:
    """
    UC_RPT_16 (vista menu_centro) — Centro -> menus que lo alimentan.
    Llama: sp_rpt_menu_centro(p_quarter, p_segmento)
    """
    return _call_sp('sp_rpt_menu_centro', [quarter, segmento])


# Segmentos y quarters validos para validacion en views
SEGMENTOS_VALIDOS  = {'todas', 'nacional_A', 'nacional_B', 'puebla'}
QUARTERS_VALIDOS   = {
    'Q01_25', 'Q02_25', 'Q03_25', 'Q04_25',
    'Q01_26', 'Q02_26',
}
