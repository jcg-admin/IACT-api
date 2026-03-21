# METODOLOGÍA — Creación de Documentos Extensos
## IACT API — Guía de Referencia para Claude Code

**Versión:** 1.1.0
**Fecha:** 2026-03-21
**Aplica a:** Todos los documentos en `documentos/`

---

## PROBLEMA CONOCIDO

El tool `Write` falla al crear archivos grandes directamente en el repositorio:

```
Error: "An error occurred while attempting to create the file"
```

Esto ocurre cuando el contenido supera cierto umbral de tamaño (aprox. >15KB).

---

## SOLUCIÓN: STAGING CON /tmp

Siempre crear primero en `/tmp`, luego copiar al destino final con `cp`.

### Nomenclatura en /tmp (flujo básico)

Usar siempre el prefijo `tmp_` para identificar el archivo en el directorio compartido:

```
/tmp/tmp_{nombre_final}.md
```

### Flujo básico (archivo pequeño/mediano)

```bash
# 1. Crear en staging con prefijo tmp_
cat > /tmp/tmp_nombre_archivo.md << 'ENDOFDOC'
# Contenido del documento
Múltiples líneas
Con cualquier formato markdown
ENDOFDOC

# 2. Copiar al destino final (sin prefijo tmp_)
cp /tmp/tmp_nombre_archivo.md /home/user/IACT-api/documentos/carpeta/nombre_archivo.md

# 3. Verificar
ls -lh /home/user/IACT-api/documentos/carpeta/nombre_archivo.md
```

---

## FLUJO POR PARTES (archivo muy grande)

Cuando el contenido es muy extenso (>300 líneas aprox.), dividir en partes
para evitar truncamiento del heredoc y errores de buffer.

### Nomenclatura de archivos temporales en /tmp

`/tmp` es un directorio compartido donde coexisten muchos archivos.
Para identificar correctamente cada parte, usar el prefijo `tmp_` seguido
del nombre final del archivo y el número de parte:

```
/tmp/tmp_{nombre_final}_{parte}.md
```

Ejemplos concretos:
```
/tmp/tmp_plan_implementacion_v2.2.1_parte1.md
/tmp/tmp_plan_implementacion_v2.2.1_parte2.md
/tmp/tmp_plan_implementacion_v2.2.1_parte3.md
/tmp/tmp_plan_implementacion_v2.2.1.md          ← archivo combinado final
```

```bash
# PARTE 1 — Escribir primera sección
cat > /tmp/tmp_plan_implementacion_v2.2.1_parte1.md << 'ENDOFPART1'
# Título del documento
## Sección 1
Contenido de la primera parte...
ENDOFPART1

# PARTE 2 — Segunda sección
cat > /tmp/tmp_plan_implementacion_v2.2.1_parte2.md << 'ENDOFPART2'
## Sección 2
Contenido de la segunda parte...
ENDOFPART2

# PARTE 3 — Tercera sección (si es necesario)
cat > /tmp/tmp_plan_implementacion_v2.2.1_parte3.md << 'ENDOFPART3'
## Sección 3
Contenido de la tercera parte...
ENDOFPART3

# COMBINAR todas las partes en el archivo final (también en /tmp)
cat /tmp/tmp_plan_implementacion_v2.2.1_parte1.md \
    /tmp/tmp_plan_implementacion_v2.2.1_parte2.md \
    /tmp/tmp_plan_implementacion_v2.2.1_parte3.md \
    > /tmp/tmp_plan_implementacion_v2.2.1.md

# VERIFICAR resultado combinado
wc -l /tmp/tmp_plan_implementacion_v2.2.1.md
head -5 /tmp/tmp_plan_implementacion_v2.2.1.md
tail -5 /tmp/tmp_plan_implementacion_v2.2.1.md

# COPIAR al destino final (sin prefijo tmp_)
cp /tmp/tmp_plan_implementacion_v2.2.1.md \
   /home/user/IACT-api/documentos/planes/plan_implementacion_v2.2.1_20260321214437.md

# CONFIRMAR
echo "Creado: $(ls -lh /home/user/IACT-api/documentos/planes/plan_implementacion_v2.2.1_20260321214437.md)"
```

---

## CONVENCIONES DE NOMENCLATURA

### Planes de implementación
```
documentos/planes/plan_implementacion_v{X.Y.Z}_{YYYYMMDDHHMMSS}.md
```
Ejemplos:
- `plan_implementacion_v1.0.0_210326040159.md`
- `plan_implementacion_v2.0.1_210326.md`
- `plan_implementacion_v2.2.1_210326214437.md`

### Análisis
```
documentos/analisis/ANALISIS_{TEMA}_{DDMMYYYY}.md
documentos/analisis/ANALISIS_{TEMA}_v{X.Y.Z}.md
```
Ejemplos:
- `ANALISIS_BRECHAS_AUTH_LOGIN_15032026.md`
- `ANALISIS_ESTADO_TESTS_v2_2_1.md`

### Documentación general
```
documentos/analisis/DOCUMENTACION_COMPLETA_v{X_Y_Z}.md
```

---

## VERSIONADO

El versionado sigue el formato `MAJOR.MINOR.PATCH` (`X.Y.Z`):

| Cambio                              | Versión que sube |
|-------------------------------------|-----------------|
| Nuevo plan desde cero               | MAJOR (2→3)     |
| Actualización importante/nueva fase | MINOR (2.0→2.1) |
| Corrección/refinamiento menor       | PATCH (2.1.0→2.1.1) |
| Nueva iteración del mismo ciclo     | MINOR (2.0.0→2.1.0) |

**Regla:** El número de versión del plan debe estar alineado con la
versión de la documentación (`DOCUMENTACION_COMPLETA_vX_Y_Z.md`) cuando
corresponda a ese ciclo de análisis.

---

## COMMIT Y PUSH

Siempre hacer commit + push después de crear un documento:

```bash
cd /home/user/IACT-api
git add documentos/carpeta/nombre_archivo.md
git commit -m "docs: descripción concisa del documento

https://claude.ai/code/session_01U262KqV4B5cVPgD8QhkYeh"
git push -u origin claude/check-tools-ZDoAR
```

---

## CHECKLIST ANTES DE CREAR UN DOCUMENTO

- [ ] ¿El documento es extenso? → Usar flujo por partes
- [ ] ¿El nombre final sigue la convención de nomenclatura?
- [ ] ¿Los archivos en `/tmp` usan el prefijo `tmp_` y sufijo `_parteN`?
- [ ] ¿La versión es coherente con el ciclo actual?
- [ ] ¿El staging en `/tmp` fue verificado (`wc -l`, `head`, `tail`)?
- [ ] ¿Se copió al destino final con `cp` (sin prefijo `tmp_`)?
- [ ] ¿Se hizo commit + push?

