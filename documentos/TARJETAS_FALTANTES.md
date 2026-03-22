# TARJETAS FALTANTES - ESTADO DE DOCUMENTACION

Sistema IACT - Analisis IVR
Version: 1.0.0
Fecha: 2026-03-22
Modelo RBAC: v7.0.0

---

## RESUMEN EJECUTIVO

| Concepto | Cantidad |
|---|---|
| Total de funciones en el sistema | 46 |
| Tarjetas de flujos creadas | 25 |
| Tarjetas de flujos FALTANTES | 21 |
| Porcentaje completado | 54.3% |

**Nota:** El DICCIONARIO_PERMISOS_TARJETAS_DETALLADAS.md documenta las 46 funciones a nivel de permisos (que hacen). El DICCIONARIO_FLUJOS_TARJETAS_DETALLADAS.md documenta las mismas a nivel de flujos detallados (como se usan). Este documento traquea el estado de las tarjetas de FLUJOS.

---

## MODULOS COMPLETOS (25 tarjetas de flujo creadas)

### MOD_Auth - Autenticacion (4/4 - 100%)

| # | Funcion | Archivo | Estado |
|---|---|---|---|
| 1 | auth.login | Tarjeta auth login.md | COMPLETA |
| 2 | auth.logout | Tarjeta auth logout.md | COMPLETA |
| 3 | auth.recover_password | Tarjeta auth recover password.md | COMPLETA |
| 4 | auth.manage_sessions | Tarjeta auth manage sessions.md | COMPLETA |

### MOD_Users - Gestion de Usuarios (9/9 - 100%)

| # | Funcion | Archivo | Estado |
|---|---|---|---|
| 5 | users.view | Tarjeta users view.md | COMPLETA |
| 6 | users.create | Tarjeta users create.md | COMPLETA |
| 7 | users.edit | Tarjeta users edit.md | COMPLETA |
| 8 | users.delete | Tarjeta users delete.md | COMPLETA |
| 9 | users.reset_password | Tarjeta users reset password.md | COMPLETA |
| 10 | users.lock | Tarjeta users lock.md | COMPLETA |
| 11 | users.unlock | Tarjeta users unlock.md | COMPLETA |
| 12 | users.search | Tarjeta users search.md | COMPLETA |
| 13 | users.export | Tarjeta users export.md | COMPLETA |

### MOD_Access - Gestion de Permisos (3/3 - 100%)

| # | Funcion | Archivo | Estado |
|---|---|---|---|
| 14 | access.view | Tarjeta access view.md | COMPLETA |
| 15 | access.assign | Tarjeta access assign.md | COMPLETA |
| 16 | access.revoke | Tarjeta access revoke.md | COMPLETA |

### MOD_Reports - Reportes y Analisis (6/6 - 100%)

| # | Funcion | Archivo | Estado |
|---|---|---|---|
| 17 | reports.view_basic | Tarjeta reports view basic.md | COMPLETA |
| 18 | reports.view_advanced | Tarjeta reports view advanced.md | COMPLETA |
| 19 | reports.export | Tarjeta reports export.md | COMPLETA |
| 20 | reports.modify_data | Tarjeta reports modify data.md | COMPLETA |
| 21 | reports.approve | Tarjeta reports approve.md | COMPLETA |
| 22 | reports.schedule | Tarjeta reports schedule.md | COMPLETA |

### MOD_Audit - Auditoria y Compliance (3/3 - 100%)

| # | Funcion | Archivo | Estado |
|---|---|---|---|
| 23 | audit.view | Tarjeta audit view.md | COMPLETA |
| 24 | audit.search | Tarjeta audit search.md | COMPLETA |
| 25 | audit.delete | Tarjeta audit delete.md | COMPLETA |

---

## TARJETAS FALTANTES (21 funciones sin documentar)

Los 5 modulos anteriores suman 25 funciones. El sistema IACT tiene 46 funciones en total. Las 21 funciones restantes corresponden a modulos adicionales aun NO catalogados.

### Estado de los modulos adicionales

Estos modulos existen en el sistema pero no han sido incorporados al DICCIONARIO_FLUJOS ni al DICCIONARIO_PERMISOS. Requieren discovery y documentacion.

| # | Modulo estimado | Funciones estimadas | Estado |
|---|---|---|---|
| MOD_? | Por identificar | 21 funciones | SIN CATALOGAR |

### Acciones necesarias para completar el 100%

1. **Identificar los modulos faltantes**: Analizar el codigo fuente, endpoints y modelos para identificar los 21 modulos/funciones adicionales del sistema.

2. **Catalogar en DICCIONARIO_PERMISOS**: Para cada funcion nueva, agregar su tarjeta de permisos (que hace, endpoint, SoD si aplica).

3. **Crear tarjetas de flujos**: Para cada funcion nueva, crear el archivo correspondiente en documentos/flujos/ con el formato estandar.

4. **Actualizar diccionarios**: Actualizar los indices en DICCIONARIO_FLUJOS y DICCIONARIO_PERMISOS.

---

## DONDE BUSCAR LOS MODULOS FALTANTES

Para identificar las 21 funciones restantes, revisar:

### En el codigo fuente

```bash
# Buscar endpoints registrados
grep -r "path(" callcentersite/ --include="urls.py"

# Buscar vistas y viewsets
grep -r "class.*ViewSet\|class.*APIView" callcentersite/ --include="*.py"

# Buscar permisos custom definidos
grep -r "has_permission\|has_object_permission" callcentersite/ --include="*.py"
```

### Modulos probables (por descubrir)

Basado en el tipo de sistema (IVR/CallCenter), los modulos faltantes podrian incluir:

| Modulo Probable | Funciones Posibles |
|---|---|
| MOD_IVR - Configuracion IVR | ivr.view, ivr.create, ivr.edit, ivr.delete, ivr.activate |
| MOD_Queues - Gestion de Colas | queues.view, queues.create, queues.edit, queues.delete |
| MOD_Agents - Gestion de Agentes | agents.view, agents.create, agents.edit, agents.delete |
| MOD_Config - Configuracion del Sistema | config.view, config.edit |
| MOD_Notifications - Notificaciones | notifications.view, notifications.send |
| Otros | Por descubrir en el analisis del codigo |

**Nota:** Los nombres anteriores son estimaciones. Los nombres reales deben obtenerse del analisis del codigo fuente y endpoints del sistema.

---

## HISTORIAL DE CREACION

| Fecha | Tarjetas creadas | Responsable |
|---|---|---|
| 2026-03-14 | 12 tarjetas iniciales (auth + users parcial + audit.delete) | Equipo inicial |
| 2026-03-22 | 13 tarjetas (users completo + access + reports + audit completo) | Claude Code |

---

## PROXIMOS PASOS RECOMENDADOS

**Prioridad ALTA:**
1. Identificar y catalogar los 21 modulos/funciones faltantes analizando el codigo
2. Verificar si todos los endpoints del sistema tienen su correspondiente funcion en el modelo RBAC

**Prioridad MEDIA:**
3. Revisar el ESTADO DE IMPLEMENTACION en las tarjetas existentes y actualizar donde el codigo ya converge con el diseno
4. Agregar secciones de INTERACCIONES CON OTRAS FUNCIONES en las tarjetas nuevas creadas

**Prioridad BAJA:**
5. Unificar el formato de las tarjetas antiguas (auth login.md tiene formato mas detallado que las nuevas de users)
6. Agregar seccion de ESTADO DE IMPLEMENTACION a todas las tarjetas del modulo MOD_Users, MOD_Access, MOD_Reports y MOD_Audit

---

Documento: TARJETAS FALTANTES - ESTADO DE DOCUMENTACION
Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha: 2026-03-22 | Modelo RBAC: v7.0.0
