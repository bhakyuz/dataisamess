#!/usr/bin/env python3
"""
Test Data Generator for Duplicate Finder
Creates a simple test archive with image/video duplicates for testing.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

try:
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not available. Install with: pip install Pillow")

def create_test_image(filepath, pattern='beach', size=(400, 300)):
    """
    Create a real, viewable test image with visual content.

    Args:
        filepath: Path to save the image
        pattern: Type of image pattern ('beach', 'mountain', 'sunset')
        size: Image dimensions (width, height)
    """
    if not PIL_AVAILABLE:
        print(f"Skipping image creation for {filepath} - PIL not available")
        return

    img = Image.new('RGB', size)
    draw = ImageDraw.Draw(img)

    if pattern == 'beach':
        # Blue sky gradient at top
        for y in range(size[1] // 2):
            color = (135 - y // 3, 206 - y // 3, 235)
            draw.rectangle([0, y, size[0], y + 1], fill=color)
        # Sandy beach at bottom
        for y in range(size[1] // 2, size[1]):
            color = (238, 214, 175)
            draw.rectangle([0, y, size[0], y + 1], fill=color)
        # Sun
        draw.ellipse([size[0] - 100, 30, size[0] - 30, 100], fill=(255, 255, 0))
        # Add text
        draw.text((10, 10), "Beach Vacation", fill=(255, 255, 255))

    elif pattern == 'mountain':
        # Sky
        for y in range(size[1] * 2 // 3):
            color = (100, 149, 237)
            draw.rectangle([0, y, size[0], y + 1], fill=color)
        # Mountain
        points = [(0, size[1]), (size[0] // 2, size[1] // 3), (size[0], size[1])]
        draw.polygon(points, fill=(139, 137, 137))
        # Add text
        draw.text((10, 10), "Mountain View", fill=(255, 255, 255))

    elif pattern == 'sunset':
        # Gradient sunset sky
        for y in range(size[1]):
            r = int(255 - (y / size[1]) * 100)
            g = int(140 - (y / size[1]) * 100)
            b = int(50 + (y / size[1]) * 100)
            draw.rectangle([0, y, size[0], y + 1], fill=(r, g, b))
        # Sun
        draw.ellipse([size[0] // 2 - 50, size[1] // 2 - 50,
                     size[0] // 2 + 50, size[1] // 2 + 50], fill=(255, 200, 0))
        # Add text
        draw.text((10, 10), "Beautiful Sunset", fill=(255, 255, 255))

    # Save image
    img.save(filepath)

def create_resized_variant(source_path, dest_path, scale=0.5):
    """Create a resized version of an image."""
    if not PIL_AVAILABLE:
        return

    img = Image.open(source_path)
    new_size = (int(img.width * scale), int(img.height * scale))
    resized = img.resize(new_size, Image.Resampling.LANCZOS)
    resized.save(dest_path)

def create_quality_variant(source_path, dest_path, quality=50):
    """Create a different quality version of a JPEG image."""
    if not PIL_AVAILABLE:
        return

    img = Image.open(source_path)
    img.save(dest_path, quality=quality)

def create_brightness_variant(source_path, dest_path, factor=1.3):
    """Create a brightness-adjusted version of an image."""
    if not PIL_AVAILABLE:
        return

    img = Image.open(source_path)
    enhancer = ImageEnhance.Brightness(img)
    brightened = enhancer.enhance(factor)
    brightened.save(dest_path)

def create_format_variant(source_path, dest_path):
    """Convert image to different format (JPG to PNG or vice versa)."""
    if not PIL_AVAILABLE:
        return

    img = Image.open(source_path)
    # Convert RGBA to RGB if saving as JPEG
    if dest_path.lower().endswith('.jpg') or dest_path.lower().endswith('.jpeg'):
        if img.mode == 'RGBA':
            img = img.convert('RGB')
    img.save(dest_path)

def create_test_archive(base_path='test_archive'):
    """
    Create test archive with real, viewable images and variations for perceptual hash testing.

    Test scenarios:
    1. Beach image: Original + resized + different quality + brightness adjusted
    2. Mountain image: Original + format converted (PNG)
    3. Sunset image: Completely different (no duplicates)
    """

    if not PIL_AVAILABLE:
        print("ERROR: PIL is required to create test images")
        print("Install with: pip install Pillow")
        return

    # Remove existing test archive
    if os.path.exists(base_path):
        shutil.rmtree(base_path)

    print(f"Creating test archive at: {base_path}")

    # Create folder structure
    folders = [
        'vacation',
        'photos/2024',
        'photos/edits',
        'backup',
        'downloads',
    ]

    for folder in folders:
        os.makedirs(os.path.join(base_path, folder), exist_ok=True)

    # Scenario 1: Beach image with variations (perceptual hash should find these)
    print("\n1. Creating beach photo with variations...")
    beach_original = os.path.join(base_path, 'vacation', 'beach.jpg')
    create_test_image(beach_original, pattern='beach', size=(400, 300))
    print(f"   Created original: {beach_original} (400x300)")

    # Resized version (smaller)
    beach_resized = os.path.join(base_path, 'photos/2024', 'beach_thumbnail.jpg')
    create_resized_variant(beach_original, beach_resized, scale=0.5)
    print(f"   Created resized: {beach_resized} (200x150, should match with perceptual hash)")

    # Different JPEG quality
    beach_compressed = os.path.join(base_path, 'backup', 'beach_compressed.jpg')
    create_quality_variant(beach_original, beach_compressed, quality=30)
    print(f"   Created compressed: {beach_compressed} (low quality, should match)")

    # Brightness adjusted
    beach_bright = os.path.join(base_path, 'photos/edits', 'beach_brightened.jpg')
    create_brightness_variant(beach_original, beach_bright, factor=1.3)
    print(f"   Created brightened: {beach_bright} (brighter, should match)")

    # Format converted to PNG
    beach_png = os.path.join(base_path, 'backup', 'beach_copy.png')
    create_format_variant(beach_original, beach_png)
    print(f"   Created PNG version: {beach_png} (different format, should match)")

    # Scenario 2: Mountain image with one variant
    print("\n2. Creating mountain photo with variant...")
    mountain_original = os.path.join(base_path, 'vacation', 'mountain.jpg')
    create_test_image(mountain_original, pattern='mountain', size=(400, 300))
    print(f"   Created original: {mountain_original}")

    mountain_resized = os.path.join(base_path, 'downloads', 'mountain_small.jpg')
    create_resized_variant(mountain_original, mountain_resized, scale=0.7)
    print(f"   Created resized: {mountain_resized} (should match)")

    # Scenario 3: Sunset image (completely different, no duplicates)
    print("\n3. Creating unique sunset photo (no duplicates)...")
    sunset_img = os.path.join(base_path, 'photos/2024', 'sunset.jpg')
    create_test_image(sunset_img, pattern='sunset', size=(400, 300))
    print(f"   Created: {sunset_img} (unique, no duplicates)")

    print("\n" + "=" * 80)
    print("Test archive created successfully!")
    print("=" * 80)
    print("\nTest scenarios:")
    print("  1. Beach photo: 5 variations (original, resized, compressed, brightened, PNG)")
    print("     - Content hash: WON'T find (different file content)")
    print("     - Perceptual hash: WILL find all 5 as similar")
    print("\n  2. Mountain photo: 2 variations (original, resized)")
    print("     - Content hash: WON'T find")
    print("     - Perceptual hash: WILL find both")
    print("\n  3. Sunset photo: Unique (no duplicates)")
    print("\nTotal files: 8 images")
    print("\nTo test:")
    print(f"\n  # Content hash (finds only exact duplicates - will find NONE):")
    print(f"  .venv/bin/python3 duplicate_finder.py {base_path} --check-hash")
    print(f"\n  # Perceptual hash (finds similar images - will find 2 groups):")
    print(f"  .venv/bin/python3 duplicate_finder.py {base_path} --check-perceptual-hash")
    print(f"\n  # Stricter perceptual threshold (may find fewer matches):")
    print(f"  .venv/bin/python3 duplicate_finder.py {base_path} --check-perceptual-hash --perceptual-threshold 5")
    print(f"\n  # More lenient threshold (finds more variations):")
    print(f"  .venv/bin/python3 duplicate_finder.py {base_path} --check-perceptual-hash --perceptual-threshold 15")
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
