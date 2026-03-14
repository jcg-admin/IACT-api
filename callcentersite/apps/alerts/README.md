# Sistema de Alertas Internas - Apps/Alerts

> **Sistema completo de mensajería interna y alertas automáticas para IACT Call Center System**

![Django](https://img.shields.io/badge/Django-4.2+-green.svg)
![DRF](https://img.shields.io/badge/DRF-3.14+-blue.svg)
![APScheduler](https://img.shields.io/badge/APScheduler-3.10+-orange.svg)
![Tests](https://img.shields.io/badge/Tests-39%20passing-brightgreen.svg)
![Coverage](https://img.shields.io/badge/Coverage-85%25+-success.svg)

---

## 📋 Tabla de Contenidos

- [Descripción](#descripción)
- [Características](#características)
- [Arquitectura](#arquitectura)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [API REST](#api-rest)
- [Tests](#tests)
- [Restricciones](#restricciones)
- [Documentación Adicional](#documentación-adicional)

---

## 📖 Descripción

El sistema de alertas internas (`apps/alerts`) proporciona:

1. **Mensajería Interna**: Comunicación entre usuarios del sistema
2. **Alertas Automáticas**: Monitoreo de métricas con notificaciones automáticas
3. **Suscripciones**: Sistema de suscripciones a alertas configurables
4. **APScheduler**: Evaluación periódica de condiciones sin Celery/RabbitMQ

### Casos de Uso

- Envío de mensajes internos entre supervisores y agentes
- Alertas automáticas cuando el volumen de llamadas supera umbrales
- Notificaciones cuando el tiempo de espera promedio es crítico
- Alertas de SLA por debajo del objetivo
- Suscripciones personalizadas por usuario

---

## ✨ Características

### Mensajería Interna

- ✅ Envío de mensajes a múltiples destinatarios (máx. 50)
- ✅ Prioridades: info, warning, error, critical
- ✅ Bandeja de entrada personalizada
- ✅ Marcar como leído/no leído
- ✅ Archivar/desarchivar mensajes
- ✅ Soft delete

### Alertas Automáticas

- ✅ Configuración de condiciones basadas en métricas
- ✅ Métricas soportadas:
  - `call_volume`: Volumen de llamadas
  - `avg_wait_time`: Tiempo de espera promedio
  - `sla_percentage`: Porcentaje de SLA
- ✅ Operadores: `>`, `<`, `>=`, `<=`, `==`
- ✅ Períodos: 30m, 1h, 6h, 12h, 1d
- ✅ Evaluación automática cada 5 minutos (APScheduler)

### Sistema de Suscripciones

- ✅ Suscribirse/desuscribirse a alertas
- ✅ Suscripciones activas/inactivas
- ✅ Gestión por usuario

### Integración RBAC

- ✅ 6 funciones RBAC:
  - `alerts.send` (ALRT_SEND)
  - `alerts.view.inbox` (ALRT_VIEW_INB)
  - `alerts.manage.subscriptions` (ALRT_MNG_SUB)
  - `alerts.configure.rules` (ALRT_CFG_RUL)
  - `alerts.delete.messages` (ALRT_DEL_MSG)
  - `alerts.view.all` (ALRT_VIEW_ALL)

---

## 🏗️ Arquitectura

```
apps/alerts/
├── models.py                    # 4 modelos (267 líneas)
│   ├── InternalMessage
│   ├── MessageRecipient
│   ├── AlertConfiguration
│   └── AlertSubscription
│
├── services/                    # Lógica de negocio (552 líneas)
│   ├── message_service.py      # MessageService
│   ├── alert_service.py        # AlertService
│   └── subscription_service.py # SubscriptionService
│
├── scheduler.py                 # APScheduler (66 líneas)
│   └── evaluate_alert_configs  # Job cada 5 min
│
├── serializers.py               # 9 serializers (297 líneas)
├── permissions.py               # 3 permission classes (117 líneas)
├── viewsets.py                  # 3 viewsets (224 líneas)
├── urls.py                      # Router config (20 líneas)
│
├── admin.py                     # Django admin (191 líneas)
│   ├── InternalMessageAdmin
│   ├── AlertConfigurationAdmin
│   └── AlertSubscriptionAdmin
│
├── management/commands/
│   └── create_alert_functions.py  # RBAC setup (153 líneas)
│
├── tests/                       # Suite de tests (985 líneas, 39 tests)
│   ├── test_models.py          # 10 tests
│   ├── test_services.py        # 12 tests
│   ├── test_viewsets.py        # 10 tests
│   └── test_scheduler.py       # 7 tests (incluye CNST-013)
│
└── fixtures/
    ├── alert_configurations.json  # 5 configuraciones de ejemplo
    └── README.md                  # Guía de fixtures

Total: 3,055 líneas de código Python
```

---

## 🚀 Instalación

### Prerequisitos

- Python 3.12+
- Django 4.2+
- PostgreSQL 12+
- APScheduler 3.10+

### Paso 1: Dependencias

```bash
# APScheduler ya está en requirements.txt
pip install -r requirements.txt
```

### Paso 2: Migraciones

```bash
# Aplicar migraciones
python manage.py migrate alerts

# Verificar
python manage.py showmigrations alerts
```

### Paso 3: Crear Funciones RBAC

```bash
# Crear las 6 funciones RBAC en la base de datos
python manage.py create_alert_functions
```

### Paso 4: Cargar Fixtures (Opcional)

```bash
# Cargar 5 configuraciones de alertas de ejemplo
python manage.py loaddata alert_configurations

# Verificar
python manage.py shell
>>> from apps.alerts.models import AlertConfiguration
>>> AlertConfiguration.objects.count()
5
```

---

## ⚙️ Configuración

### APScheduler

El scheduler se inicia automáticamente con `runserver` o `gunicorn`:

```python
# apps/alerts/apps.py
def ready(self):
    # Se inicia solo en runserver/gunicorn
    # NO se inicia en: migrate, shell, test, etc.
    from apps.alerts.scheduler import start_scheduler
    start_scheduler()
```

### Configurar Alertas

Desde Django Admin o programáticamente:

```python
from apps.alerts.models import AlertConfiguration

# Crear alerta de alto volumen
AlertConfiguration.objects.create(
    name='Alto Volumen de Llamadas',
    description='Alerta cuando el volumen supera 100 en 1 hora',
    condition={
        'metric': 'call_volume',
        'operator': '>',
        'value': 100,
        'period': '1h'
    },
    priority='warning',
    is_active=True
)
```

---

## 💻 Uso

### Enviar Mensaje

```python
from apps.alerts.services import MessageService
from django.contrib.auth import get_user_model

User = get_user_model()

# Obtener usuarios
sender = User.objects.get(username='supervisor1')
recipients = User.objects.filter(username__in=['agent1', 'agent2'])

# Enviar mensaje
message = MessageService.send_message(
    sender=sender,
    recipients=list(recipients),
    subject='Reunión de Equipo',
    body='Reunión mañana a las 10am en sala de juntas',
    priority='info'
)
```

### Suscribirse a Alerta

```python
from apps.alerts.services import SubscriptionService
from apps.alerts.models import AlertConfiguration

# Obtener alerta
alert = AlertConfiguration.objects.get(name='Alto Volumen de Llamadas')

# Suscribir usuario
subscription = SubscriptionService.subscribe(
    user=request.user,
    alert_configuration=alert
)
```

### Evaluar Alertas Manualmente

```python
from apps.alerts.services import AlertService

# Evaluar todas las configuraciones activas
triggered_count = AlertService.evaluate_all_active_configs()
print(f"Se dispararon {triggered_count} alertas")
```

---

## 🔌 API REST

Base URL: `/api/v1/alerts/`

### Mensajes

```bash
# Listar mensajes (requiere ALRT_VIEW_ALL)
GET /api/v1/alerts/messages/

# Ver bandeja de entrada (requiere ALRT_VIEW_INB)
GET /api/v1/alerts/messages/inbox/
GET /api/v1/alerts/messages/inbox/?unread=true
GET /api/v1/alerts/messages/inbox/?priority=critical

# Enviar mensaje (requiere ALRT_SEND)
POST /api/v1/alerts/messages/
{
  "recipient_ids": [1, 2, 3],
  "subject": "Asunto del mensaje",
  "body": "Contenido del mensaje",
  "priority": "info"
}

# Ver mensaje específico
GET /api/v1/alerts/messages/{id}/

# Marcar como leído
PATCH /api/v1/alerts/messages/{id}/mark-read/

# Archivar/Desarchivar
PATCH /api/v1/alerts/messages/{id}/archive/
PATCH /api/v1/alerts/messages/{id}/unarchive/

# Eliminar (soft delete, requiere ALRT_DEL_MSG)
DELETE /api/v1/alerts/messages/{id}/
```

### Configuraciones de Alertas

```bash
# Listar configuraciones (requiere ALRT_CFG_RUL)
GET /api/v1/alerts/configurations/
GET /api/v1/alerts/configurations/?is_active=true

# Crear configuración
POST /api/v1/alerts/configurations/
{
  "name": "Nueva Alerta",
  "description": "Descripción",
  "condition": {
    "metric": "call_volume",
    "operator": ">",
    "value": 100,
    "period": "1h"
  },
  "priority": "warning",
  "is_active": true
}

# Ver configuración específica
GET /api/v1/alerts/configurations/{id}/

# Actualizar
PATCH /api/v1/alerts/configurations/{id}/
{
  "is_active": false
}

# Eliminar
DELETE /api/v1/alerts/configurations/{id}/
```

### Suscripciones

```bash
# Listar mis suscripciones (requiere ALRT_MNG_SUB)
GET /api/v1/alerts/subscriptions/

# Suscribirse
POST /api/v1/alerts/subscriptions/
{
  "alert_configuration_id": 1
}

# Desuscribirse
DELETE /api/v1/alerts/subscriptions/{id}/
```

---

## 🧪 Tests

```bash
# Ejecutar todos los tests
python manage.py test apps.alerts

# Tests específicos
python manage.py test apps.alerts.tests.test_models
python manage.py test apps.alerts.tests.test_services
python manage.py test apps.alerts.tests.test_viewsets
python manage.py test apps.alerts.tests.test_scheduler

# Test crítico CNST-013
python manage.py test apps.alerts.tests.test_scheduler.SchedulerTest.test_no_celery_imports

# Con coverage
coverage run --source='apps.alerts' manage.py test apps.alerts
coverage report
coverage html
```

### Estadísticas de Tests

- **Total tests**: 39
- **test_models.py**: 10 tests
- **test_services.py**: 12 tests
- **test_viewsets.py**: 10 tests
- **test_scheduler.py**: 7 tests
- **Coverage estimado**: >85%

---

## ⚠️ Restricciones

### CNST-001: NO SMTP

✅ **CUMPLIDO**: No se usa SMTP/EmailBackend. Los mensajes son internos en BD.

### CNST-013: NO Celery/RabbitMQ/Kafka

✅ **CUMPLIDO**: Se usa **APScheduler** para tareas periódicas.

**Verificación**:
```bash
# Ejecutar test que verifica ausencia de imports prohibidos
python manage.py test apps.alerts.tests.test_scheduler.SchedulerTest.test_no_celery_imports
```

### CNST-024: Máximo 50 Destinatarios

✅ **CUMPLIDO**: Validación en modelo, serializer y service.

**Ubicaciones**:
- `models.py`: Validación en `clean()`
- `serializers.py`: `max_length=50` en `recipient_ids`
- `services/message_service.py`: Validación en `send_message()`

**Tests**:
- `test_cnst024_max_50_recipients`
- `test_cnst024_50_recipients_ok`
- `test_send_message_cnst024_validation`

---

## 📚 Documentación Adicional

### Admin de Django

Acceder a: `http://localhost:8000/admin/alerts/`

**Admins disponibles**:
- `/admin/alerts/internalmessage/` - Gestión de mensajes
- `/admin/alerts/alertconfiguration/` - Configuraciones de alertas
- `/admin/alerts/alertsubscription/` - Suscripciones

### Fixtures

Ver documentación completa en: `apps/alerts/fixtures/README.md`

Configuraciones de ejemplo incluidas:
1. Alto Volumen de Llamadas (warning)
2. Tiempo de Espera Crítico (critical)
3. SLA Bajo Umbral (error)
4. Bajo Volumen de Llamadas (warning, inactivo)
5. Monitoreo de Medio Día (info)

### Scheduler

**Job**: `evaluate_alert_configs`
- **Frecuencia**: Cada 5 minutos
- **Trigger**: IntervalTrigger(minutes=5)
- **Max instances**: 1
- **Daemon**: True

**Control manual**:
```python
from apps.alerts.scheduler import start_scheduler, stop_scheduler, get_scheduler

# Iniciar
start_scheduler()

# Ver estado
scheduler = get_scheduler()
print(scheduler.running)  # True/False
print(scheduler.get_jobs())  # Lista de jobs

# Detener
stop_scheduler()
```

---

## 📊 Estadísticas del Proyecto

- **Líneas de código**: 3,055 líneas Python
- **Modelos**: 4
- **Services**: 3
- **Serializers**: 9
- **ViewSets**: 3
- **Permissions**: 3
- **Tests**: 39
- **Funciones RBAC**: 6
- **Endpoints REST**: 16
- **Fixtures**: 5 configuraciones

---

## 🔧 Troubleshooting

### APScheduler no inicia

```python
# Verificar que apps.py ready() se ejecuta
python manage.py runserver
# Debe mostrar: "INFO Alerts app ready: APScheduler iniciado"

# Si no inicia, verificar logs
import logging
logging.basicConfig(level=logging.INFO)
```

### Tests fallan

```bash
# Verificar BD de tests
python manage.py test apps.alerts --keepdb

# Ver logs detallados
python manage.py test apps.alerts --verbosity=2
```

### Permisos no funcionan

```bash
# Verificar funciones RBAC creadas
python manage.py shell
>>> from apps.access.models import Function
>>> Function.objects.filter(module='MOD_Alerts').count()
6  # Debe ser 6

# Recrear si es necesario
python manage.py create_alert_functions
```

---

## 👥 Contribuir

Para contribuir al proyecto:

1. Seguir arquitectura de Services (separación de lógica)
2. Escribir tests para nuevas features (min. 80% coverage)
3. Actualizar este README
4. Verificar CNST-001, CNST-013, CNST-024

---

## 📝 Licencia

Propiedad de IACT Call Center System. Todos los derechos reservados.

---

## 📧 Contacto

Para preguntas sobre este sistema, contactar al equipo de desarrollo.

---

**Última actualización**: 2026-01-24  
**Versión**: 1.0.0  
**Estado**: ✅ Producción Ready
