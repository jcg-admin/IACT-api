# 📊 Dashboard App - Sistema de Dashboards Configurables

Sistema completo de dashboards personalizables para visualización de métricas y datos del call center.

## 📋 Índice

- [Características](#características)
- [Modelos](#modelos)
- [API REST](#api-rest)
- [Servicios](#servicios)
- [Permisos](#permisos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Tests](#tests)

---

## ✨ Características

- ✅ **Dashboards personalizables** por usuario
- ✅ **8 tipos de widgets** predefinidos
- ✅ **Filtros guardados** reutilizables
- ✅ **Sistema de permisos** RBAC completo
- ✅ **Cache de widgets** para mejor rendimiento
- ✅ **Import/Export** de configuraciones
- ✅ **Signals automáticos** para dashboard default
- ✅ **API REST completa** con Django REST Framework
- ✅ **Admin personalizado** con Django Admin
- ✅ **68 tests** unitarios y de integración

---

## 📦 Modelos

### DashboardConfig

Dashboard personalizable del usuario.

**Campos principales**:
- `user` - Propietario del dashboard
- `config_name` - Nombre del dashboard
- `description` - Descripción opcional
- `layout_config` - Configuración de layout (JSON)
- `is_default` - Dashboard por defecto del usuario
- `is_public` - Visible para otros usuarios

**Relaciones**:
- `widgets` - Relación 1:N con WidgetConfig

### WidgetConfig

Widget individual dentro de un dashboard.

**Tipos de widgets**:
1. `METRICS_SUMMARY` - Resumen de métricas
2. `CALLS_CHART` - Gráfico de llamadas
3. `TRANSFERS_CHART` - Gráfico de transferencias
4. `RESPONSE_TIME_CHART` - Tiempos de respuesta
5. `ABANDONMENT_CHART` - Gráfico de abandonos
6. `RECENT_CALLS_TABLE` - Tabla de llamadas recientes
7. `TOP_DIDS_TABLE` - Tabla de DIDs principales
8. `CUSTOM` - Widget personalizado

**Campos principales**:
- `dashboard` - Dashboard padre
- `widget_type` - Tipo de widget
- `widget_name` - Nombre del widget
- `position_x`, `position_y` - Posición en el grid
- `width`, `height` - Dimensiones
- `config_data` - Configuración específica (JSON)
- `refresh_interval_seconds` - Intervalo de actualización

### SavedFilter

Filtro guardado reutilizable.

**Tipos de filtros**:
- `call` - Filtro de llamadas
- `transfer` - Filtro de transferencias
- `custom` - Filtro personalizado

**Campos principales**:
- `user` - Propietario del filtro
- `filter_name` - Nombre del filtro
- `filter_type` - Tipo de filtro
- `filter_config` - Configuración del filtro (JSON)
- `is_public` - Visible para otros usuarios

### UserDashboardPreference

Preferencias de usuario para dashboards.

**Campos principales**:
- `user` - Usuario (OneToOne)
- `default_dashboard` - Dashboard por defecto
- `theme` - Tema (light/dark)
- `refresh_enabled` - Auto-refresh activado
- `refresh_interval_seconds` - Intervalo de refresh
- `show_notifications` - Mostrar notificaciones
- `preferences` - Configuración adicional (JSON)

---

## 🔌 API REST

### Base URL

```
/api/v1/dashboard/
```

### Endpoints - Dashboards

```
GET    /api/v1/dashboard/dashboards/                   # Listar dashboards
POST   /api/v1/dashboard/dashboards/                   # Crear dashboard
GET    /api/v1/dashboard/dashboards/{id}/              # Detalle de dashboard
PUT    /api/v1/dashboard/dashboards/{id}/              # Actualizar dashboard
PATCH  /api/v1/dashboard/dashboards/{id}/              # Actualizar parcial
DELETE /api/v1/dashboard/dashboards/{id}/              # Eliminar dashboard

# Actions custom
POST   /api/v1/dashboard/dashboards/{id}/set_default/  # Marcar como default
POST   /api/v1/dashboard/dashboards/{id}/clone/        # Clonar dashboard
GET    /api/v1/dashboard/dashboards/{id}/export/       # Exportar configuración
POST   /api/v1/dashboard/dashboards/import/            # Importar configuración
```

### Endpoints - Widgets

```
GET    /api/v1/dashboard/widgets/                # Listar widgets
POST   /api/v1/dashboard/widgets/                # Crear widget
GET    /api/v1/dashboard/widgets/{id}/           # Detalle de widget
PUT    /api/v1/dashboard/widgets/{id}/           # Actualizar widget
PATCH  /api/v1/dashboard/widgets/{id}/           # Actualizar parcial
DELETE /api/v1/dashboard/widgets/{id}/           # Eliminar widget

# Actions custom
GET    /api/v1/dashboard/widgets/{id}/data/      # Obtener datos calculados
POST   /api/v1/dashboard/widgets/{id}/refresh_cache/ # Refrescar cache
```

### Endpoints - Filtros

```
GET    /api/v1/dashboard/filters/           # Listar filtros
POST   /api/v1/dashboard/filters/           # Crear filtro
GET    /api/v1/dashboard/filters/{id}/      # Detalle de filtro
PUT    /api/v1/dashboard/filters/{id}/      # Actualizar filtro
DELETE /api/v1/dashboard/filters/{id}/      # Eliminar filtro

# Actions custom
POST   /api/v1/dashboard/filters/{id}/apply/ # Aplicar filtro
```

### Endpoints - Preferencias

```
GET    /api/v1/dashboard/preferences/        # Listar preferencias (admin)
GET    /api/v1/dashboard/preferences/me/     # Obtener mis preferencias
PUT    /api/v1/dashboard/preferences/me/     # Actualizar mis preferencias
PATCH  /api/v1/dashboard/preferences/me/     # Actualizar parcial
```

### Ejemplos de Uso

**Crear un dashboard**:

```bash
curl -X POST http://localhost:8000/api/v1/dashboard/dashboards/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "config_name": "Mi Dashboard",
    "description": "Dashboard principal",
    "layout_config": {"columns": 12, "rowHeight": 100},
    "is_public": false
  }'
```

**Crear un widget**:

```bash
curl -X POST http://localhost:8000/api/v1/dashboard/widgets/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard": 1,
    "widget_type": "METRICS_SUMMARY",
    "widget_name": "Resumen General",
    "position_x": 0,
    "position_y": 0,
    "width": 12,
    "height": 4,
    "config_data": {"metrics": ["total_calls", "answered_calls"]}
  }'
```

**Obtener datos de un widget**:

```bash
curl -X GET "http://localhost:8000/api/v1/dashboard/widgets/1/data/?date_from=2025-01-01&date_to=2025-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## ⚙️ Servicios

### FilterService

Servicio para aplicar y validar filtros.

**Métodos**:
- `apply_filter_to_queryset(queryset, filter_config)` - Aplica filtros a un queryset
- `validate_filter_config(filter_config)` - Valida configuración de filtro
- `parse_date_range(date_range)` - Parsea rangos de fechas predefinidos

**Rangos de fechas soportados**:
- `today` - Hoy
- `yesterday` - Ayer
- `last_7_days` - Últimos 7 días
- `last_30_days` - Últimos 30 días
- `this_week` - Esta semana
- `this_month` - Este mes

### DashboardService

Servicio para operaciones sobre dashboards.

**Métodos**:
- `create_default_dashboard(user)` - Crea dashboard por defecto
- `clone_dashboard(dashboard_id, target_user)` - Clona un dashboard
- `set_as_default(dashboard_id, user)` - Marca como default
- `export_config(dashboard_id)` - Exporta configuración a JSON
- `import_config(config_data, user)` - Importa configuración desde JSON
- `delete_dashboard(dashboard_id, user)` - Elimina dashboard (soft delete)

### WidgetService

Servicio para operaciones sobre widgets.

**Métodos**:
- `get_widget_data(widget_id, date_range, use_cache)` - Obtiene datos del widget
- `calculate_metrics_summary(widget, date_range)` - Calcula métricas resumidas
- `calculate_calls_chart_data(widget, date_range)` - Datos de gráfico de llamadas
- `calculate_transfers_chart_data(widget, date_range)` - Datos de transferencias
- `calculate_response_time_chart_data(widget, date_range)` - Tiempos de respuesta
- `calculate_abandonment_chart_data(widget, date_range)` - Datos de abandonos
- `calculate_recent_calls_table_data(widget, date_range)` - Llamadas recientes
- `calculate_top_dids_table_data(widget, date_range)` - DIDs principales
- `refresh_widget_cache(widget_id)` - Invalida cache del widget

---

## 🔐 Permisos

### Sistema RBAC

El sistema implementa control de acceso basado en roles (RBAC).

**Roles**:
- **Owner** - Propietario del recurso
- **Admin** - Administrador del sistema
- **Other** - Otro usuario autenticado
- **Anonymous** - Usuario no autenticado

### Funciones de Permisos

**Dashboard**:
- `can_view_dashboard(user, dashboard)` - Puede ver el dashboard
- `can_edit_dashboard(user, dashboard)` - Puede editar el dashboard
- `can_delete_dashboard(user, dashboard)` - Puede eliminar el dashboard
- `can_create_dashboard(user)` - Puede crear dashboards

**Widget**:
- `can_view_widget(user, widget)` - Puede ver el widget
- `can_edit_widget(user, widget)` - Puede editar el widget
- `can_delete_widget(user, widget)` - Puede eliminar el widget

**Filter**:
- `can_view_filter(user, saved_filter)` - Puede ver el filtro
- `can_edit_filter(user, saved_filter)` - Puede editar el filtro

### Decoradores RBAC (para FBV)

```python
from apps.dashboard.rbac import (
    require_dashboard_owner,
    require_dashboard_view,
    require_widget_owner
)

@require_dashboard_owner
def update_dashboard(request, dashboard_id):
    dashboard = request.dashboard  # Inyectado por el decorador
    # Solo ejecuta si usuario es propietario
    ...

@require_dashboard_view
def view_dashboard(request, dashboard_id):
    dashboard = request.dashboard
    # Ejecuta si usuario puede ver (propietario, público, admin)
    ...
```

### Clases de Permisos DRF

- `IsDashboardOwnerOrReadOnly` - GET para todos, modificación solo owner/admin
- `IsWidgetOwnerOrReadOnly` - Hereda permisos del dashboard padre
- `IsFilterOwnerOrReadOnly` - GET para todos, modificación solo owner/admin
- `IsPreferenceOwner` - Solo puede acceder a sus propias preferencias

---

## 🚀 Instalación

### 1. La app ya está instalada en `INSTALLED_APPS`

```python
# config/settings/base.py
INSTALLED_APPS = [
    ...
    'apps.dashboard',
    ...
]
```

### 2. Aplicar migraciones

```bash
python manage.py migrate
```

### 3. Crear superusuario (si no existe)

```bash
python manage.py createsuperuser
```

### 4. El dashboard se crea automáticamente al crear usuarios

Gracias al signal `create_default_dashboard_for_new_user`, cada nuevo usuario obtiene automáticamente:
- Un dashboard por defecto
- 3 widgets predefinidos (Metrics Summary, Calls Chart, Transfers Chart)
- Preferencias de usuario inicializadas

---

## 💡 Uso

### Desde Django Admin

1. Acceder a `/admin/`
2. Navegar a **Dashboard** → **Dashboards**
3. Crear/editar dashboards
4. Agregar widgets inline
5. Marcar como default o público usando acciones

### Desde API REST

Ver sección [API REST](#api-rest) para ejemplos de uso.

### Desde Código Python

```python
from apps.dashboard.services import DashboardService, WidgetService
from apps.dashboard.models import DashboardConfig

# Crear dashboard por defecto para un usuario
dashboard = DashboardService.create_default_dashboard(user)

# Clonar dashboard
cloned = DashboardService.clone_dashboard(dashboard.id, other_user)

# Obtener datos de widget
widget = dashboard.widgets.first()
data = WidgetService.get_widget_data(
    widget.id,
    date_range=('2025-01-01', '2025-01-31'),
    use_cache=True
)

# Exportar/Importar configuración
config = DashboardService.export_config(dashboard.id)
imported = DashboardService.import_config(config, user)
```

---

## 🧪 Tests

### Ejecutar todos los tests

```bash
python manage.py test apps.dashboard.tests
```

### Ejecutar tests específicos

```bash
# Tests de services
python manage.py test apps.dashboard.tests.test_filter_service
python manage.py test apps.dashboard.tests.test_dashboard_service

# Tests de signals
python manage.py test apps.dashboard.tests.test_signals

# Tests de permissions
python manage.py test apps.dashboard.tests.test_permissions

# Tests de viewsets
python manage.py test apps.dashboard.tests.test_viewsets
```

### Coverage

```bash
# Generar reporte de cobertura
coverage run --source='apps.dashboard' manage.py test apps.dashboard.tests
coverage report
coverage html

# Ver reporte HTML
open htmlcov/index.html
```

### Estadísticas de Tests

- **68 tests** implementados
- **5 archivos** de tests
- **Cobertura**: Services, Signals, Permissions, ViewSets
- **Tipos**: Unitarios, Integración, API

---

## 📚 Arquitectura

```
apps/dashboard/
├── models.py              # 4 modelos (551 líneas)
├── services/              # 3 services (1,273 líneas)
│   ├── filter_service.py
│   ├── dashboard_service.py
│   └── widget_service.py
├── serializers.py         # 12 serializers (620 líneas)
├── viewsets.py            # 4 ViewSets (662 líneas)
├── permissions.py         # 10 funciones + 4 clases DRF (420 líneas)
├── rbac.py                # 7 decoradores + 6 helpers (547 líneas)
├── signals.py             # 3 signals (141 líneas)
├── admin.py               # 4 admin classes (400 líneas)
├── urls.py                # Router DRF (38 líneas)
└── tests/                 # 68 tests (1,393 líneas)
    ├── test_filter_service.py
    ├── test_dashboard_service.py
    ├── test_signals.py
    ├── test_permissions.py
    └── test_viewsets.py
```

---

## 📝 Notas de Desarrollo

### Signals Automáticos

1. **create_default_dashboard_for_new_user**: Se dispara al crear un usuario, crea dashboard y widgets por defecto
2. **ensure_only_one_default_dashboard**: Asegura que solo un dashboard sea default por usuario
3. **invalidate_widget_cache_on_update**: Invalida cache al actualizar un widget

### Cache de Widgets

Los widgets utilizan cache de Django para mejorar el rendimiento:

- **Key pattern**: `widget_data_{widget_id}`
- **Timeout**: Configurable por widget (60-3600 segundos)
- **Invalidación**: Automática al actualizar widget

### Soft Delete

Los modelos DashboardConfig y SavedFilter implementan soft delete:

- Campo `deleted_at` para marcar como eliminado
- Los queries filtran automáticamente los eliminados
- Se puede recuperar estableciendo `deleted_at=None`

---

## 🤝 Contribución

Para contribuir al desarrollo de esta app:

1. Seguir las convenciones de código del proyecto
2. Escribir tests para nuevas funcionalidades
3. Documentar cambios en este README
4. Actualizar versión en `__init__.py`

---

## 📄 Licencia

Propiedad de IACT Call Center System.

---

## ✅ Checklist de Implementación

- [x] Modelos implementados
- [x] Services implementados
- [x] Signals implementados
- [x] Serializers implementados
- [x] Permissions implementados
- [x] ViewSets implementados
- [x] RBAC implementado
- [x] Tests implementados
- [x] Admin implementado
- [x] URLs integradas
- [x] Documentación completa

**Estado**: ✅ **COMPLETADO** (100%)

---

**Total de líneas**: ~6,000+ líneas de código
**Total de tests**: 68 tests
**Cobertura**: Completa (services, signals, permissions, viewsets)
