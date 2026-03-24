"""
Database Router - IACT Call Center System.

CNST-003: Enforce READ-ONLY access to IVR Legacy database.

Routing rules:
- Models de apps.core (CallRecord, etc) -> 'default' (PostgreSQL)
- Models de apps.ivr (legacy) -> 'ivr' (MariaDB READ-ONLY)

Compliance: CNST-003
"""


class DatabaseRouter:
    """
    Database router para dual-database setup.
    
    - default (PostgreSQL): Analytics DB (READ + WRITE)
    - ivr (MariaDB): IVR Legacy DB (READ-ONLY)
    """
    
    # Apps que usan ivr (READ-ONLY)
    ivr_apps = {'ivr'}  # Se agrega en Sprint 1
    
    # Apps que usan default (READ + WRITE)
    default_apps = {'core', 'authentication', 'users', 'reports'}
    
    def db_for_read(self, model, **hints):
        """
        Determinar database para READ.
        
        Args:
            model: Model class
        
        Returns:
            str: 'default' o 'ivr'
        """
        app_label = model._meta.app_label
        
        if app_label in self.ivr_apps:
            return 'ivr'
        
        if app_label in self.default_apps:
            return 'default'
        
        return None
    
    def db_for_write(self, model, **hints):
        """
        Determinar database para WRITE.
        
        CNST-003: ivr_legacy es READ-ONLY
        
        Args:
            model: Model class
        
        Returns:
            str: 'default' o None (prohibido write a ivr_legacy)
        """
        app_label = model._meta.app_label
        
        # CNST-003: NO permitir writes a ivr_legacy
        if app_label in self.ivr_apps:
            return None  # Bloquear writes
        
        if app_label in self.default_apps:
            return 'default'
        
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Permitir relaciones entre models.
        
        Args:
            obj1: Model instance
            obj2: Model instance
        
        Returns:
            bool: True si misma DB
        """
        db_set = {'default', 'ivr'}
        
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Determinar si migrations permitidas.
        
        CNST-003: NO migrations en ivr_legacy (legacy read-only)
        
        Args:
            db: Database alias
            app_label: App label
        
        Returns:
            bool: True si permitir migrations
        """
        # IVR apps: NO migrations (legacy database)
        if app_label in self.ivr_apps:
            return db == 'ivr'  # False para default
        
        # Default apps: migrations solo en default
        if app_label in self.default_apps:
            return db == 'default'
        
        return None


# ==============================================================================
# TESTS DE VALIDACION
# ==============================================================================

def test_router_read():
    """Test routing READ operations."""
    from django.contrib.auth.models import User
    
    router = DatabaseRouter()
    
    # User debe ir a default
    assert router.db_for_read(User) == 'default'


def test_router_write_readonly():
    """Test WRITE prohibido a ivr_legacy (CNST-003)."""
    router = DatabaseRouter()
    
    # Mock model de ivr app
    class MockIVRModel:
        class _meta:
            app_label = 'ivr'
    
    # Write debe retornar None (prohibido)
    assert router.db_for_write(MockIVRModel) is None


def test_router_migrations_readonly():
    """Test migrations prohibidas en ivr_legacy (CNST-003)."""
    router = DatabaseRouter()
    
    # Migrations de app ivr solo permitidas en ivr_legacy
    assert router.allow_migrate('default', 'ivr') is False
    assert router.allow_migrate('ivr', 'ivr') is True
    
    # Migrations de app core solo permitidas en default
    assert router.allow_migrate('default', 'core') is True
    assert router.allow_migrate('ivr', 'core') is False
