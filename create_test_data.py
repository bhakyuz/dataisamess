#!/usr/bin/env python3
"""
Test Data Generator for Duplicate Finder
Creates a simple test archive with image/video duplicates for testing.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def create_minimal_image(filepath, content_id=1):
    """
    Create a minimal valid PNG image.
    Different content_id creates different images.
    """
    # Minimal 1x1 PNG with different colors based on content_id
    png_headers = {
        1: b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x00\x00\x00\x00IEND\xaeB`\x82',  # Red pixel
        2: b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\x00\x00\x00\x00\xff\xff\x00\x00\x00\x00IEND\xaeB`\x82',  # Green pixel
        3: b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x00\x00\x02\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82',  # Blue pixel
    }

    with open(filepath, 'wb') as f:
        f.write(png_headers.get(content_id, png_headers[1]))

def create_minimal_video(filepath, content_id=1):
    """
    Create a minimal valid MP4 video file.
    Different content_id creates different videos.
    """
    # Minimal MP4 structure (dummy data, but valid enough for testing)
    mp4_data = {
        1: b'ftypisom\x00\x00\x02\x00isomiso2mp41' + b'\x00' * 100 + bytes([content_id] * 50),
        2: b'ftypisom\x00\x00\x02\x00isomiso2mp41' + b'\x00' * 100 + bytes([content_id] * 50),
        3: b'ftypisom\x00\x00\x02\x00isomiso2mp41' + b'\x00' * 100 + bytes([content_id] * 50),
    }

    with open(filepath, 'wb') as f:
        f.write(mp4_data.get(content_id, mp4_data[1]))

def create_test_archive(base_path='test_archive'):
    """
    Create test archive with image/video duplicates.

    Structure:
    - vacation/ - Original vacation photo
    - photos/ - Copy of vacation photo with different name
    - backup/ - Another copy of vacation photo
    - videos/ - Original and duplicate video
    - downloads/ - Different image file
    """

    # Remove existing test archive
    if os.path.exists(base_path):
        shutil.rmtree(base_path)

    print(f"Creating test archive at: {base_path}")

    # Create folder structure
    folders = [
        'vacation',
        'photos/2024',
        'backup',
        'videos',
        'downloads',
    ]

    for folder in folders:
        os.makedirs(os.path.join(base_path, folder), exist_ok=True)

    # Scenario 1: Same image content, different names (hash will find these)
    print("\n1. Creating vacation photo duplicates (same content, different names)...")
    vacation_img = os.path.join(base_path, 'vacation', 'beach.jpg')
    create_minimal_image(vacation_img, content_id=1)
    print(f"   Created: {vacation_img}")

    # Copy with different name
    photo_copy = os.path.join(base_path, 'photos/2024', 'summer_vacation.jpg')
    shutil.copy2(vacation_img, photo_copy)
    print(f"   Copied to: {photo_copy} (same content, different name)")

    # Another copy in backup
    backup_copy = os.path.join(base_path, 'backup', 'IMG_001.jpg')
    shutil.copy2(vacation_img, backup_copy)
    print(f"   Copied to: {backup_copy} (same content, different name)")

    # Scenario 2: Different image
    print("\n2. Creating different image...")
    different_img = os.path.join(base_path, 'downloads', 'screenshot.png')
    create_minimal_image(different_img, content_id=2)
    print(f"   Created: {different_img} (different content)")

    # Scenario 3: Video duplicates
    print("\n3. Creating video duplicates...")
    original_video = os.path.join(base_path, 'videos', 'trip.mp4')
    create_minimal_video(original_video, content_id=1)
    print(f"   Created: {original_video}")

    duplicate_video = os.path.join(base_path, 'videos', 'trip_backup.mp4')
    shutil.copy2(original_video, duplicate_video)
    print(f"   Copied to: {duplicate_video} (same content)")

    print("\n" + "=" * 70)
    print("Test archive created successfully!")
    print("=" * 70)
    print("\nTest scenarios:")
    print("  1. Vacation photo: 3 copies with DIFFERENT names (beach.jpg, summer_vacation.jpg, IMG_001.jpg)")
    print("     - Metadata detection: WON'T find (different names)")
    print("     - Hash detection: WILL find (same content)")
    print("\n  2. Video: 2 copies with different names (trip.mp4, trip_backup.mp4)")
    print("     - Metadata detection: WON'T find (different names)")
    print("     - Hash detection: WILL find (same content)")
    print("\n  3. Screenshot: Unique file (no duplicates)")
    print("\nTo test:")
    print(f"  # Metadata-based (won't find renamed duplicates):")
    print(f"  python3 duplicate_finder.py {base_path} --no-check-timestamp")
    print(f"\n  # Hash-based (finds all duplicates):")
    print(f"  python3 duplicate_finder.py {base_path} --check-hash")
    print()

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate test data for duplicate finder testing"
    )
    parser.add_argument(
        '--output',
        default='test_archive',
        help='Output directory for test archive (default: test_archive)'
    )

    args = parser.parse_args()
    create_test_archive(args.output)

if __name__ == '__main__':
    main()
