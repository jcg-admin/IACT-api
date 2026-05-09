"""
Views de reportes IVR — B-01.

Expone los SPs de MariaDB como endpoints DRF.
Cada view valida quarter y segment, invoca el servicio y retorna JSON.
"""
from django.db import OperationalError
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.access.permissions.function_permissions import HasFunction
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
    'segment', str,
    enum=['todas', 'nacional_A', 'nacional_B', 'puebla'],
    default='todas',
    description="Segmento de negocio. Default: todas",
)


def _validate(quarter: str | None = None,
              segment: str | None = None) -> list[str]:
    """
    Validates quarter and segment parameters.
    Quarter validated against base_ivr_detalle (no cache, CNST-010).
    """
    errors = []
    if quarter:
        available = svc.get_available_quarters()
        if available and quarter not in available:
            errors.append(
                f'Invalid quarter: {quarter}. '
                f'Available: {sorted(available)}'
            )
    if segment and segment not in svc.VALID_SEGMENTS:
        errors.append(
            f'Invalid segment: {segment}. '
            f'Valid: {sorted(svc.VALID_SEGMENTS)}'
        )
    return errors


def _ivr_response(fn, *args, extra=None):
    """Ejecuta fn(*args), maneja OperationalError y retorna Response."""
    try:
        data = fn(*args)
    except OperationalError as e:
        return Response(
            {'error': 'Could not connect to the IVR database.', 'detail': str(e)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    payload = {'total_rows': len(data), 'data': data}
    if extra:
        payload.update(extra)
    return Response(payload)


@extend_schema(
    summary="UC_RPT_17 — Clientes unicos por segment",
    description="Invoca sp_rpt_clientes(p_quarter) en MariaDB. Retorna 3 filas: nacional_A, nacional_B, puebla.",
    parameters=[_IVR_QUARTER_PARAM],
    responses={200: OpenApiResponse(description="Lista de clientes por segment"),
               400: OpenApiResponse(description="Quarter invalido"),
               503: OpenApiResponse(description="MariaDB no disponible")},
    tags=["Reportes de Llamadas"]
)
class ClientesReportView(APIView):
    """
    UC_RPT_17 — Clientes unicos por segment.
    GET /api/reports/ivr/clients/?quarter=Q01_25
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'reports.view_ivr'

    def get(self, request):
        quarter = request.query_params.get('quarter', 'Q01_25')
        errors = _validate(quarter=quarter)
        if errors:
            return Response({'errors': errors}, status=400)
        return _ivr_response(svc.get_clients, quarter,
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
    GET /api/reports/ivr/transfer-centers/?quarter=Q01_25&segment=todas
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'reports.view_ivr'

    def get(self, request):
        quarter  = request.query_params.get('quarter',  'Q01_25')
        segment = request.query_params.get('segment', 'todas')
        errors = _validate(quarter=quarter, segment=segment)
        if errors:
            return Response({'errors': errors}, status=400)
        return _ivr_response(svc.get_transfer_centers, quarter, segment,
                              extra={'quarter': quarter, 'segment': segment})


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
    GET /api/reports/ivr/abandoned/?quarter=Q01_25&segment=todas
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'reports.view_ivr'

    def get(self, request):
        quarter  = request.query_params.get('quarter',  'Q01_25')
        segment = request.query_params.get('segment', 'todas')
        errors = _validate(quarter=quarter, segment=segment)
        if errors:
            return Response({'errors': errors}, status=400)
        return _ivr_response(svc.get_abandoned_calls, quarter, segment,
                              extra={'quarter': quarter, 'segment': segment})


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
    GET /api/reports/ivr/menu-errors/?quarter=Q01_25&segment=todas
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'reports.view_ivr'

    def get(self, request):
        quarter  = request.query_params.get('quarter',  'Q01_25')
        segment = request.query_params.get('segment', 'todas')
        errors = _validate(quarter=quarter, segment=segment)
        if errors:
            return Response({'errors': errors}, status=400)
        return _ivr_response(svc.get_cmenu_errors, quarter, segment,
                              extra={'quarter': quarter, 'segment': segment})


@extend_schema(
    summary="UC_RPT_15 — KPIs SLA por centro y segment",
    parameters=[_IVR_QUARTER_PARAM],
    responses={200: OpenApiResponse(description="KPIs de nivel de servicio por centro"),
               503: OpenApiResponse(description="MariaDB no disponible")},
    tags=["Reportes de Llamadas"]
)
class CentrosXSegmentoView(APIView):
    """
    UC_RPT_15 — KPIs SLA por centro y segment.
    GET /api/reports/ivr/centers-by-segment/?quarter=Q01_25
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'reports.view_ivr'

    def get(self, request):
        quarter = request.query_params.get('quarter', 'Q01_25')
        errors = _validate(quarter=quarter)
        if errors:
            return Response({'errors': errors}, status=400)
        return _ivr_response(svc.get_centers_by_segment, quarter,
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
    GET /api/reports/ivr/menus/?quarter=Q01_25&vista=redirigidos&segment=todas
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'reports.view_ivr'

    def get(self, request):
        quarter  = request.query_params.get('quarter',  'Q01_25')
        vista    = request.query_params.get('vista',    'redirigidos')
        segment = request.query_params.get('segment', 'todas')

        errors = _validate(quarter=quarter, segment=segment)
        if vista not in ('redirigidos', 'menu_centro'):
            errors.append('vista invalida: usar redirigidos o menu_centro')
        if errors:
            return Response({'errors': errors}, status=400)

        fn = svc.get_redirected_menus if vista == 'redirigidos' else svc.get_center_menus
        return _ivr_response(fn, quarter, segment,
                              extra={'quarter': quarter, 'vista': vista, 'segment': segment})


class MenuRedirigidosView(APIView):
    """
    GET /api/reports/ivr/menu-redirigidos/
    Distribución de opciones elegidas por el llamante en cada menú IVR.
    Grain: menu × opcion. Fuente: sp_rpt_menu_redirigidos.
    """
    permission_classes = [IsAuthenticated, HasIVRReportPermission]

    @extend_schema(
        parameters=[
            OpenApiParameter('quarter', str, description='Q0N_YY'),
            OpenApiParameter('segment', str, description='todas|nacional_A|nacional_B|puebla'),
        ],
        responses={200: OpenApiTypes.OBJECT, 503: OpenApiResponse(description="MariaDB no disponible")},
    )
    def get(self, request):
        quarter = request.query_params.get('quarter', 'Q01_25')
        segment = request.query_params.get('segment', 'todas')
        errors = _validate(quarter=quarter, segment=segment)
        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        return _ivr_response(svc.get_redirected_menus, quarter, segment)


class MenuCentroView(APIView):
    """
    GET /api/reports/ivr/menu-centro/
    Distribución de centros de transferencia por menú IVR.
    Grain: menu × centro_transferencia. Fuente: sp_rpt_menu_centro.
    """
    permission_classes = [IsAuthenticated, HasIVRReportPermission]

    @extend_schema(
        parameters=[
            OpenApiParameter('quarter', str, description='Q0N_YY'),
            OpenApiParameter('segment', str, description='todas|nacional_A|nacional_B|puebla'),
        ],
        responses={200: OpenApiTypes.OBJECT, 503: OpenApiResponse(description="MariaDB no disponible")},
    )
    def get(self, request):
        quarter = request.query_params.get('quarter', 'Q01_25')
        segment = request.query_params.get('segment', 'todas')
        errors = _validate(quarter=quarter, segment=segment)
        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        return _ivr_response(svc.get_center_menus, quarter, segment)
