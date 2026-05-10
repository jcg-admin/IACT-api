#!/bin/bash
# =============================================================================
# schema_temp_prueba.sh — MariaDB: crea tbl_temp_prueba_ivr y siembra datos
# =============================================================================
# Crea la tabla de prueba IVR con 3000 registros via Stored Procedure.
# Python solo CONSUME esta tabla (SELECT).
#
# IDEMPOTENTE:
#   · Si la tabla ya existe con 3000+ registros → salta el seed
#   · CREATE TABLE usa IF NOT EXISTS
#   · SP se crea, ejecuta y se descarta en cada run
#
# Estructura de tbl_temp_prueba_ivr:
#   id     INT AUTO_INCREMENT PRIMARY KEY
#   numero CHAR(10) NOT NULL   ← número random de 10 caracteres
#
# Uso:
#   sudo bash scripts/provisioners/mariadb/schema_temp_prueba.sh
#
# Variables leídas desde .env (raíz del proyecto):
#   IVR_DB_NAME  — nombre de la base de datos (default: ivr_legacy)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

source "${PROJECT_ROOT}/scripts/utils/logging.sh"

# =============================================================================
# CONFIGURACIÓN
# =============================================================================
ENV_FILE="${PROJECT_ROOT}/.env"
if [[ -f "$ENV_FILE" ]]; then
    set -a; source "$ENV_FILE"; set +a
fi

DB_NAME="${IVR_DB_NAME:-ivr_legacy}"
TARGET_ROWS=3000
TOTAL_STEPS=4

# =============================================================================
# HELPERS
# =============================================================================
my_root() {
    sudo mysql --batch "$@" 2>&1
}

my_root_silent() {
    sudo mysql --batch --silent --skip-column-names "$@" 2>/dev/null
}

# =============================================================================
# PASO 1 — Prerequisitos
# =============================================================================
check_prerequisites() {
    log_step 1 $TOTAL_STEPS "Verificando prerequisitos"

    [[ $EUID -ne 0 ]] && log_fatal "Ejecuta con sudo" && exit 1

    command -v mysql &>/dev/null \
        || { log_fatal "mysql client no encontrado."; exit 1; }

    if ! my_root_silent -e "SELECT 1;" > /dev/null; then
        log_fatal "No hay acceso root a MariaDB via socket unix"
        exit 1
    fi

    # Verificar que la BD existe
    local exists
    exists=$(my_root_silent -e \
        "SELECT COUNT(*) FROM information_schema.SCHEMATA
         WHERE SCHEMA_NAME = '${DB_NAME}';" || echo "0")

    if [[ "$exists" -eq 0 ]]; then
        log_fatal "Base de datos ${DB_NAME} no existe. Ejecuta primero db_setup.sh"
        exit 1
    fi

    log_success "MariaDB accesible — base ${DB_NAME} existe"
}

# =============================================================================
# PASO 2 — Crear tabla tbl_temp_prueba_ivr
# =============================================================================
create_table() {
    log_step 2 $TOTAL_STEPS "Creando tabla tbl_temp_prueba_ivr"

    local sql="
    CREATE TABLE IF NOT EXISTS \`${DB_NAME}\`.\`tbl_temp_prueba_ivr\` (
        \`id\`     INT(11)     NOT NULL AUTO_INCREMENT,
        \`numero\` CHAR(10)    NOT NULL,
        PRIMARY KEY (\`id\`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    "

    my_root -e "${sql}" > /dev/null
    log_success "Tabla tbl_temp_prueba_ivr lista"
}

# =============================================================================
# PASO 3 — Sembrar 3000 registros via Stored Procedure
# =============================================================================
seed_data() {
    log_step 3 $TOTAL_STEPS "Sembrando ${TARGET_ROWS} registros"

    # Verificar si ya tiene suficientes registros
    local current_count
    current_count=$(my_root_silent "${DB_NAME}" -e \
        "SELECT COUNT(*) FROM \`tbl_temp_prueba_ivr\`;" || echo "0")

    if [[ "$current_count" -ge "$TARGET_ROWS" ]]; then
        log_info "Tabla ya tiene ${current_count} registros — seed omitido"
        return 0
    fi

    log_info "Registros actuales: ${current_count} — insertando hasta ${TARGET_ROWS}"

    # Crear SP, ejecutar, destruir
    local sp_sql="
    DROP PROCEDURE IF EXISTS sp_seed_tbl_temp_prueba_ivr;
    "
    my_root "${DB_NAME}" -e "${sp_sql}" > /dev/null

    # Nota: el delimitador en CLI requiere --delimiter o heredoc con pipe
    local rows_to_insert=$(( TARGET_ROWS - current_count ))

    my_root "${DB_NAME}" << ENDSQL
DROP PROCEDURE IF EXISTS sp_seed_tbl_temp_prueba_ivr;

CREATE PROCEDURE sp_seed_tbl_temp_prueba_ivr(IN p_rows INT)
BEGIN
    DECLARE i INT DEFAULT 0;
    WHILE i < p_rows DO
        INSERT INTO \`tbl_temp_prueba_ivr\` (\`numero\`)
        VALUES (LPAD(FLOOR(RAND() * 9999999999), 10, '0'));
        SET i = i + 1;
    END WHILE;
END;

CALL sp_seed_tbl_temp_prueba_ivr(${rows_to_insert});

DROP PROCEDURE IF EXISTS sp_seed_tbl_temp_prueba_ivr;
ENDSQL

    log_success "SP ejecutado: ${rows_to_insert} registros insertados"
}

# =============================================================================
# PASO 4 — Verificar resultado
# =============================================================================
verify_result() {
    log_step 4 $TOTAL_STEPS "Verificando resultado"

    local final_count
    final_count=$(my_root_silent "${DB_NAME}" -e \
        "SELECT COUNT(*) FROM \`tbl_temp_prueba_ivr\`;" || echo "0")

    if [[ "$final_count" -ge "$TARGET_ROWS" ]]; then
        log_success "tbl_temp_prueba_ivr tiene ${final_count} registros ✓"
    else
        log_error "Esperado: ${TARGET_ROWS} — Obtenido: ${final_count}"
        exit 1
    fi

    # Mostrar muestra de los datos
    log_info "Muestra (5 registros):"
    my_root_silent "${DB_NAME}" -e \
        "SELECT id, numero FROM tbl_temp_prueba_ivr LIMIT 5;" | \
        while read -r line; do log_info "  ${line}"; done

    # Verificar que numero tiene exactamente 10 caracteres
    local bad_count
    bad_count=$(my_root_silent "${DB_NAME}" -e \
        "SELECT COUNT(*) FROM tbl_temp_prueba_ivr
         WHERE CHAR_LENGTH(numero) != 10;" || echo "0")

    if [[ "$bad_count" -eq 0 ]]; then
        log_success "Todos los registros tienen numero de 10 caracteres ✓"
    else
        log_warn "${bad_count} registros con numero != 10 chars (RAND puede generar menos cifras)"
    fi
}

# =============================================================================
# MAIN
# =============================================================================
log_header "MariaDB — tbl_temp_prueba_ivr Schema & Seed"

echo "  Base de datos : ${DB_NAME}"
echo "  Tabla         : tbl_temp_prueba_ivr"
echo "  Registros     : ${TARGET_ROWS}"
echo "  Columnas      : id (PK AUTO_INCREMENT), numero (CHAR 10)"
echo ""

check_prerequisites
create_table
seed_data
verify_result

echo ""
log_success "tbl_temp_prueba_ivr lista para consumo Python (SELECT only)."
