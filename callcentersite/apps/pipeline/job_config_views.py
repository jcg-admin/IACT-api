"""
apps/pipeline/job_config_views.py

UC_PIP_05 — Gestionar configuracion del job ETL.

GET  /api/pipeline/job-config/           PIP-001  lista de jobs
GET  /api/pipeline/job-config/{name}/    PIP-001  detalle
PATCH /api/pipeline/job-config/{name}/  PIP-005  habilitar/deshabilitar

BR-ETL-01: solo is_enabled y notas son modificables via API.
BR-ETL-02: job_name debe existir en job_config.
BR-ETL-03: actualizado_en lo gestiona MariaDB ON UPDATE.
"""
from django.db import connections, OperationalError
from drf_spectacular.utils import OpenApiResponse, extend_schema, OpenApiParameter
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction
from apps.audit.services import AuditLogService

_TAG = 'Pipeline — Configuracion'

_COLUMNS = [
    'job_name', 'is_enabled', 'timeout_seconds',
    'ventana_inicio', 'ventana_fin', 'min_intervalo_h',
    'notas', 'actualizado_en',
]


# ─── helpers ──────────────────────────────────────────────────────────────────

def _row_to_dict(row):
    d = dict(zip(_COLUMNS, row))
    # Convertir time/datetime a string para serialización JSON
    for k in ('ventana_inicio', 'ventana_fin', 'actualizado_en'):
        if d.get(k) is not None:
            d[k] = str(d[k])
    d['is_enabled'] = bool(d['is_enabled'])
    return d


def _fetch_jobs(job_name=None):
    """Leer job_config desde MariaDB. Lanza OperationalError si no hay conexión."""
    sql = 'SELECT ' + ', '.join(_COLUMNS) + ' FROM job_config'
    params = []
    if job_name:
        sql += ' WHERE job_name = %s'
        params.append(job_name)
    sql += ' ORDER BY job_name'
    with connections['ivr'].cursor() as cur:
        cur.execute(sql, params)
        return [_row_to_dict(r) for r in cur.fetchall()]


# ─── serializers ──────────────────────────────────────────────────────────────

class JobConfigPatchSerializer(serializers.Serializer):
    """Campos modificables via API (BR-ETL-01)."""
    is_enabled = serializers.BooleanField(required=False)
    notas      = serializers.CharField(
        required=False, allow_blank=True, max_length=1000)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                'Se requiere al menos is_enabled o notas.')
        return attrs


# ─── vistas ───────────────────────────────────────────────────────────────────

class JobConfigListView(APIView):
    """GET /api/pipeline/job-config/ — UC_PIP_05 lista."""
    serializer_class   = JobConfigPatchSerializer
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'PIP-001'

    @extend_schema(
        operation_id='pipeline_job_config_list',
        summary='UC_PIP_05 — Listar configuracion de jobs ETL',
        tags=[_TAG],
        responses={
            200: OpenApiResponse(description='Lista de configuraciones de jobs'),
            503: OpenApiResponse(description='MariaDB no disponible'),
        },
    )
    def get(self, request):
        try:
            jobs = _fetch_jobs()
        except OperationalError:
            return Response(
                {'error': 'IVR_DB_UNAVAILABLE'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        habilitados   = sum(1 for j in jobs if j['is_enabled'])
        deshabilitados = len(jobs) - habilitados
        return Response({
            'resumen': {
                'total':          len(jobs),
                'habilitados':    habilitados,
                'deshabilitados': deshabilitados,
            },
            'jobs': jobs,
        })


class JobConfigDetailView(APIView):
    """GET|PATCH /api/pipeline/job-config/{job_name}/ — UC_PIP_05 detalle."""
    serializer_class   = JobConfigPatchSerializer
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'PIP-001'

    @extend_schema(
        operation_id='pipeline_job_config_detail',
        summary='UC_PIP_05 — Detalle de configuracion de job ETL',
        tags=[_TAG],
        parameters=[OpenApiParameter('job_name', str, description='Nombre del job')],
        responses={
            200: OpenApiResponse(description='Configuracion del job'),
            404: OpenApiResponse(description='Job no encontrado'),
            503: OpenApiResponse(description='MariaDB no disponible'),
        },
    )
    def get(self, request, job_name):
        try:
            jobs = _fetch_jobs(job_name=job_name)
        except OperationalError:
            return Response(
                {'error': 'IVR_DB_UNAVAILABLE'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        if not jobs:
            return Response({'error': 'JOB_NOT_FOUND'}, status=status.HTTP_404_NOT_FOUND)
        return Response(jobs[0])

    @extend_schema(
        operation_id='pipeline_job_config_update',
        summary='UC_PIP_05 — Habilitar/deshabilitar job ETL (BR-ETL-01)',
        tags=[_TAG],
        request=JobConfigPatchSerializer,
        responses={
            200: OpenApiResponse(description='Configuracion actualizada'),
            400: OpenApiResponse(description='Campo no modificable via API o sin campos'),
            403: OpenApiResponse(description='Sin PIP-005 manage_pipeline_config'),
            404: OpenApiResponse(description='Job no encontrado'),
        },
    )
    def patch(self, request, job_name):
        # BR-ETL-01: solo is_enabled y notas
        forbidden = set(request.data.keys()) - {'is_enabled', 'notas'}
        if forbidden:
            return Response(
                {'error': 'CAMPO_NO_MODIFICABLE',
                 'detail': f'Campos no modificables via API: {sorted(forbidden)}. '
                           'Requieren despliegue de BD.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ser = JobConfigPatchSerializer(data=request.data)
        if not ser.is_valid():
            return Response(
                {'error': 'VALIDATION_ERROR', 'fields': ser.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verificar permiso de escritura (PIP-005) — HasFunction.has_permission
        # revisa required_function del view. Para el PATCH necesitamos PIP-005
        # que es diferente al PIP-001 del GET. Verificamos inline.
        if not request.user.is_superuser and                 not request.user.has_function_by_code('PIP-005'):
            return Response(
                {'error': 'PERMISSION_DENIED', 'required': 'PIP-005'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Construir SET clause dinámica
        updates = ser.validated_data
        set_parts = []
        params    = []
        if 'is_enabled' in updates:
            set_parts.append('is_enabled = %s')
            params.append(1 if updates['is_enabled'] else 0)
        if 'notas' in updates:
            set_parts.append('notas = %s')
            params.append(updates['notas'])
        # actualizado_en tiene ON UPDATE en MariaDB — no se toca
        params.append(job_name)

        try:
            with connections['ivr'].cursor() as cur:
                cur.execute(
                    f'UPDATE job_config SET {", ".join(set_parts)}, '
                    f'actualizado_en = NOW() WHERE job_name = %s',
                    params,
                )
                if cur.rowcount == 0:
                    return Response({'error': 'JOB_NOT_FOUND'}, status=status.HTTP_404_NOT_FOUND)
                cur.execute(
                    'SELECT ' + ', '.join(_COLUMNS) + ' FROM job_config WHERE job_name = %s',
                    [job_name],
                )
                row = cur.fetchone()
        except OperationalError:
            return Response(
                {'error': 'IVR_DB_UNAVAILABLE'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        updated = _row_to_dict(row)

        if 'is_enabled' in updates:
            AuditLogService.emit(
                event_type='JOB_CONFIG_UPDATED',
                actor_user_id=request.user.pk,
                payload={
                    'job_name':    job_name,
                    'is_enabled':  updates['is_enabled'],
                    'changed_by':  request.user.username,
                },
            )

        return Response(updated)
