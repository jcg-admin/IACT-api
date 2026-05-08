#!/bin/bash

# Database Management Script for Django Project
# Located in: scripts/run_db.sh
# Searches for manage.py in: ../callcentersite/
# Date: 2026-01-25

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DJANGO_DIR="$PROJECT_ROOT/callcentersite"

# Verify manage.py exists in callcentersite
if [ ! -f "$DJANGO_DIR/manage.py" ]; then
    echo -e "${RED}[ERROR]${NC} manage.py not found in $DJANGO_DIR/"
    echo -e "${RED}[ERROR]${NC} Expected location: $DJANGO_DIR/manage.py"
    exit 1
fi

# Functions
write_header() {
    echo ""
    echo -e "${BLUE}======================================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}======================================================================${NC}"
    echo ""
}

write_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

write_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

write_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

write_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Main header
write_header "DATABASE MANAGEMENT - Django v5.0.1"

# Main menu
echo "Select an option:"
echo ""
echo "  1) Fresh Reset (DELETE migrations + db, recreate everything)"
echo "  2) Make Migrations (create migration files)"
echo "  3) Migrate (apply migrations to database)"
echo "  4) Check (verify Django setup)"
echo "  5) Delete Migrations (DESTRUCTIVE - requires confirmation)"
echo "  6) Delete Database (DESTRUCTIVE - requires confirmation)"
echo "  7) Make Migrations + Migrate (combined)"
echo "  8) Verify Setup (check + showmigrations)"
echo "  9) Exit"
echo ""
read -p "Option: " option

case $option in
    1)
        write_header "FRESH RESET - DELETE EVERYTHING AND RECREATE"

        # Confirm
        write_warning "This will DELETE all migrations and database!"
        read -p "Type 'yes' to confirm: " confirm

        if [ "$confirm" = "yes" ]; then
            write_info "Step 1/4: Deleting migrations..."

            # List files before deleting
            migration_files=$(find "$DJANGO_DIR/apps" -path "*/migrations/*.py" ! -name "__init__.py" 2>/dev/null)
            if [ -n "$migration_files" ]; then
                echo "$migration_files" | while read file; do
                    echo -e "  ${BLUE}Deleting:${NC} $file"
                done
            fi

            find "$DJANGO_DIR/apps" -path "*/migrations/*.py" ! -name "__init__.py" -delete 2>/dev/null
            write_success "Migrations deleted"

            write_info "Step 2/4: Deleting database..."
            echo -e "  ${YELLOW}NOTE:${NC} IACT-api databases are managed by IACT-db."
            echo -e "  ${YELLOW}      ${NC} See IACT-db/docs/architecture/SEPARACION-IACT-API.md"
            echo -e "  ${YELLOW}      ${NC} To recreate PostgreSQL: see HALLAZGOS-IACT-API-2026-05-07.md"
            fi
            write_success "Database deleted"

            write_info "Step 3/4: Creating new migrations..."
            cd "$DJANGO_DIR"
            python manage.py makemigrations
            if [ $? -eq 0 ]; then
                write_success "Migrations created"
            else
                write_error "Failed to create migrations"
                exit 1
            fi

            write_info "Step 4/4: Applying migrations..."
            python manage.py migrate
            if [ $? -eq 0 ]; then
                write_success "Migrations applied"
            else
                write_error "Failed to apply migrations"
                exit 1
            fi

            write_info "Verifying setup..."
            python manage.py check
            if [ $? -eq 0 ]; then
                write_success "Fresh reset completed successfully!"
            fi
        else
            write_warning "Cancelled"
        fi
        ;;

    2)
        write_header "MAKE MIGRATIONS"
        write_info "Creating migration files..."
        echo ""

        cd "$DJANGO_DIR"
        python manage.py makemigrations

        if [ $? -eq 0 ]; then
            write_success "Migrations created successfully"
        else
            write_error "Failed to create migrations"
            exit 1
        fi
        ;;

    3)
        write_header "MIGRATE"
        write_info "Applying migrations to database..."
        echo ""

        cd "$DJANGO_DIR"
        python manage.py migrate

        if [ $? -eq 0 ]; then
            write_success "Migrations applied successfully"
        else
            write_error "Failed to apply migrations"
            exit 1
        fi
        ;;

    4)
        write_header "CHECK DJANGO SETUP"
        write_info "Verifying Django configuration..."
        echo ""

        cd "$DJANGO_DIR"
        python manage.py check

        if [ $? -eq 0 ]; then
            write_success "Django setup is correct"
        else
            write_error "Django setup has issues"
            exit 1
        fi
        ;;

    5)
        write_header "DELETE MIGRATIONS"
        write_warning "This will DELETE all migration files!"
        read -p "Type 'yes' to confirm: " confirm

        if [ "$confirm" = "yes" ]; then
            write_info "Deleting migrations..."

            # List files before deleting
            migration_files=$(find "$DJANGO_DIR/apps" -path "*/migrations/*.py" ! -name "__init__.py" 2>/dev/null)
            if [ -n "$migration_files" ]; then
                count=$(echo "$migration_files" | wc -l)
                echo -e "  ${BLUE}Found $count migration file(s):${NC}"
                echo "$migration_files" | while read file; do
                    echo -e "    ${BLUE}-${NC} $file"
                done
            else
                write_info "No migration files found to delete"
                exit 0
            fi

            find "$DJANGO_DIR/apps" -path "*/migrations/*.py" ! -name "__init__.py" -delete
            write_success "Migrations deleted"
        else
            write_warning "Cancelled"
        fi
        ;;

    6)
        write_header "DELETE DATABASE"
        write_warning "This will DELETE the database file!"
        read -p "Type 'yes' to confirm: " confirm

        if [ "$confirm" = "yes" ]; then
            write_info "Deleting database..."

            echo -e "  ${YELLOW}NOTE:${NC} IACT-api does not use SQLite."
            echo -e "         PostgreSQL + MariaDB are managed by IACT-db."
            echo -e "         See: IACT-db/docs/architecture/SEPARACION-IACT-API.md"
            write_info "To reset the database, use IACT-db provisioning scripts."
        else
            write_warning "Cancelled"
        fi
        ;;

    7)
        write_header "MAKE MIGRATIONS + MIGRATE"

        write_info "Step 1/2: Creating migration files..."
        cd "$DJANGO_DIR"
        python manage.py makemigrations
        if [ $? -eq 0 ]; then
            write_success "Migrations created"
        else
            write_error "Failed to create migrations"
            exit 1
        fi

        echo ""
        write_info "Step 2/2: Applying migrations..."
        python manage.py migrate
        if [ $? -eq 0 ]; then
            write_success "Migrations applied"
        else
            write_error "Failed to apply migrations"
            exit 1
        fi
        ;;

    8)
        write_header "VERIFY SETUP"

        write_info "Checking Django configuration..."
        cd "$DJANGO_DIR"
        python manage.py check
        echo ""

        write_info "Showing migrations status..."
        python manage.py showmigrations
        ;;

    9)
        write_info "Exiting..."
        exit 0
        ;;

    *)
        write_error "Invalid option"
        exit 1
        ;;
esac

echo ""
write_header "DATABASE OPERATION COMPLETED"
echo ""