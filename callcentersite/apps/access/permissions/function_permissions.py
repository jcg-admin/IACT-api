"""
apps/access/permissions/function_permissions.py

DRF Permission class para RBAC v5.4.0.

Verifica que el usuario tiene la función RBAC requerida usando
el código canónico (AUTH-001, RPT-001, etc.) del catálogo v5.4.0.

ADR-BACK-006: la verificación final siempre pasa por Function.code.
CNST-010: permission_classes explícito en toda view DRF.
CNST-033: códigos en inglés, formato MOD-NNN.

Hallazgo F0-H-007: la versión anterior buscaba por permission_django
('reports.view') que es el campo de namespace legacy. En v5.4.0
el campo canónico es code ('RPT-001'). Todos los required_function
en las views se actualizan a códigos v5.4.0.
"""
from rest_framework.permissions import BasePermission


class HasFunction(BasePermission):
    """
    Verifica que el usuario tiene la función RBAC requerida.

    La view debe definir:
        required_function = 'RPT-001'   # Código canónico v5.4.0 MOD-NNN

    Proceso de verificación (ADR-BACK-006):
        1. Usuario autenticado (IsAuthenticated lo garantiza antes)
        2. Superuser → bypass
        3. Obtiene required_function de la view
        4. Si no hay required_function → permite (sin restricción RBAC)
        5. Verifica con user.has_function_by_code(code)
           que internamente usa get_user_functions() o user_has_function()

    Uso:
        class ReportListView(APIView):
            permission_classes = [IsAuthenticated, HasFunction]
            required_function = 'RPT-001'  # view_reports (CNST-010)

    CNST-010: permission_classes explícito — nunca dejar vacío.
    """

    message = 'No tiene permiso para realizar esta acción.'

    def has_permission(self, request, view) -> bool:
        # 1. Usuario autenticado
        if not request.user or not request.user.is_authenticated:
            return False

        # 2. Superuser bypass
        if request.user.is_superuser:
            return True

        # 3. Código de función requerido
        required_code = getattr(view, 'required_function', None)

        # 4. Sin restricción si no se define
        if not required_code:
            return True

        # 5. Verificar por código canónico v5.4.0
        return request.user.has_function_by_code(required_code)
