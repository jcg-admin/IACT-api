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
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from . import ivr_services as svc

# Parametros comunes a todos los endpoints IVR
_IVR_QUARTER_PARAM = OpenApiParameter(
    'quarter', str,
    description="Quarter a consultar. Valores validos: Q01_25..Q02_26",
    required=True,
)
_IVR_SEGMENTO_PARAM = OpenApiParameter(
    'segmento', str,
    enum=['todas', 'nacional_A', 'nacional_B', 'puebla'],
    default='todas',
    description="Segmento de negocio. Default: todas",
)


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


@extend_schema(
    summary="UC_RPT_17 — Clientes unicos por segmento",
    description="Invoca sp_rpt_clientes(p_quarter) en MariaDB. Retorna 3 filas: nacional_A, nacional_B, puebla.",
    parameters=[_IVR_QUARTER_PARAM],
    responses={200: OpenApiResponse(description="Lista de clientes por segmento"),
               400: OpenApiResponse(description="Quarter invalido"),
               503: OpenApiResponse(description="MariaDB no disponible")},
    tags=["Reportes de Llamadas"]
)
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


@extend_schema(
    summary="UC_RPT_12 — Centros de transferencia",
    parameters=[_IVR_QUARTER_PARAM, _IVR_SEGMENTO_PARAM],
    responses={200: OpenApiResponse(description="Detalle de centros de transferencia"),
               503: OpenApiResponse(description="MariaDB no disponible")},
    tags=["Reportes de Llamadas"]
)
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


@extend_schema(
    summary="UC_RPT_13 — Llamadas abandonadas por menu",
    parameters=[_IVR_QUARTER_PARAM, _IVR_SEGMENTO_PARAM],
    responses={200: OpenApiResponse(description="Llamadas abandonadas por menu IVR"),
               503: OpenApiResponse(description="MariaDB no disponible")},
    tags=["Reportes de Llamadas"]
)
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


@extend_schema(
    summary="UC_RPT_14 — Anomalias cMenu con telefono",
    description="Invoca sp_rpt_cMENU_ERROR. Detecta menus que contienen numero de telefono en el campo cMENU.",
    parameters=[_IVR_QUARTER_PARAM, _IVR_SEGMENTO_PARAM],
    responses={200: OpenApiResponse(description="Registros con anomalia cMENU"),
               503: OpenApiResponse(description="MariaDB no disponible")},
    tags=["Reportes de Llamadas"]
)
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


@extend_schema(
    summary="UC_RPT_15 — KPIs SLA por centro y segmento",
    parameters=[_IVR_QUARTER_PARAM],
    responses={200: OpenApiResponse(description="KPIs de nivel de servicio por centro"),
               503: OpenApiResponse(description="MariaDB no disponible")},
    tags=["Reportes de Llamadas"]
)
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


@extend_schema(
    summary="UC_RPT_16 — Menus IVR",
    description="Vista redirigidos: menus que dispararon transferencia. Vista menu_centro: centro → menus que lo alimentan.",
    parameters=[
        _IVR_QUARTER_PARAM,
        _IVR_SEGMENTO_PARAM,
        OpenApiParameter('vista', str,
            enum=['redirigidos', 'menu_centro'], default='redirigidos'),
    ],
    responses={200: OpenApiResponse(description="Datos de menus IVR segun la vista seleccionada"),
               503: OpenApiResponse(description="MariaDB no disponible")},
    tags=["Reportes de Llamadas"]
)
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
