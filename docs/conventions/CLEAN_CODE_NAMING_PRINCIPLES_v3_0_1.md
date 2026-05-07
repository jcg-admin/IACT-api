# Principios de nombrado — IACT API

**Version:** 3.0.1
**Estado:** Vigente
**Aplica a:** Todo el codigo Python de callcentersite/

---

## Regla principal

Los nombres de clases, modelos, funciones y variables deben expresar
que hace la cosa, no que patron de diseno implementa ni que acronimo
tecnico representa.

El nombre debe ser legible por alguien que no conoce el patron. Si el
nombre del patron es la unica forma de entender para que sirve la clase,
el nombre es incorrecto.

---

## Prohibiciones explicitas

### 1. Acronimos de conceptos de seguridad como nombre de clase

| Prohibido        | Razon                            | Correcto                  |
|------------------|----------------------------------|---------------------------|
| SodRule          | SOD es un acronimo               | SeparationRule            |
| SodRuleViewSet   | Mismo problema                   | SeparationRuleViewSet     |
| SOD_RULES        | Acronimo en constante            | SEPARATION_RULES          |
| fetchSodRules    | camelCase + acronimo             | fetchSeparationRules      |
| sodRule          | Variable con acronimo            | separationRule            |

Nota: Los strings que el backend entrega al frontend como capacidades
(access:update_sod, adm:create_sod) son valores opacos del contrato
de API. No son nombres de clase y no se renombran por esta regla.

### 2. Patrones de diseno como nombre de clase

| Prohibido         | Razon                    | Correcto                  |
|-------------------|--------------------------|---------------------------|
| UserSingleton     | Expone el patron         | CurrentUser               |
| ReportFactory     | Expone el patron         | ReportBuilder             |
| ObserverAlert     | Expone el patron         | AlertNotifier             |
| StrategyExport    | Expone el patron         | ExportHandler             |
| FacadeService     | Expone el patron         | Usar nombre del dominio   |

Excepcion: Factory en tests/factories/ es aceptado porque es convencion
de factory_boy y todos los archivos viven en tests/.

### 3. Abreviaciones que oscurecen el significado

| Prohibido   | Correcto              |
|-------------|-----------------------|
| usr_perm    | user_permission       |
| acc_grp     | access_group          |
| exc_perm    | exceptional_permission|
| fn_code     | function_code         |

---

## Guia de nombrado por tipo

### Modelos Django

El nombre expresa que entidad del dominio de negocio representa.

```python
# Correcto
class SeparationRule(SoftDeleteModel):
    """Regla que define que dos funciones son incompatibles."""

class AccessGroup(SoftDeleteModel):
    """Agrupador de funciones asignable a un usuario."""

class ExceptionalPermission(models.Model):
    """Permiso temporal fuera del flujo normal de asignacion de funciones."""

# Prohibido
class SodRule(SoftDeleteModel)           # SOD = acronimo
class UserSingleton(models.Model)        # Singleton = patron
```

### ViewSets y APIViews

```python
# Correcto
class SeparationRuleViewSet(viewsets.ModelViewSet): ...
class EffectivePermissionsView(APIView): ...

# Prohibido
class SodRuleViewSet(viewsets.ModelViewSet): ...
```

### Funciones de servicio

```python
# Correcto
def get_user_separation_rules(user): ...
def check_separation_conflict(fn_a, fn_b): ...

# Prohibido
def get_sod_rules(user): ...
def fetchSodRules(user): ...
```

### Constantes

```python
# Correcto
SEPARATION_RULES = 'separation_rules'

# Prohibido
SOD_RULES = 'sod_rules'
SOD_RULES_INFO = 'sod_rules_info'
```

---

## Correcciones pendientes — nombres introducidos antes de este documento

| Archivo                    | Nombre actual    | Nombre correcto        |
|----------------------------|------------------|------------------------|
| apps/access/models.py      | SodRule          | SeparationRule         |
| apps/access/views.py       | SodRuleViewSet   | SeparationRuleViewSet  |
| apps/access/urls.py        | sod-rules        | separation-rules       |

Las migraciones Django generadas con el nombre anterior se mantienen.
La tabla en DB (access_sod_rule) no se renombra hasta decision explicita.

---

## Por que no patrones como nombre de clase

Un patron de diseno es una solucion a un problema de implementacion.
Es un detalle interno. El nombre de una clase publica comunica el
rol en el dominio, no la mecanica de implementacion.

ReportFactory dice como esta hecho (con Factory). ReportBuilder dice
para que sirve. El primero acopla al lector al conocimiento del patron.
El segundo es autoexplicativo.
