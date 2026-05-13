"""
Modelos pipeline - IACT Call Center System.

ETLExecution, Center, Service, CallRecord y CallNote eliminados en FASE 3.
UC_OPR/UC_SUP/UC_CLI están fuera del scope analítico de IACT-api.

Los datos de llamadas se obtienen desde MariaDB via ivr_services.py (SPs).
El tracking de ETL se realiza sobre etl_runs en MariaDB (raw SQL).
"""
