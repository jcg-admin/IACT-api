# Generated manually — FASE 3 — 2026-05-13
#
# Elimina los modelos Center, Service, CallRecord, CallNote y ETLExecution.
# UC_OPR/UC_SUP/UC_CLI están fuera del scope analítico de IACT-api.
# Los datos de llamadas se obtienen desde MariaDB via sp_rpt_* (ivr_services.py).
#
# Orden de eliminación (respeta FKs):
#   1. CallNote      → FK CASCADE a CallRecord, FK PROTECT a User
#   2. CallRecord    → FK SET_NULL a Service, FK SET_NULL a User
#   3. Service       → FK PROTECT a Center
#   4. Center        → sin FKs salientes a otros modelos a eliminar
#   5. ETLExecution  → sin FKs
#
# Tablas eliminadas en PostgreSQL (iact_analytics):
#   pipeline_call_notes, core_call_records, core_services,
#   core_centers, etl_executions

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pipeline', '0002_initial'),
    ]

    operations = [
        migrations.DeleteModel(name='CallNote'),
        migrations.DeleteModel(name='CallRecord'),
        migrations.DeleteModel(name='Service'),
        migrations.DeleteModel(name='Center'),
        migrations.DeleteModel(name='ETLExecution'),
    ]
