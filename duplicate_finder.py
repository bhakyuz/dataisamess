#!/usr/bin/env python3
"""
Duplicate File Finder
Finds duplicate files based on filename, size, and/or creation timestamp.
"""

import os
import sys
import argparse
import hashlib
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


def calculate_file_hash(filepath, algorithm='sha256', chunk_size=8192):
    """
    Calculate hash of file content.

    Args:
        filepath: Path to the file
        algorithm: Hash algorithm to use (md5, sha1, sha256)
        chunk_size: Size of chunks to read (8KB default)

    Returns:
        Hexadecimal hash string
    """
    hash_obj = hashlib.new(algorithm)
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except (OSError, IOError) as e:
        print(f"Error hashing {filepath}: {e}")
        return None


def calculate_perceptual_hash(filepath, hash_size=16):
    """
    Calculate perceptual hash of an image.
    Uses phash (DCT-based) which is good for finding resized/edited images.

    Args:
        filepath: Path to the image file
        hash_size: Size of the hash (16 = 64x64 image comparison)

    Returns:
        imagehash object (can be compared with other hashes)
    """
    try:
        from PIL import Image
        import imagehash
    except ImportError:
        print("Error: imagehash and Pillow libraries required for perceptual hashing")
        print("Install with: pip install Pillow imagehash")
        return None

    # Supported image formats
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    ext = os.path.splitext(filepath)[1].lower()

    if ext not in image_extensions:
        return None  # Not an image file

    try:
        img = Image.open(filepath)
        # Use phash with custom hash_size (16 = 64x64, 8 = 8x8)
        # Higher hash_size = more accuracy but less tolerance for changes
        phash = imagehash.phash(img, hash_size=hash_size)
        return phash
    except (OSError, IOError, Exception) as e:
        # Skip files that can't be opened as images
        return None


def find_duplicates(root_path, check_name=True, check_size=True, check_timestamp=True,
                    check_hash=False, hash_algorithm='sha256',
                    check_perceptual_hash=False, perceptual_threshold=10, perceptual_hash_size=16):
    """
    Find duplicate files based on selected criteria.

    Args:
        root_path: Root directory to search
        check_name: Include filename in duplicate detection
        check_size: Include file size in duplicate detection
        check_timestamp: Include modification timestamp in duplicate detection
        check_hash: Use content hash for duplicate detection (overrides other criteria)
        hash_algorithm: Hash algorithm to use (md5, sha1, sha256)
        check_perceptual_hash: Use perceptual hash for image duplicate detection
        perceptual_threshold: Hamming distance threshold for perceptual hash (0-64, lower = more strict)
        perceptual_hash_size: Hash size for perceptual hashing (16 = 64x64 image)

    Returns:
        Dictionary where key is tuple of selected attributes and value is list of (filepath, metadata) tuples
    """
    file_map = defaultdict(list)
    file_count = 0

    # Build criteria description
    criteria = []
    if check_perceptual_hash:
        criteria.append("perceptual_hash")
        print(f"Scanning directory: {root_path}")
        print(f"Duplicate criteria: perceptual hash (image similarity)")
        print(f"Similarity threshold: {perceptual_threshold} (0=identical, 64=completely different)")
        print(f"Hash size: {perceptual_hash_size}x{perceptual_hash_size} = {perceptual_hash_size*4}x{perceptual_hash_size*4} pixel comparison")
        print("Note: Only processes image files (jpg, png, gif, bmp, tiff, webp)")
    elif check_hash:
        criteria.append("hash")
        print(f"Scanning directory: {root_path}")
        print(f"Duplicate criteria: content hash ({hash_algorithm})")
        print("Note: Hash-based detection ignores name, size, and timestamp")
    else:
        if check_name:
            criteria.append("name")
        if check_size:
            criteria.append("size")
        if check_timestamp:
            criteria.append("timestamp")

        criteria_str = ", ".join(criteria) if criteria else "no criteria (all files will match!)"
        print(f"Scanning directory: {root_path}")
        print(f"Duplicate criteria: {criteria_str}")

    # First pass: collect all files
    all_files = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            all_files.append((filepath, filename))

    total_files = len(all_files)
    print(f"Found {total_files} files to process")

    # Second pass: process files with progress
    perceptual_hashes = []  # List of (filepath, phash, metadata) for perceptual mode

    for idx, (filepath, filename) in enumerate(all_files, 1):
        try:
            stat_info = os.stat(filepath)
            file_size = stat_info.st_size
            file_mtime = int(stat_info.st_mtime)

            # Calculate hash if requested
            file_hash = None
            file_phash = None

            if check_perceptual_hash:
                # Show progress
                if idx % 10 == 0 or idx == total_files:
                    print(f"Calculating perceptual hashes... {idx}/{total_files} ({idx*100//total_files}%)", end='\r', flush=True)
                file_phash = calculate_perceptual_hash(filepath, hash_size=perceptual_hash_size)
                if file_phash is None:
                    continue  # Skip non-image files or files that failed
                # Store for later comparison
                metadata = {
                    'name': filename,
                    'size': file_size,
                    'mtime': file_mtime,
                    'mtime_str': datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'phash': str(file_phash),
                    'phash_obj': file_phash
                }
                perceptual_hashes.append((filepath, file_phash, metadata))
                file_count += 1
            elif check_hash:
                # Show progress every 10 files or for the last file
                if idx % 10 == 0 or idx == total_files:
                    print(f"Hashing files... {idx}/{total_files} ({idx*100//total_files}%)", end='\r', flush=True)
                file_hash = calculate_file_hash(filepath, hash_algorithm)
                if file_hash is None:
                    continue  # Skip files that failed to hash

                # Build key and store
                key = (file_hash,)
                metadata = {
                    'name': filename,
                    'size': file_size,
                    'mtime': file_mtime,
                    'mtime_str': datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'hash': file_hash
                }
                file_map[key].append((filepath, metadata))
                file_count += 1
            else:
                # Metadata-based detection
                key_parts = []
                if check_name:
                    key_parts.append(filename)
                if check_size:
                    key_parts.append(file_size)
                if check_timestamp:
                    key_parts.append(file_mtime)
                key = tuple(key_parts) if key_parts else ("all_files",)

                metadata = {
                    'name': filename,
                    'size': file_size,
                    'mtime': file_mtime,
                    'mtime_str': datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'hash': None
                }
                file_map[key].append((filepath, metadata))
                file_count += 1
        except (OSError, IOError) as e:
            print(f"\nError accessing {filepath}: {e}")

    if check_hash or check_perceptual_hash:
        print()  # New line after progress
    print(f"Processed {file_count} files")

    # Post-process perceptual hashes to find similar images
    if check_perceptual_hash:
        print(f"Comparing {file_count} images for similarity...")
        processed = set()

        for i, (filepath1, phash1, metadata1) in enumerate(perceptual_hashes):
            if filepath1 in processed:
                continue

            # Find all similar images
            similar_group = [(filepath1, metadata1)]
            processed.add(filepath1)

            for j, (filepath2, phash2, metadata2) in enumerate(perceptual_hashes):
                if i >= j or filepath2 in processed:
                    continue

                # Calculate Hamming distance
                distance = phash1 - phash2

                if distance <= perceptual_threshold:
                    similar_group.append((filepath2, metadata2))
                    processed.add(filepath2)

            # Only add groups with 2+ similar images
            if len(similar_group) >= 2:
                # Use first image's hash as key
                key = (str(phash1),)
                file_map[key] = similar_group

        print(f"Found {len(file_map)} groups of similar images")

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
        if 'perceptual_hash' in criteria:
            print(f"  Perceptual Hash: {first_metadata.get('phash', 'N/A')[:16]}...")
            print(f"  Size: {first_metadata['size']:,} bytes")
            print(f"  Similar images found: {len(file_list)}")
        elif 'hash' in criteria:
            print(f"  Content Hash: {first_metadata['hash'][:16]}... ({len(first_metadata['hash'])} chars)")
            print(f"  Size: {first_metadata['size']:,} bytes")
        else:
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
            if 'perceptual_hash' in criteria:
                # Show name, size, timestamp, and similarity distance
                extra_info.append(f"name: {metadata['name']}")
                extra_info.append(f"size: {metadata['size']:,} bytes")
                extra_info.append(f"modified: {metadata['mtime_str']}")
                # Calculate distance from first image
                if i > 1 and 'phash_obj' in metadata and 'phash_obj' in first_metadata:
                    distance = first_metadata['phash_obj'] - metadata['phash_obj']
                    extra_info.append(f"similarity distance: {distance}")
            elif 'hash' in criteria:
                # Show name and timestamp as extra info
                extra_info.append(f"name: {metadata['name']}")
                extra_info.append(f"modified: {metadata['mtime_str']}")
            else:
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
        description="Find and manage duplicate files based on filename, size, timestamp, or content hash",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find duplicates (default: check name, size, and timestamp)
  python duplicate_finder.py /path/to/folder

  # Find duplicates by content hash (most accurate, slower)
  python duplicate_finder.py /path/to/folder --check-hash

  # Find visually similar images (perceptual hash)
  python duplicate_finder.py /path/to/folder --check-perceptual-hash

  # Find similar images with stricter threshold (0-64, lower=stricter)
  python duplicate_finder.py /path/to/folder --check-perceptual-hash --perceptual-threshold 5

  # Find duplicates by name and size only (ignore timestamp)
  python duplicate_finder.py /path/to/folder --no-check-timestamp

  # Find duplicates by name only
  python duplicate_finder.py /path/to/folder --no-check-size --no-check-timestamp

  # Find and interactively delete duplicates
  python duplicate_finder.py /path/to/folder --delete-interactive

  # Find similar images and delete interactively
  python duplicate_finder.py /path/to/folder --check-perceptual-hash -i

  # Find by hash and delete interactively
  python duplicate_finder.py /path/to/folder --check-hash -i

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

    parser.add_argument(
        '--check-hash',
        dest='check_hash',
        action='store_true',
        default=False,
        help='Use content hash for duplicate detection (most accurate, overrides other criteria)'
    )

    parser.add_argument(
        '--hash-algorithm',
        dest='hash_algorithm',
        default='sha256',
        choices=['md5', 'sha1', 'sha256'],
        help='Hash algorithm to use with --check-hash (default: sha256)'
    )

    parser.add_argument(
        '--check-perceptual-hash',
        dest='check_perceptual_hash',
        action='store_true',
        default=False,
        help='Use perceptual hash for image duplicate detection (finds visually similar images)'
    )

    parser.add_argument(
        '--perceptual-threshold',
        dest='perceptual_threshold',
        type=int,
        default=10,
        help='Similarity threshold for perceptual hash (0=identical, 64=very different, default: 10)'
    )

    parser.add_argument(
        '--perceptual-hash-size',
        dest='perceptual_hash_size',
        type=int,
        default=16,
        help='Hash size for perceptual hashing (8, 16, or 32; higher=more accurate; default: 16 for 64x64)'
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

    # When using perceptual hash, override other criteria
    if args.check_perceptual_hash:
        print("Using perceptual hash for image duplicate detection")
        print("Note: Only image files will be processed\n")
        duplicates, criteria = find_duplicates(
            args.path,
            check_perceptual_hash=True,
            perceptual_threshold=args.perceptual_threshold,
            perceptual_hash_size=args.perceptual_hash_size
        )
    # When using content hash, override other criteria
    elif args.check_hash:
        print("Using content hash for duplicate detection")
        print("Note: Name, size, and timestamp criteria are ignored when using --check-hash\n")
        duplicates, criteria = find_duplicates(
            args.path,
            check_hash=True,
            hash_algorithm=args.hash_algorithm
        )
    else:
        # Validate criteria - at least one must be checked
        if not (args.check_name or args.check_size or args.check_timestamp):
            print("Error: At least one criteria (name, size, or timestamp) must be checked")
            return 1

        # Find duplicates using metadata
        duplicates, criteria = find_duplicates(
            args.path,
            check_name=args.check_name,
            check_size=args.check_size,
            check_timestamp=args.check_timestamp,
            check_hash=False
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
