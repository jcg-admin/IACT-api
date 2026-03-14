#!/usr/bin/env python3
"""
Database Management Script for Django Project
Located in: scripts/run_db.py
Searches for manage.py in: ../callcentersite/
Date: 2026-01-25
"""

import sys
import os
import subprocess


# Color codes
class Colors:
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def print_header(text: str) -> None:
    """Print formatted header"""
    print()
    print(f"{Colors.BLUE}{'=' * 70}{Colors.NC}")
    print(f"{Colors.BLUE}  {text}{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 70}{Colors.NC}")
    print()


def format_size(bytes_size: int) -> str:
    """Format bytes to human readable size"""
    if bytes_size > 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_size / 1024:.2f} KB"


def get_migration_files() -> list:
    """Get all migration files recursively"""
    migration_files = []

    for root, dirs, files in os.walk(APPS_DIR):
        if MIGRATIONS_DIR_NAME in root:
            for file in files:
                if file.endswith(PYTHON_EXTENSION) and file != INIT_FILENAME:
                    migration_files.append(os.path.join(root, file))

    return sorted(migration_files)


def delete_file(file_path: str, show_size: bool = False) -> bool:
    """Delete a file with logging"""
    try:
        if os.path.isfile(file_path):
            if show_size:
                size = os.path.getsize(file_path)
                size_str = format_size(size)
                print(f"  {Colors.BLUE}Deleting:{Colors.NC} {file_path}")
                print(f"  {Colors.BLUE}Size:{Colors.NC} {size_str}")
            else:
                print(f"  {Colors.BLUE}Deleting:{Colors.NC} {file_path}")
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print_error(f"Failed to delete {file_path}: {e}")
        return False


def print_info(text: str) -> None:
    """Print info message"""
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {text}")


def print_success(text: str) -> None:
    """Print success message"""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {text}")


def print_error(text: str) -> None:
    """Print error message"""
    print(f"{Colors.RED}[ERROR]{Colors.NC} {text}")


def print_warning(text: str) -> None:
    """Print warning message"""
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {text}")


def run_command(cmd: list, cwd: str = None) -> bool:
    """Execute a command and return success status"""
    try:
        current_dir = os.getcwd()

        # Change directory if specified
        if cwd:
            os.chdir(cwd)

        print()
        result = subprocess.run(cmd)

        # Return to original directory
        os.chdir(current_dir)

        return result.returncode == 0
    except Exception as e:
        print_error(f"Failed to execute command: {e}")
        return False


# ============================================================================
# PATH SETUP
# ============================================================================

# Get paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DJANGO_DIR = os.path.join(PROJECT_ROOT, "callcentersite")
MANAGE_PY = os.path.join(DJANGO_DIR, "manage.py")

# Constants for file and directory names
APPS_DIR_NAME = "apps"
MIGRATIONS_DIR_NAME = "migrations"
DB_FILENAME = "db.sqlite3"
INIT_FILENAME = "__init__.py"
PYTHON_EXTENSION = ".py"

# Derived paths
APPS_DIR = os.path.join(DJANGO_DIR, APPS_DIR_NAME)
DB_FILE = os.path.join(DJANGO_DIR, DB_FILENAME)

# Verify manage.py exists
if not os.path.isfile(MANAGE_PY):
    print_error(f"manage.py not found in {DJANGO_DIR}/")
    print_error(f"Expected location: {MANAGE_PY}")
    sys.exit(1)


# ============================================================================
# MENU OPTIONS
# ============================================================================

def option_fresh_reset():
    """Option 1: Fresh Reset"""
    print_header("FRESH RESET - DELETE EVERYTHING AND RECREATE")

    print_warning("This will DELETE all migrations and database!")
    confirm = input("Type 'yes' to confirm: ").strip()

    if confirm != "yes":
        print_warning("Cancelled")
        return

    # Step 1: Delete migrations
    print_info("Step 1/4: Deleting migrations...")

    migration_files = get_migration_files()
    for file in migration_files:
        delete_file(file)

    print_success("Migrations deleted")

    # Step 2: Delete database
    print_info("Step 2/4: Deleting database...")

    if delete_file(DB_FILE, show_size=True):
        pass  # delete_file already printed success

    print_success("Database deleted")

    # Step 3: Make migrations
    print_info("Step 3/4: Creating new migrations...")
    if run_command(["python", "manage.py", "makemigrations"], cwd=DJANGO_DIR):
        print_success("Migrations created")
    else:
        print_error("Failed to create migrations")
        return

    # Step 4: Migrate
    print_info("Step 4/4: Applying migrations...")
    if run_command(["python", "manage.py", "migrate"], cwd=DJANGO_DIR):
        print_success("Migrations applied")
    else:
        print_error("Failed to apply migrations")
        return

    # Verify
    print_info("Verifying setup...")
    if run_command(["python", "manage.py", "check"], cwd=DJANGO_DIR):
        print_success("Fresh reset completed successfully!")


def option_make_migrations():
    """Option 2: Make Migrations"""
    print_header("MAKE MIGRATIONS")
    print_info("Creating migration files...")

    if run_command(["python", "manage.py", "makemigrations"], cwd=DJANGO_DIR):
        print_success("Migrations created successfully")
    else:
        print_error("Failed to create migrations")
        sys.exit(1)


def option_migrate():
    """Option 3: Migrate"""
    print_header("MIGRATE")
    print_info("Applying migrations to database...")

    if run_command(["python", "manage.py", "migrate"], cwd=DJANGO_DIR):
        print_success("Migrations applied successfully")
    else:
        print_error("Failed to apply migrations")
        sys.exit(1)


def option_check():
    """Option 4: Check"""
    print_header("CHECK DJANGO SETUP")
    print_info("Verifying Django configuration...")

    if run_command(["python", "manage.py", "check"], cwd=DJANGO_DIR):
        print_success("Django setup is correct")
    else:
        print_error("Django setup has issues")
        sys.exit(1)


def option_delete_migrations():
    """Option 5: Delete Migrations"""
    print_header("DELETE MIGRATIONS")
    print_warning("This will DELETE all migration files!")
    confirm = input("Type 'yes' to confirm: ").strip()

    if confirm != "yes":
        print_warning("Cancelled")
        return

    print_info("Deleting migrations...")

    migration_files = get_migration_files()

    if migration_files:
        print(f"  {Colors.BLUE}Found {len(migration_files)} migration file(s):{Colors.NC}")
        for file in migration_files:
            print(f"    {Colors.BLUE}-{Colors.NC} {file}")

        for file in migration_files:
            delete_file(file)

        print_success("Migrations deleted")
    else:
        print_info("No migration files found to delete")


def option_delete_database():
    """Option 6: Delete Database"""
    print_header("DELETE DATABASE")
    print_warning("This will DELETE the database file!")
    confirm = input("Type 'yes' to confirm: ").strip()

    if confirm != "yes":
        print_warning("Cancelled")
        return

    print_info("Deleting database...")

    if delete_file(DB_FILE, show_size=True):
        print_success("Database deleted")
    else:
        print_info("Database file not found (already deleted or doesn't exist)")


def option_make_and_migrate():
    """Option 7: Make Migrations + Migrate"""
    print_header("MAKE MIGRATIONS + MIGRATE")

    print_info("Step 1/2: Creating migration files...")
    if not run_command(["python", "manage.py", "makemigrations"], cwd=DJANGO_DIR):
        print_error("Failed to create migrations")
        sys.exit(1)

    print_success("Migrations created")

    print_info("Step 2/2: Applying migrations...")
    if not run_command(["python", "manage.py", "migrate"], cwd=DJANGO_DIR):
        print_error("Failed to apply migrations")
        sys.exit(1)

    print_success("Migrations applied")


def option_verify_setup():
    """Option 8: Verify Setup"""
    print_header("VERIFY SETUP")

    print_info("Checking Django configuration...")
    run_command(["python", "manage.py", "check"], cwd=DJANGO_DIR)

    print()
    print_info("Showing migrations status...")
    run_command(["python", "manage.py", "showmigrations"], cwd=DJANGO_DIR)


def option_exit():
    """Option 9: Exit"""
    print_info("Exiting...")
    sys.exit(0)


# ============================================================================
# MAIN MENU
# ============================================================================

def main():
    """Main menu loop"""
    print_header("DATABASE MANAGEMENT - Django v5.0.1")

    print("Select an option:")
    print()
    print("  1) Fresh Reset (DELETE migrations + db, recreate everything)")
    print("  2) Make Migrations (create migration files)")
    print("  3) Migrate (apply migrations to database)")
    print("  4) Check (verify Django setup)")
    print("  5) Delete Migrations (DESTRUCTIVE - requires confirmation)")
    print("  6) Delete Database (DESTRUCTIVE - requires confirmation)")
    print("  7) Make Migrations + Migrate (combined)")
    print("  8) Verify Setup (check + showmigrations)")
    print("  9) Exit")
    print()

    try:
        option = input("Option: ").strip()
    except KeyboardInterrupt:
        print()
        print_warning("Cancelled by user")
        sys.exit(0)

    # Map options to functions
    options = {
        "1": option_fresh_reset,
        "2": option_make_migrations,
        "3": option_migrate,
        "4": option_check,
        "5": option_delete_migrations,
        "6": option_delete_database,
        "7": option_make_and_migrate,
        "8": option_verify_setup,
        "9": option_exit,
    }

    if option in options:
        options[option]()
    else:
        print_error("Invalid option")
        sys.exit(1)

    # Print completion message
    print()
    print_header("DATABASE OPERATION COMPLETED")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()