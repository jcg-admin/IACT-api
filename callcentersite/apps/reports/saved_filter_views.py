"""
apps/reports/saved_filter_views.py

UC_RPT_09 — Configurar Filtros. POST/GET /api/me/filters/
UC_RPT_10 — Guardar Vista.      POST/GET /api/me/views/
"""
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import AuditLogService
from apps.reports.models import SavedFilter, SavedView
from apps.reports.saved_filter_service import SavedFilterValidator
from apps.reports.saved_view_service import SavedViewValidator
from apps.reports.serializers.report_serializers import ReportSerializer
from apps.reports.serializers.scheduled_report_serializers import SavedViewSerializer



_TAG = 'Reportes'


# ---------------------------------------------------------------------------
# UC_RPT_09 — SavedFilter
# ---------------------------------------------------------------------------

class SavedFilterCreateSerializer(serializers.Serializer):
    name        = serializers.CharField(max_length=100)
    report_type = serializers.CharField(max_length=50, required=False, default='')
    applies_to  = serializers.ListField(child=serializers.CharField(), default=list)
    filters     = serializers.DictField(default=dict)
    is_default  = serializers.BooleanField(default=False)


class SavedFilterPatchSerializer(serializers.Serializer):
    name        = serializers.CharField(required=False, max_length=100)
    filters     = serializers.DictField(required=False)
    is_default  = serializers.BooleanField(required=False)


def _filter_to_dict(sf: SavedFilter) -> dict:
    return {
        'id': sf.pk, 'name': sf.name, 'report_type': sf.report_type,
        'applies_to': sf.applies_to, 'filters': sf.filters,
        'is_default': sf.is_default, 'is_valid': sf.is_valid,
        'actor': sf.actor_id, 'created_at': sf.created_at.isoformat(),
    }


@extend_schema_view(
    get=extend_schema(
        operation_id='saved_filter_list',
        summary='UC_RPT_09 — Listar filtros guardados del usuario',
        tags=[_TAG],
    ),
    post=extend_schema(
        operation_id='saved_filter_create',
        summary='UC_RPT_09 — Crear filtro guardado',
        responses={
            201: OpenApiResponse(description='Filtro creado'),
            400: OpenApiResponse(description='NAME_DUPLICATE | VALIDATION_ERROR'),
            429: OpenApiResponse(description='FILTER_LIMIT_EXCEEDED — > 50 filtros'),
        },
        tags=[_TAG],
    ),
)
class SavedFilterListView(APIView):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = SavedFilter.objects.filter(actor=request.user).order_by('-created_at')
        return Response({'count': qs.count(), 'results': [_filter_to_dict(f) for f in qs]})

    def post(self, request):
        ser = SavedFilterCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        data = ser.validated_data
        try:
            SavedFilterValidator.validate(data)
            SavedFilterValidator.check_duplicate(request.user.pk, data['name'])
        except ValueError as e:
            err_msg = str(e)
            code = 'NAME_DUPLICATE' if 'duplicado' in err_msg else 'VALIDATION_ERROR'
            return Response({'error': code, 'detail': err_msg}, status=400)

        active = SavedFilter.objects.filter(actor=request.user).count()
        if active >= SavedFilter.MAX_FILTERS_PER_USER:
            return Response({'error': 'FILTER_LIMIT_EXCEEDED'}, status=429)

        # CA-09: is_default único por report_type
        if data.get('is_default') and data.get('report_type'):
            SavedFilter.objects.filter(
                actor=request.user, report_type=data['report_type'], is_default=True,
            ).update(is_default=False)

        sf = SavedFilter.objects.create(
            actor=request.user,
            name=data['name'], report_type=data['report_type'],
            applies_to=data['applies_to'], filters=data['filters'],
            is_default=data['is_default'],
        )
        AuditLogService.emit(
            event_type='SAVED_FILTER_CREATED',
            actor_user_id=request.user.pk,
            payload={'filter_id': sf.pk, 'name': sf.name},
        )
        return Response(_filter_to_dict(sf), status=201)


@extend_schema_view(
    get=extend_schema(
        operation_id='saved_filter_detail',
        summary='UC_RPT_09 — Detalle de filtro guardado',
        tags=[_TAG],
    ),
    patch=extend_schema(
        operation_id='saved_filter_update',
        summary='UC_RPT_09 — Actualizar filtro guardado',
        tags=[_TAG],
    ),
    delete=extend_schema(
        operation_id='saved_filter_delete',
        summary='UC_RPT_09 — Eliminar filtro guardado',
        tags=[_TAG],
    ),
)
class SavedFilterDetailView(APIView):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def _get(self, pk, user):
        try:
            return SavedFilter.objects.get(pk=pk, actor=user)
        except SavedFilter.DoesNotExist:
            return None

    def get(self, request, pk):
        sf = self._get(pk, request.user)
        if not sf:
            return Response({'error': 'NOT_FOUND'}, status=404)
        return Response(_filter_to_dict(sf))

    def patch(self, request, pk):
        sf = self._get(pk, request.user)
        if not sf:
            return Response({'error': 'NOT_FOUND'}, status=404)
        ser = SavedFilterPatchSerializer(data=request.data, partial=True)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)
        for field, value in ser.validated_data.items():
            setattr(sf, field, value)
        sf.save()
        AuditLogService.emit(
            event_type='SAVED_FILTER_UPDATED',
            actor_user_id=request.user.pk,
            payload={'filter_id': sf.pk},
        )
        return Response(_filter_to_dict(sf))

    def delete(self, request, pk):
        sf = self._get(pk, request.user)
        if not sf:
            return Response({'error': 'NOT_FOUND'}, status=404)
        sf_id = sf.pk
        sf.delete()
        AuditLogService.emit(
            event_type='SAVED_FILTER_DELETED',
            actor_user_id=request.user.pk,
            payload={'filter_id': sf_id},
        )
        return Response({'deleted': sf_id})


# ---------------------------------------------------------------------------
# UC_RPT_10 — SavedView
# ---------------------------------------------------------------------------

class SavedViewCreateSerializer(serializers.Serializer):
    name         = serializers.CharField(max_length=100)
    report_type  = serializers.CharField(max_length=50, required=False, default='call_summary')
    columns      = serializers.ListField(child=serializers.CharField(), default=list)
    filters      = serializers.DictField(default=dict)
    chart_config = serializers.DictField(default=dict)
    is_default   = serializers.BooleanField(default=False)


def _view_to_dict(sv: SavedView) -> dict:
    return {
        'id': sv.pk, 'name': sv.name, 'report_type': sv.report_type,
        'columns': sv.columns, 'filters': sv.filters,
        'chart_config': sv.chart_config,
        'is_default': sv.is_default, 'is_available': sv.is_available,
        'actor': sv.actor_id, 'created_at': sv.created_at.isoformat(),
    }


@extend_schema_view(
    get=extend_schema(
        operation_id='saved_view_list',
        summary='UC_RPT_10 — Listar vistas guardadas del usuario',
        tags=[_TAG],
    ),
    post=extend_schema(
        operation_id='saved_view_create',
        summary='UC_RPT_10 — Crear vista guardada',
        responses={
            201: OpenApiResponse(description='Vista creada'),
            429: OpenApiResponse(description='VIEW_LIMIT_EXCEEDED — > 30 vistas'),
        },
        tags=[_TAG],
    ),
)
class SavedViewListView(APIView):
    serializer_class = SavedViewSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = SavedView.objects.filter(actor=request.user).order_by('-created_at')
        return Response({'count': qs.count(), 'results': [_view_to_dict(v) for v in qs]})

    def post(self, request):
        ser = SavedViewCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        data = ser.validated_data
        try:
            SavedViewValidator.validate(data)
        except ValueError as e:
            return Response({'error': 'VALIDATION_ERROR', 'detail': str(e)}, status=400)

        active = SavedView.objects.filter(actor=request.user).count()
        if active >= SavedView.MAX_VIEWS_PER_USER:
            return Response({'error': 'VIEW_LIMIT_EXCEEDED'}, status=429)

        if data.get('is_default') and data.get('report_type'):
            SavedView.objects.filter(
                actor=request.user, report_type=data['report_type'], is_default=True,
            ).update(is_default=False)

        sv = SavedView.objects.create(
            actor=request.user,
            name=data['name'], report_type=data['report_type'],
            columns=data['columns'], filters=data['filters'],
            chart_config=data['chart_config'], is_default=data['is_default'],
        )
        AuditLogService.emit(
            event_type='SAVED_VIEW_CREATED',
            actor_user_id=request.user.pk,
            payload={'view_id': sv.pk, 'name': sv.name},
        )
        return Response(_view_to_dict(sv), status=201)


@extend_schema_view(
    get=extend_schema(operation_id='saved_view_detail', summary='UC_RPT_10 — Detalle de vista', tags=[_TAG]),
    patch=extend_schema(operation_id='saved_view_update', summary='UC_RPT_10 — Actualizar vista', tags=[_TAG]),
    delete=extend_schema(operation_id='saved_view_delete', summary='UC_RPT_10 — Eliminar vista', tags=[_TAG]),
)
class SavedViewDetailView(APIView):
    serializer_class = SavedViewSerializer
    permission_classes = [IsAuthenticated]

    def _get(self, pk, user):
        try:
            return SavedView.objects.get(pk=pk, actor=user)
        except SavedView.DoesNotExist:
            return None

    def get(self, request, pk):
        sv = self._get(pk, request.user)
        if not sv:
            return Response({'error': 'NOT_FOUND'}, status=404)
        return Response(_view_to_dict(sv))

    def patch(self, request, pk):
        sv = self._get(pk, request.user)
        if not sv:
            return Response({'error': 'NOT_FOUND'}, status=404)
        for field in ('name', 'columns', 'filters', 'chart_config', 'is_default'):
            if field in request.data:
                setattr(sv, field, request.data[field])
        sv.save()
        AuditLogService.emit(
            event_type='SAVED_VIEW_UPDATED',
            actor_user_id=request.user.pk,
            payload={'view_id': sv.pk},
        )
        return Response(_view_to_dict(sv))

    def delete(self, request, pk):
        sv = self._get(pk, request.user)
        if not sv:
            return Response({'error': 'NOT_FOUND'}, status=404)
        sv_id = sv.pk
        sv.delete()
        AuditLogService.emit(
            event_type='SAVED_VIEW_DELETED',
            actor_user_id=request.user.pk,
            payload={'view_id': sv_id},
        )
        return Response({'deleted': sv_id})


@extend_schema_view(
    post=extend_schema(operation_id='saved_view_clone',
    summary='UC_RPT_10 CA-07 — Clonar vista guardada',
    tags=[_TAG],)
)
class SavedViewCloneView(APIView):
    serializer_class = SavedViewSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            original = SavedView.objects.get(pk=pk, actor=request.user)
        except SavedView.DoesNotExist:
            return Response({'error': 'NOT_FOUND'}, status=404)

        clone_name = f'{original.name} (copia)'
        sv = SavedView.objects.create(
            actor=request.user,
            name=clone_name, report_type=original.report_type,
            columns=original.columns, filters=original.filters,
            chart_config=original.chart_config, is_default=False,
        )
        AuditLogService.emit(
            event_type='SAVED_VIEW_CLONED',
            actor_user_id=request.user.pk,
            payload={'original_id': pk, 'clone_id': sv.pk},
        )
        return Response(_view_to_dict(sv), status=201)
