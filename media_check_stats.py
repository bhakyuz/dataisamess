#!/usr/bin/env python3
"""
Media Camera Statistics Analyzer
Analyzes images and videos to extract camera information from metadata.
Groups files by camera make/model and shows statistics.
"""

import os
import sys
import argparse
from collections import defaultdict
from pathlib import Path
import exifread
from pymediainfo import MediaInfo
from tqdm import tqdm


# File type definitions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif',
                   '.cr2', '.nef', '.arw', '.dng', '.orf', '.rw2',
                   '.cr3', '.raf', '.raw', '.pef', '.srw'}

VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.m4v',
                   '.wmv', '.flv', '.webm', '.mts', '.m2ts',
                   '.3gp', '.mpg', '.mpeg', '.ogv'}


def extract_image_metadata(filepath):
    """
    Extract camera make and model from image EXIF data.

    Args:
        filepath: Path to image file

    Returns:
        tuple: (make, model) or (None, None) if no EXIF data
    """
    try:
        with open(filepath, 'rb') as f:
            tags = exifread.process_file(f, details=False)

        make = tags.get('Image Make')
        model = tags.get('Image Model')

        # Convert to string and strip whitespace
        make = str(make).strip() if make else None
        model = str(model).strip() if model else None

        return make, model
    except Exception as e:
        # If we can't read the file, return None
        return None, None


def extract_video_metadata(filepath):
    """
    Extract camera make and model from video metadata.

    Args:
        filepath: Path to video file

    Returns:
        tuple: (make, model) or (None, None) if no metadata
    """
    try:
        media_info = MediaInfo.parse(filepath)

        make = None
        model = None

        for track in media_info.tracks:
            if track.track_type == 'General':
                # Try different possible tag names
                make = (getattr(track, 'make', None) or
                       getattr(track, 'encoded_application', None) or
                       getattr(track, 'publisher', None))
                model = (getattr(track, 'model', None) or
                        getattr(track, 'camera_model_name', None))

                # Also check for com.apple.quicktime tags (common in MOV files)
                if hasattr(track, 'com_apple_quicktime_make'):
                    make = track.com_apple_quicktime_make
                if hasattr(track, 'com_apple_quicktime_model'):
                    model = track.com_apple_quicktime_model

                break

        # Strip whitespace if found
        make = make.strip() if make else None
        model = model.strip() if model else None

        return make, model
    except Exception as e:
        return None, None


def select_smart_examples(file_paths, max_examples=5):
    """
    Select example file paths, preferring files from different directories.

    Args:
        file_paths: List of file paths
        max_examples: Maximum number of examples to return

    Returns:
        List of selected file paths
    """
    if len(file_paths) <= max_examples:
        return file_paths

    # Track which directories we've used
    selected = []
    used_dirs = set()

    # First pass: select one file from each unique directory
    for filepath in file_paths:
        if len(selected) >= max_examples:
            break

        directory = os.path.dirname(filepath)
        if directory not in used_dirs:
            selected.append(filepath)
            used_dirs.add(directory)

    # Second pass: if we haven't reached max_examples, add more files
    if len(selected) < max_examples:
        for filepath in file_paths:
            if len(selected) >= max_examples:
                break
            if filepath not in selected:
                selected.append(filepath)

    return selected


def analyze_media_files(root_path, max_examples=5, show_progress=True):
    """
    Analyze all media files in the given directory.

    Args:
        root_path: Root directory to search
        max_examples: Number of example paths to store per camera
        show_progress: Whether to show progress bar

    Returns:
        tuple: (camera_data, other_files_count, total_images, total_videos)
    """
    camera_data = defaultdict(lambda: {
        'make': None,
        'model': None,
        'count': 0,
        'examples': [],
        'file_types': defaultdict(int)
    })

    other_files = defaultdict(int)
    total_images = 0
    total_videos = 0

    # Collect all files first for progress bar
    all_files = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        for filename in filenames:
            all_files.append(os.path.join(dirpath, filename))

    # Process files with progress bar
    iterator = tqdm(all_files, desc="Processing files", disable=not show_progress)

    for filepath in iterator:
        ext = os.path.splitext(filepath)[1].lower()

        # Determine file type
        is_image = ext in IMAGE_EXTENSIONS
        is_video = ext in VIDEO_EXTENSIONS

        if not is_image and not is_video:
            # Track other file types
            if ext:
                other_files[ext[1:]] += 1  # Remove the dot
            else:
                other_files['no_extension'] += 1
            continue

        # Extract metadata
        if is_image:
            make, model = extract_image_metadata(filepath)
            total_images += 1
        else:  # is_video
            make, model = extract_video_metadata(filepath)
            total_videos += 1

        # Handle partial metadata
        make = make if make else "Unknown"
        model = model if model else "Unknown"

        # Create unique key for this camera
        key = f"{make}|{model}"

        # Update camera data
        camera_data[key]['make'] = make
        camera_data[key]['model'] = model
        camera_data[key]['count'] += 1
        camera_data[key]['examples'].append(filepath)
        camera_data[key]['file_types'][ext[1:]] += 1  # Remove dot from extension

    # Select smart examples for each camera
    for key in camera_data:
        examples = camera_data[key]['examples']
        camera_data[key]['examples'] = select_smart_examples(examples, max_examples)

    return dict(camera_data), dict(other_files), total_images, total_videos


def display_results(camera_data, other_files, total_images, total_videos, root_path):
    """
    Display the analysis results in a formatted way.

    Args:
        camera_data: Dictionary of camera statistics
        other_files: Dictionary of other file type counts
        total_images: Total number of images processed
        total_videos: Total number of videos processed
        root_path: Root path that was analyzed
    """
    print("\n" + "="*60)
    print("Media Camera Statistics")
    print("="*60)
    print(f"Analyzed: {root_path}")
    print(f"Found: {total_images + total_videos:,} media files ({total_images:,} images, {total_videos:,} videos)")
    print()

    # Sort cameras by count (descending)
    sorted_cameras = sorted(camera_data.items(),
                           key=lambda x: x[1]['count'],
                           reverse=True)

    # Display each camera
    for key, data in sorted_cameras:
        make = data['make']
        model = data['model']
        count = data['count']

        print(f"{make} | {model} ({count:,} files)")

        # Show file types
        file_types_str = ", ".join([f"{ext.upper()} ({cnt})"
                                   for ext, cnt in sorted(data['file_types'].items())])
        print(f"  File types: {file_types_str}")

        # Show examples
        print("  Examples:")
        for example in data['examples']:
            print(f"    • {example}")

        print()

    # Display other file types if any
    if other_files:
        print("-" * 60)
        print("Other file types found (not analyzed):")
        for ext, count in sorted(other_files.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {ext.upper()}: {count:,} files")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Analyze media files and extract camera statistics from metadata.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze all media files in a directory
  python media_check_stats.py /path/to/photos

  # Show more examples per camera
  python media_check_stats.py /path/to/photos --max-examples 10

  # Disable progress bar
  python media_check_stats.py /path/to/photos --no-progress
        """
    )

    parser.add_argument(
        'path',
        help='Directory to analyze'
    )

    parser.add_argument(
        '--max-examples',
        type=int,
        default=5,
        help='Number of example paths to show per camera (default: 5)'
    )

    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress bar'
    )

    args = parser.parse_args()

    # Validate path
    if not os.path.isdir(args.path):
        print(f"Error: '{args.path}' is not a valid directory", file=sys.stderr)
        sys.exit(1)

    # Analyze files
    camera_data, other_files, total_images, total_videos = analyze_media_files(
        args.path,
        max_examples=args.max_examples,
        show_progress=not args.no_progress
    )

    # Display results
    display_results(camera_data, other_files, total_images, total_videos, args.path)


if __name__ == '__main__':
    main()
