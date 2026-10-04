# Bulk File Renamer

A lightweight, reliable, beginner-readable command-line utility built in Python to safely batch-rename files within a directory. 

Whether organizing event photos, renaming academic assignments, managing downloads, or preparing documents for upload, **Bulk File Renamer** provides a intuitive interactive menu and flexible CLI options—complete with dry-run previews and safety guardrails to ensure zero accidental file overwrites.

---

## Features

- **Prefix & Suffix Support**: Add custom text before the filename stem or after the stem (preserving file extensions).
- **Automated Date Stamping**: Prepend or append the runtime current date (`YYYY-MM-DD`).
- **Zero-Padded Sequential Numbering**: Add configurable numbered ordering (e.g., `001_`, `002_`).
- **Combination Operations**: Seamlessly combine date, prefix, numbering, original stem, and suffix.
- **Dry-Run Preview**: Preview exact rename operations and statuses before touching disk.
- **Pre-Execution Conflict Detection**: Identifies target collisions or existing file conflicts prior to execution.
- **Extension Preservation**: Handles filename stems and extensions separately so `.pdf`, `.jpg`, `.docx`, etc. remain intact.
- **Recursive Directory Handling**: Optional flag to process nested directories in-place without flattening folders.
- **Dual Interface**: Runs in guided interactive menu mode or direct CLI flag mode.

---

## Why This Project?

Manual file renaming is tedious and error-prone. While basic batch utilities exist, many lack visual previews or overwrite files silently when conflicts occur. **Bulk File Renamer** was built as a clean, production-ready tool that balances safety and ease of use, serving as both a practical everyday utility and an exemplary standard-library Python repository.

---

## Technologies

- **Python 3.10+**
- `pathlib` (Object-oriented filesystem navigation)
- `argparse` (Command-line option parsing)
- `datetime` (Runtime date generation)
- `typing` & `dataclasses` (Strong typing and clean data modeling)
- `unittest` (Standard-library test automation)

---

## Installation

No external dependencies are required. This utility relies exclusively on Python standard library modules.

1. Ensure Python 3.10 or higher is installed:
   ```bash
   python --version
   ```
2. Clone the repository:
   ```bash
   git clone https://github.com/Turzo/bulk-file-renamer.git
   cd bulk-file-renamer
   ```

---

## Usage

### Interactive Mode

Simply launch the script without options to start the step-by-step interactive menu:

```bash
python src/bulk_renamer.py
```

#### Example Menu:
```text
==================================================
      BULK FILE RENAMER - INTERACTIVE MODE      
==================================================

Enter target folder path (or 'q' to quit): demo_files

Found 5 file(s) in 'C:\BulkFileRenamer\demo_files'.

Choose an operation:
1. Add prefix
2. Add suffix
3. Add date
4. Add prefix + suffix
5. Add date + prefix
6. Add sequential numbering
7. Custom combination
8. Exit

Enter choice [1-8]: 5
Enter prefix: Trip_
Process subdirectories recursively? (y/N): n
Run as dry-run preview only? (y/N): n
```

---

### Command-Line Arguments (CLI Mode)

Run `python src/bulk_renamer.py --help` to view all command options:

```bash
python src/bulk_renamer.py --help
```

| Flag | Description | Default |
| --- | --- | --- |
| `--folder`, `-f` | Target directory containing files to rename | Required for CLI mode |
| `--prefix`, `-p` | Text prefix to add before filename stem | `""` |
| `--suffix`, `-s` | Text suffix to add after stem (before extension) | `""` |
| `--date`, `-d` | Prepend current runtime date (`YYYY-MM-DD`) | `False` |
| `--number`, `-n` | Prepend sequential zero-padded numbering | `False` |
| `--start` | Starting integer for sequential numbering | `1` |
| `--padding` | Zero-padding width for numbers | `3` |
| `--recursive`, `-r` | Process subdirectories recursively | `False` |
| `--dry-run` | Display preview without modifying disk files | `False` |
| `--yes`, `-y` | Confirm renames automatically without prompt | `False` |

---

## Command-Line Examples

#### 1. Add a Prefix to All Files
```bash
python src/bulk_renamer.py --folder demo_files --prefix "Trip_"
```

#### 2. Add Date + Prefix with Dry-Run Preview
```bash
python src/bulk_renamer.py --folder demo_files --date --prefix "Project_" --dry-run
```

#### 3. Sequential Numbering starting at 100
```bash
python src/bulk_renamer.py --folder demo_files --number --start 100 --padding 3
```

#### 4. Recursive Rename in Nested Subdirectories
```bash
python src/bulk_renamer.py --folder demo_files --prefix "Archive_" --recursive
```

---

## Dry Run

Using `--dry-run` allows you to inspect all proposed renaming operations without making any changes to your files:

```bash
python src/bulk_renamer.py --folder demo_files --prefix "Demo_" --dry-run
```

#### Sample Dry Run Output:
```text
================================================================================
PREVIEW OF RENAME OPERATIONS
================================================================================
Target Directory: C:\BulkFileRenamer\demo_files

OLD FILENAME                        -> NEW FILENAME                        STATUS         
--------------------------------------------------------------------------------
data.csv                            -> Demo_data.csv                       OK (Planned)   
notes.txt                           -> Demo_notes.txt                      OK (Planned)   
photo1.jpg                          -> Demo_photo1.jpg                     OK (Planned)   
photo2.jpg                          -> Demo_photo2.jpg                     OK (Planned)   
report.pdf                          -> Demo_report.pdf                     OK (Planned)   
================================================================================
Total files analyzed : 5
Files to rename      : 5
Files skipped        : 0
Conflicts detected   : 0
================================================================================

==================================================
DRY RUN COMPLETE (No files were changed)
==================================================
Files found:       5
Files renamed:     5
Files skipped:     0
Errors encountered: 0
Output directory:  C:\BulkFileRenamer\demo_files
==================================================
```

---

## Safety Features

1. **Pre-Execution Conflict Detection**: Scans for existing target filenames on disk or name collisions within the batch *before* modifying any file.
2. **Explicit User Confirmation**: Prompts for confirmation (`Apply these changes? [y/N]:`) with a safe default of `NO`.
3. **No Overwrites**: Operations abort cleanly if any target file already exists.
4. **Extension Isolation**: Stems and extensions are separated cleanly so extensions are never altered or lost.
5. **Graceful Interrupt Handling**: Responds to `Ctrl+C` cleanly without unhandled stack trace dumps.

---

## Project Structure

```text
C:\BulkFileRenamer
│
├── src
│   └── bulk_renamer.py       # Core application logic and CLI/Interactive entry points
│
├── tests
│   └── test_bulk_renamer.py  # Standard unittest test suite
│
├── demo_files                # Isolated test directory for safe demonstrations
│   └── README.md
│
├── screenshots               # Visual outputs and terminal documentation
│   └── README.md
│
├── README.md                 # Project documentation
├── requirements.txt          # Dependency manifest (zero external packages)
├── .gitignore                # Python git ignore rules
└── LICENSE                   # MIT License
```

---

## Testing

Run the unit test suite locally using Python's standard `unittest` runner:

```bash
python -m unittest discover -s tests -v
```

All tests operate within temporary, isolated directories and will never modify personal user files.

---

## Example Before & After

| Original Filename | Renaming Rule Applied | Final Filename |
| --- | --- | --- |
| `photo1.jpg` | Prefix `Trip_` | `Trip_photo1.jpg` |
| `report.pdf` | Suffix `_final` | `report_final.pdf` |
| `notes.txt` | Date + Prefix `2026-10-05_Draft_` | `2026-10-05_Draft_notes.txt` |
| `data.csv` | Numbering `--number --start 1` | `001_data.csv` |

---

## Limitations

- **Case Sensitivity on Windows**: On case-insensitive file systems (such as Windows default NTFS), renaming `file.txt` to `FILE.txt` may require intermediate renaming steps.
- **Standard Rename**: Does not support regular expression (regex) patterns or EXIF metadata parsing out of the box in the initial standard library build.

---

## Future Improvements

- [ ] Multi-level Undo / Rollback log file generation
- [ ] Regular expression (Regex) search and replace support
- [ ] EXIF camera metadata date extraction for photos
- [ ] Configurable template syntax (e.g. `{date}_{prefix}_{orig}`)
- [ ] Cross-platform Desktop GUI interface (Tkinter / PySimpleGUI)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
