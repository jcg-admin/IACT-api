# Restricciones arquitectonicas — IACT API

**Version:** 1.0.0
**Aplica a:** callcentersite/

---

## RA-001 — Sin logica de negocio en Views

Las views solo coordinan: reciben la request, delegan a un servicio
o modelo, y retornan la response. Sin queries directas en views.

```python
# Prohibido en views.py
def my_view(request):
    users = User.objects.filter(is_active=True).select_related(...)

# Correcto
def my_view(request):
    users = UserService.get_active_users()
```

Excepcion: views que leen MariaDB via connections['ivr'].cursor()
son aceptadas porque el "servicio" es la propia conexion raw.

## RA-002 — Sin queries en Serializers

Los serializers no ejecutan queries adicionales salvo a traves
de `select_related` o `prefetch_related` declarados en el ViewSet.

## RA-003 — Sin imports circulares entre apps

El orden de dependencia permitido:
  utils → core → (authentication, users, access, audit, alerts, pipeline, reports, logs)
Ninguna app de la segunda capa puede importar de otra de la misma capa.

## RA-004 — Sin nombres de patrones de diseno como nombre de clase

Ver CLEAN_CODE_NAMING_PRINCIPLES_v3_0_1.md.

## RA-005 — Sin acronimos de seguridad como nombre de clase

Ver CLEAN_CODE_NAMING_PRINCIPLES_v3_0_1.md.

## RA-006 — connections['ivr'] solo en Capa 1

Las consultas a MariaDB via connections['ivr'].cursor() solo ocurren en:
  - apps/pipeline/views.py
  - apps/reports/ivr_services.py
  - apps/logs/views.py (ETLLogTailView)

Ningun model Django tiene managed=False apuntando a ivr_legacy.

## RA-007 — ivr_legacy es READ-ONLY desde Django

El DatabaseRouter prohibe writes a 'ivr'. Los SPs de MariaDB
que modifican datos (sp_etl_*) son llamados via callproc() exclusivamente.
No hay INSERT/UPDATE/DELETE desde Python a tablas de ivr_legacy.

## RA-008 — Todo endpoint nuevo tiene @extend_schema de drf_spectacular

Ningun endpoint nuevo se agrega sin su decorador @extend_schema
con al menos: summary, tags, responses.

## RA-009 — Acciones de acceso emiten evento de auditoria

Cualquier accion que modifique permisos, grupos o roles de un usuario
debe emitir un evento en AuditLog. Esto incluye:
  - asignar/revocar funcion
  - asignar/revocar grupo
  - aprobar/revocar permiso excepcional
  - crear/desactivar SeparationRule

## RA-010 — Migraciones no renombran tablas existentes sin decision explicita

Si un modelo cambia de nombre (ej: SodRule → SeparationRule), la migracion
crea la nueva tabla y marca la vieja como deprecated. El renombrado fisico
de tabla en produccion es una decision de operaciones, no automatica.
