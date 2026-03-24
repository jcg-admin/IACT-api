#!/bin/bash
# =============================================================================
# DEPRECATED: check_tools.sh se movió a scripts/provisioners/system/
# Este archivo redirige a la nueva ubicación para compatibilidad.
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "${SCRIPT_DIR}/provisioners/system/check_tools.sh" "$@"
