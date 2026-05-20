# IACT-api · docs/ (historico de implementacion)

> **Politica:** la documentacion canonica del proyecto IACT vive en
> [`IACT-docs/source/`](../../IACT-docs/source/). Este directorio
> contiene **archivos historicos** de las sesiones de implementacion
> del backend, preservados como evidencia de trazabilidad.

## Que contiene este directorio

- `HALLAZGOS-FASE*-*.md`, `HALLAZGOS-*-2026-*.md` — logs efimeros de
  hallazgos por sesion. **No se actualizan**. Su contenido fue
  absorbido en iniciativas en
  `IACT-docs/source/gestion/pm/iniciativas/`.
- `PLAN-IMPL-*.md`, `IMPLEMENTATION_PLAN_*.md` — versiones sucesivas
  de planes de implementacion superseded por iniciativas vigentes.
  **No se actualizan**.
- `architecture/`, `conventions/`, `plans/`, `revision/` — analisis
  arquitectonicos y de convenciones. Los items con valor permanente
  fueron portados a IACT-docs (ver iniciativa
  `integrar-docs-internos-multi-repo`).
- `setup/` — guias de configuracion local. Las vigentes fueron
  portadas a `IACT-docs/source/onboarding/`.

## Donde se actualiza la documentacion canonica

Toda nueva decision, convencion, ADR o guia operativa **se documenta
directamente en `IACT-docs/source/*`**, no aqui. Los archivos de este
directorio son referencia historica para auditoria, no documentacion
viva.

Ver:
- `IACT-docs/source/backend/` — ADRs y convenciones del backend.
- `IACT-docs/source/arquitectura-tecnica/` — vistas arquitectonicas.
- `IACT-docs/source/onboarding/` — guias de setup.
- `IACT-docs/source/normativa/restricciones/` — restricciones
  arquitectonicas (CNST-*).

## Iniciativa de archivado

La decision de archivar (vs portar) se documenta en
`IACT-docs/source/gestion/pm/iniciativas/integrar-docs-internos-multi-repo/`.
