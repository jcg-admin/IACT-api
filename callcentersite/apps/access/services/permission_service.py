"""
apps/access/services/permission_service.py

UC_PERM_07 — Verificar Permiso.

Componentes:
  GrantInfo         — datos de un permiso excepcional GRANT activo
  CheckResult       — resultado de una verificación de permiso
  PrecedenceEvaluator — evalúa la precedencia de fuentes (función pura)
  PermissionCache   — cache de permisos con TTL (DatabaseCache)
  PermissionService — punto de entrada para verificación

Reglas de precedencia (plan § FASE 1.2 / uc-perm-07/criterios-aceptacion.rst):
  P1: ExceptionalPermission REVOKE activo → DENIED (gana siempre)
  P2: ExceptionalPermission GRANT activo → ALLOWED
  P3: AccessGroup ACTIVE con la función → ALLOWED
  P4: ningún match → DENIED_NO_GRANT

Fuente: uc-perm-07/, ADR-BACK-006 § 2.3, CNST-010
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from django.core.cache import cache
from django.utils import timezone


# ---------------------------------------------------------------------------
# Tipos de datos
# ---------------------------------------------------------------------------

@dataclass
class GrantInfo:
    """Datos de un ExceptionalPermission GRANT activo."""
    valid_until: Optional[datetime]  # None = sin expiración


@dataclass
class CheckResult:
    """Resultado de PermissionService.check()."""
    allowed: bool
    origin: str          # GRANTED_BY_AGR | GRANTED_EXCEPTIONAL | REVOKED_EXCEPTIONAL | DENIED_NO_GRANT
    via_agr_codes: list[str] = field(default_factory=list)
    valid_until: Optional[datetime] = None
    cache: bool = False  # True si vino del cache


# ---------------------------------------------------------------------------
# PrecedenceEvaluator — función pura (UT-01..UT-09 del plan)
# ---------------------------------------------------------------------------

class PrecedenceEvaluator:
    """
    Evalúa la precedencia de fuentes de permiso.

    Función pura — sin efectos secundarios, sin BD, sin I/O.
    Facilita testing unitario sin fixtures de BD.

    Reglas (uc-perm-07/criterios-aceptacion.rst § 9.1..9.9):
      P1: revoke_active → REVOKED_EXCEPTIONAL (gana sobre todo)
      P2: grant_active  → GRANTED_EXCEPTIONAL
      P3: agr_codes     → GRANTED_BY_AGR (lista completa)
      P4: ninguno       → DENIED_NO_GRANT
    """

    @staticmethod
    def evaluate(
        revoke_active: bool,
        grant_active: Optional[GrantInfo],
        agr_codes: list[str],
    ) -> CheckResult:
        """
        Evalúa las fuentes de permiso y retorna el resultado.

        Args:
            revoke_active: True si hay ExceptionalPermission REVOKE activo.
            grant_active: GrantInfo si hay GRANT activo, None si no.
            agr_codes: Lista de códigos de AGR que otorgan la función.

        Returns:
            CheckResult con allowed, origin y metadata.
        """
        # P1: Revocación excepcional gana sobre todo (UT-01, UT-09)
        if revoke_active:
            return CheckResult(
                allowed=False,
                origin='REVOKED_EXCEPTIONAL',
            )

        # P2: Concesión excepcional (UT-02)
        if grant_active is not None:
            return CheckResult(
                allowed=True,
                origin='GRANTED_EXCEPTIONAL',
                valid_until=grant_active.valid_until,
            )

        # P3: AccessGroup otorga (UT-03)
        if agr_codes:
            return CheckResult(
                allowed=True,
                origin='GRANTED_BY_AGR',
                via_agr_codes=list(agr_codes),
            )

        # P4: Sin ninguna fuente (UT-04)
        return CheckResult(
            allowed=False,
            origin='DENIED_NO_GRANT',
        )


# ---------------------------------------------------------------------------
# PermissionCache — DatabaseCache por defecto, TTL 60s (UT-05..UT-10)
# ---------------------------------------------------------------------------

CACHE_DEFAULT_TTL = 60   # segundos — configurable
CACHE_KEY_PREFIX = 'perm'


class PermissionCache:
    """
    Cache de permisos sobre Django's cache framework (DatabaseCache).

    CNST-010: NO Redis. La caché es DatabaseCache configurada en settings.
    TTL: min(default_ttl, remaining_validity) — UT-05, UT-06.

    Key format: perm:{user_id}:{function_code} — UT-07.
    """

    @staticmethod
    def build_key(user_id: int, function_code: str) -> str:
        """UT-07: clave canónica perm:{user_id}:{function_code}."""
        return f'{CACHE_KEY_PREFIX}:{user_id}:{function_code}'

    @staticmethod
    def build_prefix(user_id: int) -> str:
        """Prefijo para invalidar todas las claves de un usuario."""
        return f'{CACHE_KEY_PREFIX}:{user_id}:'

    @staticmethod
    def compute_ttl(
        default: int,
        valid_until: Optional[datetime],
    ) -> int:
        """
        UT-05: TTL = min(default, remaining_seconds_until_valid_until).
        UT-06: Si valid_until=None → TTL = default.
        """
        if valid_until is None:
            return default
        remaining = int((valid_until - timezone.now()).total_seconds())
        return min(default, max(0, remaining))

    @classmethod
    def get(cls, user_id: int, function_code: str) -> Optional[CheckResult]:
        """Recupera del cache. Retorna None en cache miss."""
        key = cls.build_key(user_id, function_code)
        data = cache.get(key)
        if data is None:
            return None
        result = CheckResult(**data)
        result.cache = True
        return result

    @classmethod
    def set(
        cls,
        user_id: int,
        function_code: str,
        result: CheckResult,
        ttl: Optional[int] = None,
    ) -> None:
        """Almacena resultado en cache con TTL calculado."""
        key = cls.build_key(user_id, function_code)
        effective_ttl = ttl if ttl is not None else CACHE_DEFAULT_TTL

        # Truncar TTL si el resultado tiene valid_until
        if result.valid_until:
            effective_ttl = cls.compute_ttl(effective_ttl, result.valid_until)

        if effective_ttl <= 0:
            return  # No cachear si ya expiró

        # Serializar dataclass a dict (sin cache flag)
        data = {
            'allowed': result.allowed,
            'origin': result.origin,
            'via_agr_codes': result.via_agr_codes,
            'valid_until': result.valid_until,
            'cache': False,
        }
        cache.set(key, data, timeout=effective_ttl)

    @classmethod
    def invalidate(cls, user_id: int) -> None:
        """
        UT-10: Invalida todas las claves perm:{user_id}:* del cache.

        Django's cache framework no soporta wildcard delete nativamente.
        Usamos un set de claves conocidas por user_id almacenado en un
        índice auxiliar.
        """
        index_key = f'{CACHE_KEY_PREFIX}:index:{user_id}'
        known_codes = cache.get(index_key) or []
        keys_to_delete = [cls.build_key(user_id, code) for code in known_codes]
        if keys_to_delete:
            cache.delete_many(keys_to_delete)
        cache.delete(index_key)

    @classmethod
    def _register_key(cls, user_id: int, function_code: str) -> None:
        """Registra function_code en el índice de claves del user."""
        index_key = f'{CACHE_KEY_PREFIX}:index:{user_id}'
        known = cache.get(index_key) or []
        if function_code not in known:
            known.append(function_code)
            cache.set(index_key, known, timeout=CACHE_DEFAULT_TTL * 2)


# ---------------------------------------------------------------------------
# PermissionService — punto de entrada (IT-01..IT-06)
# ---------------------------------------------------------------------------

class PermissionService:
    """
    Verifica si un usuario tiene una función RBAC activa.

    Flujo (IT-01..IT-06):
      1. Cache lookup (PermissionCache.get).
      2. Cache hit → retornar con cache=True.
      3. Cache miss → consultar BD.
      4. Evaluar precedencia con PrecedenceEvaluator.evaluate().
      5. Almacenar en cache.
      6. Retornar resultado.

    ADR-BACK-006: la verificación definitiva siempre pasa por la BD
    en cache miss. El ORM Django puede implementar la verificación;
    las funciones SQL son para el middleware de alto tráfico.
    """

    @classmethod
    def check(cls, user_id: int, function_code: str) -> CheckResult:
        """
        Verifica si user_id tiene function_code.

        CA-01..CA-10 del UC_PERM_07.

        Raises:
            User.DoesNotExist: CA-13 — usuario no existe.
            ValueError: CA-12 — function_code no existe en catálogo.
        """
        # Validar existencia de función (CA-12)
        from apps.access.models import Function
        if not Function.objects.filter(code=function_code, is_active=True).exists():
            raise ValueError(f"Función no encontrada: {function_code!r}")

        # Validar existencia de usuario (CA-13)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not User.objects.filter(pk=user_id, state='ACTIVE').exists():
            raise LookupError(f"Usuario activo no encontrado: {user_id}")

        # 1. Cache lookup
        cached = PermissionCache.get(user_id, function_code)
        if cached is not None:
            return cached  # CA-09: cache hit

        # 2. Consultar BD
        result = cls._query_db(user_id, function_code)

        # 3. Almacenar en cache
        PermissionCache.set(user_id, function_code, result)
        PermissionCache._register_key(user_id, function_code)

        return result

    @classmethod
    def check_bulk(
        cls,
        user_id: int,
        function_codes: list[str],
    ) -> dict[str, CheckResult]:
        """
        CA-11: verifica múltiples funciones con una sola query para cache misses.

        Returns: dict {function_code: CheckResult}
        """
        results: dict[str, CheckResult] = {}
        misses: list[str] = []

        # Separar hits y misses
        for code in function_codes:
            cached = PermissionCache.get(user_id, code)
            if cached is not None:
                results[code] = cached
            else:
                misses.append(code)

        # Resolver misses en bulk
        for code in misses:
            try:
                result = cls._query_db(user_id, code)
                PermissionCache.set(user_id, code, result)
                PermissionCache._register_key(user_id, code)
                results[code] = result
            except (ValueError, LookupError) as exc:
                results[code] = CheckResult(
                    allowed=False, origin='DENIED_NO_GRANT',
                )

        return results

    @staticmethod
    def _query_db(user_id: int, function_code: str) -> CheckResult:
        """
        Consulta BD para resolver permiso (cache miss).
        Una sola ronda a BD per CA-11.
        """
        from apps.access.models import ExceptionalPermission, UserAccessGroup
        from django.utils import timezone
        now = timezone.now()

        # ExceptionalPermission REVOKE activo?
        revoke_active = ExceptionalPermission.objects.filter(
            user_id=user_id,
            function__code=function_code,
            status='revoked',
            valid_from__lte=now,
        ).filter(
            models_q_not_expired(now)
        ).exists()

        # ExceptionalPermission GRANT activo?
        grant_qs = ExceptionalPermission.objects.filter(
            user_id=user_id,
            function__code=function_code,
            status='approved',
            valid_from__lte=now,
        ).filter(models_q_not_expired(now)).values('valid_until').first()

        grant_info: Optional[GrantInfo] = None
        if grant_qs is not None:
            grant_info = GrantInfo(valid_until=grant_qs['valid_until'])

        # AccessGroups que otorgan la función (CA-08: multi-AGR)
        agr_codes = list(
            UserAccessGroup.objects.filter(
                user_id=user_id,
                access_group__is_active=True,
                access_group__functions__code=function_code,
                access_group__functions__is_active=True,
            ).values_list('access_group__code', flat=True).distinct()
        )

        return PrecedenceEvaluator.evaluate(
            revoke_active=revoke_active,
            grant_active=grant_info,
            agr_codes=agr_codes,
        )


def models_q_not_expired(now=None):
    """Q helper para filtrar ExceptionalPermission no expirados."""
    from django.db.models import Q
    if now is None:
        now = timezone.now()
    return Q(valid_until__isnull=True) | Q(valid_until__gt=now)
