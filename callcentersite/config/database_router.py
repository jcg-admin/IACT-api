"""
Database Router para IACT Call Center.

CNST-003: Base de datos IVR es READ-ONLY.

Arquitectura:
- default (Analytics): Django ORM completo (read/write)
- ivr_production (IVR): Solo lectura (NO migrations)
- ivr_backup (IVR Backup): Solo lectura (NO migrations)
"""


class IVRRouter:
    """
    Router base datos dual.
    
    CNST-003: IVR solo lectura, NO migrations.
    """
    
    # Apps que usan IVR legacy
    ivr_legacy_apps = {'ivr_legacy'}
    
    # Bases de datos IVR (read-only)
    ivr_databases = {'ivr_production', 'ivr_backup', 'ivr_legacy'}
    
    def db_for_read(self, model, **hints):
        """
        Lecturas de IVR van a ivr_production.
        Resto va a default.
        """
        if model._meta.app_label in self.ivr_legacy_apps:
            return 'ivr_production'
        return 'default'
    
    def db_for_write(self, model, **hints):
        """
        Escrituras de IVR: PROHIBIDO.
        
        CNST-003: IVR es read-only.
        """
        if model._meta.app_label in self.ivr_legacy_apps:
            # IVR es solo lectura
            return None
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Permitir relaciones dentro de mismo DB.
        """
        db1 = obj1._meta.app_label
        db2 = obj2._meta.app_label
        
        # Ambos en IVR
        if db1 in self.ivr_legacy_apps and db2 in self.ivr_legacy_apps:
            return True
        
        # Ambos en default
        if db1 not in self.ivr_legacy_apps and db2 not in self.ivr_legacy_apps:
            return True
        
        # Cross-database: NO
        return False
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Migrations SOLO en default.
        
        CNST-003 CRÍTICO: NO migrations en IVR.
        """
        # IVR databases: NO migrations NUNCA
        if db in self.ivr_databases:
            return False
        
        # Apps IVR: NO migrations en ningún DB
        if app_label in self.ivr_legacy_apps:
            return db == 'default'  # False si es IVR, True si es default
        
        # Resto: default solamente
        return db == 'default'
