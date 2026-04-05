# Duplicate File Finder

A fast Python tool to find and delete duplicate files based on filename, file size, modification timestamp, or **content hash**.

## Features

- **Fast scanning**: Uses efficient file traversal with os.walk()
- **Flexible duplicate detection**: Choose which criteria to use (name, size, timestamp, or hash)
- **Content hash detection**: Find true duplicates regardless of filename or timestamp (SHA-256, SHA-1, MD5)
- **Timestamp support**: Includes file modification date in duplicate detection
- **Multiple deletion modes**: Interactive (with single-key input) or automatic
- **Single-key interactive mode**: Press y/n/q without hitting Enter - instant response!
- **Input validation**: Invalid keys are rejected with helpful error messages
- **Progress tracking**: Shows real-time progress when hashing files
- **Safe by default**: Always keeps one copy (first occurrence)
- **Detailed reporting**: Shows wasted space, file counts, timestamps, and hashes

## Usage

### 1. Find Duplicates Only (No Deletion)

```bash
# Default: Check name, size, and timestamp (fast metadata check)
python3 duplicate_finder.py /path/to/folder

# Content hash: Most accurate (finds renamed duplicates, slower)
python3 duplicate_finder.py /path/to/folder --check-hash

# Use MD5 instead of SHA-256 for faster hashing
python3 duplicate_finder.py /path/to/folder --check-hash --hash-algorithm md5

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
- **Single-key input**: No need to press Enter! Just press the key and it will respond immediately
- Invalid keys will show an error and ask again

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

The program has been tested with various test archives:

**Test 1: Content Hash Detection (--check-hash)**
- Test case: 3 files with identical content but different names and timestamps
  - `beach.jpg` (modified: 18:42:38)
  - `beach_copy.jpg` (modified: 18:42:39)
  - `vacation_pic.jpg` (modified: 18:42:40)
- Result: Found 1 set of duplicates (3 files)
- **Metadata-based detection**: Found NO duplicates (different names)
- **Hash-based detection**: Found ALL 3 duplicates (same content)
- Demonstrates: Hash detection finds renamed/moved duplicates

**Test 2: Default criteria (name + size + timestamp)**
- Scanned: 14 files
- Found: 3 sets of duplicates (4 duplicate files with same name, size, AND timestamp)
- Wasted space: 108 bytes

**Test 3: Name + Size only (--no-check-timestamp)**
- Scanned: 14 files
- Found: 3 sets of duplicates (5 duplicate files with same name and size)
- Includes files with same name/size but different timestamps
- Wasted space: 139 bytes

**Test 4: Hash algorithms**
- Tested: MD5, SHA-1, SHA-256
- All algorithms correctly identified duplicates
- SHA-256: Most secure, slightly slower
- MD5: Fastest, sufficient for duplicate detection

**After deletion:**
- All duplicates successfully removed while keeping one copy of each
- No data loss - first occurrence always preserved

## Duplicate Detection Criteria

### Metadata-Based Detection (Default - Fast)

By default, the tool checks **all three metadata criteria** (name, size, timestamp) to identify duplicates. You can customize which criteria to use:

- `--check-name` / `--no-check-name`: Include/exclude filename
- `--check-size` / `--no-check-size`: Include/exclude file size
- `--check-timestamp` / `--no-check-timestamp`: Include/exclude modification timestamp

**Default behavior**: `--check-name --check-size --check-timestamp`

This means files are only considered duplicates if they have:
- The same filename AND
- The same size AND
- The same modification timestamp

### Content Hash Detection (Most Accurate - Slower)

Use `--check-hash` for true content-based duplicate detection:

- `--check-hash`: Enable content hash comparison (overrides all other criteria)
- `--hash-algorithm [md5|sha1|sha256]`: Choose hash algorithm (default: sha256)

**Hash mode behavior**: Files are considered duplicates if they have the **exact same content**, regardless of:
- Filename (beach.jpg vs vacation_pic.jpg)
- File size metadata
- Modification timestamp

### When to Use Different Criteria

- **Content Hash (--check-hash)**: **MOST ACCURATE** - finds all true duplicates even if renamed or modified timestamp
  - Use for: Finding renamed duplicates, identical files across different folders
  - Speed: Slower (must read all file content)
  - Best for: Photo archives, backup cleanup, finding copied files

- **Name + Size + Timestamp (default)**: Fast metadata check - only exact copies
  - Use for: Quick scans, finding obvious duplicates
  - Speed: Very fast (only reads file metadata)

- **Name + Size only**: Find files with same name and size but created at different times
  - Use for: Files copied at different times

- **Name only**: Find all files with the same name regardless of size or timestamp
  - Use for: Finding different versions of same file

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

**Metadata Mode (default):**
- Detects duplicates based on **metadata only** (filename, size, timestamp)
- Files with identical content but different names won't be detected
- Use `--check-hash` for content-based detection

**Hash Mode (--check-hash):**
- Slower than metadata detection (must read entire file content)
- Memory efficient (processes files in 8KB chunks)
- Hash collisions are theoretically possible but extremely rare with SHA-256

**General:**
- Uses modification timestamp (`st_mtime`), not creation timestamp, as it's more reliable across platforms
- Symbolic links are followed and treated as regular files
- Hidden files (starting with `.`) are included in scans

## Examples

```bash
# Find true duplicates by content (most accurate, finds renamed files)
python3 duplicate_finder.py ~/Pictures --check-hash

# Find and delete content duplicates interactively
python3 duplicate_finder.py ~/Pictures --check-hash -i

# Use faster MD5 hash for large archives
python3 duplicate_finder.py ~/Videos --check-hash --hash-algorithm md5

# Scan your photo archive (fast metadata mode: name + size + timestamp)
python3 duplicate_finder.py ~/Pictures

# Find photos with same name and size, even if saved at different times
python3 duplicate_finder.py ~/Pictures --no-check-timestamp

# Interactively clean up downloads folder (ignore timestamps)
python3 duplicate_finder.py ~/Downloads --no-check-timestamp -i

# Find all files with duplicate names, regardless of size or timestamp
python3 duplicate_finder.py ~/Documents --no-check-size --no-check-timestamp

# Auto-clean backups using content hash
python3 duplicate_finder.py /backup/photos --check-hash -a
```
