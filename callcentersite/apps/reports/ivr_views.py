"""
Views de reportes IVR — B-01.

Expone los SPs de MariaDB como endpoints DRF.
Cada view valida quarter y segmento, invoca el servicio y retorna JSON.
"""
from django.db import OperationalError
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from . import ivr_services as svc


def _validate(quarter=None, segmento=None):
    errores = []
    if quarter and quarter not in svc.QUARTERS_VALIDOS:
        errores.append(f'quarter invalido: {quarter}. Validos: {sorted(svc.QUARTERS_VALIDOS)}')
    if segmento and segmento not in svc.SEGMENTOS_VALIDOS:
        errores.append(f'segmento invalido: {segmento}. Validos: {sorted(svc.SEGMENTOS_VALIDOS)}')
    return errores


def _ivr_response(fn, *args, extra=None):
    """Ejecuta fn(*args), maneja OperationalError y retorna Response."""
    try:
        data = fn(*args)
    except OperationalError as e:
        return Response(
            {'error': 'No se pudo conectar a la base de datos IVR.', 'detail': str(e)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    payload = {'total_filas': len(data), 'datos': data}
    if extra:
        payload.update(extra)
    return Response(payload)


class ClientesReportView(APIView):
    """
    UC_RPT_17 — Clientes unicos por segmento.
    GET /api/reports/ivr/clients/?quarter=Q01_25
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        quarter = request.query_params.get('quarter', 'Q01_25')
        errores = _validate(quarter=quarter)
        if errores:
            return Response({'errores': errores}, status=400)
        return _ivr_response(svc.get_clientes, quarter,
                              extra={'quarter': quarter})


class CentrosTransferenciaView(APIView):
    """
    UC_RPT_12 — Detalle centros de transferencia.
    GET /api/reports/ivr/transfer-centers/?quarter=Q01_25&segmento=todas
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        quarter  = request.query_params.get('quarter',  'Q01_25')
        segmento = request.query_params.get('segmento', 'todas')
        errores = _validate(quarter=quarter, segmento=segmento)
        if errores:
            return Response({'errores': errores}, status=400)
        return _ivr_response(svc.get_centros_transferencia, quarter, segmento,
                              extra={'quarter': quarter, 'segmento': segmento})


class LlamadasAbandonadasView(APIView):
    """
    UC_RPT_13 — Llamadas abandonadas.
    GET /api/reports/ivr/abandoned/?quarter=Q01_25&segmento=todas
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        quarter  = request.query_params.get('quarter',  'Q01_25')
        segmento = request.query_params.get('segmento', 'todas')
        errores = _validate(quarter=quarter, segmento=segmento)
        if errores:
            return Response({'errores': errores}, status=400)
        return _ivr_response(svc.get_llamadas_abandonadas, quarter, segmento,
                              extra={'quarter': quarter, 'segmento': segmento})


class CMENUErrorView(APIView):
    """
    UC_RPT_14 — Anomalias cMenu con numero de telefono.
    GET /api/reports/ivr/menu-errors/?quarter=Q01_25&segmento=todas
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        quarter  = request.query_params.get('quarter',  'Q01_25')
        segmento = request.query_params.get('segmento', 'todas')
        errores = _validate(quarter=quarter, segmento=segmento)
        if errores:
            return Response({'errores': errores}, status=400)
        return _ivr_response(svc.get_cmenu_error, quarter, segmento,
                              extra={'quarter': quarter, 'segmento': segmento})


class CentrosXSegmentoView(APIView):
    """
    UC_RPT_15 — KPIs SLA por centro y segmento.
    GET /api/reports/ivr/centers-by-segment/?quarter=Q01_25
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        quarter = request.query_params.get('quarter', 'Q01_25')
        errores = _validate(quarter=quarter)
        if errores:
            return Response({'errores': errores}, status=400)
        return _ivr_response(svc.get_centros_xsegmento, quarter,
                              extra={'quarter': quarter})


class MenusIVRView(APIView):
    """
    UC_RPT_16 — Menus IVR (redirigidos o menu_centro).
    GET /api/reports/ivr/menus/?quarter=Q01_25&vista=redirigidos&segmento=todas
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        quarter  = request.query_params.get('quarter',  'Q01_25')
        vista    = request.query_params.get('vista',    'redirigidos')
        segmento = request.query_params.get('segmento', 'todas')

        errores = _validate(quarter=quarter, segmento=segmento)
        if vista not in ('redirigidos', 'menu_centro'):
            errores.append('vista invalida: usar redirigidos o menu_centro')
        if errores:
            return Response({'errores': errores}, status=400)

        fn = svc.get_menu_redirigidos if vista == 'redirigidos' else svc.get_menu_centro
        return _ivr_response(fn, quarter, segmento,
                              extra={'quarter': quarter, 'vista': vista, 'segmento': segmento})
