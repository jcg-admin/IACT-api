"""
Servicio de gestión de sesiones.

CLEAN_CODE v3.0.1: Nombre descriptivo.
SOLID SRP: Solo gestión de sesiones.

CNST-031: Auditoría de sesiones.
CNST-010: Sessions en PostgreSQL.
"""

from typing import List, Optional
from django.utils import timezone
from django.contrib.sessions.models import Session as DjangoSession

from apps.core.services.base_service import BaseService  # [SUCCESS] BaseService
from apps.authentication.models import SessionLog


class SessionService(BaseService):  # [SUCCESS] Hereda de BaseService
    """
    Servicio de gestión de sesiones.
    
    SOLID SRP: Solo sesiones.
    
    Responsabilidades:
    - Listar sesiones activas de usuario
    - Obtener historial de sesiones
    - Invalidar sesión específica
    - Invalidar todas las sesiones de un usuario
    
    CNST-031: Auditoría de sesiones.
    CNST-010: Sessions en PostgreSQL.
    """
    
    def __init__(self):
        """Initialize service."""
        super().__init__()  # [SUCCESS] Llamar super
        self.log_info("SessionService initialized")
    
    def get_active_sessions(self, user) -> List[SessionLog]:
        """
        Obtiene sesiones activas del usuario.
        
        Args:
            user: User object
        
        Returns:
            List[SessionLog]: Sesiones activas
        """
        # [SUCCESS] Usar active() para excluir soft deleted
        sessions = SessionLog.objects.active().filter(
            user=user,
            is_active=True
        ).order_by('-created_at')  # [SUCCESS] login_at = created_at
        
        count = sessions.count()
        self.log_info(f"Retrieved {count} active sessions for user '{user.username}'")
        
        return list(sessions)
    
    def get_session_history(
        self,
        user,
        limit: int = 10
    ) -> List[SessionLog]:
        """
        Obtiene historial de sesiones del usuario.
        
        Args:
            user: User object
            limit: Número máximo de registros
        
        Returns:
            List[SessionLog]: Historial de sesiones
        """
        # [SUCCESS] Usar active() (excluye soft deleted)
        sessions = SessionLog.objects.active().filter(
            user=user
        ).order_by('-created_at')[:limit]  # [SUCCESS] login_at = created_at
        
        count = sessions.count()
        self.log_info(f"Retrieved {count} session history records for user '{user.username}'")
        
        return list(sessions)
    
    def invalidate_session(
        self,
        session_key: str,
        user=None
    ) -> bool:
        """
        Invalida una sesión específica.
        
        SOLID SRP: Solo invalida sesión.
        
        Args:
            session_key: Django session key
            user: User object (opcional, para verificar ownership)
        
        Returns:
            bool: True si invalidada exitosamente
        """
        # Actualizar SessionLog
        filters = {'session_key': session_key, 'is_active': True}
        
        if user:
            filters['user'] = user
        
        # [SUCCESS] Usar active() para excluir soft deleted
        session_log = SessionLog.objects.active().filter(**filters).first()
        
        if session_log:
            session_log.logout_at = timezone.now()
            session_log.is_active = False
            session_log.save()
            
            self.log_info(f"SessionLog invalidated for session_key '{session_key}'")
        
        # Invalidar sesión de Django
        try:
            django_session = DjangoSession.objects.get(session_key=session_key)
            django_session.delete()
            
            self.log_info(f"Django session deleted for session_key '{session_key}'")
            
            return True
        
        except DjangoSession.DoesNotExist:
            self.log_warning(f"Django session not found for session_key '{session_key}'")
            return False
    
    def invalidate_all_user_sessions(
        self,
        user,
        except_current: Optional[str] = None
    ) -> int:
        """
        Invalida todas las sesiones de un usuario.
        
        Útil para:
        - Cambio de contraseña
        - Logout de todos los dispositivos
        - Seguridad (sesión comprometida)
        
        Args:
            user: User object
            except_current: Session key a excluir (sesión actual)
        
        Returns:
            int: Número de sesiones invalidadas
        """
        # Obtener sesiones activas
        # [SUCCESS] Usar active()
        sessions = SessionLog.objects.active().filter(
            user=user,
            is_active=True
        )
        
        # Excluir sesión actual si se especifica
        if except_current:
            sessions = sessions.exclude(session_key=except_current)
        
        count = 0
        
        for session_log in sessions:
            if self.invalidate_session(session_log.session_key, user):
                count += 1
        
        self.log_info(
            f"Invalidated {count} sessions for user '{user.username}' "
            f"(except_current: {except_current})"
        )
        
        return count
    
    def get_session_details(
        self,
        session_key: str,
        user=None
    ) -> Optional[SessionLog]:
        """
        Obtiene detalles de una sesión.
        
        Args:
            session_key: Django session key
            user: User object (opcional, para verificar ownership)
        
        Returns:
            SessionLog: Detalles de la sesión o None
        """
        filters = {'session_key': session_key}
        
        if user:
            filters['user'] = user
        
        # [SUCCESS] Usar active()
        session_log = SessionLog.objects.active().filter(**filters).first()
        
        if session_log:
            self.log_info(f"Retrieved session details for session_key '{session_key}'")
        else:
            self.log_warning(f"Session not found for session_key '{session_key}'")
        
        return session_log
