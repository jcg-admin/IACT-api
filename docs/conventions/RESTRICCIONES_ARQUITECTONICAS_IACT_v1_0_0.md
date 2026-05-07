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

## RA-011 — Idioma por capa: inglés en Python, español en base de datos

Cada capa usa un idioma de forma consistente. No se mezclan idiomas
dentro de la misma capa.

### Capa Python (IACT-api)

Todos los identificadores de Python son en inglés sin excepción:
clases, métodos, atributos de modelos Django, variables locales,
parámetros de función, constantes y nombres de serializers.

```python
# Correcto
class SeparationRule(SoftDeleteModel):
    justification = models.TextField()
    status        = models.CharField(...)
    created_by    = models.ForeignKey(...)
    valid_from    = models.DateTimeField()
    valid_until   = models.DateTimeField()

# Prohibido
class SeparationRule(SoftDeleteModel):
    justificacion = models.TextField()   # español en modelo Django
    estado        = models.CharField()   # español en modelo Django
```

### Capa MariaDB (IACT-db)

Los nombres de tablas, columnas, procedimientos almacenados y
funciones pueden estar en español porque:

1. Los operadores de base de datos trabajan directamente con SQL
   en el idioma del negocio.
2. Los SPs (`sp_rpt_llamadas_abandonadas`, `sp_etl_base_detalle`)
   son términos del dominio comprensibles para los administradores
   de la base de datos sin conocer Python.
3. Renombrar columnas en tablas con datos reales introduce riesgo
   operacional sin ganancia funcional para el usuario final.

```sql
-- Aceptable — capa de base de datos internamente consistente en español
CREATE TABLE base_ivr_detalle (
    trimestre           VARCHAR(10),
    segmento            VARCHAR(20),
    centro_transferencia VARCHAR(100),
    total_llamadas      INT
);
```

### Capa de traducción (services.py)

La capa de servicio en Python es la responsable del mapeo entre
los dos idiomas. Los nombres de función son inglés; los strings
que se pasan a MariaDB son los nombres reales del contrato de DB.

```python
# Correcto: nombre de función en inglés, SP en español como string opaco
def get_abandoned_calls(quarter: str, segment: str = 'all') -> list[dict]:
    return _call_sp('sp_rpt_llamadas_abandonadas', [quarter, segment])

# Los parámetros de columna también son strings opacos del contrato de DB
cursor.execute("SELECT trimestre, segmento FROM base_ivr_detalle")
```

Los strings que referencian objetos de MariaDB (`'sp_rpt_clientes'`,
`'trimestre'`, `'job_execution_log'`) son parte del contrato con la
base de datos — son valores literales, no identificadores de Python,
y no están sujetos a la regla de inglés.

### Resumen

| Elemento | Idioma | Razón |
|---|---|---|
| Clases, métodos, atributos Python | Inglés | Capa de aplicación |
| Variables locales Python | Inglés | Capa de aplicación |
| Tablas y columnas MariaDB | Español | Capa de datos, dominio de negocio |
| SPs y funciones MariaDB | Español | Capa de datos, dominio de negocio |
| Strings de contrato DB en Python | Español | Son valores, no identificadores |
| Comentarios y docstrings | Español o inglés | No son identificadores |
