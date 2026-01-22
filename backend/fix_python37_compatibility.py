#!/usr/bin/env python3
"""
Fix Python 3.7 compatibility issues by patching typing imports

This script finds and fixes:
- from typing import Literal -> try/except with typing_extensions
- from typing import Annotated -> try/except with typing_extensions
"""

import re
from pathlib import Path
from typing import Tuple


def fix_literal_import(content):
    # type: (str) -> Tuple[str, bool]
    """Fix Literal import for Python 3.7 compatibility"""
    pattern = r'^from typing import Literal$'

    if re.search(pattern, content, re.MULTILINE):
        replacement = '''try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal'''

        new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        return new_content, True

    return content, False


def fix_annotated_import(content):
    # type: (str) -> Tuple[str, bool]
    """Fix Annotated import for Python 3.7 compatibility"""
    # Check if Annotated is imported from typing (not typing_extensions)
    pattern = r'^from typing import (.+)$'

    fixed = False
    lines = content.split('\n')
    new_lines = []

    for line in lines:
        match = re.match(pattern, line)
        if match:
            imports = match.group(1)
            if 'Annotated' in imports:
                # Replace the entire import line
                other_imports = [imp.strip() for imp in imports.split(',') if 'Annotated' not in imp]

                if other_imports:
                    new_lines.append(f"from typing import {', '.join(other_imports)}")

                new_lines.append('''try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated''')

                fixed = True
                continue

        new_lines.append(line)

    if fixed:
        return '\n'.join(new_lines), True

    return content, False


def process_file(file_path):
    # type: (Path) -> bool
    """Process a single Python file"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content

        # Fix Literal imports
        content, literal_fixed = fix_literal_import(content)

        # Fix Annotated imports
        content, annotated_fixed = fix_annotated_import(content)

        if literal_fixed or annotated_fixed:
            file_path.write_text(content, encoding='utf-8')
            changes = []
            if literal_fixed:
                changes.append('Literal')
            if annotated_fixed:
                changes.append('Annotated')

            print(f"Fixed {', '.join(changes)} in: {file_path}")
            return True

        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function"""
    print("=" * 60)
    print("Python 3.7 Compatibility Patcher")
    print("=" * 60)
    print()

    # Find all Python files in app directory
    app_dir = Path("app")
    python_files = list(app_dir.rglob("*.py"))

    print(f"Scanning {len(python_files)} Python files...")
    print()

    fixed_count = 0

    for file_path in python_files:
        if process_file(file_path):
            fixed_count += 1

    print()
    print("=" * 60)
    print(f"Summary: Fixed {fixed_count} files")
    print("=" * 60)

    if fixed_count > 0:
        print()
        print("All typing imports have been patched for Python 3.7")
        print("You can now try starting the backend service again")
    else:
        print()
        print("No fixes needed - all files are already compatible")


if __name__ == "__main__":
    main()
