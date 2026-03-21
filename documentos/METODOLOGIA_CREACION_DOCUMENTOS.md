# METODOLOGÍA — Creación de Documentos Extensos
## IACT API — Guía de Referencia para Claude Code

**Versión:** 1.0.0
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

### Flujo básico (archivo pequeño/mediano)

```bash
# 1. Crear en staging
cat > /tmp/nombre_archivo.md << 'ENDOFDOC'
# Contenido del documento
Múltiples líneas
Con cualquier formato markdown
ENDOFDOC

# 2. Copiar al destino final
cp /tmp/nombre_archivo.md /home/user/IACT-api/documentos/carpeta/nombre_archivo.md

# 3. Verificar
ls -lh /home/user/IACT-api/documentos/carpeta/nombre_archivo.md
```

---

## FLUJO POR PARTES (archivo muy grande)

Cuando el contenido es muy extenso (>300 líneas aprox.), dividir en partes
para evitar truncamiento del heredoc y errores de buffer.

```bash
# PARTE 1 — Escribir primera sección
cat > /tmp/nombre_archivo_p1.md << 'ENDOFPART1'
# Título del documento
## Sección 1
Contenido de la primera parte...
ENDOFPART1

# PARTE 2 — Segunda sección
cat > /tmp/nombre_archivo_p2.md << 'ENDOFPART2'
## Sección 2
Contenido de la segunda parte...
ENDOFPART2

# PARTE 3 — Tercera sección (si es necesario)
cat > /tmp/nombre_archivo_p3.md << 'ENDOFPART3'
## Sección 3
Contenido de la tercera parte...
ENDOFPART3

# COMBINAR todas las partes en un solo archivo
cat /tmp/nombre_archivo_p1.md \
    /tmp/nombre_archivo_p2.md \
    /tmp/nombre_archivo_p3.md \
    > /tmp/nombre_archivo.md

# VERIFICAR resultado combinado
wc -l /tmp/nombre_archivo.md
head -5 /tmp/nombre_archivo.md
tail -5 /tmp/nombre_archivo.md

# COPIAR al destino final
cp /tmp/nombre_archivo.md /home/user/IACT-api/documentos/carpeta/nombre_archivo.md

# CONFIRMAR
echo "Creado: $(ls -lh /home/user/IACT-api/documentos/carpeta/nombre_archivo.md)"
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
- [ ] ¿El nombre sigue la convención de nomenclatura?
- [ ] ¿La versión es coherente con el ciclo actual?
- [ ] ¿El staging en `/tmp` fue verificado (`wc -l`, `head`, `tail`)?
- [ ] ¿Se copió al destino final con `cp`?
- [ ] ¿Se hizo commit + push?

