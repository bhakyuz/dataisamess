#!/usr/bin/env python3
"""
Duplicate File Finder
Finds duplicate files based on filename, size, and/or creation timestamp.
"""

import os
import sys
import argparse
from collections import defaultdict
from pathlib import Path
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


def find_duplicates(root_path, check_name=True, check_size=True, check_timestamp=True):
    """
    Find duplicate files based on selected criteria.

    Args:
        root_path: Root directory to search
        check_name: Include filename in duplicate detection
        check_size: Include file size in duplicate detection
        check_timestamp: Include modification timestamp in duplicate detection

    Returns:
        Dictionary where key is tuple of selected attributes and value is list of (filepath, metadata) tuples
    """
    file_map = defaultdict(list)
    file_count = 0

    # Build criteria description
    criteria = []
    if check_name:
        criteria.append("name")
    if check_size:
        criteria.append("size")
    if check_timestamp:
        criteria.append("timestamp")

    criteria_str = ", ".join(criteria) if criteria else "no criteria (all files will match!)"
    print(f"Scanning directory: {root_path}")
    print(f"Duplicate criteria: {criteria_str}")

    for dirpath, dirnames, filenames in os.walk(root_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                stat_info = os.stat(filepath)
                file_size = stat_info.st_size
                # Use modification time (most reliable across platforms)
                file_mtime = int(stat_info.st_mtime)

                # Build key based on selected criteria
                key_parts = []
                if check_name:
                    key_parts.append(filename)
                if check_size:
                    key_parts.append(file_size)
                if check_timestamp:
                    key_parts.append(file_mtime)

                key = tuple(key_parts) if key_parts else ("all_files",)

                # Store filepath along with metadata for display
                metadata = {
                    'name': filename,
                    'size': file_size,
                    'mtime': file_mtime,
                    'mtime_str': datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d %H:%M:%S')
                }
                file_map[key].append((filepath, metadata))
                file_count += 1
            except (OSError, IOError) as e:
                print(f"Error accessing {filepath}: {e}")

    print(f"Scanned {file_count} files")

    # Filter to only duplicates (where there are 2+ files with same key)
    duplicates = {k: v for k, v in file_map.items() if len(v) > 1}

    return duplicates, criteria


def display_duplicates(duplicates, criteria):
    """Display found duplicates in a readable format."""
    if not duplicates:
        print("\nNo duplicates found!")
        return

    print(f"\nFound {len(duplicates)} sets of duplicates:")
    print("=" * 80)

    total_duplicate_files = 0
    total_wasted_space = 0

    for key, file_list in duplicates.items():
        # Get metadata from first file for display
        first_metadata = file_list[0][1]

        print(f"\nDuplicate set:")
        if 'name' in criteria:
            print(f"  Filename: {first_metadata['name']}")
        if 'size' in criteria:
            print(f"  Size: {first_metadata['size']:,} bytes")
        if 'timestamp' in criteria:
            print(f"  Modified: {first_metadata['mtime_str']}")

        print(f"  Found {len(file_list)} copies:")
        for i, (path, metadata) in enumerate(file_list, 1):
            # Show additional info if not used in criteria
            extra_info = []
            if 'timestamp' not in criteria:
                extra_info.append(f"modified: {metadata['mtime_str']}")
            if 'size' not in criteria:
                extra_info.append(f"size: {metadata['size']:,} bytes")

            extra_str = f" ({', '.join(extra_info)})" if extra_info else ""
            print(f"    [{i}] {path}{extra_str}")

        total_duplicate_files += len(file_list) - 1
        total_wasted_space += (len(file_list) - 1) * first_metadata['size']

    print("=" * 80)
    print(f"Total duplicate files (excluding originals): {total_duplicate_files}")
    print(f"Wasted space: {total_wasted_space:,} bytes ({total_wasted_space / (1024*1024):.2f} MB)")


def delete_duplicates_interactive(duplicates):
    """Interactively delete duplicates, keeping the first occurrence."""
    if not duplicates:
        print("No duplicates to delete.")
        return

    deleted_count = 0
    for file_list in duplicates.values():
        first_path, first_metadata = file_list[0]

        print(f"\n{'=' * 80}")
        print(f"Duplicate set: {first_metadata['name']} ({first_metadata['size']:,} bytes)")
        print(f"Modified: {first_metadata['mtime_str']}")
        print(f"Found {len(file_list)} copies:")
        for i, (path, metadata) in enumerate(file_list, 1):
            print(f"  [{i}] {path}")

        print(f"\nKeeping: {first_path}")
        print(f"Duplicates to delete: {len(file_list) - 1}")

        # Loop until valid input is received
        while True:
            print("Delete duplicates? [y/N/q(quit)]: ", end='', flush=True)
            response = getch().lower()
            print(response)  # Echo the character

            if response == 'q':
                print("Quitting...")
                break
            elif response == 'y':
                for path, _ in file_list[1:]:
                    try:
                        os.remove(path)
                        print(f"  Deleted: {path}")
                        deleted_count += 1
                    except OSError as e:
                        print(f"  Error deleting {path}: {e}")
                break
            elif response == 'n' or response == '\r' or response == '\n':
                print("  Skipped")
                break
            else:
                print(f"  Invalid input '{response}'. Please press 'y', 'n', or 'q'.")

        # Break out of outer loop if user quit
        if response == 'q':
            break

    print(f"\n{deleted_count} files deleted.")


def delete_duplicates_auto(duplicates, keep_first=True):
    """
    Automatically delete duplicates.

    Args:
        duplicates: Dictionary of duplicate files
        keep_first: If True, keep the first occurrence; otherwise keep the last
    """
    if not duplicates:
        print("No duplicates to delete.")
        return

    print("\nAuto-deleting duplicates (keeping first occurrence)...")
    deleted_count = 0

    for file_list in duplicates.values():
        # Keep first, delete rest
        keep_index = 0 if keep_first else -1
        to_delete = file_list[1:] if keep_first else file_list[:-1]

        keep_path = file_list[keep_index][0]
        print(f"\nKeeping: {keep_path}")
        for path, _ in to_delete:
            try:
                os.remove(path)
                print(f"  Deleted: {path}")
                deleted_count += 1
            except OSError as e:
                print(f"  Error deleting {path}: {e}")

    print(f"\nTotal {deleted_count} files deleted.")


def main():
    parser = argparse.ArgumentParser(
        description="Find and manage duplicate files based on filename, size, and/or timestamp",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find duplicates (default: check name, size, and timestamp)
  python duplicate_finder.py /path/to/folder

  # Find duplicates by name and size only (ignore timestamp)
  python duplicate_finder.py /path/to/folder --no-check-timestamp

  # Find duplicates by name only
  python duplicate_finder.py /path/to/folder --no-check-size --no-check-timestamp

  # Find and interactively delete duplicates
  python duplicate_finder.py /path/to/folder --delete-interactive

  # Automatically delete duplicates (keep first occurrence)
  python duplicate_finder.py /path/to/folder --delete-auto
        """
    )

    parser.add_argument(
        'path',
        help='Root directory to scan for duplicates'
    )

    # Criteria options
    parser.add_argument(
        '--check-name',
        dest='check_name',
        action='store_true',
        default=True,
        help='Check filename when finding duplicates (default: True)'
    )
    parser.add_argument(
        '--no-check-name',
        dest='check_name',
        action='store_false',
        help='Do not check filename when finding duplicates'
    )

    parser.add_argument(
        '--check-size',
        dest='check_size',
        action='store_true',
        default=True,
        help='Check file size when finding duplicates (default: True)'
    )
    parser.add_argument(
        '--no-check-size',
        dest='check_size',
        action='store_false',
        help='Do not check file size when finding duplicates'
    )

    parser.add_argument(
        '--check-timestamp',
        dest='check_timestamp',
        action='store_true',
        default=True,
        help='Check modification timestamp when finding duplicates (default: True)'
    )
    parser.add_argument(
        '--no-check-timestamp',
        dest='check_timestamp',
        action='store_false',
        help='Do not check modification timestamp when finding duplicates'
    )

    # Deletion options
    delete_group = parser.add_mutually_exclusive_group()
    delete_group.add_argument(
        '--delete-interactive', '-i',
        action='store_true',
        help='Interactively choose which duplicates to delete'
    )
    delete_group.add_argument(
        '--delete-auto', '-a',
        action='store_true',
        help='Automatically delete duplicates (keep first occurrence)'
    )

    args = parser.parse_args()

    # Validate path
    if not os.path.isdir(args.path):
        print(f"Error: '{args.path}' is not a valid directory")
        return 1

    # Validate criteria - at least one must be checked
    if not (args.check_name or args.check_size or args.check_timestamp):
        print("Error: At least one criteria (name, size, or timestamp) must be checked")
        return 1

    # Find duplicates
    duplicates, criteria = find_duplicates(
        args.path,
        check_name=args.check_name,
        check_size=args.check_size,
        check_timestamp=args.check_timestamp
    )

    # Display results
    display_duplicates(duplicates, criteria)

    # Handle deletion if requested
    if args.delete_interactive:
        print("\n" + "=" * 80)
        print("INTERACTIVE DELETION MODE")
        print("=" * 80)
        delete_duplicates_interactive(duplicates)
    elif args.delete_auto:
        print("\n" + "=" * 80)
        print("AUTOMATIC DELETION MODE")
        print("=" * 80)
        confirm = input("This will automatically delete duplicates. Continue? [y/N]: ")
        if confirm.strip().lower() == 'y':
            delete_duplicates_auto(duplicates)
        else:
            print("Cancelled.")

    return 0


if __name__ == "__main__":
    exit(main())
