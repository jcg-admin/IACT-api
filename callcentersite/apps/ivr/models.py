"""
Modelos IVR - IACT Call Center System.

CNST-003: Modelo unmanaged apuntando a ivr_legacy DB (MariaDB).
Acceso READ-ONLY (Database Router enforza).

Schema creado por:
    scripts/provisioners/mariadb/schema_temp_prueba.sh
"""
from django.db import models


# =============================================================================
# DEUDA TÉCNICA — PENDIENTE
# =============================================================================
# Fecha de eliminación: 2026-03-21
# Motivo: El modelo CallLog fue desactivado. La tabla call_logs no existe
#         en ivr_legacy. El schema real de ivr_legacy es responsabilidad
#         de los scripts MariaDB, no de Django.
#         Reactivar cuando:
#           1. scripts/provisioners/mariadb/schema.sh esté implementado
#           2. La tabla call_logs exista en ivr_legacy (producción)
#           3. Los tests de integración real con MariaDB sean necesarios
# Ver: documentos/planes/PLAN_IVR_SIMPLIFICACION_20260321.md
# =============================================================================
#
# class CallLog(models.Model):
#     fecha                = models.DateField(help_text='Fecha de las llamadas')
#     telefono             = models.CharField(max_length=20)
#     servicio_800         = models.CharField(max_length=20)
#     total_llamadas       = models.IntegerField(default=0)
#     llamadas_contestadas = models.IntegerField(default=0)
#     llamadas_abandonadas = models.IntegerField(default=0)
#     created_at           = models.DateTimeField()
#
#     class Meta:
#         managed  = False
#         db_table = 'call_logs'
#         ordering = ['-fecha']


class TblTempPruebaIvr(models.Model):
    """
    Tabla de prueba IVR — consume tbl_temp_prueba_ivr en MariaDB.

    Python solo hace SELECT. Schema y datos creados por:
        scripts/provisioners/mariadb/schema_temp_prueba.sh

    Columnas:
        id     — PK AUTO_INCREMENT
        numero — CHAR(10), número random de 10 caracteres

    CNST-003: READ-ONLY (managed=False, db_router enforza)
    """

    numero = models.CharField(max_length=10)

    class Meta:
        managed  = False
        db_table = 'tbl_temp_prueba_ivr'
        ordering = ['id']
        verbose_name        = 'Temp Prueba IVR'
        verbose_name_plural = 'Temp Prueba IVR'

    def __str__(self):
        return f"[{self.id}] {self.numero}"
