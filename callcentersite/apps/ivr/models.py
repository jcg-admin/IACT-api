"""
Modelos IVR Legacy - IACT Call Center System.

CNST-003: Modelos unmanaged apuntando a ivr_legacy DB (MariaDB).
Acceso READ-ONLY (Database Router enforza).

IMPORTANTE:
- Estos modelos NO generan migrations
- NO se pueden modificar (READ-ONLY)
- Apuntan a tablas existentes en MariaDB legacy
"""
from django.db import models


class CallLog(models.Model):
    """
    Log de llamadas legacy (READ-ONLY).
    
    Mapea a tabla call_logs en ivr_legacy DB (MariaDB).
    
    CNST-003:
    - Database: ivr_legacy (MariaDB)
    - Usuario: ivr_readonly (SOLO SELECT)
    - NO permitir writes
    """
    
    fecha = models.DateField(
        help_text='Fecha de las llamadas'
    )
    
    telefono = models.CharField(
        max_length=20,
        help_text='Numero telefonico'
    )
    
    servicio_800 = models.CharField(
        max_length=20,
        help_text='Numero servicio 800'
    )
    
    total_llamadas = models.IntegerField(
        default=0,
        help_text='Total llamadas'
    )
    
    llamadas_contestadas = models.IntegerField(
        default=0,
        help_text='Llamadas contestadas'
    )
    
    llamadas_abandonadas = models.IntegerField(
        default=0,
        help_text='Llamadas abandonadas'
    )
    
    created_at = models.DateTimeField(
        help_text='Timestamp creacion'
    )
    
    class Meta:
        managed = False  # NO generar migrations
        db_table = 'call_logs'  # Tabla existente en ivr_legacy
        ordering = ['-fecha']
        verbose_name = 'Call Log Legacy'
        verbose_name_plural = 'Call Logs Legacy'
    
    def __str__(self):
        return f"{self.fecha} - {self.telefono}"
