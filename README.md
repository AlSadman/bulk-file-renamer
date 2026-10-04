# Bulk File Renamer

A simple, dependency-free Python CLI tool to bulk rename files in a directory.

## Features
*   **Zero Dependencies**: Uses only Python standard libraries (`os`, `pathlib`, `argparse`).
*   **Prefix & Suffix**: Easily prepend or append strings to filenames.
*   **Find & Replace**: Replace specific text within filenames.
*   **Dry Run Safety**: Preview changes without modifying any files on disk using the `--dry-run` flag.

## Tech Stack
*   Python 3

## How to Use

1.  **Clone or download** this repository.
2.  **Open a terminal** and navigate to the project directory.

### Basic Examples

**Preview changes (Dry Run - Safe):**
```bash
python renamer.py ./test_sandbox --prefix "NEW_" --dry-run
```

**Add a prefix to all files:**
```bash
python renamer.py ./test_sandbox --prefix "2023_"
```

**Find and replace text:**
```bash
python renamer.py ./test_sandbox --replace "report" --with_text "final_report"
```

**Combine options:**
```bash
python renamer.py ./test_sandbox --prefix "v2_" --replace "raw" --with_text "clean"
```
