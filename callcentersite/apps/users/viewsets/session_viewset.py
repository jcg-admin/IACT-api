"""
apps/users/viewsets/session_viewset.py

Stub de compatibilidad — SessionHistory fue eliminado.

El historial de sesiones se gestiona via:
  GET /api/sessions/               → authentication.SessionViewSet (SessionLog)
  POST /api/sessions/{id}/invalidate/ → authentication.SessionViewSet
"""

class SessionHistoryViewSet:
    """
    Stub de compatibilidad.
    Las sesiones se gestionan en apps.authentication.viewsets.SessionViewSet.
    """
    pass
