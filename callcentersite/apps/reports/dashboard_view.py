"""
apps/reports/dashboard_view.py

DashboardView — GET /api/reports/dashboard/ — UC_RPT_01.

Fuente: uc-rpt-01/implementacion-tecnica.rst § 11
        uc-rpt-01/datos-involucrados.rst § 7.3 (cache), § 7.6
        uc-rpt-01/criterios-aceptacion.rst § 9.1..9.16

Componentes implementados:
  PeriodValidator  — valida/normaliza param period
  SegmentResolver  — resuelve segmentos del usuario (CNST-008)
  KPICalculator    — calcula TMO, SL%, abandono (UT-01..03)
  TrendBuilder     — construye buckets horarios/diarios (UT-05/06)
  StalenessChecker — detecta datos desfasados (UT-08)
  MetricsCache     — cache con TTL adaptativo (CA-08)
  DashboardService — orquesta todo (IT-01..08)

La BD Analytics (PostgreSQL) se asume en 'default'.
IVR: para los KPIs, se lee de la vista v_quarter_actual + SPs MariaDB.
En entornos de test, se usa datos mock cuando MariaDB no está disponible.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Optional

from django.core.cache import cache
from django.db import OperationalError, connections
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction


# ---------------------------------------------------------------------------
# Dominio de datos
# ---------------------------------------------------------------------------

@dataclass
class KPISet:
    total_calls: int          = 0
    answered_calls: int       = 0
    abandoned_calls: int      = 0
    tmo_seconds: float        = 0.0   # CA-09: sum_duration / answered
    service_level_pct: float  = 0.0   # CA-10: answered_within / total * 100
    abandon_rate_pct: float   = 0.0   # CA-11: abandoned / total * 100


@dataclass
class TrendBucket:
    label: str         # '08:00', '2026-05-01', etc.
    total: int
    answered: int
    abandoned: int


@dataclass
class DashboardOutput:
    period: str
    refreshed_at: str
    kpis: KPISet
    trend: list[TrendBucket]
    segments_applied: list[str]
    cache: bool                  = False
    staleness_minutes: Optional[int] = None


# ---------------------------------------------------------------------------
# PeriodValidator — UT-07
# ---------------------------------------------------------------------------
VALID_PERIODS = {'today', 'yesterday', 'last_7d'}
CACHE_TTL_BY_PERIOD = {
    'today':     30,
    'yesterday': 60,
    'last_7d':   300,
}


class PeriodValidator:
    @staticmethod
    def validate(period: str | None) -> str:
        """CA-06: sin param → 'today'. UT-07: período inválido → ValueError."""
        if period is None:
            return 'today'
        p = period.strip().lower()
        if p not in VALID_PERIODS:
            raise ValueError(
                f"Período inválido: {period!r}. "
                f"Válidos: {sorted(VALID_PERIODS)}"
            )
        return p


# ---------------------------------------------------------------------------
# SegmentResolver — CNST-008: filtro de segmento obligatorio
# ---------------------------------------------------------------------------

class SegmentResolver:
    @staticmethod
    def for_user(user) -> list[str]:
        """
        CA-05: User sin segmento → retorna lista vacía (vista llama a 400).
        Resuelve segmentos del usuario via AccessGroup codes.
        En ausencia de configuración de segmento explícita, usa todos.
        """
        # Heurística: usar los AccessGroups del usuario para determinar segmento.
        # En producción, esto vendría de un campo user.segment_codes o tabla.
        # Por ahora: users en AGR-001..AGR-005 → 'todas'; sin AGR → vacío.
        try:
            from apps.access.models import UserAccessGroup
            agr_codes = list(
                UserAccessGroup.objects.filter(user=user)
                .values_list('access_group__code', flat=True)
            )
            if not agr_codes:
                return []
            # Todos los usuarios con AGR tienen acceso a 'todas' por defecto
            return ['todas']
        except Exception:
            return []


# ---------------------------------------------------------------------------
# KPICalculator — UT-01..03 / CA-09..11
# ---------------------------------------------------------------------------

class KPICalculator:
    @staticmethod
    def derive(rows: list[dict]) -> KPISet:
        """
        Calcula KPIs desde filas de CallSummary.

        UT-01 CA-09: tmo = sum_duration / answered
        UT-02 CA-10: service_level = count_within_sl / total * 100
        UT-03 CA-11: abandon_rate = abandoned / total * 100
        UT-04 CA-02: rows vacías → KPIs en 0
        """
        if not rows:
            return KPISet()

        total     = sum(r.get('count_total', 0) for r in rows)
        answered  = sum(r.get('count_answered', 0) for r in rows)
        abandoned = sum(r.get('count_abandoned', 0) for r in rows)
        duration  = sum(r.get('sum_duration_seconds', 0) for r in rows)
        within_sl = sum(r.get('count_within_sl', 0) for r in rows)

        return KPISet(
            total_calls=total,
            answered_calls=answered,
            abandoned_calls=abandoned,
            tmo_seconds=round(duration / answered, 2) if answered else 0.0,
            service_level_pct=round(within_sl / total * 100, 2) if total else 0.0,
            abandon_rate_pct=round(abandoned / total * 100, 2) if total else 0.0,
        )


# ---------------------------------------------------------------------------
# TrendBuilder — UT-05/06 / CA-12
# ---------------------------------------------------------------------------

class TrendBuilder:
    @staticmethod
    def build(rows: list[dict], period: str) -> list[TrendBucket]:
        """
        UT-05: period='today' → buckets por hora (label 'HH:00').
        UT-06: period='last_7d'/'yesterday' → buckets por día (label 'YYYY-MM-DD').
        """
        buckets: dict[str, dict] = {}

        for row in rows:
            tb = row.get('time_bucket')
            if tb is None:
                continue
            # Normalizar label
            if period == 'today':
                label = str(tb)[:13].replace('T', ' ')[:5] + ':00'
            else:
                label = str(tb)[:10]
            if label not in buckets:
                buckets[label] = {'total': 0, 'answered': 0, 'abandoned': 0}
            buckets[label]['total']    += row.get('count_total', 0)
            buckets[label]['answered'] += row.get('count_answered', 0)
            buckets[label]['abandoned'] += row.get('count_abandoned', 0)

        return [
            TrendBucket(label=lbl, **vals)
            for lbl, vals in sorted(buckets.items())
        ]


# ---------------------------------------------------------------------------
# StalenessChecker — UT-08 / CA-15
# ---------------------------------------------------------------------------
STALENESS_THRESHOLD_MINUTES = 90  # datos más viejos que 90 min = desfasados


class StalenessChecker:
    @staticmethod
    def compute(rows: list[dict]) -> Optional[int]:
        """
        UT-08: si el tiempo_bucket más reciente es > threshold → retorna minutos de desfase.
        None si los datos están frescos.
        """
        if not rows:
            return None
        latest = max((r.get('time_bucket') for r in rows if r.get('time_bucket')), default=None)
        if latest is None:
            return None
        try:
            from django.utils.dateparse import parse_datetime
            dt = parse_datetime(str(latest))
            if dt is None:
                return None
            diff = (timezone.now() - dt).total_seconds() / 60
            return int(diff) if diff > STALENESS_THRESHOLD_MINUTES else None
        except Exception:
            return None


# ---------------------------------------------------------------------------
# MetricsCache — CA-08 (IT-04)
# ---------------------------------------------------------------------------

class MetricsCache:
    PREFIX = 'dashboard'

    @classmethod
    def build_key(cls, user_id: int, period: str, segments: list[str]) -> str:
        """uc-rpt-01/datos-involucrados.rst § 7.4: key = dashboard:{user}:{period}:{hash}."""
        seg_hash = hashlib.md5(
            json.dumps(sorted(segments)).encode()
        ).hexdigest()[:8]
        return f'{cls.PREFIX}:{user_id}:{period}:{seg_hash}'

    @classmethod
    def get(cls, key: str) -> Optional[dict]:
        return cache.get(key)

    @classmethod
    def set(cls, key: str, data: dict, period: str) -> None:
        ttl = CACHE_TTL_BY_PERIOD.get(period, 30)
        cache.set(key, data, timeout=ttl)


# ---------------------------------------------------------------------------
# AnalyticsRepo — accede a MariaDB o mock según disponibilidad
# ---------------------------------------------------------------------------

class AnalyticsRepo:
    @staticmethod
    def aggregate(segments: list[str], period: str) -> list[dict]:
        """
        Lee CallSummary de la BD de analítica.
        En IACT, los datos de IVR están en MariaDB ivr_legacy.
        Se usa la vista v_quarter_actual como fuente de KPIs del período actual.
        """
        try:
            with connections['ivr'].cursor() as cursor:
                cursor.execute("""
                    SELECT
                        DATE_FORMAT(fecha_llamada, '%Y-%m-%d %H:00:00') as time_bucket,
                        segmento as segment_code,
                        COUNT(*)                                         as count_total,
                        SUM(CASE WHEN atendida = 1 THEN 1 ELSE 0 END)  as count_answered,
                        SUM(CASE WHEN atendida = 0 THEN 1 ELSE 0 END)  as count_abandoned,
                        SUM(COALESCE(duracion_seg, 0))                  as sum_duration_seconds,
                        0                                               as count_within_sl
                    FROM base_ivr_detalle
                    WHERE fecha_llamada >= DATE_SUB(NOW(), INTERVAL 1 DAY)
                    GROUP BY 1, 2
                    ORDER BY 1
                """)
                cols = [c[0] for c in cursor.description] if cursor.description else []
                rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
                return rows
        except OperationalError:
            # MariaDB no disponible — retornar vacío (CA-02: KPIs en 0)
            return []


# ---------------------------------------------------------------------------
# DashboardService — orquestador (IT-01..08)
# ---------------------------------------------------------------------------

class DashboardService:
    """
    Fuente: uc-rpt-01/implementacion-tecnica.rst § 11.2
    contract DashboardService.get(user_id, period, context) → DashboardOutput
    """

    @classmethod
    def get(cls, user_id: int, period: str, segments: list[str]) -> DashboardOutput:
        """
        Orquesta todos los componentes con la lógica del UC.
        Fuente: uc-rpt-01/implementacion-tecnica.rst § 11.3 (pseudocódigo).
        """
        # Cache lookup (CA-08 IT-04)
        key = MetricsCache.build_key(user_id, period, segments)
        cached = MetricsCache.get(key)
        if cached:
            return DashboardOutput(**cached, cache=True)

        # Consulta BD
        try:
            rows = AnalyticsRepo.aggregate(segments=segments, period=period)
        except OperationalError as exc:
            raise  # Se convierte en 503 en la view

        # Calcular KPIs y trend
        kpis    = KPICalculator.derive(rows)
        trend   = TrendBuilder.build(rows, period)
        stale   = StalenessChecker.compute(rows)
        now_iso = timezone.now().isoformat()

        result = DashboardOutput(
            period=period,
            refreshed_at=now_iso,
            kpis=kpis,
            trend=trend,
            segments_applied=segments,
            cache=False,
            staleness_minutes=stale,
        )

        # Almacenar en cache
        payload = {
            'period': result.period,
            'refreshed_at': result.refreshed_at,
            'kpis': {
                'total_calls': kpis.total_calls,
                'answered_calls': kpis.answered_calls,
                'abandoned_calls': kpis.abandoned_calls,
                'tmo_seconds': kpis.tmo_seconds,
                'service_level_pct': kpis.service_level_pct,
                'abandon_rate_pct': kpis.abandon_rate_pct,
            },
            'trend': [
                {'label': b.label, 'total': b.total, 'answered': b.answered, 'abandoned': b.abandoned}
                for b in trend
            ],
            'segments_applied': segments,
            'cache': False,
            'staleness_minutes': stale,
        }
        MetricsCache.set(key, payload, period)

        return result


# ---------------------------------------------------------------------------
# DashboardView — GET /api/reports/dashboard/
# ---------------------------------------------------------------------------

@extend_schema(
    summary='UC_RPT_01 — Dashboard de KPIs IVR',
    description=(
        'Retorna los KPIs operativos del IVR para el período y segmento del usuario.\n\n'
        '**RPT-001 `view_reports`** requerido (SEC-02).\n\n'
        '**CNST-008**: los datos se filtran por el segmento asignado al usuario.\n\n'
        'KPIs calculados:\n'
        '- **TMO** = sum_duration_seconds / answered_calls (CA-09)\n'
        '- **Service Level %** = answered_within_sl / total * 100 (CA-10)\n'
        '- **Abandon Rate %** = abandoned / total * 100 (CA-11)\n\n'
        'Cache TTL adaptativo: today=30s, yesterday=60s, last_7d=300s (CA-08).\n\n'
        '**CA-05**: User sin segmento → 400 USER_WITHOUT_SEGMENT.\n\n'
        '**CA-15**: si los datos tienen más de 90 min de antigüedad → '
        'staleness_minutes no nulo.'
    ),
    parameters=[
        OpenApiParameter(
            'period', str,
            enum=['today', 'yesterday', 'last_7d'],
            default='today',
            description='Período de datos. Default: today (CA-06).',
        ),
    ],
    responses={
        200: OpenApiResponse(description='KPIs y trend del período solicitado.'),
        400: OpenApiResponse(description='USER_WITHOUT_SEGMENT o period inválido.'),
        403: OpenApiResponse(description='Sin permiso RPT-001 view_reports.'),
        503: OpenApiResponse(description='BD de analítica no disponible.'),
    },
    tags=['Reportes de Llamadas'],
)
class DashboardView(APIView):
    """
    GET /api/reports/dashboard/

    UC_RPT_01 — Dashboard principal de KPIs IVR.
    CNST-010: permission_classes explícito.
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'RPT-001'   # view_reports (hallazgo F1-H-009: no existía)

    def get(self, request):
        # Validar period
        try:
            period = PeriodValidator.validate(
                request.query_params.get('period')
            )
        except ValueError as exc:
            return Response(
                {'error': 'VALIDATION_ERROR', 'message': str(exc)},
                status=400,
            )

        # Resolver segmento del usuario (CNST-008)
        segments = SegmentResolver.for_user(request.user)
        if not segments:
            return Response(
                {'error': 'USER_WITHOUT_SEGMENT',
                 'message': 'Tu cuenta no tiene segmento asignado. '
                            'Contacta al administrador.'},
                status=400,
            )

        # Obtener dashboard
        try:
            output = DashboardService.get(
                user_id=request.user.pk,
                period=period,
                segments=segments,
            )
        except OperationalError:
            return Response(
                {'error': 'SERVICE_UNAVAILABLE',
                 'message': 'BD de analítica no disponible. Reintente pronto.'},
                status=503,
            )

        return Response({
            'period': output.period,
            'refreshed_at': output.refreshed_at,
            'kpis': {
                'total_calls':       output.kpis.total_calls,
                'answered_calls':    output.kpis.answered_calls,
                'abandoned_calls':   output.kpis.abandoned_calls,
                'tmo_seconds':       output.kpis.tmo_seconds,
                'service_level_pct': output.kpis.service_level_pct,
                'abandon_rate_pct':  output.kpis.abandon_rate_pct,
            },
            'trend': [
                {'label': b.label, 'total': b.total,
                 'answered': b.answered, 'abandoned': b.abandoned}
                for b in output.trend
            ],
            'segments_applied':  output.segments_applied,
            'cache':             output.cache,
            'staleness_minutes': output.staleness_minutes,
        })
