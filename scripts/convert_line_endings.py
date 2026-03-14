#!/usr/bin/env python3
"""
Convert Line Endings: CRLF to LF
Converts Windows line endings (CRLF) to Unix line endings (LF)
Date: 2026-01-25
"""

import sys
import argparse
from pathlib import Path
from typing import List, Tuple

# Color codes
class Colors:
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def print_header(text: str) -> None:
    """Print formatted header"""
    print()
    print(f"{Colors.BLUE}{'='*66}{Colors.NC}")
    print(f"{Colors.BLUE}  {text}{Colors.NC}")
    print(f"{Colors.BLUE}{'='*66}{Colors.NC}")
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
  python3 convert_line_endings.py [OPTIONS]

{Colors.BLUE}OPTIONS{Colors.NC}
  -p, --path PATH        Search path (default: current directory)
  -e, --extensions EXT   File extensions to check (space-separated)
                         (default: sh py ps1 txt bash powershell java js ts go rb yml yaml)
  -d, --dry-run          Show changes without modifying files
  -r, --recursive        Search recursively (default: true)
  -h, --help             Show this help message

{Colors.BLUE}EXAMPLES{Colors.NC}
  python3 convert_line_endings.py
  python3 convert_line_endings.py -p ./callcentersite
  python3 convert_line_endings.py -p ./callcentersite -d
  python3 convert_line_endings.py -e "py js ts"

{Colors.BLUE}NOTES{Colors.NC}
  - Converts CRLF (Windows) to LF (Unix/Linux/macOS)
  - Always use -d (dry-run) first to see what will change
  - Works recursively by default

""")

# ============================================================================
# MAIN CLASS
# ============================================================================

class LineEndingConverter:
    """Convert line endings from CRLF to LF"""
    
    def __init__(self, search_path: str, extensions: List[str], dry_run: bool = False):
        self.search_path = Path(search_path)
        self.extensions = extensions
        self.dry_run = dry_run
        
        # Statistics
        self.total_files_scanned = 0
        self.files_with_crlf: List[str] = []
        self.files_modified = 0
        self.total_lines_converted = 0
    
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
    
    def file_has_crlf(self, file_path: Path) -> bool:
        """Check if file contains CRLF line endings"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Check for CRLF (0x0D 0x0A)
            return b'\r\n' in content
        
        except Exception as e:
            print_error(f"Error reading {file_path}: {e}")
            return False
    
    def scan_files(self) -> None:
        """Scan all files for CRLF line endings"""
        print_info(f"Searching in: {self.search_path.absolute()}")
        print_info(f"File extensions: {', '.join(self.extensions)}")
        print()
        
        files = self.find_files()
        
        if not files:
            print_warn("No files found with specified extensions")
            return
        
        self.total_files_scanned = len(files)
        
        for file_path in files:
            if self.file_has_crlf(file_path):
                self.files_with_crlf.append(str(file_path))
                rel_path = file_path.relative_to(self.search_path)
                print_found(f"{rel_path}")
    
    def process_file(self, file_path: Path) -> bool:
        """Convert CRLF to LF in file"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Check if has CRLF
            if b'\r\n' not in content:
                return False
            
            # Convert CRLF to LF
            new_content = content.replace(b'\r\n', b'\n')
            
            # Write back if not dry-run
            if not self.dry_run:
                with open(file_path, 'wb') as f:
                    f.write(new_content)
                
                self.files_modified += 1
                # Count how many CRLF were converted
                crlf_count = content.count(b'\r\n')
                self.total_lines_converted += crlf_count
                
                rel_path = file_path.relative_to(self.search_path)
                print_success(f"Converted {rel_path} ({crlf_count} line endings)")
            else:
                crlf_count = content.count(b'\r\n')
                rel_path = file_path.relative_to(self.search_path)
                print_warn(f"Would convert {rel_path} ({crlf_count} line endings)")
            
            return True
        
        except Exception as e:
            print_error(f"Error processing {file_path}: {e}")
            return False
    
    def process_files(self) -> None:
        """Process all files with CRLF"""
        if not self.files_with_crlf:
            print_success("No files with CRLF found!")
            return
        
        print()
        
        if self.dry_run:
            print_warn(f"DRY-RUN mode: No files will be modified")
        else:
            print_warn(f"Found {len(self.files_with_crlf)} file(s) with CRLF")
            response = input(f"Proceed with conversion? (yes/no): ").strip().lower()
            
            if response != 'yes':
                print_warn("Cancelled by user")
                return
        
        print()
        
        for file_path in self.files_with_crlf:
            self.process_file(Path(file_path))
    
    def generate_report(self) -> None:
        """Generate final report"""
        print_header("CONVERSION REPORT")
        
        print(f"Total files scanned:          {self.total_files_scanned}")
        print(f"Files with CRLF found:        {len(self.files_with_crlf)}")
        print()
        
        if self.dry_run:
            print_warn("DRY-RUN mode: No files were actually modified")
        else:
            print(f"Files converted:              {self.files_modified}")
            print(f"Total line endings converted: {self.total_lines_converted}")
        
        print()
    
    def run(self) -> int:
        """Main execution"""
        print_header("CONVERT LINE ENDINGS: CRLF -> LF")
        
        if not self.validate():
            return 1
        
        self.scan_files()
        self.process_files()
        self.generate_report()
        
        print_header("COMPLETED")
        
        return 0

# ============================================================================
# ENTRY POINT
# ============================================================================

def main() -> int:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Convert line endings from CRLF to LF',
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
    
    # Create converter and run
    converter = LineEndingConverter(
        search_path=args.path,
        extensions=extensions,
        dry_run=args.dry_run
    )
    
    return converter.run()

if __name__ == '__main__':
    sys.exit(main())
