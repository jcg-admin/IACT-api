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
from apps.audit.models import AuditLog
from apps.authentication.models import SessionLog
from .user_test_data import UserTestData


# ============================================================================
# AUDITLOG FACTORIES
# ============================================================================

class AuditLogTestData(DjangoModelFactory):
    """
    Factory para AuditLog (registro inmutable de acciones).
    
    IMPORTANTE: AuditLog es IMMUTABLE (no se puede modificar ni eliminar).
    
    Uso básico:
        log = AuditLogTestData(
            action='CREATE',
            user=user,
            model_name='Report'
        )
    
    Batch:
        logs = AuditLogTestData.create_batch(10)
    """
    
    class Meta:
        model = AuditLog
    
    action = factory.Iterator(['CREATE', 'UPDATE', 'DELETE', 'VIEW', 'ACCESS_DENIED'])
    user = factory.SubFactory(UserTestData)
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


class CreateAuditLogTestData(AuditLogTestData):
    """Factory para logs de acción CREATE."""
    action = 'CREATE'
    changes = factory.LazyFunction(lambda: {'created': True})


class UpdateAuditLogTestData(AuditLogTestData):
    """Factory para logs de acción UPDATE."""
    action = 'UPDATE'
    changes = factory.LazyFunction(lambda: {
        'field': 'status',
        'old': 'PENDING',
        'new': 'COMPLETED'
    })


class DeleteAuditLogTestData(AuditLogTestData):
    """Factory para logs de acción DELETE."""
    action = 'DELETE'
    changes = factory.LazyFunction(lambda: {'deleted': True})


class AccessDeniedAuditLogTestData(AuditLogTestData):
    """
    Factory para logs de acceso denegado.
    
    Uso:
        log = AccessDeniedAuditLogTestData(
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

class SessionLogTestData(DjangoModelFactory):
    """
    Factory para SessionLog (authentication.models.SessionLog).

    Campos reales del modelo: session_key, ip_address, user_agent,
    is_active, logout_at.

    El modelo SessionLog no tiene action, timestamp ni details.
    """

    class Meta:
        model = SessionLog

    user       = factory.SubFactory(UserTestData)
    session_key = factory.Sequence(lambda n: f'session_key_{n}')
    ip_address  = factory.Faker('ipv4')
    user_agent  = factory.Faker('user_agent')
    is_active   = True
    created_by  = factory.SelfAttribute('user')


class LoginSessionLogTestData(SessionLogTestData):
    """Factory para logs de LOGIN (sesión activa)."""
    is_active = True

class LogoutSessionLogTestData(SessionLogTestData):
    """Factory para logs de LOGOUT (sesión cerrada)."""
    is_active = False

class ExpiredSessionLogTestData(SessionLogTestData):
    """Factory para logs de sesión expirada."""
    is_active = False

class UserSessionTestData(UserTestData):
    """
    Factory que crea Usuario con sesión activa (LOGIN log).
    
    Uso:
        user = UserSessionTestData()
        # Usuario con login log automático
    """
    
    @factory.post_generation
    def session_log(self, create, extracted, **kwargs):
        if not create:
            return
        
        LoginSessionLogTestData(user=self)


class AuditTrailTestData:
    """
    Factory que crea un trail completo de auditoría.
    
    Uso:
        trail = AuditTrailTestData.create_trail(
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
        create_log = CreateAuditLogTestData(
            user=user,
            model_name=model_name,
            object_id=object_id
        )
        
        update_log = UpdateAuditLogTestData(
            user=user,
            model_name=model_name,
            object_id=object_id
        )
        
        delete_log = DeleteAuditLogTestData(
            user=user,
            model_name=model_name,
            object_id=object_id
        )
        
        return [create_log, update_log, delete_log]


class SessionHistoryTestData:
    """
    Factory que crea historial de sesiones de un usuario.
    
    Uso:
        history = SessionHistoryTestData.create_history(user, days=7)
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
            login_log = LoginSessionLogTestData(
                user=user,
                timestamp=date.replace(hour=9, minute=0)
            )
            logs.append(login_log)
            
            # Logout por la tarde
            logout_log = LogoutSessionLogTestData(
                user=user,
                timestamp=date.replace(hour=18, minute=0)
            )
            logs.append(logout_log)
        
        return logs


# ============================================================================
# TOTAL FACTORIES: 13
# 
# AuditLog Factories (5):
#   - AuditLogTestData (base)
#   - CreateAuditLogTestData
#   - UpdateAuditLogTestData
#   - DeleteAuditLogTestData
#   - AccessDeniedAuditLogTestData
# 
# SessionLog Factories (4):
#   - SessionLogTestData (base)
#   - LoginSessionLogTestData
#   - LogoutSessionLogTestData
#   - ExpiredSessionLogTestData
# 
# Helper Factories (2):
#   - UserSessionTestData
#   - AuditTrailTestData (static methods)
#   - SessionHistoryTestData (static methods)
# 
# CNST-031: Auditoría completa [SUCCESS]
# CLEAN_CODE v3.0.1: Nombres auto-documentados [SUCCESS]
# ============================================================================
