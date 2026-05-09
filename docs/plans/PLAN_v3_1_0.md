# Plan de implementación v3.2.0 — IACT API

**Versión:** 3.2.0
**Fecha:** 2026-05-08
**Prerrequisito:** Plan v3.1.0 completado
**Scope:** UC_RPT_03, UC_RPT_09, UC_RPT_11, UC_AUD_03

---

## Contexto

Este plan cierra los UCs de reportes y auditoría que tienen código cero
o código parcial sin tests. Los modelos base ya existen:
- `Report` — `apps/reports/models.py:13`
- `SavedView` — `apps/reports/models.py:233`
- `ExportJob` — `apps/reports/models.py:96`
- `AuditLog` — `apps/audit/models.py:7`

`UC_AUD_04` (verificar integridad con HMAC-SHA256) ya está implementado
como `AuditIntegrityView` — no es gap de este plan.

---

## Estado de partida esperado

```
tests/unit/         >= 660 passed, 0 failed (post v3.1.0)
tests/integration/  >= 17 passed
Django check:       0 issues
```

---

## Tareas

### T-201 — Implementar `UC_RPT_03` — Ver Reportes Históricos

**Causa raíz:** No existe ningún endpoint ni lógica para reportes históricos.
El modelo `Report` existe pero sin views de análisis retrospectivo.

**Qué hace UC_RPT_03:**
Análisis retrospectivo de datos IVR: tendencias mes a mes, comparativos
periodo vs periodo, detalle por día/hora. Fuente: `base_ivr_detalle` en
MariaDB via `connections['ivr']`.

**Periodos soportados** (del spec `requisitos/casos-uso/reports/uc-rpt-03`):
- `last_24h`, `last_7d`, `last_30d`, `last_90d`
- `custom` (con `date_from`, `date_to`)
- `year_to_date`

**Archivos a crear o modificar:**
```
apps/reports/views.py          — HistoricalReportView
apps/reports/urls.py           — path('historical/', ...)
apps/reports/serializers/      — HistoricalReportSerializer
```

**Función RBAC:** `view_reports`

---

### T-202 — Implementar `UC_RPT_09` — Configurar Filtros Guardados

**Causa raíz:** No existe el modelo `SavedFilter` ni endpoints para CRUD
de filtros guardados. `SavedView` (UC_RPT_10) existe pero es distinto:
`SavedView` guarda una vista completa (filtros + columnas + nombre);
`SavedFilter` guarda solo la configuración de filtros reutilizable.

**Verificación:** `grep -n "SavedFilter" apps/reports/models.py` → vacío.

**Modelo a crear:**
```python
class SavedFilter(models.Model):
    name        = models.CharField(max_length=100)
    report_type = models.CharField(max_length=50)
    filters     = models.JSONField(default=dict)
    created_by  = models.ForeignKey(User, on_delete=models.CASCADE,
                                    related_name='saved_filters')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'reports'
```

**Archivos a crear o modificar:**
```
apps/reports/models.py           — agregar SavedFilter
apps/reports/migrations/         — migración nueva
apps/reports/views.py            — SavedFilterViewSet
apps/reports/serializers/        — SavedFilterSerializer
apps/reports/urls.py             — router.register('saved-filters', ...)
```

**Función RBAC:** `view_reports`

---

### T-203 — Implementar `UC_RPT_11` — Compartir Reporte

**Causa raíz:** No existe endpoint para compartir una `SavedView` con
otros usuarios. El modelo `SavedView` existe pero no tiene campo
`shared_with` ni lógica de sharing.

**Extensión al modelo `SavedView`:**
```python
# Agregar a SavedView
is_public   = models.BooleanField(default=False)
shared_with = models.ManyToManyField(
                  User,
                  blank=True,
                  related_name='shared_views',
              )
```

**Archivos a crear o modificar:**
```
apps/reports/models.py       — campos is_public + shared_with a SavedView
apps/reports/migrations/     — migración nueva
apps/reports/views.py        — ShareSavedViewView (POST /saved-views/{id}/share/)
apps/reports/serializers/    — ShareSavedViewSerializer
apps/reports/urls.py         — path en el router de SavedView
```

**Función RBAC:** `view_reports`

---

### T-204 — Implementar `UC_AUD_03` — Exportar Auditoría (async)

**Causa raíz:** No existe endpoint para exportación asíncrona de `AuditLog`.
El `ExportJob` de `apps/reports/models.py` es para reportes generales
(no para auditoría). UC_AUD_03 requiere un job específico de auditoría.

**Qué hace UC_AUD_03** (del spec `use-case-view/audit/uc-aud-03`):
Genera archivo CSV/JSON con `AuditEvent` para auditores externos.
Operación async — retorna 202 + `job_id`. Worker procesa
streaming + sanitize (PII) + storage. Hash del archivo para integridad.

**Modelo a crear:**
```python
class AuditExportJob(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Pendiente'),
        ('running',   'Ejecutando'),
        ('completed', 'Completado'),
        ('failed',    'Fallido'),
    ]
    FORMAT_CHOICES = [('csv', 'CSV'), ('json', 'JSON')]

    requested_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                     related_name='audit_export_jobs')
    date_from    = models.DateTimeField()
    date_to      = models.DateTimeField()
    format       = models.CharField(max_length=10, choices=FORMAT_CHOICES,
                                    default='csv')
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                    default='pending')
    file_path    = models.CharField(max_length=500, blank=True, default='')
    file_hash    = models.CharField(max_length=64,  blank=True, default='')
    error        = models.TextField(blank=True, default='')
    created_at   = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'audit'
```

**Restricción ADR-BACK-012:** Sin Redis/RabbitMQ. El worker se ejecuta
con APScheduler o con un thread en background, mismo patrón que `run_etl`.

**Archivos a crear o modificar:**
```
apps/audit/models.py         — agregar AuditExportJob
apps/audit/migrations/       — migración nueva
apps/audit/views.py          — AuditExportJobView (POST → 202 + job_id)
                               AuditExportStatusView (GET job_id → estado)
apps/audit/services/         — audit_export_service.py
apps/audit/urls.py           — registrar endpoints
```

**Función RBAC:** `export_audit_log`

---

### T-205 — Tests unitarios e integración del plan v3.2.0

**Archivos a crear:**
```
tests/unit/reports/test_historical_report_view.py
tests/unit/reports/test_saved_filter_viewset.py
tests/unit/reports/test_share_saved_view.py
tests/unit/audit/test_audit_export_job.py
```

**Prerequisito:** T-201, T-202, T-203, T-204.

---

## Dependencias entre tareas

```
T-201  sin prerequisito  (Report ya existe)
T-202  sin prerequisito  (modelo nuevo independiente)
T-203  sin prerequisito  (SavedView ya existe)
T-204  sin prerequisito  (AuditLog ya existe)
T-205  depende de T-201, T-202, T-203, T-204
```

T-201..T-204 pueden ejecutarse en paralelo.

---

## Criterio de cierre

```bash
# 1. Tests unitarios — 0 failed
python -m pytest tests/unit/ --tb=no -q

# 2. Endpoints nuevos existen
python -c "
from django.urls import reverse
print(reverse('reports:historical'))
print(reverse('reports:savedfilter-list'))
print(reverse('audit:audit-export'))
"

# 3. Modelos con migración aplicada
python manage.py shell -c "
from apps.reports.models import SavedFilter
from apps.audit.models import AuditExportJob
print('SavedFilter:', SavedFilter)
print('AuditExportJob:', AuditExportJob)
"

# 4. Django check limpio
python manage.py check
```
