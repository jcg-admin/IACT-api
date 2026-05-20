"""
apps/access/exceptional_permission_views.py

UC_ACC_08/PERM_03 — Conceder permiso excepcional.
UC_PERM_03        — Preview sin persistir.
UC_PERM_04        — Revocar permiso excepcional.

POST   /api/users/{user_id}/exceptional-permissions/
GET    /api/users/{user_id}/exceptional-permissions/preview/
DELETE /api/users/{user_id}/exceptional-permissions/{permission_id}/
"""
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction
from apps.access.exceptional_permission_service import (
    ExceptionalPermissionService, GrantPreviewService,
)
from apps.access.models import ExceptionalPermission
from apps.access.serializers.exceptional_permission_serializers import ExceptionalPermissionSerializer


_TAG = 'Permisos Excepcionales'


# ---------------------------------------------------------------------------
# Serializers de request
# ---------------------------------------------------------------------------

class ExceptionalGrantSerializer(serializers.Serializer):
    function_ids      = serializers.ListField(child=serializers.IntegerField(), min_length=1)
    expires_at        = serializers.DateTimeField()
    justification     = serializers.CharField(min_length=20)
    ticket_reference  = serializers.CharField(required=False, allow_blank=True, default='')


class ExceptionalRevokeSerializer(serializers.Serializer):
    revoke_reason = serializers.CharField(min_length=20)


# ---------------------------------------------------------------------------
# UC_ACC_08 / UC_PERM_03 — Grant + Preview
# ---------------------------------------------------------------------------

@extend_schema_view(
    post=extend_schema(
        operation_id='access_exceptional_grant',
        summary='UC_ACC_08 — Conceder permiso excepcional temporal',
        description=(
            'CA-07: mailbox HARD — rollback si falla.\n'
            'CA-09: idempotencia parcial — skipped[] si ya ACTIVE.\n'
            'CA-05: SELF_GRANT_FORBIDDEN.\n'
            'CNST-001: cero email externo.'
        ),
        responses={
            201: OpenApiResponse(description='Permisos otorgados — {granted, skipped}'),
            400: OpenApiResponse(description='SELF_GRANT_FORBIDDEN | VALIDATION_ERROR'),
            403: OpenApiResponse(description='Sin ACC-008 grant_exceptional_permission'),
            409: OpenApiResponse(description='SEPARATION_RULE_VIOLATION (SoD)'),
            500: OpenApiResponse(description='MAILBOX_FAILED — rollback total'),
        },
        tags=[_TAG],
    ),
    get=extend_schema(
        operation_id='access_exceptional_permissions_for_user',
        summary='UC_ACC_08 — Listar permisos excepcionales del usuario',
        tags=[_TAG],
    ),
)
class ExceptionalGrantView(APIView):
    serializer_class = ExceptionalPermissionSerializer
    """POST/GET /api/users/{user_id}/exceptional-permissions/ — UC_ACC_08"""

    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ACC-008'

    def _get_target(self, user_id):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def get(self, request, user_id):
        target = self._get_target(user_id)
        if not target:
            return Response({'error': 'USER_NOT_FOUND'}, status=404)
        perms = ExceptionalPermission.objects.filter(user=target).order_by('-created_at')
        return Response({
            'count': perms.count(),
            'results': [
                {
                    'id': p.pk, 'function_code': p.function.code,
                    'status': p.status, 'expires_at': (
                        p.expires_at.isoformat() if p.expires_at else None),
                    'justification': p.justification,
                }
                for p in perms
            ],
        })

    def post(self, request, user_id):
        target = self._get_target(user_id)
        if not target:
            return Response({'error': 'USER_NOT_FOUND'}, status=404)

        ser = ExceptionalGrantSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        data = ser.validated_data
        try:
            ip_admin = (
                request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
                or request.META.get('REMOTE_ADDR', '')
            ) or None
            result = ExceptionalPermissionService.grant(
                target_user=target,
                function_ids=data['function_ids'],
                expires_at=data['expires_at'],
                justification=data['justification'],
                ticket_reference=data.get('ticket_reference', ''),
                invoker=request.user,
                ip_address=ip_admin,
            )
        except ValueError as e:
            err = str(e)
            code = err.split(':')[0] if ':' in err else 'VALIDATION_ERROR'
            http_status = 409 if 'SOD' in code or 'SEPARATION' in code else 400
            return Response({'error': code, 'detail': err}, status=http_status)
        except Exception:
            return Response({'error': 'MAILBOX_FAILED'}, status=500)

        return Response(result, status=201)


@extend_schema_view(
    get=extend_schema(
    operation_id='access_exceptional_preview',
    summary='UC_PERM_03 — Preview de permiso excepcional (sin persistir)',
    description='CA-PERM-01: ZERO ExceptionalPermission, ZERO AuditEvent.',
    responses={200: OpenApiResponse(description='Preview con SoD impact + duration')},
    tags=[_TAG],
)
)
class ExceptionalPreviewView(APIView):
    """GET /api/users/{user_id}/exceptional-permissions/preview/ — UC_PERM_03"""

    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ACC-008'

    def get(self, request, user_id):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            target = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'USER_NOT_FOUND'}, status=404)

        fn_ids_raw  = request.query_params.get('function_ids', '')
        expires_raw = request.query_params.get('expires_at', '')

        try:
            function_ids = [int(i) for i in fn_ids_raw.split(',') if i.strip()]
        except ValueError:
            return Response({'error': 'function_ids inválidos'}, status=400)

        try:
            from django.utils.dateparse import parse_datetime
            expires_at = parse_datetime(expires_raw)
            if not expires_at:
                raise ValueError('expires_at inválido')
        except (ValueError, TypeError):
            return Response({'error': 'expires_at inválido'}, status=400)

        try:
            preview = GrantPreviewService.preview(target, function_ids, expires_at)
        except ValueError as e:
            return Response({'error': 'VALIDATION_ERROR', 'detail': str(e)}, status=400)

        return Response(preview)


# ---------------------------------------------------------------------------
# UC_PERM_04 — Revocar
# ---------------------------------------------------------------------------

@extend_schema_view(
    delete=extend_schema(
    operation_id='access_exceptional_revoke',
    summary='UC_PERM_04 — Revocar permiso excepcional',
    description=(
        'CA-01: state=REVOKED + revoked_by_admin_id.\n'
        'CA-03: idempotencia — ya REVOKED → 200 REVOKE_NOOP.\n'
        'CA-07: anti-self (P-11).\n'
        'CA-08: mailbox HARD — rollback si falla.'
    ),
    responses={
        200: OpenApiResponse(description='Revocación exitosa o NOOP'),
        400: OpenApiResponse(description='INVALID_STATE | SELF_REVOKE_FORBIDDEN | VALIDATION_ERROR'),
        403: OpenApiResponse(description='Sin ACC-009 revoke_exceptional_permission'),
        500: OpenApiResponse(description='MAILBOX_FAILED — rollback total'),
    },
    tags=[_TAG],
)
)
class ExceptionalRevokeView(APIView):
    """DELETE /api/users/{user_id}/exceptional-permissions/{permission_id}/ — UC_PERM_04"""

    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ACC-009'

    def delete(self, request, user_id, permission_id):
        ser = ExceptionalRevokeSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        try:
            perm = ExceptionalPermission.objects.select_related('function', 'user').get(
                pk=permission_id, user_id=user_id,
            )
        except ExceptionalPermission.DoesNotExist:
            return Response({'error': 'PERMISSION_NOT_FOUND'}, status=404)

        # CA-09: URL mismatch
        if perm.user_id != int(user_id):
            return Response({'error': 'URL_MISMATCH'}, status=400)

        try:
            ip_admin = (
                request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
                or request.META.get('REMOTE_ADDR', '')
            ) or None
            result = ExceptionalPermissionService.revoke(
                permission=perm,
                invoker=request.user,
                revoke_reason=ser.validated_data['revoke_reason'],
                ip_address=ip_admin,
            )
        except ValueError as e:
            err = str(e)
            code = err.split(':')[0] if ':' in err else 'VALIDATION_ERROR'
            return Response({'error': code, 'detail': err}, status=400)
        except Exception:
            return Response({'error': 'MAILBOX_FAILED'}, status=500)

        return Response(result)
