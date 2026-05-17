# Análisis — Convención de Idiomas en IACT-api

**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Alcance:** 423 archivos Python, 949 clases, 2232 funciones/métodos
**Método:** Escaneo sistemático de identificadores, comentarios y docstrings

---

## Veredicto

El proyecto **no es consistentemente en inglés**. Tiene tres convenciones
distintas aplicadas en capas diferentes, con una zona de mezcla problemática
en los modelos y vistas del dominio IVR.

---

## Patrón por capa

### Capa 1 — Inglés puro (consistente)

Estas apps siguen inglés en todo: nombres de clases, campos de modelo,
métodos y serializers.

| App | Clases | Campos de modelo |
|---|---|---|
| `access` | `Module`, `Function`, `UserPermission`, `AccessGroup` | `name`, `code`, `icon`, `order`, `parent` |
| `alerts` | `InternalMessage`, `AlertConfiguration`, `AlertSubscription` | `sender`, `subject`, `body`, `priority` |
| `audit` | `AuditLog` | `user`, `action`, `resource`, `result`, `timestamp` |
| `users` | `User`, `AuthenticationService`, `ProfileService` | `avatar`, `phone`, `is_active` |
| `authentication` | `CustomTokenObtainPairSerializer` | todos en inglés |
| `reports` | `Report`, `ExportJob`, `ScheduledReport`, `SavedView` | `name`, `report_type`, `created_by` |
| `dashboard` | `DashboardService`, `WidgetService`, `FilterService` | todos en inglés |

**Servicios** — 100% inglés en toda la capa de servicios:
```python
# users:
login(), logout(), create_user(), get_user_by_id(), activate_user()

# pipeline (servicios de negocio):
create_center(), update_center(), get_records_by_date_range()

# alerts:
send_message(), subscribe(), unsubscribe(), mark_as_read()
```

---

### Capa 2 — Mezcla sistemática: dominio IVR en español, framework en inglés

Esta es la zona problemática. El dominio IVR (call center) usa términos
en español como base del nombre, con el sufijo técnico en inglés.

**Clases en `ivr_views.py`:**
```python
# Patrón: [término-dominio-ES] + [sufijo-framework-EN]
ClientesReportView           # clientes (ES) + ReportView (EN)
CentrosTransferenciaView     # centros transferencia (ES) + View (EN)
LlamadasAbandonadasView      # llamadas abandonadas (ES) + View (EN)
CentrosXSegmentoView         # centros × segmento (ES) + View (EN)
MenuRedirigidosView          # menu redirigidos (ES) + View (EN)
```

**Contraste con `ivr_services.py` — el mismo dominio, todo en inglés:**
```python
# El servicio TRADUCE los conceptos al inglés:
get_clients()                # ← clientes → clients
get_transfer_centers()       # ← centros transferencia → transfer_centers
get_abandoned_calls()        # ← llamadas abandonadas → abandoned_calls
get_centers_by_segment()     # ← centros × segmento → centers_by_segment
get_redirected_menus()       # ← menus redirigidos → redirected_menus
```

Esta inconsistencia entre capas es el problema central: `ivr_views.py`
y `ivr_services.py` representan el mismo dominio con convenciones opuestas.

**Función auxiliar en `pipeline/views.py`:**
```python
def _build_resumen_salud(runs):   # ← resumen_salud en español, en código de producción
```

---

### Capa 3 — Modelos con campos en español (mezcla incoherente)

`pipeline/models.py` mezcla inglés y español **en el mismo modelo**:

```python
class Center(models.Model):
    nombre      = models.CharField(...)   # ← español
    codigo      = models.CharField(...)   # ← español
    descripcion = models.TextField(...)   # ← español
    activo      = models.BooleanField()   # ← español
    created_at  = models.DateTimeField()  # ← inglés
    updated_at  = models.DateTimeField()  # ← inglés

class CallRecord(models.Model):
    fecha                  = models.CharField(...)   # ← español
    telefono               = models.CharField(...)   # ← español
    servicio_800           = models.CharField(...)   # ← español
    total_llamadas         = models.IntegerField()   # ← español
    llamadas_contestadas   = models.IntegerField()   # ← español
    llamadas_abandonadas   = models.IntegerField()   # ← español
    duracion_total_segundos= models.IntegerField()   # ← español
    started_at             = models.DateTimeField()  # ← inglés
    completed_at           = models.DateTimeField()  # ← inglés
    error_message          = models.TextField()      # ← inglés
```

No hay una regla que explique por qué `nombre` es español pero `created_at`
es inglés en el mismo modelo. Son dos convenciones mezcladas sin criterio.

---

### Capa 4 — Comentarios y docstrings: casi 100% español

```
Archivos con SOLO comentarios en español:  101 / 167 (60%)
Archivos MIXTOS (ambos idiomas):            16 / 167 (10%)
Archivos con SOLO comentarios en inglés:     4 / 167 (2%)
Archivos sin comentarios:                   46 / 167 (27%)
```

El código está documentado internamente en español. Las docstrings de
clases, métodos y funciones están en español. Esto es consistente con
el contexto del proyecto (equipo hispanohablante).

---

## Mapa de consistencia

| Capa | Idioma | Consistencia |
|---|---|---|
| Nombres de clases (apps de infraestructura) | Inglés | Alta |
| Nombres de clases (vistas IVR) | Mixto ES+EN | Baja |
| Nombres de métodos en servicios | Inglés | Alta |
| Campos de modelo (apps de infraestructura) | Inglés | Alta |
| Campos de modelo (pipeline — dominio IVR) | Mezcla ES/EN | Muy baja |
| Serializers | Inglés (mayoría) | Media |
| Comentarios y docstrings | Español | Alta |
| Nombres de funciones helper internas | Mixto | Baja |

---

## La raíz del problema

Los modelos e identificadores del dominio IVR (`Center`, `CallRecord`,
`CallNote`, `Service`) mapean directamente contra las tablas `base_ivr_*`
de MariaDB, que tienen nombres de columna en español (`total_llamadas`,
`nombre`, `fecha`, `segmento`). Los campos de Django siguen el nombre de
la columna de BD — de ahí el español en esa capa.

La pregunta de diseño que nunca se resolvió explícitamente es: ¿el modelo
Django usa el nombre de la columna de BD (español) o una traducción propia
(inglés)?

Las apps de infraestructura (`access`, `alerts`, `audit`) no tienen este
problema porque sus tablas las controla Django directamente — los nombres
de columna son lo que el equipo decidió, y decidieron inglés.

---

## Recomendación

Dos opciones coherentes — elegir una y aplicarla en todo el proyecto:

**Opción A — Todo inglés (incluyendo vistas y modelos del dominio IVR):**
```python
# ivr_views.py
class ClientsReportView(APIView): ...         # no ClientesReportView
class TransferCentersView(APIView): ...       # no CentrosTransferenciaView
class AbandonedCallsView(APIView): ...        # no LlamadasAbandonadasView

# pipeline/models.py
class CallRecord(models.Model):
    date               = models.CharField(...)   # no fecha
    phone              = models.CharField(...)   # no telefono
    total_calls        = models.IntegerField()   # no total_llamadas
    answered_calls     = models.IntegerField()   # no llamadas_contestadas
    abandoned_calls    = models.IntegerField()   # no llamadas_abandonadas
```

**Opción B — Todo español en el dominio IVR (consistente con los SPs y la BD):**
```python
# ivr_services.py
def get_clientes(trimestre: str) -> list[dict]: ...
def get_centros_transferencia(trimestre: str, segmento: str) -> list[dict]: ...
def get_llamadas_abandonadas(trimestre: str, segmento: str) -> list[dict]: ...

# ivr_views.py — ya están en español, mantener
class ClientesReportView(APIView): ...
```

**La Opción A es la recomendada** porque:
1. Django, DRF y drf-spectacular usan inglés en su API pública
2. Los clientes de la API REST reciben JSON — los nombres de campo son
   parte de la interfaz pública y conviene que sean en inglés
3. `ivr_services.py` ya usa inglés — es la capa más coherente del proyecto
4. `access`, `alerts`, `audit` ya están en inglés — uniformidad total

La Opción B requeriría cambiar más código (ivr_services.py, pipeline/models.py)
pero sería igualmente coherente si el equipo prefiere mantener los términos
del dominio en español.

Lo que no es coherente es el estado actual: la mitad del dominio IVR en
español, la otra mitad en inglés, sin un criterio documentado.
