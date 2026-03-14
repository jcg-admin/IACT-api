#!/usr/bin/env python3
"""
Clean Emojis & Unicode Icons from Project
Replaces emojis and decorative unicode with standard prefixes
Date: 2026-01-25
"""

import sys
import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple


# Color codes
class Colors:
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'


# ============================================================================
# EMOJI REPLACEMENT MAPPING
# ============================================================================
EMOJI_MAP: Dict[str, str] = {
    # Success/Completion
    '✅': '[SUCCESS]',
    '✓': '[OK]',
    '☑': '[OK]',
    '✔': '[OK]',
    '🎉': '[DONE]',
    '✨': '[OK]',

    # Error/Failure
    '❌': '[ERROR]',
    '✗': '[FAIL]',
    '☒': '[FAIL]',
    '✘': '[FAIL]',

    # Warning/Caution
    '⚠️': '[WARN]',
    '⚠': '[WARN]',
    '⚡': '[WARN]',
    '⛔': '[WARN]',

    # Information
    'ℹ️': '[INFO]',
    'ℹ': '[INFO]',
    '💡': '[INFO]',
    '📢': '[INFO]',

    # Process/Running
    '🚀': '[START]',
    '▶': '[RUN]',
    '⏳': '[PENDING]',
    '🔄': '[RUNNING]',
    '⌛': '[WAITING]',

    # File/Directory
    '📁': '[DIR]',
    '📄': '[FILE]',
    '💾': '[SAVE]',
    '🗂️': '[FOLDER]',
    '🗂': '[FOLDER]',

    # Debugging
    '🐛': '[DEBUG]',
    '🔍': '[SEARCH]',

    # Time/Date
    '⏰': '[TIME]',
    '⏱️': '[TIMER]',
    '⏱': '[TIMER]',
    '📅': '[DATE]',
    '🕐': '[TIME]',
    '🗓️': '[DATE]',
    '🗓': '[DATE]',

    # Network/Connection
    '🌐': '[NETWORK]',
    '📡': '[NETWORK]',

    # User/People
    '👤': '[USER]',
    '👥': '[USERS]',

    # Start/End
    '🏁': '[END]',
    '⏹️': '[STOP]',
    '⏹': '[STOP]',

    # Arrows
    '→': '->',
    '⇒': '=>',
    '➜': '->',
    '➔': '->',
    '←': '<-',
    '⇐': '<=',
    '↑': '^',
    '↓': 'v',

    # Bullets/Markers
    '●': '*',
    '★': '*',
    '♦': '*',
    '▸': '-',
    '»': '-',
}

# Unicode box drawing characters (decorative)
BOX_DRAWING_CHARS = {
    '╔': '', '╗': '', '╚': '', '╝': '',
    '║': '-', '═': '=',
    '┌': '', '┐': '', '└': '', '┘': '',
    '│': '-', '─': '=',
    '├': '', '┤': '', '┬': '', '┴': '', '┼': '',
}

# Merge maps
EMOJI_MAP.update(BOX_DRAWING_CHARS)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def print_header(text: str) -> None:
    """Print formatted header"""
    print()
    print(f"{Colors.BLUE}{'=' * 66}{Colors.NC}")
    print(f"{Colors.BLUE}  {text}{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 66}{Colors.NC}")
    print()


def print_info(text: str) -> None:
    """Print info message"""
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {text}")


def print_success(text: str) -> None:
    """Print success message"""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {text}")


def print_error(text: str) -> None:
    """Print error message"""
    print(f"{Colors.RED}[ERROR]{Colors.NC} {text}")


def print_warn(text: str) -> None:
    """Print warning message"""
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {text}")


def print_found(text: str) -> None:
    """Print found message"""
    print(f"{Colors.CYAN}[FOUND]{Colors.NC} {text}")


def show_usage() -> None:
    """Display usage information"""
    print(f"""
{Colors.BLUE}USAGE{Colors.NC}
  python3 clean_emojis.py [OPTIONS]

{Colors.BLUE}OPTIONS{Colors.NC}
  -p, --path PATH        Search path (default: current directory)
  -e, --extensions EXT   File extensions to check (space-separated)
                         (default: sh py ps1 txt bash powershell)
  -d, --dry-run          Show changes without modifying files
  -r, --recursive        Search recursively (default: true)
  -s, --stats            Show statistics after processing
  -h, --help             Show this help message

{Colors.BLUE}EXAMPLES{Colors.NC}
  python3 clean_emojis.py
  python3 clean_emojis.py -p ./myproject
  python3 clean_emojis.py -p ./myproject -d
  python3 clean_emojis.py -e "sh py js ts" -d

{Colors.BLUE}EXIT CODES{Colors.NC}
  0  Success
  1  Error

""")


# ============================================================================
# MAIN CLASS
# ============================================================================

class EmojiCleaner:
    def __init__(self, search_path: str, extensions: List[str],
                 dry_run: bool = False):
        self.search_path = Path(search_path)
        self.extensions = extensions
        self.dry_run = dry_run

        # Statistics
        self.total_files_scanned = 0
        self.files_with_emojis: List[str] = []
        self.files_modified = 0
        self.total_replacements = 0
        # Format: {file_path: [(emoji, replacement, count), ...]}
        self.replacement_details: Dict[str, List[Tuple[str, str, int]]] = {}

    def validate(self) -> bool:
        """Validate environment and input"""
        if not self.search_path.exists():
            print_error(f"Path does not exist: {self.search_path}")
            return False

        if not self.search_path.is_dir():
            print_error(f"Path is not a directory: {self.search_path}")
            return False

        return True

    def find_files(self) -> List[Path]:
        """Find all files matching extensions"""
        files = []

        for ext in self.extensions:
            # Make sure extension doesn't have a leading dot
            ext = ext.lstrip('.')

            # Search for files
            for file_path in self.search_path.rglob(f"*.{ext}"):
                if file_path.is_file():
                    files.append(file_path)

        return sorted(list(set(files)))  # Remove duplicates and sort

    @staticmethod
    def file_has_emojis(file_path: Path) -> Tuple[bool, List[str]]:
        """Check if file contains any emojis using regex"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            found_emojis = []
            for emoji in EMOJI_MAP.keys():
                # Use regex to find all occurrences
                escaped_emoji = re.escape(emoji)
                matches = re.findall(escaped_emoji, content)
                if matches:
                    count = len(matches)
                    found_emojis.append(f"{emoji} ({count}x)")

            return len(found_emojis) > 0, found_emojis

        except Exception as e:
            print_error(f"Error reading {file_path}: {e}")
            return False, []

    def scan_files(self) -> None:
        """Scan all files for emojis"""
        print_info(f"Searching in: {self.search_path.absolute()}")
        print_info(f"File extensions: {', '.join(self.extensions)}")
        print()

        files = self.find_files()

        if not files:
            print_warn("No files found with specified extensions")
            return

        self.total_files_scanned = len(files)

        for file_path in files:
            has_emojis, emojis = EmojiCleaner.file_has_emojis(file_path)

            if has_emojis:
                self.files_with_emojis.append(str(file_path))
                emojis_str = ", ".join(emojis)
                print_found(f"{file_path.relative_to(self.search_path)} [{emojis_str}]")

    def process_file(self, file_path: Path) -> int:
        """Process single file and replace emojis using regex"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()

            modified_content = original_content
            replacements = []

            # Apply replacements using re.sub() - more efficient
            for emoji, replacement in EMOJI_MAP.items():
                # Escape special regex characters in emoji
                escaped_emoji = re.escape(emoji)
                # Count occurrences before replacement
                count = len(re.findall(escaped_emoji, modified_content))

                if count > 0:
                    # Use re.sub() for replacement
                    modified_content = re.sub(escaped_emoji, replacement, modified_content)
                    replacements.append((emoji, replacement, count))

            # Write back if changes were made and not dry-run
            if replacements and not self.dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)

                self.files_modified += 1
                total_count = sum(count for _, _, count in replacements)
                self.total_replacements += total_count

                rel_path = file_path.relative_to(self.search_path)
                print_success(f"Modified {rel_path} ({total_count} replacements)")

                self.replacement_details[str(rel_path)] = [
                    (emoji, replacement, count) for emoji, replacement, count in replacements
                ]
            elif replacements and self.dry_run:
                total_count = sum(count for _, _, count in replacements)
                rel_path = file_path.relative_to(self.search_path)
                print_warn(f"Would modify {rel_path} ({total_count} replacements)")

                for emoji, replacement, count in replacements:
                    print(f"       {emoji} -> {replacement} ({count}x)")

            return sum(count for _, _, count in replacements)

        except Exception as e:
            print_error(f"Error processing {file_path}: {e}")
            return 0

    def process_files(self) -> None:
        """Process all files with emojis"""
        if not self.files_with_emojis:
            print_success("No emojis or unicode icons found!")
            return

        print()

        if self.dry_run:
            print_warn(f"DRY-RUN mode: No files will be modified")
        else:
            print_warn(f"Found {len(self.files_with_emojis)} file(s) with emojis")
            response = input(f"Proceed with replacements? (yes/no): ").strip().lower()

            if response != 'yes':
                print_warn("Cancelled by user")
                return

        print()

        for file_path in self.files_with_emojis:
            self.process_file(Path(file_path))

    def generate_report(self) -> None:
        """Generate final report"""
        print_header("SCAN & REPLACEMENT REPORT")

        print(f"Total files scanned:        {self.total_files_scanned}")
        print(f"Files with emojis found:    {len(self.files_with_emojis)}")
        print()

        if self.dry_run:
            print_warn("DRY-RUN mode: No files were actually modified")
        else:
            print(f"Files modified:             {self.files_modified}")
            print(f"Total replacements:         {self.total_replacements}")

        if self.replacement_details and not self.dry_run:
            print()
            print("Replacement details:")
            for file, replacements in self.replacement_details.items():
                print(f"  {file}:")
                for emoji, replacement, count in replacements:
                    print(f"    {emoji} -> {replacement} ({count}x)")

    @staticmethod
    def show_reference_table() -> None:
        """Show reference table"""
        print_header("REFERENCE TABLE")
        print("Common Replacements:")
        print()
        print("  Emoji          Replacement      Description")
        print("  " + "-" * 60)

        reference = [
            ("✅", "[SUCCESS]", "Operation successful"),
            ("❌", "[ERROR]", "Error occurred"),
            ("⚠️", "[WARN]", "Warning message"),
            ("ℹ️", "[INFO]", "Information"),
            ("✓", "[OK]", "Confirmation"),
            ("🚀", "[START]", "Starting process"),
            ("⏳", "[PENDING]", "Waiting/Pending"),
            ("📁", "[DIR]", "Directory"),
            ("📄", "[FILE]", "File"),
            ("🐛", "[DEBUG]", "Debug information"),
            ("→", "->", "Arrow right"),
            ("⇒", "=>", "Double arrow right"),
        ]

        for emoji, repl, desc in reference:
            print(f"  {emoji:<15}{repl:<17}{desc}")

        print()

    def run(self) -> int:
        """Main execution"""
        print_header("EMOJI & UNICODE ICON CLEANER")

        if not self.validate():
            return 1

        self.scan_files()
        self.process_files()
        self.generate_report()
        EmojiCleaner.show_reference_table()  # ← Llamada a método estático

        print_header("COMPLETED")

        return 0


# ============================================================================
# ENTRY POINT
# ============================================================================

def main() -> int:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Clean emojis and unicode icons from project files',
        add_help=False
    )

    parser.add_argument('-p', '--path',
                        default='.',
                        help='Search path (default: current directory)')

    parser.add_argument('-e', '--extensions',
                        default='sh py ps1 txt bash powershell java js ts go rb yml yaml',
                        help='File extensions to check (space-separated)')

    parser.add_argument('-d', '--dry-run',
                        action='store_true',
                        help='Show changes without modifying files')

    parser.add_argument('-r', '--recursive',
                        action='store_true',
                        default=True,
                        help='Search recursively')

    parser.add_argument('-h', '--help',
                        action='store_true',
                        help='Show help message')

    args = parser.parse_args()

    if args.help:
        show_usage()
        return 0

    # Parse extensions
    extensions = args.extensions.split()

    # Create cleaner and run
    cleaner = EmojiCleaner(
        search_path=args.path,
        extensions=extensions,
        dry_run=args.dry_run
    )

    return cleaner.run()


if __name__ == '__main__':
    sys.exit(main())