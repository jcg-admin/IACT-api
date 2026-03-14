# Fixtures de Alertas

Este directorio contiene datos de ejemplo para el sistema de alertas.

## Archivos

### alert_configurations.json

Contiene 5 configuraciones de alerta de ejemplo:

1. **Alto Volumen de Llamadas** (warning)
   - Métrica: call_volume > 100 en 1h
   - Detecta picos de llamadas

2. **Tiempo de Espera Crítico** (critical)
   - Métrica: avg_wait_time > 300 segundos (5 min) en 30m
   - Alerta crítica de tiempos de espera altos

3. **SLA Bajo Umbral** (error)
   - Métrica: sla_percentage < 85% en 1h
   - Detecta cuando el SLA cae

4. **Bajo Volumen de Llamadas** (warning, INACTIVO)
   - Métrica: call_volume < 10 en 1h
   - Detecta posibles problemas de sistema

5. **Monitoreo de Medio Día** (info)
   - Métrica: call_volume > 50 en 6h
   - Monitoreo general

## Cargar Fixtures

```bash
# Cargar configuraciones de alertas
python manage.py loaddata alert_configurations

# Verificar que se cargaron
python manage.py shell
>>> from apps.alerts.models import AlertConfiguration
>>> AlertConfiguration.objects.all().count()
5
```

## Crear Suscripciones

Después de cargar las configuraciones, puedes crear suscripciones:

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from apps.alerts.models import AlertConfiguration, AlertSubscription

User = get_user_model()

# Obtener usuario
user = User.objects.first()  # o get(username='admin')

# Suscribir a alertas críticas
critical_alerts = AlertConfiguration.objects.filter(priority='critical')
for alert in critical_alerts:
    AlertSubscription.objects.get_or_create(
        user=user,
        alert_configuration=alert,
        defaults={'is_active': True}
    )

print(f"Usuario {user.username} suscrito a {AlertSubscription.objects.filter(user=user).count()} alertas")
```

## Modificar Configuraciones

Las configuraciones se pueden modificar desde el admin de Django:

```
http://localhost:8000/admin/alerts/alertconfiguration/
```

O programáticamente:

```python
from apps.alerts.models import AlertConfiguration

# Cambiar umbral
config = AlertConfiguration.objects.get(name='Alto Volumen de Llamadas')
config.condition['value'] = 150  # Cambiar de 100 a 150
config.save()

# Activar/desactivar
config.is_active = False
config.save()
```

## Probar Alertas

Para probar el sistema de alertas:

```python
from apps.alerts.services import AlertService

# Evaluar todas las configuraciones activas
triggered_count = AlertService.evaluate_all_active_configs()
print(f"Se dispararon {triggered_count} alertas")
```

## Estructura de condition

Todas las configuraciones usan un JSONField `condition` con esta estructura:

```json
{
  "metric": "call_volume|avg_wait_time|sla_percentage",
  "operator": ">|<|>=|<=|==",
  "value": <número>,
  "period": "30m|1h|6h|12h|1d"
}
```

## Limpiar Datos

Para eliminar las configuraciones:

```bash
python manage.py shell
```

```python
from apps.alerts.models import AlertConfiguration
AlertConfiguration.objects.all().delete()
```

O usar soft delete:

```python
from django.utils import timezone
AlertConfiguration.objects.all().update(deleted_at=timezone.now())
```
