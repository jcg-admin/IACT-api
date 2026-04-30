"""
Utils package — IACT.
Re-exporta solo lo que el codigo del proyecto realmente usa.
"""

from apps.utils.models import SoftDeleteMixin, SoftDeleteManager, SoftDeleteQuerySet
from apps.utils.request import get_client_ip, get_user_agent, should_exclude_path

__all__ = [
    'SoftDeleteMixin',
    'SoftDeleteManager',
    'SoftDeleteQuerySet',
    'get_client_ip',
    'get_user_agent',
    'should_exclude_path',
]
