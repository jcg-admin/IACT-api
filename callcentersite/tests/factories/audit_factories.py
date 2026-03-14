"""
Factories para apps/audit/.

Factory boy para generación de datos test de auditoría.
Basado en análisis ANALISIS_APP_AUDIT_v3_0_0.md (3 partes).

CNST-031: Auditoría completa de acciones.
CLEAN_CODE v3.0.1: Nombres auto-documentados.
"""

import factory
from factory.django import DjangoModelFactory
from factory import fuzzy
from apps.audit.models import AuditLog, SessionLog
from .user_factory import UserFactory


# ============================================================================
# AUDITLOG FACTORIES
# ============================================================================

class AuditLogFactory(DjangoModelFactory):
    """
    Factory para AuditLog (registro inmutable de acciones).
    
    IMPORTANTE: AuditLog es IMMUTABLE (no se puede modificar ni eliminar).
    
    Uso básico:
        log = AuditLogFactory(
            action='CREATE',
            user=user,
            model_name='Report'
        )
    
    Batch:
        logs = AuditLogFactory.create_batch(10)
    """
    
    class Meta:
        model = AuditLog
    
    action = factory.Iterator(['CREATE', 'UPDATE', 'DELETE', 'VIEW', 'ACCESS_DENIED'])
    user = factory.SubFactory(UserFactory)
    model_name = factory.Iterator([
        'User', 'Module', 'Function', 'Role',
        'Report', 'Dashboard', 'Alert', 'ETLJob'
    ])
    object_id = factory.Sequence(lambda n: str(n))
    object_repr = factory.Faker('sentence', nb_words=4)
    changes = factory.LazyFunction(lambda: {
        'field': 'status',
        'old': 'PENDING',
        'new': 'SUCCESS'
    })
    ip_address = factory.Faker('ipv4')
    user_agent = factory.Faker('user_agent')
    timestamp = factory.Faker('date_time_this_month')


class CreateAuditLogFactory(AuditLogFactory):
    """Factory para logs de acción CREATE."""
    action = 'CREATE'
    changes = factory.LazyFunction(lambda: {'created': True})


class UpdateAuditLogFactory(AuditLogFactory):
    """Factory para logs de acción UPDATE."""
    action = 'UPDATE'
    changes = factory.LazyFunction(lambda: {
        'field': 'status',
        'old': 'PENDING',
        'new': 'COMPLETED'
    })


class DeleteAuditLogFactory(AuditLogFactory):
    """Factory para logs de acción DELETE."""
    action = 'DELETE'
    changes = factory.LazyFunction(lambda: {'deleted': True})


class AccessDeniedAuditLogFactory(AuditLogFactory):
    """
    Factory para logs de acceso denegado.
    
    Uso:
        log = AccessDeniedAuditLogFactory(
            user=user,
            model_name='Report',
            object_id='123',
            changes={'reason': 'No tiene permiso reports.view'}
        )
    """
    action = 'ACCESS_DENIED'
    changes = factory.LazyFunction(lambda: {
        'reason': 'Permission denied',
        'required_permission': 'reports.view'
    })


# ============================================================================
# SESSIONLOG FACTORIES
# ============================================================================

class SessionLogFactory(DjangoModelFactory):
    """
    Factory para SessionLog (registro de sesiones).
    
    CNST-010: Sessions en DB (NO Redis).
    
    Uso básico:
        log = SessionLogFactory(
            user=user,
            action='LOGIN'
        )
    
    Login/Logout:
        login_log = SessionLogFactory(action='LOGIN')
        logout_log = SessionLogFactory(action='LOGOUT', user=login_log.user)
    """
    
    class Meta:
        model = SessionLog
    
    user = factory.SubFactory(UserFactory)
    session_key = factory.Faker('sha256')
    ip_address = factory.Faker('ipv4')
    user_agent = factory.Faker('user_agent')
    action = factory.Iterator(['LOGIN', 'LOGOUT', 'SESSION_EXPIRED'])
    timestamp = factory.Faker('date_time_this_month')
    details = factory.LazyFunction(lambda: {
        'browser': 'Chrome',
        'os': 'Windows 10'
    })


class LoginSessionLogFactory(SessionLogFactory):
    """Factory para logs de LOGIN."""
    action = 'LOGIN'
    details = factory.LazyFunction(lambda: {
        'method': 'username_password',
        'success': True
    })


class LogoutSessionLogFactory(SessionLogFactory):
    """Factory para logs de LOGOUT."""
    action = 'LOGOUT'
    details = factory.LazyFunction(lambda: {
        'method': 'manual',
        'session_duration_seconds': 3600
    })


class ExpiredSessionLogFactory(SessionLogFactory):
    """Factory para logs de sesión expirada."""
    action = 'SESSION_EXPIRED'
    details = factory.LazyFunction(lambda: {
        'reason': 'inactivity',
        'idle_time_seconds': 1800
    })


# ============================================================================
# HELPER FACTORIES (Complex scenarios)
# ============================================================================

class UserSessionFactory(UserFactory):
    """
    Factory que crea Usuario con sesión activa (LOGIN log).
    
    Uso:
        user = UserSessionFactory()
        # Usuario con login log automático
    """
    
    @factory.post_generation
    def session_log(self, create, extracted, **kwargs):
        if not create:
            return
        
        LoginSessionLogFactory(user=self)


class AuditTrailFactory:
    """
    Factory que crea un trail completo de auditoría.
    
    Uso:
        trail = AuditTrailFactory.create_trail(
            user=user,
            model_name='Report',
            object_id='123'
        )
        # Retorna: [CREATE log, UPDATE log, DELETE log]
    """
    
    @staticmethod
    def create_trail(user, model_name, object_id):
        """
        Crea trail completo: CREATE -> UPDATE -> DELETE.
        
        Args:
            user: Usuario que ejecuta acciones
            model_name: Nombre del modelo
            object_id: ID del objeto
        
        Returns:
            list: [create_log, update_log, delete_log]
        """
        create_log = CreateAuditLogFactory(
            user=user,
            model_name=model_name,
            object_id=object_id
        )
        
        update_log = UpdateAuditLogFactory(
            user=user,
            model_name=model_name,
            object_id=object_id
        )
        
        delete_log = DeleteAuditLogFactory(
            user=user,
            model_name=model_name,
            object_id=object_id
        )
        
        return [create_log, update_log, delete_log]


class SessionHistoryFactory:
    """
    Factory que crea historial de sesiones de un usuario.
    
    Uso:
        history = SessionHistoryFactory.create_history(user, days=7)
        # Retorna lista de login/logout logs de últimos 7 días
    """
    
    @staticmethod
    def create_history(user, days=7):
        """
        Crea historial de sesiones.
        
        Args:
            user: Usuario
            days: Número de días de historial
        
        Returns:
            list: Lista de SessionLog (LOGIN/LOGOUT alternados)
        """
        from datetime import datetime, timedelta
        
        logs = []
        base_date = datetime.now()
        
        for i in range(days):
            date = base_date - timedelta(days=i)
            
            # Login por la mañana
            login_log = LoginSessionLogFactory(
                user=user,
                timestamp=date.replace(hour=9, minute=0)
            )
            logs.append(login_log)
            
            # Logout por la tarde
            logout_log = LogoutSessionLogFactory(
                user=user,
                timestamp=date.replace(hour=18, minute=0)
            )
            logs.append(logout_log)
        
        return logs


# ============================================================================
# TOTAL FACTORIES: 13
# 
# AuditLog Factories (5):
#   - AuditLogFactory (base)
#   - CreateAuditLogFactory
#   - UpdateAuditLogFactory
#   - DeleteAuditLogFactory
#   - AccessDeniedAuditLogFactory
# 
# SessionLog Factories (4):
#   - SessionLogFactory (base)
#   - LoginSessionLogFactory
#   - LogoutSessionLogFactory
#   - ExpiredSessionLogFactory
# 
# Helper Factories (2):
#   - UserSessionFactory
#   - AuditTrailFactory (static methods)
#   - SessionHistoryFactory (static methods)
# 
# CNST-031: Auditoría completa [SUCCESS]
# CLEAN_CODE v3.0.1: Nombres auto-documentados [SUCCESS]
# ============================================================================
