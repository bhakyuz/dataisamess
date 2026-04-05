# Duplicate File Finder

A fast Python tool to find and delete duplicate files based on filename, file size, and/or modification timestamp.

## Features

- **Fast scanning**: Uses efficient file traversal with os.walk()
- **Flexible duplicate detection**: Choose which criteria to use (name, size, timestamp)
- **Timestamp support**: Includes file modification date in duplicate detection
- **Multiple deletion modes**: Interactive or automatic
- **Safe by default**: Always keeps one copy (first occurrence)
- **Detailed reporting**: Shows wasted space, file counts, and timestamps

## Usage

### 1. Find Duplicates Only (No Deletion)

```bash
# Default: Check name, size, and timestamp
python3 duplicate_finder.py /path/to/folder

# Check name and size only (ignore timestamp differences)
python3 duplicate_finder.py /path/to/folder --no-check-timestamp

# Check name only (find all files with same name regardless of size/timestamp)
python3 duplicate_finder.py /path/to/folder --no-check-size --no-check-timestamp
```

This will scan the folder and report all duplicates found based on the selected criteria.

### 2. Interactive Deletion

```bash
python3 duplicate_finder.py /path/to/folder --delete-interactive
# or shorthand:
python3 duplicate_finder.py /path/to/folder -i
```

This will prompt you for each set of duplicates, asking if you want to delete them.
- Press `y` to delete the duplicates (keeping the first occurrence)
- Press `n` or Enter to skip
- Press `q` to quit

### 3. Automatic Deletion

```bash
python3 duplicate_finder.py /path/to/folder --delete-auto
# or shorthand:
python3 duplicate_finder.py /path/to/folder -a
```

This will automatically delete all duplicates after confirmation, keeping the first occurrence of each file.

### 4. Get Help

```bash
python3 duplicate_finder.py --help
```

## Test Results

The program has been tested with the included `test_archive` folder:

**Test 1: Default criteria (name + size + timestamp)**
- Scanned: 14 files
- Found: 3 sets of duplicates (4 duplicate files with same name, size, AND timestamp)
- Wasted space: 108 bytes

**Test 2: Name + Size only (--no-check-timestamp)**
- Scanned: 14 files
- Found: 3 sets of duplicates (5 duplicate files with same name and size)
- Includes files with same name/size but different timestamps
- Wasted space: 139 bytes

**Test 3: Name only (--no-check-size --no-check-timestamp)**
- Scanned: 14 files
- Found: All files with the same filename, regardless of size or timestamp
- Useful for finding renamed versions or different versions of the same file

**After deletion:**
- All duplicates successfully removed while keeping one copy of each
- No data loss - first occurrence always preserved

## Duplicate Detection Criteria

By default, the tool checks **all three criteria** (name, size, timestamp) to identify duplicates. You can customize which criteria to use:

- `--check-name` / `--no-check-name`: Include/exclude filename
- `--check-size` / `--no-check-size`: Include/exclude file size
- `--check-timestamp` / `--no-check-timestamp`: Include/exclude modification timestamp

**Default behavior**: `--check-name --check-size --check-timestamp`

This means files are only considered duplicates if they have:
- The same filename AND
- The same size AND
- The same modification timestamp

### When to Use Different Criteria

- **Name + Size + Timestamp (default)**: Most strict - only files that are truly identical copies
- **Name + Size only**: Find files with same name and size but created at different times
- **Name only**: Find all files with the same name regardless of size or timestamp
- **Custom combinations**: Mix and match based on your needs

## How It Works

1. **Scanning**: Recursively walks through all subdirectories
2. **Identification**: Groups files by selected criteria (name, size, timestamp)
3. **Detection**: Identifies groups with 2+ files as duplicates
4. **Deletion**: Removes all but the first occurrence in each group

## Safety Features

- Always keeps the first occurrence of each duplicate
- Provides confirmation before auto-deletion
- Shows exactly which files will be kept and deleted
- Reports errors if file deletion fails
- Read-only mode by default (no deletions without explicit flags)

## Limitations

- Detects duplicates based on **metadata only** (filename, size, timestamp)
- Does not use file content hashing (faster but less accurate for detecting renamed duplicates)
- Files with identical content but different names/sizes/timestamps won't be detected
- For content-based duplicate detection, you would need to add MD5/SHA256 hashing
- Uses modification timestamp (`st_mtime`), not creation timestamp, as it's more reliable across platforms

## Examples

```bash
# Scan your photo archive (strict mode: name + size + timestamp)
python3 duplicate_finder.py ~/Pictures

# Find photos with same name and size, even if saved at different times
python3 duplicate_finder.py ~/Pictures --no-check-timestamp

# Interactively clean up downloads folder (ignore timestamps)
python3 duplicate_finder.py ~/Downloads --no-check-timestamp -i

# Find all files with duplicate names, regardless of size or timestamp
python3 duplicate_finder.py ~/Documents --no-check-size --no-check-timestamp

# Auto-clean backups using strict criteria
python3 duplicate_finder.py /backup/photos -a
```
