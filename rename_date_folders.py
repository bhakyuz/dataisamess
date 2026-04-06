#!/usr/bin/env python3
"""
Rename folders with date-like names to ISO format (YYYY-MM-DD).

Converts folders like:
  23,01,2013 → 2013-01-23 (DD-MM-YYYY)
  2013-01-23 → 2013-01-23 (already correct)
  01-23-2013 → 2013-01-23 (MM-DD-YYYY)
  02.03.13 → 2013-03-02 (DD-MM-YY)

Supports multiple date formats with various separators.
Century inference: Years 00-40 → 2000s, 41-99 → 1900s
"""

import os
import sys
import argparse
import re
from datetime import datetime


def getch():
    """
    Read a single character from stdin without requiring Enter.
    Works on both Unix/Linux and Windows.
    Falls back to regular input if not in a terminal.
    """
    # Check if stdin is a terminal
    if not sys.stdin.isatty():
        # Fallback to regular input when piping or redirecting
        line = input()
        return line.strip()[:1] if line else 'n'

    try:
        # Unix/Linux/macOS
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    except (ImportError, AttributeError, OSError):
        # Windows or fallback
        try:
            import msvcrt
            return msvcrt.getch().decode('utf-8')
        except ImportError:
            # Final fallback
            line = input()
            return line.strip()[:1] if line else 'n'


def infer_century(two_digit_year, cutoff=40):
    """
    Convert 2-digit year to 4-digit year by inferring the century.

    Args:
        two_digit_year: 2-digit year (0-99)
        cutoff: Years <= cutoff are 2000s, > cutoff are 1900s (default: 40)

    Returns:
        4-digit year

    Examples:
        13 -> 2013 (13 <= 40)
        99 -> 1999 (99 > 40)
        40 -> 2040 (40 <= 40)
        41 -> 1941 (41 > 40)
    """
    year = int(two_digit_year)
    if year <= cutoff:
        return 2000 + year
    else:
        return 1900 + year


def parse_date_folder(folder_name, year_cutoff=40):
    """
    Try to parse a folder name as a date.

    Supports multiple formats with various separators (comma, dot, dash, underscore, space):
    - DD-MM-YYYY (e.g., 23-01-2013, 23.01.2013, 23,01,2013)
    - YYYY-MM-DD (e.g., 2013-01-23, 2013.01.23, 2013,01,23)
    - MM-DD-YYYY (e.g., 01-23-2013, 01.23.2013, 01,23,2013)
    - DD-MM-YY (e.g., 02-03-13, 02.03.13 -> 2013-03-02)
    - YY-MM-DD (e.g., 13-03-02, 13.03.02 -> 2013-03-02)
    - MM-DD-YY (e.g., 03-02-13, 03.02.13 -> 2013-03-02)

    Tries formats in order and returns the first valid match.
    Priority: YYYY-MM-DD > DD-MM-YYYY > MM-DD-YYYY > DD-MM-YY > YY-MM-DD > MM-DD-YY

    Args:
        folder_name: Folder name to parse
        year_cutoff: For 2-digit years, years <= cutoff are 2000s, > cutoff are 1900s

    Returns:
        tuple: (datetime object, format_name) if valid date, (None, None) otherwise
    """
    # Pattern: any 2-4 digit numbers separated by common separators
    # Supports: comma, dot, dash, underscore, space
    pattern = r'^(\d{1,4})[,.\-_\s]+(\d{1,2})[,.\-_\s]+(\d{1,4})$'

    match = re.match(pattern, folder_name)
    if not match:
        return None, None

    part1, part2, part3 = match.groups()

    # Try different date formats in order of preference
    formats_to_try = []

    # If first part is 4 digits, likely YYYY-MM-DD or YYYY-DD-MM
    if len(part1) == 4:
        formats_to_try.append((f"{part1}-{part2}-{part3}", "%Y-%m-%d", "YYYY-MM-DD"))
        formats_to_try.append((f"{part1}-{part3}-{part2}", "%Y-%d-%m", "YYYY-DD-MM"))
    # If last part is 4 digits, likely DD-MM-YYYY or MM-DD-YYYY
    elif len(part3) == 4:
        # Try DD-MM-YYYY first (European format)
        formats_to_try.append((f"{part1}-{part2}-{part3}", "%d-%m-%Y", "DD-MM-YYYY"))
        # Then try MM-DD-YYYY (US format)
        formats_to_try.append((f"{part1}-{part2}-{part3}", "%m-%d-%Y", "MM-DD-YYYY"))
    # All parts are 2 digits or less - could be 2-digit year format
    elif len(part1) <= 2 and len(part2) <= 2 and len(part3) <= 2:
        # Try to determine which part is the year based on context
        # Most common: DD-MM-YY (European)
        # Also try: YY-MM-DD and MM-DD-YY

        # Try DD-MM-YY first (e.g., 02.03.13 -> 02-03-2013)
        year_4digit = infer_century(part3, year_cutoff)
        formats_to_try.append((f"{part1}-{part2}-{year_4digit}", "%d-%m-%Y", "DD-MM-YY"))

        # Try YY-MM-DD (e.g., 13.03.02 -> 2013-03-02)
        year_4digit = infer_century(part1, year_cutoff)
        formats_to_try.append((f"{year_4digit}-{part2}-{part3}", "%Y-%m-%d", "YY-MM-DD"))

        # Try MM-DD-YY (e.g., 03.02.13 -> 2013-03-02)
        year_4digit = infer_century(part3, year_cutoff)
        formats_to_try.append((f"{part1}-{part2}-{year_4digit}", "%m-%d-%Y", "MM-DD-YY"))
    else:
        # Mixed format or unusual pattern, skip
        return None, None

    # Try each format
    for date_string, format_string, format_name in formats_to_try:
        try:
            date_obj = datetime.strptime(date_string, format_string)
            # Additional validation: year should be reasonable (1900-2100)
            if 1900 <= date_obj.year <= 2100:
                return date_obj, format_name
        except ValueError:
            continue

    return None, None


def get_new_folder_name(folder_name):
    """
    Convert folder name to ISO format (YYYY-MM-DD).

    Args:
        folder_name: Original folder name

    Returns:
        tuple: (new_name, detected_format, date_obj) or (None, None, None) if not a date
    """
    date_obj, format_name = parse_date_folder(folder_name)
    if date_obj is None:
        return None, None, None

    # Format as YYYY-MM-DD
    new_name = date_obj.strftime("%Y-%m-%d")
    return new_name, format_name, date_obj


def find_date_folders(root_path):
    """
    Find all folders with date-like names.

    Args:
        root_path: Root directory to search

    Returns:
        List of tuples: (full_path, old_name, new_name, detected_format, date_obj)
    """
    date_folders = []

    for dirpath, dirnames, _ in os.walk(root_path):
        for dirname in dirnames:
            new_name, format_name, date_obj = get_new_folder_name(dirname)
            if new_name:
                full_path = os.path.join(dirpath, dirname)
                date_folders.append((full_path, dirname, new_name, format_name, date_obj))

    return date_folders


def rename_folders_interactive(root_path):
    """
    Interactively rename date folders to ISO format.

    Args:
        root_path: Root directory to process

    Returns:
        Tuple: (success_count, skip_count, error_count)
    """
    date_folders = find_date_folders(root_path)

    if not date_folders:
        print("No date-formatted folders found.")
        return 0, 0, 0

    print(f"\nFound {len(date_folders)} date-formatted folder(s)")
    print("=" * 80)

    success_count = 0
    skip_count = 0
    error_count = 0

    for idx, (full_path, old_name, new_name, format_name, date_obj) in enumerate(date_folders, 1):
        parent_dir = os.path.dirname(full_path)
        new_path = os.path.join(parent_dir, new_name)

        print(f"\n[{idx}/{len(date_folders)}] Folder: {old_name}")
        print(f"  Location: {parent_dir}")
        print(f"  Detected format: {format_name}")

        # Show human-readable date interpretation
        human_date = date_obj.strftime("%B %d, %Y")  # e.g., "March 02, 2013"
        print(f"  Interpreted as: {new_name} ({human_date})")

        if old_name != new_name:
            print(f"  New name: {new_name}")

        # Check if already in correct format
        if old_name == new_name:
            print(f"  ℹ️  Already in ISO format, skipping")
            skip_count += 1
            continue

        # Check if target already exists
        if os.path.exists(new_path):
            print(f"  ⚠️  Target folder already exists, skipping")
            skip_count += 1
            continue

        # Loop until valid input is received
        while True:
            print("  Rename this folder? [y/N/q(quit)]: ", end='', flush=True)
            response = getch().lower()
            print(response)  # Echo the character

            if response == 'q':
                print("\nQuitting...")
                return success_count, skip_count, error_count
            elif response == 'y':
                try:
                    os.rename(full_path, new_path)
                    print(f"  ✅ Renamed: {old_name} → {new_name}")
                    success_count += 1
                except Exception as e:
                    print(f"  ❌ Error: {e}")
                    error_count += 1
                break
            elif response == 'n' or response == '\r' or response == '\n':
                print("  ⏭️  Skipped")
                skip_count += 1
                break
            else:
                print(f"  Invalid input '{response}'. Please press 'y', 'n', or 'q'.")

    return success_count, skip_count, error_count


def rename_folders_auto(root_path, dry_run=True):
    """
    Automatically rename date folders to ISO format.

    Args:
        root_path: Root directory to process
        dry_run: If True, only show what would be renamed

    Returns:
        Tuple: (success_count, skip_count, error_count)
    """
    date_folders = find_date_folders(root_path)

    if not date_folders:
        print("No date-formatted folders found.")
        return 0, 0, 0

    print(f"\nFound {len(date_folders)} date-formatted folder(s):")
    print("=" * 70)

    success_count = 0
    skip_count = 0
    error_count = 0

    for full_path, old_name, new_name, format_name, date_obj in date_folders:
        parent_dir = os.path.dirname(full_path)
        new_path = os.path.join(parent_dir, new_name)

        # Skip if already in correct format
        if old_name == new_name:
            if not dry_run:
                print(f"ℹ️  SKIP: {old_name} (already in ISO format)")
                print(f"   Path: {parent_dir}")
                print()
            skip_count += 1
            continue

        # Check if target already exists
        if os.path.exists(new_path):
            print(f"⚠️  SKIP: {old_name} → {new_name}")
            print(f"   Reason: Target folder already exists")
            print(f"   Path: {parent_dir}")
            print()
            skip_count += 1
            continue

        if dry_run:
            print(f"📋 WOULD RENAME: {old_name} → {new_name}")
            print(f"   Detected format: {format_name}")
            print(f"   Path: {parent_dir}")
            print()
            success_count += 1
        else:
            try:
                os.rename(full_path, new_path)
                print(f"✅ RENAMED: {old_name} → {new_name}")
                print(f"   Detected format: {format_name}")
                print(f"   Path: {parent_dir}")
                print()
                success_count += 1
            except Exception as e:
                print(f"❌ ERROR: {old_name} → {new_name}")
                print(f"   Reason: {e}")
                print(f"   Path: {parent_dir}")
                print()
                error_count += 1

    return success_count, skip_count, error_count


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Rename folders with date-like names to ISO format (YYYY-MM-DD).',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview what would be renamed (dry run)
  python rename_date_folders.py /path/to/photos

  # Interactively rename folders (validate each one)
  python rename_date_folders.py /path/to/photos --interactive

  # Automatically rename all folders
  python rename_date_folders.py /path/to/photos --execute

Supported date formats (4-digit years):
  - DD-MM-YYYY (e.g., 23-01-2013, 23.01.2013, 23,01,2013 → 2013-01-23)
  - YYYY-MM-DD (e.g., 2013-01-23, 2013.01.23 → 2013-01-23)
  - MM-DD-YYYY (e.g., 01-23-2013, 01.23.2013 → 2013-01-23)

Supported date formats (2-digit years):
  - DD-MM-YY (e.g., 02.03.13, 02-03-13 → 2013-03-02)
  - YY-MM-DD (e.g., 13.03.02, 13-03-02 → 2013-03-02)
  - MM-DD-YY (e.g., 03.02.13, 03-02-13 → 2013-03-02)

Century inference: Years 00-40 → 2000s, 41-99 → 1900s
Separators: comma, dot, dash, underscore, space
Non-date folders are left unchanged.
        """
    )

    parser.add_argument(
        'path',
        help='Directory to search for date-formatted folders'
    )

    # Mode options (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Interactively confirm each rename'
    )
    mode_group.add_argument(
        '--execute', '-e',
        action='store_true',
        help='Automatically rename all folders (no confirmation)'
    )

    args = parser.parse_args()

    # Validate path
    if not os.path.isdir(args.path):
        print(f"Error: '{args.path}' is not a valid directory", file=sys.stderr)
        sys.exit(1)

    # Show mode
    if args.interactive:
        print("🔍 INTERACTIVE MODE - Confirm each rename")
        print("=" * 80)
        success, skip, error = rename_folders_interactive(args.path)
    elif args.execute:
        print("🚀 EXECUTION MODE - Folders will be renamed")
        print()
        success, skip, error = rename_folders_auto(args.path, dry_run=False)
    else:
        print("👀 DRY RUN MODE - No changes will be made")
        print("   Use --interactive or --execute to rename folders")
        print()
        success, skip, error = rename_folders_auto(args.path, dry_run=True)

    # Summary
    print("\n" + "=" * 70)
    print("Summary:")
    if args.execute or args.interactive:
        print(f"  ✅ Successfully renamed: {success}")
        print(f"  ⏭️  Skipped: {skip}")
        if error > 0:
            print(f"  ❌ Errors: {error}")
    else:
        print(f"  📋 Would rename: {success}")
        print(f"  ⏭️  Would skip: {skip}")

        if success > 0:
            print("\n💡 Run with --interactive to confirm each rename")
            print("💡 Run with --execute to rename all automatically")


if __name__ == '__main__':
    main()
