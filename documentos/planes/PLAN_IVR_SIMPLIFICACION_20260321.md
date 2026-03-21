# PLAN — Simplificación IVR: tbl_temp_prueba_ivr
## Python solo consume, MariaDB es el dueño del schema

**Versión:** 1.0.0
**Fecha:** 2026-03-21
**Estado:** COMPLETADO
**Fecha de cierre:** 2026-03-21

---

## CONTEXTO

Todo el código Python actual que interactúa con MariaDB IVR será marcado
como **DEUDA TÉCNICA** y comentado. La única integración activa será
que Python consuma (`SELECT`) la tabla `tbl_temp_prueba_ivr`, cuyo schema
y datos son responsabilidad exclusiva de los scripts MariaDB.

---

## INVENTARIO — Código Python a eliminar / marcar como PENDIENTE

### Capa de configuración

| Archivo | Cambio |
|---|---|
| `config/settings/base.py` | DATABASES `'ivr'` → queda pero apunta a `tbl_temp_prueba_ivr` |
| `config/settings/testing.py` | Eliminar comentario PENDIENTE sobre call_logs |
| `config/db_router.py` | Mantener router (sigue siendo necesario para `managed=False`) |

### Capa de dominio IVR (`apps/ivr/`)

| Archivo | Cambio |
|---|---|
| `apps/ivr/models.py` | Eliminar `CallLog` → nuevo modelo `TblTempPruebaIvr` |
| `apps/ivr/migrations/0001_initial.py` | Reemplazar migration (nuevo modelo) |
| `apps/ivr/adapters.py` | Comentar todo → **DEUDA TÉCNICA** |
| `apps/ivr/viewsets.py` | Reemplazar viewset para `TblTempPruebaIvr` |
| `apps/ivr/serializers/calllog_serializers.py` | Comentar todo → **DEUDA TÉCNICA** |
| `apps/ivr/serializers/__init__.py` | Nuevo serializer para `TblTempPruebaIvr` |
| `apps/ivr/urls.py` | Actualizar ruta al nuevo viewset |
| `apps/ivr/tests/test_viewsets.py` | Comentar todo → **DEUDA TÉCNICA** |

### Capa de servicios

| Archivo | Cambio |
|---|---|
| `apps/pipeline/services/etl_service.py` | Comentar import IVRAdapter → **DEUDA TÉCNICA** |
| `apps/core/services/etl_service.py` | Comentar import IVRAdapter → **DEUDA TÉCNICA** |

### Capa de tests

| Archivo | Cambio |
|---|---|
| `tests/factories/ivr_factories.py` | Comentar todo → **DEUDA TÉCNICA** (11 modelos no existen) |
| `tests/unit/ivr_legacy/test_ivr_models.py` | Comentar → **DEUDA TÉCNICA** |
| `tests/unit/ivr_legacy/test_ivr_app.py` | Comentar → **DEUDA TÉCNICA** |
| `tests/unit/ivr_legacy/test_ivr_adapters.py` | Comentar → **DEUDA TÉCNICA** |
| `tests/mocks/database_mocks.py` | Comentar fixtures IVR → **DEUDA TÉCNICA** |
| `tests/conftest.py` | Remover carga de database_mocks de pytest_plugins |

---

## TAREAS

### TAREA 1 — Script MariaDB: crear tabla + poblar con SP

**Archivo nuevo:** `scripts/provisioners/mariadb/schema_temp_prueba.sh`

**Responsabilidad:** 100% MariaDB. Python no participa en la creación.

**Schema de `tbl_temp_prueba_ivr`:**

```sql
CREATE TABLE IF NOT EXISTS `tbl_temp_prueba_ivr` (
    `id`     INT(11) NOT NULL AUTO_INCREMENT,
    `numero` CHAR(10) NOT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Stored Procedure para 3000 registros:**

```sql
DROP PROCEDURE IF EXISTS sp_seed_tbl_temp_prueba_ivr;

DELIMITER $$
CREATE PROCEDURE sp_seed_tbl_temp_prueba_ivr()
BEGIN
    DECLARE i INT DEFAULT 0;
    WHILE i < 3000 DO
        INSERT INTO `tbl_temp_prueba_ivr` (`numero`)
        VALUES (LPAD(FLOOR(RAND() * 9999999999), 10, '0'));
        SET i = i + 1;
    END WHILE;
END$$
DELIMITER ;

CALL sp_seed_tbl_temp_prueba_ivr();
DROP PROCEDURE IF EXISTS sp_seed_tbl_temp_prueba_ivr;
```

> El SP se llama una vez, siembra los 3000 registros y luego se descarta.
> Idempotente: si la tabla ya tiene datos, se salta con `IF NOT EXISTS`
> combinado con lógica de conteo.

**El script Bash:**
- Verifica que MariaDB esté corriendo
- Crea la tabla (idempotente)
- Verifica si ya tiene 3000 registros (evita doble inserción)
- Crea SP → llama SP → elimina SP
- Verifica `COUNT(*) = 3000`

---

### TAREA 2 — Actualizar `db_setup.sh`: permisos para `tbl_temp_prueba_ivr`

**Archivo:** `scripts/provisioners/mariadb/db_setup.sh`

Agregar en `grant_privileges()`:
```sql
-- Permisos SELECT en tbl_temp_prueba_ivr (READ-ONLY desde Django)
GRANT SELECT ON `ivr_legacy`.`tbl_temp_prueba_ivr` TO 'django_user'@'%';
GRANT SELECT ON `ivr_legacy`.`tbl_temp_prueba_ivr` TO 'django_user'@'localhost';
```

El usuario `django_user` ya tiene `SELECT ON ivr_legacy.*`, por lo que
este paso puede ser una nota de documentación más que un cambio real.

---

### TAREA 3 — Nuevo modelo Django: `TblTempPruebaIvr`

**Archivo:** `apps/ivr/models.py`

```python
# DEUDA TÉCNICA — CallLog eliminado, pendiente schema real de ivr_legacy
# Ver: documentos/analisis/ANALISIS_IVR_SCHEMA_PROVISIONER_20260321224221.md

class TblTempPruebaIvr(models.Model):
    """
    Tabla de prueba IVR — consume tbl_temp_prueba_ivr en MariaDB.

    Solo SELECT. Schema creado por:
        scripts/provisioners/mariadb/schema_temp_prueba.sh

    CNST-003: READ-ONLY (managed=False, db_router enforza)
    """
    numero = models.CharField(max_length=10)

    class Meta:
        managed  = False
        db_table = 'tbl_temp_prueba_ivr'
        ordering = ['id']
```

---

### TAREA 4 — Nuevo serializer: `TblTempPruebaIvrSerializer`

**Archivo:** `apps/ivr/serializers/temp_prueba_serializer.py`

```python
class TblTempPruebaIvrSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TblTempPruebaIvr
        fields = ['id', 'numero']
        read_only_fields = fields
```

---

### TAREA 5 — Nuevo viewset: `TblTempPruebaIvrViewSet`

**Archivo:** `apps/ivr/viewsets.py`

```python
class TblTempPruebaIvrViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API READ-ONLY para tbl_temp_prueba_ivr.
    Lista los 3000 registros de prueba MariaDB IVR.
    CNST-003: Solo GET permitido.
    """
    queryset         = TblTempPruebaIvr.objects.using('ivr').all()
    serializer_class = TblTempPruebaIvrSerializer
    permission_classes = [IsAuthenticated]
```

---

### TAREA 6 — Marcar DEUDA TÉCNICA en todos los archivos afectados

Patrón estándar a usar:

```python
# =============================================================================
# DEUDA TÉCNICA — PENDIENTE
# =============================================================================
# Fecha de eliminación: 2026-03-21
# Motivo: El código IVR de Python fue desactivado. El schema y los datos
#         de ivr_legacy son responsabilidad de los scripts MariaDB.
#         Reactivar cuando:
#           1. Schema real de ivr_legacy sea provisionado (call_logs, etc.)
#           2. scripts/provisioners/mariadb/schema.sh esté implementado
#           3. Los tests de integración real con MariaDB sean necesarios
# Ver: documentos/analisis/ANALISIS_IVR_SCHEMA_PROVISIONER_20260321224221.md
# =============================================================================
```

---

### TAREA 7 — Nuevo test: `test_tbl_temp_prueba_ivr.py`

Test mínimo que verifica que Python puede consumir la tabla:

```python
# tests/unit/ivr_legacy/test_tbl_temp_prueba_ivr.py

def test_modelo_importable():
    from apps.ivr.models import TblTempPruebaIvr
    assert TblTempPruebaIvr._meta.managed is False
    assert TblTempPruebaIvr._meta.db_table == 'tbl_temp_prueba_ivr'

def test_campos():
    from apps.ivr.models import TblTempPruebaIvr
    field_names = [f.name for f in TblTempPruebaIvr._meta.get_fields()]
    assert 'id' in field_names
    assert 'numero' in field_names
```

> Nota: El test de que `COUNT(*) == 3000` requiere la BD real corriendo.
> Se marca como integration test (no corre en CI sin MariaDB).

---

## ORDEN DE EJECUCIÓN

```
1. schema_temp_prueba.sh     → MariaDB crea tabla + 3000 registros via SP
2. apps/ivr/models.py        → TblTempPruebaIvr (managed=False)
3. migration                 → nueva 0001_initial.py
4. serializer                → TblTempPruebaIvrSerializer
5. viewsets.py               → TblTempPruebaIvrViewSet
6. serializers/__init__.py   → actualizar exports
7. urls.py                   → registrar nuevo viewset
8. Marcar DEUDA TÉCNICA:
   - apps/ivr/adapters.py
   - apps/ivr/tests/test_viewsets.py
   - apps/ivr/serializers/calllog_serializers.py
   - tests/factories/ivr_factories.py
   - tests/unit/ivr_legacy/test_ivr_models.py
   - tests/unit/ivr_legacy/test_ivr_app.py
   - tests/unit/ivr_legacy/test_ivr_adapters.py
   - tests/mocks/database_mocks.py (fixtures IVR)
   - apps/pipeline/services/etl_service.py
   - apps/core/services/etl_service.py
9. tests/conftest.py         → remover database_mocks de plugins
10. test_tbl_temp_prueba_ivr.py → nuevo test de modelo
11. Verificar que pytest collect no tiene ImportError de IVR
```

---

## LO QUE NO CAMBIA

| Elemento | Por qué se mantiene |
|---|---|
| `config/settings/base.py` DATABASES['ivr'] | Alias 'ivr' necesario para el router |
| `config/db_router.py` | Router necesario para `managed=False` |
| `config/settings/testing.py` DATABASES['ivr'] TEST | Configuración test DB MariaDB |
| `apps/ivr/apps.py` | App config con `app_label='ivr'` |
| `apps/ivr/migrations/` | Se reemplaza 0001 con nuevo modelo |

---

## CRITERIOS DE DONE

- [x] `scripts/provisioners/mariadb/schema_temp_prueba.sh` ejecutable e idempotente
- [x] MariaDB tiene tabla `tbl_temp_prueba_ivr` con 3000 filas (verificado: 3000 rows, todos numero=10 chars)
- [x] `pytest` collect sin ImportError relacionados a IVR (13 tests colectados, 0 errores)
- [x] `TblTempPruebaIvr._meta.managed is False` y `db_table == 'tbl_temp_prueba_ivr'`
- [x] Endpoint GET `/api/ivr/temp-prueba/` definido (viewset + url registrados)
- [x] Todo código IVR previo tiene comentario `# DEUDA TÉCNICA — PENDIENTE`
- [x] `tests/unit/ivr_legacy/test_tbl_temp_prueba_ivr.py` pasa (13/13 passed)

---

## AUDITORÍA DE CIERRE

### Completado según plan

| Item | Estado | Notas |
|---|---|---|
| TAREA 1 — schema_temp_prueba.sh | ✅ | Tabla + 3000 registros via SP |
| TAREA 2 — db_setup.sh permisos | ✅ N/A | `django_user` ya tiene `SELECT ON ivr_legacy.*` — no requería cambio |
| TAREA 3 — TblTempPruebaIvr model | ✅ | managed=False, db_table correcto |
| TAREA 4 — TblTempPruebaIvrSerializer | ✅ | id + numero, read_only |
| TAREA 5 — TblTempPruebaIvrViewSet | ✅ | ReadOnlyModelViewSet, using='ivr' |
| TAREA 6 — DEUDA TÉCNICA (10 archivos) | ✅ | Patrón estándar aplicado |
| TAREA 7 — test_tbl_temp_prueba_ivr.py | ✅ | 13 tests, 13 passed |
| config/settings/testing.py — remover PENDIENTE call_logs | ✅ | Comentario actualizado al estado real |
| apps/ivr/migrations/0001_initial.py | ✅ | Nueva migration con TblTempPruebaIvr |
| apps/ivr/serializers/__init__.py | ✅ | Exports actualizados |
| apps/ivr/urls.py | ✅ | GET /api/ivr/temp-prueba/ activo |
| tests/mocks/__init__.py | ✅ | Imports IVR removidos |
| pytest collect IVR | ✅ | 0 ImportErrors |

### Nota sobre conftest.py

El plan decía "Remover carga de database_mocks de pytest_plugins". Se mantuvo
la carga porque `database_mocks.py` aún tiene fixtures activas no-IVR
(`mock_postgresql_connection`, `mock_connection_error`, `mock_database_settings`,
`mock_transaction_atomic`). Removerlo hubiera roto esas fixtures.
Lo que se hizo fue limpiar las fixtures IVR dentro del archivo — que era el
objetivo real.

---

*Plan generado: 2026-03-21*
*Cerrado: 2026-03-21*
*Basado en inventario de 39 archivos Python con referencias MariaDB/IVR*
