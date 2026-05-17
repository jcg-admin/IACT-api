# Plan de Implementación TDD — FASE 3: 11 UCs ALTOS RPT/ALR/PIP/LOG

**Artefacto:** PLAN-IMPLEMENTACION-FASE3-TDD-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Fuente:** PLAN-IMPLEMENTACION-TDD-v3-20260513220000.md § FASE 3
**Metodología:** Red → Green → Refactor por CA
**Rama objetivo:** `develop` (continuación desde commit `c07f666`)

----

## Contexto — Estado post-FASE 2

FASE 0, FASE 1 y FASE 2 completadas. En `develop`:
- 61 funciones RBAC v5.4.0 + 10 AGRs + 3 SoD
- UC_AUTH_01/02/04/05, UC_USR_01/02/03/04, UC_ACC_01/02/04/05,
  UC_PERM_01/02/05/06/07/08, UC_PIP_01, UC_AUD_01, UC_RPT_01

`HasFunction` verifica `required_function` como código canónico `MOD-NNN`
(F0-H-007). Todos los `required_function` deben usar el código, no el nombre.

----

## Hallazgos pre-implementación — lectura de código existente

Los siguientes problemas se detectaron ANTES de escribir tests.
Deben resolverse como prerequisitos de FASE 3.

### H-F3-PRE-001 — `etl_errors` y `etl_retry` sin `required_function` canónico

**Archivos:** `apps/pipeline/views.py`

`etl_errors` verifica permisos con `request.user.has_function('pipeline.view_errors')` —
formato legacy `namespace.action`, no código `MOD-NNN`. `HasFunction` nunca
lo lee porque la función no tiene `required_function` asignado como atributo.
Mismo problema en `etl_data_availability` (`pipeline.view_data_availability`)
y `etl_retry` no tiene verificación de función.

**Corrección requerida antes de escribir tests UC_PIP_02/03/04:**
```python
# Reemplazar verificación inline por atributo canónico:
etl_errors.required_function           = 'PIP-002'  # view_pipeline_errors
etl_data_availability.required_function = 'PIP-003'  # view_data_availability
etl_retry.required_function            = 'PIP-004'  # request_pipeline_retry
```

### H-F3-PRE-002 — `AlertRule` y `Alert` no existen — `AlertConfiguration` es el modelo equivocado

**Archivo:** `apps/alerts/models.py`

El corpus (uc-alr-01/datos-involucrados.rst § 7.1) define `AlertRule` con
campos: `id` (uuid), `actor_id`, `metric` (enum), `scope` (JSON),
`condition` (JSON), `window_minutes`, `severity`, `actions`, `cooldown_minutes`,
`status` (active|paused), `version`, `created_at`, `updated_at`.

El modelo existente `AlertConfiguration` tiene estructura diferente
(no tiene `version`, `window_minutes`, `cooldown_minutes`, `actions`).
`AlertRule` y `AlertRuleHistory` no existen.

`Alert` (uc-alr-02/datos-involucrados.rst § 7.1) tampoco existe:
`rule_id`, `rule_name` (snapshot), `severity`, `state`
(firing|acknowledged|resolved|closed), `fired_at`,
`acknowledged_by`, `acknowledged_at`, `acknowledged_note`,
`resolved_at`, `current_value`, `threshold`.

**Corrección:** nuevas migraciones para `AlertRule`, `AlertRuleHistory`, `Alert`.
`AlertConfiguration` no se elimina — es un modelo diferente del sistema de
mensajería interna existente.

### H-F3-PRE-003 — `ETLLogTailView.required_function = 'LOG-001'` debería ser `'LOG-004'`

**Archivo:** `apps/logs/views.py`

`ETLLogTailView` implementa UC_LOG_02 (logs ETL). El catálogo v5.4.0:
- `LOG-001` = `view_application_logs` (UC_LOG_01)
- `LOG-004` = `view_etl_logs` (UC_LOG_02)

La vista tiene `required_function = 'LOG-001'` en lugar de `'LOG-004'`.

**Corrección:**
```python
class ETLLogTailView(APIView):
    required_function = 'LOG-004'  # view_etl_logs
```

### H-F3-PRE-004 — `UC_RPT_02` requiere infraestructura SSE/ASGI no disponible

El corpus define UC_RPT_02 como un stream SSE con pub/sub, throttle,
heartbeat, y connection registry. La infraestructura de Django WSGI no
soporta SSE nativo. El plan TDD v3 marca UC_RPT_02 como
"stub documentado" precisamente por esta razón.

**Corrección:** implementar un endpoint stub documentado que retorna 503
con `FEATURE_NOT_AVAILABLE` y documenta el contrato completo para
cuando la infraestructura ASGI esté disponible.

----

## Orden de implementación

```
PREREQUISITOS (H-F3-PRE-001..004)
  └─ Sin estos, los tests de FASE 3 no pueden pasar

GRUPO A — Raíces (sin dependencias pendientes):
  UC_PIP_02  Consultar Errores ETL       → req: UC_PIP_01 (done)
  UC_PIP_03  Consultar Disponibilidad    → req: UC_PIP_01 (done)
  UC_LOG_01  Ver Logs Aplicación         → raíz
  UC_LOG_02  Ver Logs ETL                → req: UC_PIP_01 (done)
  UC_RPT_02  Ver Métricas Tiempo Real    → stub (SSE no disponible)
  UC_RPT_03  Ver Reportes Históricos     → req: UC_RPT_01 (done)
  UC_ALR_01  Configurar Umbrales         → raíz

GRUPO B — Dependencias internas de FASE 3:
  UC_PIP_04  Solicitar Reintento         → req: UC_PIP_01 (done), UC_PIP_02 (A)
  UC_ALR_02  Ver Alertas Activas         → req: UC_ALR_01 (A)
  UC_RPT_04  Exportar Reporte            → req: UC_RPT_01 (done), UC_RPT_03 (A)

GRUPO C — Dependencia del Grupo B:
  UC_ALR_03  Reconocer Alerta            → req: UC_ALR_02 (B)
```

----

## PREREQUISITOS — correcciones antes del primer test

### P-1: Corregir `required_function` en `pipeline/views.py`

```python
# Al final de cada función, asignar el atributo:
etl_errors.required_function           = 'PIP-002'
etl_data_availability.required_function = 'PIP-003'
etl_retry.required_function            = 'PIP-004'
# Eliminar verificaciones inline con has_function('pipeline.*')
```

### P-2: Corregir `required_function` en `logs/views.py`

```python
class ETLLogTailView(APIView):
    required_function = 'LOG-004'  # view_etl_logs — no LOG-001
```

### P-3: Crear modelos `AlertRule`, `AlertRuleHistory`, `Alert`

**Migración:** `apps/alerts/migrations/0005_fase3_alert_rule_and_alert.py`

```python
class AlertRule(models.Model):
    """
    Regla de alerta definida por un usuario (UC_ALR_01).
    Fuente: uc-alr-01/datos-involucrados.rst § 7.1
    """
    STATUS_ACTIVE = 'active'
    STATUS_PAUSED = 'paused'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Activa'),
        (STATUS_PAUSED, 'Pausada'),
    ]
    SEVERITY_CHOICES = [
        ('info',     'Info'),
        ('warning',  'Warning'),
        ('error',    'Error'),
        ('critical', 'Critical'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4)
    actor           = models.ForeignKey(User, on_delete=models.PROTECT,
                                        related_name='alert_rules')
    name            = models.CharField(max_length=200)
    metric          = models.CharField(max_length=100)   # enum — validado por RuleValidator
    scope           = models.JSONField()                  # {segment?, queue?, campaign?}
    condition       = models.JSONField()                  # {op, threshold}
    window_minutes  = models.PositiveIntegerField()
    severity        = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    actions         = models.JSONField(default=list)      # lista de acciones
    cooldown_minutes = models.PositiveIntegerField(default=60)
    status          = models.CharField(max_length=10, choices=STATUS_CHOICES,
                                       default=STATUS_ACTIVE)
    version         = models.PositiveIntegerField(default=1)  # incrementado por update
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'alerts_alert_rule'
        indexes = [
            models.Index(fields=['actor'], name='idx_alr_actor'),
            models.Index(fields=['status', 'version'], name='idx_alr_status_ver'),
        ]


class AlertRuleHistory(models.Model):
    """
    Snapshot inmutable de AlertRule por cada update (UC_ALR_01 CA-10).
    """
    rule        = models.ForeignKey(AlertRule, on_delete=models.CASCADE,
                                    related_name='history')
    version     = models.PositiveIntegerField()
    snapshot    = models.JSONField()    # copia completa del rule en ese momento
    changed_by  = models.ForeignKey(User, on_delete=models.PROTECT)
    changed_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'alerts_alert_rule_history'
        unique_together = ('rule', 'version')


class Alert(models.Model):
    """
    Alerta disparada por una AlertRule (UC_ALR_02).
    Fuente: uc-alr-02/datos-involucrados.rst § 7.1
    """
    STATE_FIRING       = 'firing'
    STATE_ACKNOWLEDGED = 'acknowledged'
    STATE_RESOLVED     = 'resolved'
    STATE_CLOSED       = 'closed'
    STATE_CHOICES = [
        (STATE_FIRING,       'Disparada'),
        (STATE_ACKNOWLEDGED, 'Reconocida'),
        (STATE_RESOLVED,     'Resuelta'),
        (STATE_CLOSED,       'Cerrada'),
    ]

    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4)
    rule                = models.ForeignKey(AlertRule, on_delete=models.PROTECT,
                                            related_name='alerts')
    rule_name           = models.CharField(max_length=200)  # snapshot
    metric              = models.JSONField()                 # snapshot
    scope               = models.JSONField()                 # snapshot
    severity            = models.CharField(max_length=10)
    state               = models.CharField(max_length=15, choices=STATE_CHOICES,
                                           default=STATE_FIRING)
    fired_at            = models.DateTimeField()
    acknowledged_by     = models.ForeignKey(User, null=True, blank=True,
                                             on_delete=models.SET_NULL,
                                             related_name='acknowledged_alerts')
    acknowledged_at     = models.DateTimeField(null=True, blank=True)
    acknowledged_note   = models.TextField(blank=True)
    resolved_at         = models.DateTimeField(null=True, blank=True)
    current_value       = models.FloatField(null=True, blank=True)
    threshold           = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'alerts_alert'
        indexes = [
            models.Index(fields=['state', 'severity', '-fired_at'],
                         name='idx_alert_state_sev'),
            models.Index(fields=['rule', '-fired_at'], name='idx_alert_rule'),
        ]
```

### P-4: Stub UC_RPT_02

```python
# apps/reports/realtime_view.py
class RealtimeMetricsView(APIView):
    """
    UC_RPT_02 — Ver Métricas Tiempo Real (STUB).

    STUB: UC_RPT_02 requiere infraestructura SSE/ASGI (pub/sub con
    topics call_state_changes, agent_state_changes, queue_state_snapshots).
    El stack actual es WSGI. Este endpoint retorna 503 con el contrato
    documentado hasta que se migre a ASGI.

    Contrato completo: uc-rpt-02/implementacion-tecnica.rst
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'RPT-002'  # view_realtime_metrics (no existe en v5.4.0 — pendiente ACC)

    def get(self, request):
        return Response(
            {
                'error':   'FEATURE_NOT_AVAILABLE',
                'detail':  (
                    'UC_RPT_02 requiere infraestructura SSE/ASGI. '
                    'Disponible cuando se migre a ASGI server.'
                ),
                'contract': 'uc-rpt-02/implementacion-tecnica.rst',
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
```

**Nota:** `view_realtime_metrics` no existe en el catálogo v5.4.0 actual
(el catálogo tiene `RPT-001`..`RPT-011`). Añadir `RPT-002b` o usar
`IsAuthenticated` solo para el stub. A documentar como H-F3-001.

----

## GRUPO A — UC_PIP_02: Consultar Errores ETL

**Endpoint:** `GET /api/pipeline/errors/`
**Función:** `PIP-002` (`view_pipeline_errors`)
**Tests:** `tests/unit/fase3/test_uc_pip_02_errors.py`

### Tests requeridos (Parte 12 — Testing)

```python
class TestETLErrorPIIScanner:
    """UT-01: PIIScanner detecta email en stack."""
    def test_pii_scanner_redacts_email_in_stack_trace():
        raw = "Error at alice@example.com line 42"
        sanitized = PIIScanner.sanitize(raw)
        assert 'alice@example.com' not in sanitized
        assert '[REDACTED]' in sanitized or '***' in sanitized

class TestETLErrorsEndpoint:
    """IT-01..04, SEC-01..02"""
    def test_it01_list_basico_retorna_estructura_correcta(admin_client):
        # CA-01: GET errors/ → 200 con {total, page, page_size, errors}
        response = admin_client.get('/api/pipeline/errors/')
        assert response.status_code == 200
        assert 'total' in response.data
        assert 'errors' in response.data

    def test_it02_filter_pipeline_id(admin_client, error_fixture):
        # CA-02: ?pipeline_id=X → solo errores de ese pipeline
        response = admin_client.get('/api/pipeline/errors/',
                                    {'pipeline_id': error_fixture.pipeline_id})
        assert all(e['pipeline_id'] == error_fixture.pipeline_id
                   for e in response.data['errors'])

    def test_it03_sanitize_aplicado(admin_client, error_with_pii_fixture):
        # CA-03: stack_trace_sanitized no contiene PII
        response = admin_client.get('/api/pipeline/errors/')
        for e in response.data['errors']:
            assert 'stack_trace_sanitized' in e
            assert '@' not in e.get('stack_trace_sanitized', '')

    def test_it04_bd_timeout_retorna_503(admin_client, mock_ivr_timeout):
        # CA-07: BD timeout → 503
        response = admin_client.get('/api/pipeline/errors/')
        assert response.status_code == 503

    def test_sec01_sin_permiso_retorna_403(client_sin_pip002):
        # CA-06: sin PIP-002 → 403
        response = client_sin_pip002.get('/api/pipeline/errors/')
        assert response.status_code == 403

    def test_sec02_stack_no_contiene_pii(admin_client, error_with_pii):
        # CA-03 SEC: no PII en ningún campo
        response = admin_client.get('/api/pipeline/errors/')
        body = str(response.data)
        assert 'password' not in body.lower()
        assert '@example.com' not in body
```

### Implementación requerida

- `PIIScanner.sanitize(text: str) -> str` en `apps/pipeline/services/`
  (si no existe — reutilizar de `apps/audit/` si ya tiene uno)
- Actualizar `etl_errors` para:
  - Asignar `etl_errors.required_function = 'PIP-002'`
  - Eliminar verificación inline `has_function('pipeline.view_errors')`
  - Aplicar `PIIScanner` a `error_message` y cualquier stack
  - Soporte para filtro `pipeline_id` además de `quarter`
  - Soporte para `correlation_id` drill (CA-05)
  - Agrupar por `error_type` (CA-04)

----

## GRUPO A — UC_PIP_03: Consultar Disponibilidad de Datos

**Endpoint:** `GET /api/pipeline/data-availability/`
**Función:** `PIP-003` (`view_data_availability`)
**Tests:** `tests/unit/fase3/test_uc_pip_03_availability.py`

### Tests requeridos

```python
class TestDataAvailabilityStatus:
    """UT-01..03: StatusCalculator como función pura"""

    def test_ut01_status_fresh_cuando_dentro_del_threshold():
        # CA-02: last_refresh < fresh_threshold → status='fresh'
        metadata = DatasetMetadata(
            last_refresh_at=now() - timedelta(minutes=10),
            fresh_threshold_minutes=30,
            critical_threshold_minutes=120,
        )
        assert StatusCalculator.compute(metadata) == 'fresh'

    def test_ut02_status_stale_entre_thresholds():
        # CA-03: fresh_threshold < lag < critical_threshold → 'stale'
        metadata = DatasetMetadata(
            last_refresh_at=now() - timedelta(minutes=60),
            fresh_threshold_minutes=30,
            critical_threshold_minutes=120,
        )
        assert StatusCalculator.compute(metadata) == 'stale'

    def test_ut03_status_critical_stale_sobre_critical_threshold():
        # CA-04: lag > critical_threshold → 'critical_stale'
        metadata = DatasetMetadata(
            last_refresh_at=now() - timedelta(minutes=200),
            fresh_threshold_minutes=30,
            critical_threshold_minutes=120,
        )
        assert StatusCalculator.compute(metadata) == 'critical_stale'


class TestDataAvailabilityEndpoint:
    """IT-01..03, SEC-01"""

    def test_it01_get_datasets_retorna_lista_con_status(admin_client):
        # CA-01: → {datasets: [{name, status, last_refresh_at, ...}]}
        response = admin_client.get('/api/pipeline/data-availability/')
        assert response.status_code == 200
        assert 'datasets' in response.data

    def test_it02_cache_hit_segunda_llamada(admin_client, mock_cache):
        # CA-06: TTL 30s — segunda llamada usa cache
        admin_client.get('/api/pipeline/data-availability/')
        admin_client.get('/api/pipeline/data-availability/')
        assert mock_cache.get_call_count >= 1

    def test_it03_bd_timeout_retorna_503(admin_client, mock_ivr_timeout):
        # CA-07: BD timeout → 503
        response = admin_client.get('/api/pipeline/data-availability/')
        assert response.status_code == 503

    def test_sec01_sin_permiso_retorna_403(client_sin_pip003):
        # CA-05: sin PIP-003 → 403
        response = client_sin_pip003.get('/api/pipeline/data-availability/')
        assert response.status_code == 403
```

### Implementación requerida

- `StatusCalculator.compute(metadata) -> str` en `apps/pipeline/services/`
- `DatasetMetadata` — verificar si existe en `pipeline/models.py`;
  si no existe, crear modelo o leer desde MariaDB
- Corregir `etl_data_availability.required_function = 'PIP-003'`
- Eliminar verificación inline `has_function('pipeline.view_data_availability')`
- Añadir cache con TTL 30s (P-29)

----

## GRUPO A — UC_ALR_01: Configurar Umbrales de Alerta

**Endpoints:** `POST/PATCH/DELETE /api/alerts/rules/` + `POST /api/alerts/rules/dry-run/`
**Función:** `ALR-002` (`configure_alerts`) — CRUD; `ALR-003` (`configure_team_alerts`) para team scope
**Tests:** `tests/unit/fase3/test_uc_alr_01_alert_rules.py`

### Tests requeridos

```python
class TestRuleValidator:
    """UT-01..04"""

    def test_ut01_metric_desconocido_rechazado():
        with pytest.raises(ValidationError, match='metric'):
            RuleValidator.validate({'metric': 'METRIC_INEXISTENTE',
                                    'scope': {}, 'condition': {}},
                                   segments=['seg-a'])

    def test_ut02_scope_cross_segmento_rechazado():
        with pytest.raises(ValidationError, match='scope'):
            RuleValidator.validate({'metric': 'call_volume',
                                    'scope': {'segment': 'seg-otro'},
                                    'condition': {}},
                                   segments=['seg-a'])

    def test_ut03_action_target_inexistente_rechazado():
        with pytest.raises(ValidationError, match='action'):
            RuleValidator.validate({'metric': 'call_volume',
                                    'scope': {'segment': 'seg-a'},
                                    'condition': {'op': '>', 'threshold': 100},
                                    'actions': [{'type': 'notify_queue',
                                                 'target_id': 'QUEUE_INEXISTENTE'}]},
                                   segments=['seg-a'])

    def test_ut04_dry_run_engine_cuenta_hits():
        hits = DryRunEngine.evaluate_against(
            rule_payload={'metric': 'call_volume',
                          'condition': {'op': '>', 'threshold': 50}},
            period='last_24h',
        )
        assert isinstance(hits.count, int)
        assert len(hits.sample) <= 10


class TestAlertRuleEndpoints:
    """IT-01..06, SEC-01..02"""

    def test_it01_crear_rule_basico_retorna_201(client_alr, valid_rule_payload):
        # CA-01
        response = client_alr.post('/api/alerts/rules/', valid_rule_payload, format='json')
        assert response.status_code == 201
        assert 'id' in response.data
        assert AlertRule.objects.filter(id=response.data['id']).exists()

    def test_it02_update_incrementa_version(client_alr, existing_rule):
        # CA-05: PATCH → version + 1
        before = existing_rule.version
        client_alr.patch(f'/api/alerts/rules/{existing_rule.id}/',
                         {'name': 'Updated'}, format='json')
        existing_rule.refresh_from_db()
        assert existing_rule.version == before + 1

    def test_it03_pause_resume_conserva_rule(client_alr, existing_rule):
        # CA-06
        client_alr.post(f'/api/alerts/rules/{existing_rule.id}/pause/')
        existing_rule.refresh_from_db()
        assert existing_rule.status == AlertRule.STATUS_PAUSED
        client_alr.post(f'/api/alerts/rules/{existing_rule.id}/resume/')
        existing_rule.refresh_from_db()
        assert existing_rule.status == AlertRule.STATUS_ACTIVE
        # condition y metric preservados
        assert existing_rule.metric is not None

    def test_it04_delete_cascade(client_alr, existing_rule_with_alerts):
        # CA-07: DELETE → regla y sus Alert eliminados
        rule_id = existing_rule_with_alerts.id
        client_alr.delete(f'/api/alerts/rules/{rule_id}/')
        assert not AlertRule.objects.filter(id=rule_id).exists()

    def test_it05_dry_run_no_crea_alertas_reales(client_alr, valid_rule_payload):
        # CA-08
        before = Alert.objects.count()
        client_alr.post('/api/alerts/rules/dry-run/', valid_rule_payload, format='json')
        assert Alert.objects.count() == before

    def test_it06_cooldown_evita_refire(alert_evaluator, firing_rule):
        # CA-09: segunda evaluación dentro del cooldown → sin nueva Alert
        alert_evaluator.evaluate(firing_rule)
        count_after_first = Alert.objects.filter(rule=firing_rule).count()
        alert_evaluator.evaluate(firing_rule)  # dentro del cooldown
        assert Alert.objects.filter(rule=firing_rule).count() == count_after_first

    def test_sec01_cross_segmento_bloqueado(client_alr_seg_a):
        # CA-02: scope con segmento diferente al del user → 403
        payload = {'metric': 'call_volume', 'scope': {'segment': 'seg-b'}, ...}
        response = client_alr_seg_a.post('/api/alerts/rules/', payload, format='json')
        assert response.status_code == 400  # ValidationError en RuleValidator

    def test_sec02_sin_permiso_retorna_403(client_sin_alr002):
        response = client_sin_alr002.post('/api/alerts/rules/', {}, format='json')
        assert response.status_code == 403
```

### Implementación requerida

- `RuleValidator` — valida metric, scope y actions contra el contexto del usuario
- `DryRunEngine` — evalúa una regla hipotética contra datos históricos (last_24h)
- `AlertRuleListCreateView`, `AlertRuleDetailView` (CRUD)
- `AlertRuleDryRunView` (`POST /api/alerts/rules/dry-run/`)
- Acciones pause/resume como `@action` DRF o endpoints separados
- AuditEvent en cada CRUD (CA-10): `ALERT_RULE_CREATED`, `ALERT_RULE_UPDATED`,
  `ALERT_RULE_DELETED`, `ALERT_RULE_PAUSED`, `ALERT_RULE_RESUMED`

----

## GRUPO A — UC_LOG_01: Ver Logs de Aplicación

**Endpoints:** `GET /api/logs/` + `GET /api/logs/tail/` (SSE)
**Función:** `LOG-001` (`view_application_logs`)
**Tests:** `tests/unit/fase3/test_uc_log_01_app_logs.py`

### Tests requeridos

```python
class TestLogValidator:
    """UT-01..02"""

    def test_ut01_range_mayor_24h_rechazado():
        with pytest.raises(ValidationError, match='range'):
            LogRangeValidator.validate(
                from_dt=now() - timedelta(hours=25),
                to_dt=now(),
            )

    def test_ut02_pii_scanner_redacta_email_en_message():
        entry = {'message': 'User bob@corp.com logged in', 'context': {}}
        sanitized = PIIScanner.sanitize_log_entry(entry)
        assert 'bob@corp.com' not in sanitized['message']


class TestAppLogsEndpoint:
    """IT-01..04, SEC-01..02"""

    def test_it01_list_con_filtros_retorna_log_entries(client_log01):
        # CA-01..03: GET /api/logs/ → {entries: [...], total}
        response = client_log01.get('/api/logs/', {'level': 'ERROR'})
        assert response.status_code == 200
        assert all(e['level'] == 'ERROR' for e in response.data['entries'])

    def test_it02_sanitize_aplicado_a_entries(client_log01, log_with_pii):
        # CA-05: PII removido antes de retornar
        response = client_log01.get('/api/logs/')
        body = str(response.data)
        assert '@' not in body or 'REDACTED' in body

    def test_it03_logstore_timeout_retorna_503(client_log01, mock_logstore_timeout):
        # CA-07: LogStore timeout → 503
        response = client_log01.get('/api/logs/')
        assert response.status_code == 503

    def test_it04_tail_sse_es_streaming_response(client_log01):
        # CA-06: GET /api/logs/tail/ → streaming (o 503 si SSE stub)
        response = client_log01.get('/api/logs/tail/')
        assert response.status_code in (200, 503)

    def test_sec01_sin_permiso_retorna_403(client_sin_log001):
        response = client_sin_log001.get('/api/logs/')
        assert response.status_code == 403

    def test_sec02_sin_pii_en_response(client_log01, log_with_pii):
        response = client_log01.get('/api/logs/')
        assert 'password' not in str(response.data).lower()
```

### Implementación requerida

- `LogRangeValidator.validate(from_dt, to_dt)` — rechaza rango > 24h (CA-04)
- `PIIScanner.sanitize_log_entry(entry: dict) -> dict` — sanitiza
  `message` y `context` (CNST-026)
- `SystemLogsView` (GET `/api/logs/`) con filtros `level`, `service`,
  `from_dt`, `to_dt` + paginación
- `LogTailView` (GET `/api/logs/tail/`) — stub 503 o SSE si infraestructura disponible
- `required_function = 'LOG-001'` en ambas vistas

----

## GRUPO A — UC_LOG_02: Ver Logs ETL

**Endpoint:** `GET /api/logs/etl/`
**Función:** `LOG-004` (`view_etl_logs`)
**Tests:** `tests/unit/fase3/test_uc_log_02_etl_logs.py`

### Tests requeridos

```python
class TestETLLogScope:
    """UT-01: Filter scope etl"""

    def test_ut01_scope_etl_solo_retorna_servicios_etl():
        # CA-01: solo logs de etl-runner, etl-validator, etl-transformer
        entries = [
            {'service': 'etl-runner', 'message': 'ok'},
            {'service': 'web-api',    'message': 'ignored'},
        ]
        filtered = ETLLogScopeFilter.apply(entries)
        assert all(e['service'].startswith('etl-') for e in filtered)


class TestETLLogsEndpoint:
    """IT-01..04, SEC-01"""

    def test_it01_solo_logs_etl_retornados(client_log04):
        # CA-01: GET /api/logs/etl/ → solo service ∈ {etl-*}
        response = client_log04.get('/api/logs/etl/')
        assert response.status_code == 200
        for entry in response.data.get('entries', []):
            assert entry['service'].startswith('etl-')

    def test_it02_filter_pipeline_run_id_correlaciona(client_log04, etl_log_fixture):
        # CA-02: ?pipeline_run_id=X → solo logs de ese run
        response = client_log04.get('/api/logs/etl/',
                                    {'pipeline_run_id': etl_log_fixture.run_id})
        for e in response.data['entries']:
            assert e['context'].get('pipeline_run_id') == etl_log_fixture.run_id

    def test_it03_sanitize_aplicado(client_log04, etl_log_with_pii):
        # CA-03
        response = client_log04.get('/api/logs/etl/')
        assert 'password' not in str(response.data).lower()

    def test_it04_logstore_timeout_retorna_503(client_log04, mock_logstore_timeout):
        # CA-06
        response = client_log04.get('/api/logs/etl/')
        assert response.status_code == 503

    def test_sec01_sin_permiso_retorna_403(client_sin_log004):
        response = client_sin_log004.get('/api/logs/etl/')
        assert response.status_code == 403
```

### Implementación requerida

- Corregir `ETLLogTailView.required_function = 'LOG-004'`
- `ETLLogsListView` (GET `/api/logs/etl/`) — filtro por scope ETL + `pipeline_run_id`
- Reutilizar `PIIScanner` de UC_LOG_01

----

## GRUPO A — UC_RPT_03: Ver Reportes Históricos

**Endpoint:** `GET /api/reports/historical/`
**Función:** `RPT-001` (`view_reports`)
**Tests:** `tests/unit/fase3/test_uc_rpt_03_historical.py`

### Tests requeridos (selección — 9 UT + 9 IT)

```python
class TestPeriodResolver:
    """UT-01..02"""
    def test_ut01_prior_de_last_30d():
        period = PeriodSpec(preset='last_30d')
        prior  = PeriodResolver.prior(period)
        assert prior.duration_days == 30
        assert prior.end < period.start

    def test_ut02_prior_de_custom_mismo_length():
        start  = datetime(2026, 3, 1)
        end    = datetime(2026, 4, 1)
        period = PeriodSpec(start=start, end=end)
        prior  = PeriodResolver.prior(period)
        assert (prior.end - prior.start) == (end - start)


class TestFilterValidator:
    """UT-05..06"""
    def test_ut05_range_mayor_2_anos_rechazado():
        with pytest.raises(ValidationError, match='RANGE_TOO_LARGE'):
            FilterValidator.validate(period=PeriodSpec(days=730 + 1))

    def test_ut06_group_by_minute_con_range_mayor_6h_rechazado():
        with pytest.raises(ValidationError):
            FilterValidator.validate(
                period=PeriodSpec(hours=7),
                group_by=['minute'],
            )


class TestComparativeBuilder:
    """UT-03..04"""
    def test_ut03_con_datos_prior_retorna_diff_pct():
        result = ComparativeBuilder.build(current_total=120, prior_total=100)
        assert result.diff_pct == pytest.approx(20.0)
        assert result.insufficient_data is False

    def test_ut04_sin_datos_prior_retorna_insufficient_data():
        result = ComparativeBuilder.build(current_total=120, prior_total=None)
        assert result.insufficient_data is True


class TestHistoricalEndpoint:
    """IT-01..09"""
    def test_it01_last_30d_retorna_buckets_diarios(client_rpt, analytics_data):
        response = client_rpt.get('/api/reports/historical/',
                                  {'period': 'last_30d'})
        assert response.status_code == 200
        assert len(response.data['buckets']) <= 30
        assert response.data['cache'] is False

    def test_it05_cache_hit_segunda_llamada(client_rpt, analytics_data):
        client_rpt.get('/api/reports/historical/', {'period': 'last_30d'})
        response = client_rpt.get('/api/reports/historical/', {'period': 'last_30d'})
        assert response.data['cache'] is True

    def test_it07_range_mayor_2_anos_retorna_400(client_rpt):
        response = client_rpt.get('/api/reports/historical/',
                                  {'date_from': '2020-01-01', 'date_to': '2026-01-01'})
        assert response.status_code == 400
        assert response.data['error'] == 'RANGE_TOO_LARGE'

    def test_it08_bd_timeout_retorna_503(client_rpt, mock_analytics_timeout):
        response = client_rpt.get('/api/reports/historical/', {'period': 'last_30d'})
        assert response.status_code == 503
```

### Implementación requerida

- `PeriodResolver.prior(period: PeriodSpec) -> PeriodSpec`
- `FilterValidator.validate(period, group_by, page_size)`
- `ComparativeBuilder.build(current, prior) -> ComparativeResult`
- `KPICalculator.derive(bucket) -> KPIBucket` (TMO, SL, abandono)
- `HistoricalReportService.get(filters, period, group_by, page, invoker)`
- `HistoricalReportView` (GET `/api/reports/historical/`)
- Cache con TTL adaptativo (P-62):
  - `last_24h` → TTL 60s
  - `last_30d` → TTL 900s
  - Custom range largo → TTL proporcional

----

## GRUPO B — UC_PIP_04: Solicitar Reintento de Pipeline

**Endpoint:** `POST /api/pipeline/retry/`
**Función:** `PIP-004` (`request_pipeline_retry`)
**Dependencia:** UC_PIP_02 (done en Grupo A)
**Tests:** `tests/unit/fase3/test_uc_pip_04_retry.py`

### Tests requeridos

```python
class TestPipelineRetryValidation:
    """UT-01"""
    def test_ut01_reason_menor_20_chars_rechazado():
        with pytest.raises(ValidationError):
            PipelineRetryService.validate_reason('Muy corto')

    def test_ut01_reason_exactamente_20_chars_aceptado():
        PipelineRetryService.validate_reason('A' * 20)  # sin excepción

class TestPipelineRetryEndpoint:
    """IT-01..07, SEC-01"""

    def test_it01_retry_basico_retorna_202_con_run_id(client_pip04, pipeline_fixture):
        # CA-01
        response = client_pip04.post('/api/pipeline/retry/', {
            'pipeline_id': pipeline_fixture.id,
            'reason': 'Timeout en paso de transformación, reintento manual',
        }, format='json')
        assert response.status_code == 202
        assert 'new_run_id' in response.data

    def test_it02_already_running_retorna_409(client_pip04, running_pipeline):
        # CA-02
        response = client_pip04.post('/api/pipeline/retry/', {
            'pipeline_id': running_pipeline.id,
            'reason': 'Intento mientras pipeline corre',
        }, format='json')
        assert response.status_code == 409

    def test_it03_reason_missing_retorna_400(client_pip04, pipeline_fixture):
        # CA-03: sin reason
        response = client_pip04.post('/api/pipeline/retry/', {
            'pipeline_id': pipeline_fixture.id,
        }, format='json')
        assert response.status_code == 400

    def test_it04_audit_emitido(client_pip04, pipeline_fixture, audit_listener):
        # CA-04: AuditEvent PIPELINE_RETRY_REQUESTED
        client_pip04.post('/api/pipeline/retry/', {
            'pipeline_id': pipeline_fixture.id,
            'reason': 'X' * 20,
        }, format='json')
        assert audit_listener.has('PIPELINE_RETRY_REQUESTED')

    def test_it05_doble_retry_mismo_run_retorna_409(client_pip04, pipeline_fixture):
        # CA-05: idempotencia — segundo retry del mismo run_id → 409
        payload = {
            'pipeline_id': pipeline_fixture.id,
            'run_id': pipeline_fixture.last_run_id,
            'reason': 'X' * 20,
        }
        client_pip04.post('/api/pipeline/retry/', payload, format='json')
        response = client_pip04.post('/api/pipeline/retry/', payload, format='json')
        assert response.status_code == 409

    def test_it06_high_priority_encola_al_frente(client_pip04, pipeline_fixture, mock_queue):
        # CA-06
        client_pip04.post('/api/pipeline/retry/', {
            'pipeline_id': pipeline_fixture.id,
            'reason': 'X' * 20,
            'priority': 'high',
        }, format='json')
        assert mock_queue.last_enqueued_priority == 'high'

    def test_sec01_sin_permiso_retorna_403(client_sin_pip004, pipeline_fixture):
        response = client_sin_pip004.post('/api/pipeline/retry/', {
            'pipeline_id': pipeline_fixture.id,
            'reason': 'X' * 20,
        }, format='json')
        assert response.status_code == 403
```

### Implementación requerida

- Corregir `etl_retry.required_function = 'PIP-004'`
- Verificar que el retry valida `reason` ≥ 20 chars
- Implementar idempotencia por `run_id` (CA-05)
- Implementar `priority` → `high` encola al frente (CA-06)
- AuditEvent `PIPELINE_RETRY_REQUESTED` con `pipeline_id`, `run_id`,
  `reason`, `priority`, `new_run_id`

----

## GRUPO B — UC_ALR_02: Ver Alertas Activas

**Endpoint:** `GET /api/alerts/`
**Función:** `ALR-001` (`view_alerts`)
**Dependencia:** UC_ALR_01 (Grupo A — modelo Alert existe)
**Tests:** `tests/unit/fase3/test_uc_alr_02_active_alerts.py`

```python
class TestAlertOrdering:
    """UT-01"""
    def test_ut01_order_severity_desc():
        alerts = [
            Alert(severity='info', fired_at=now()),
            Alert(severity='critical', fired_at=now()),
            Alert(severity='warning', fired_at=now()),
        ]
        ordered = AlertSorter.by_severity_desc(alerts)
        assert ordered[0].severity == 'critical'
        assert ordered[-1].severity == 'info'

class TestActiveAlertsEndpoint:
    """IT-01..05, SEC-01"""

    def test_it01_list_firing_retorna_items_con_state(client_alr01, firing_alerts):
        response = client_alr01.get('/api/alerts/')
        assert response.status_code == 200
        assert all(a['state'] in ('firing', 'acknowledged')
                   for a in response.data['items'])

    def test_it02_filtro_severity(client_alr01, mixed_severity_alerts):
        response = client_alr01.get('/api/alerts/', {'severity': 'critical'})
        assert all(a['severity'] == 'critical' for a in response.data['items'])

    def test_it03_sin_alertas_retorna_lista_vacia(client_alr01):
        response = client_alr01.get('/api/alerts/')
        assert response.status_code == 200
        assert response.data['items'] == []

    def test_it04_cross_segmento_no_listado(client_alr01_seg_a, alert_seg_b):
        # CA-04: alerts de seg-b no visibles para user de seg-a
        response = client_alr01_seg_a.get('/api/alerts/')
        ids = [a['id'] for a in response.data['items']]
        assert str(alert_seg_b.id) not in ids

    def test_it05_bd_timeout_retorna_503(client_alr01, mock_db_timeout):
        response = client_alr01.get('/api/alerts/')
        assert response.status_code == 503
```

----

## GRUPO B — UC_RPT_04: Exportar Reporte (patrón Larman)

**Endpoints:** `POST /api/reports/export/`, `GET /api/reports/export/{id}/`,
`DELETE /api/reports/export/{id}/`
**Función:** `RPT-004/005/006` (export_csv/excel/pdf — 3 funciones RBAC separadas)
**Dependencia:** UC_RPT_03 (Grupo A)
**Tests:** `tests/unit/fase3/test_uc_rpt_04_export.py`

### Tests requeridos (selección — 9 UT + 11 IT)

```python
class TestPayloadValidator:
    """UT-01..03"""
    def test_ut01_payload_valido_pasa():
        PayloadValidator.validate({'format': 'csv', 'period': 'last_30d'})

    def test_ut02_format_desconocido_rechazado():
        with pytest.raises(ValidationError):
            PayloadValidator.validate({'format': 'WORD', 'period': 'last_30d'})

    def test_ut03_estimated_rows_mayor_1m_rechazado():
        with pytest.raises(RowLimitExceeded):
            JobLimiter.check_row_limit(estimated_rows=1_000_001)

class TestExportEndpoints:
    """IT-01..11"""
    def test_it01_queue_retorna_202_con_job_id(client_rpt04, valid_export_payload):
        # CA-01
        response = client_rpt04.post('/api/reports/export/', valid_export_payload,
                                      format='json')
        assert response.status_code == 202
        assert 'job_id' in response.data
        assert ExportJob.objects.filter(id=response.data['job_id'],
                                        status='queued').exists()

    def test_it07_mas_de_5_jobs_retorna_429(client_rpt04, five_active_jobs,
                                              valid_export_payload):
        # CA-08
        response = client_rpt04.post('/api/reports/export/', valid_export_payload,
                                      format='json')
        assert response.status_code == 429

    def test_it08_cancel_queued_retorna_cancelled(client_rpt04, queued_job):
        # CA-17: DELETE → cancelled
        response = client_rpt04.delete(f'/api/reports/export/{queued_job.id}/')
        queued_job.refresh_from_db()
        assert queued_job.status == 'cancelled'

    def test_it11_status_check_retorna_progress_pct(client_rpt04, running_job):
        # CA-18
        response = client_rpt04.get(f'/api/reports/export/{running_job.id}/')
        assert 'progress_pct' in response.data
        assert 'status' in response.data

class TestExportSecurity:
    """SEC-01..05"""
    def test_sec01_no_smtp_llamado(client_rpt04, valid_export_payload, mock_smtp):
        # CA-15: CNST-001 — no email externo
        client_rpt04.post('/api/reports/export/', valid_export_payload, format='json')
        mock_smtp.assert_not_called()
```

### Implementación requerida

- Verificar si `ExportJob` existente tiene todos los campos del corpus
  (status: queued/running/done/failed/expired/cancelled, progress_pct, file_url,
   file_url_expires_at, row_count, byte_count, error_code)
- `ExportView` (POST/GET `/api/reports/export/`)
- `ExportDetailView` (GET/DELETE `/api/reports/export/{id}/`)
- `ExportWorker.process(job_id)` — background task (Celery o RQ)
- `FormatWriter` con strategies CSV, XLSX, PDF
- `StorageGateway` — upload + signed URL (S3/MinIO/local)
- `JobLimiter.count_active(user_id)` — max 5 jobs por usuario
- MailboxService notify al completar (CNST-001/002)
- Re-check de permiso al ejecutar (P-64)
- AuditEvent `REPORT_EXPORT_QUEUED` + `REPORT_EXPORT_COMPLETED`/`FAILED`

----

## GRUPO C — UC_ALR_03: Reconocer Alerta

**Endpoint:** `POST /api/alerts/{id}/acknowledge/` + `POST /api/alerts/bulk-acknowledge/`
**Función:** `ALR-007` (`acknowledge_alert`)
**Dependencia:** UC_ALR_02 (Grupo B)
**Tests:** `tests/unit/fase3/test_uc_alr_03_acknowledge.py`

```python
class TestAcknowledgeValidation:
    """UT-01"""
    def test_ut01_note_mayor_500_chars_rechazado():
        with pytest.raises(ValidationError):
            AlertAckService.validate_note('X' * 501)

class TestAcknowledgeEndpoints:
    """IT-01..09, SEC-01"""

    def test_it01_ack_basico_cambia_state_a_acknowledged(client_alr07, firing_alert):
        # CA-01
        response = client_alr07.post(
            f'/api/alerts/{firing_alert.id}/acknowledge/',
            {'note': 'Revisado.'},
            format='json',
        )
        assert response.status_code == 200
        firing_alert.refresh_from_db()
        assert firing_alert.state == Alert.STATE_ACKNOWLEDGED

    def test_it03_cross_segmento_retorna_403(client_alr07_seg_a, alert_seg_b):
        # CA-03
        response = client_alr07_seg_a.post(
            f'/api/alerts/{alert_seg_b.id}/acknowledge/',
            {'note': 'Test'},
            format='json',
        )
        assert response.status_code == 403

    def test_it04_ya_ack_retorna_409(client_alr07, acked_alert):
        # CA-04: idempotencia
        response = client_alr07.post(
            f'/api/alerts/{acked_alert.id}/acknowledge/',
            {'note': 'De nuevo'},
            format='json',
        )
        assert response.status_code == 409

    def test_it06_audit_emitido(client_alr07, firing_alert, audit_listener):
        # CA-06
        client_alr07.post(
            f'/api/alerts/{firing_alert.id}/acknowledge/',
            {'note': 'OK'},
            format='json',
        )
        assert audit_listener.has('ALERT_ACKNOWLEDGED')

    def test_it09_audit_fail_rollback(client_alr07, firing_alert, mock_audit_fail):
        # CA-10: atomicidad — si audit falla, alert.state no cambia
        with pytest.raises(Exception):
            client_alr07.post(
                f'/api/alerts/{firing_alert.id}/acknowledge/',
                {'note': 'Fallará'},
                format='json',
            )
        firing_alert.refresh_from_db()
        assert firing_alert.state == Alert.STATE_FIRING
```

----

## Criterios de DONE — FASE 3

1. 100% de CAs documentados en cada `Parte 9` tienen test
2. `required_function` en todas las views usa código canónico `MOD-NNN`
3. `permission_classes` explícito en cada view (CNST-010)
4. AuditEvent emitido en operaciones de escritura:
   - UC_ALR_01: `ALERT_RULE_CREATED/UPDATED/DELETED/PAUSED/RESUMED`
   - UC_ALR_03: `ALERT_ACKNOWLEDGED`
   - UC_PIP_04: `PIPELINE_RETRY_REQUESTED`
   - UC_RPT_04: `REPORT_EXPORT_QUEUED/COMPLETED/FAILED`
5. Sin email externo (CNST-001) — `SMTP` no llamado (UC_RPT_04 SEC-01)
6. BR-009: sin DELETE físico en `AlertRule` (CA-07 verifica CASCADE, no DELETE)
7. PIIScanner aplicado en UC_PIP_02, UC_LOG_01, UC_LOG_02, UC_RPT_04
8. Cache implementado en UC_PIP_03 (TTL 30s) y UC_RPT_03 (TTL adaptativo)
9. Hallazgos documentados en `docs/architecture/HALLAZGOS-FASE3-TDD-*.md`

----

## Tabla de estimaciones y dependencias

| UC | Días | Dependencia interna | Commit esperado |
|---|---|---|---|
| PREREQUISITOS | 0.5 | — | commit-pre |
| UC_PIP_02 | 2 | — | |
| UC_PIP_03 | 2 | — | |
| UC_ALR_01 | 3 | — | |
| UC_LOG_01 | 2 | — | |
| UC_LOG_02 | 1 | — | |
| UC_RPT_02 | 0.5 | — | (stub) |
| UC_RPT_03 | 4 | — | |
| UC_PIP_04 | 2 | UC_PIP_02 | |
| UC_ALR_02 | 2 | UC_ALR_01 | |
| UC_RPT_04 | 6 | UC_RPT_03 | |
| UC_ALR_03 | 2 | UC_ALR_02 | |
| **Total** | **27** | | |
