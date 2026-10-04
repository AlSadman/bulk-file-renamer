"""
Bulk File Renamer

A reliable, beginner-friendly command-line utility to safely rename multiple files
in a specified directory with prefix, suffix, current date, and sequential numbering options.
"""

import argparse
import datetime
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Dict, Optional


@dataclass
class RenameOptions:
    """Configuration options for file renaming operations."""
    folder: Path
    prefix: str = ""
    suffix: str = ""
    add_date: bool = False
    custom_date: str = ""
    add_number: bool = False
    start_number: int = 1
    number_padding: int = 3
    recursive: bool = False
    dry_run: bool = False


@dataclass
class RenameItem:
    """Represents a single file renaming operation and its status."""
    original_path: Path
    new_path: Path
    status: str  # 'PENDING', 'SKIP_UNCHANGED', 'CONFLICT_EXISTS', 'COLLISION_DUPLICATE', 'ERROR'
    message: str = ""


def validate_directory(path_str: str | Path) -> Path:
    """
    Validate that the provided path exists and is a directory.
    
    Raises:
        FileNotFoundError: If path does not exist.
        NotADirectoryError: If path exists but is not a directory.
    """
    target_path = Path(path_str).resolve()
    if not target_path.exists():
        raise FileNotFoundError(f"Target path does not exist: '{path_str}'")
    if not target_path.is_dir():
        raise NotADirectoryError(f"Target path is not a directory: '{path_str}'")
    return target_path


def discover_files(directory: Path, recursive: bool = False) -> List[Path]:
    """
    Discover all files inside the specified directory.
    Ignores directories. If recursive is False, only immediate files are returned.
    """
    files: List[Path] = []
    try:
        if recursive:
            entries = sorted(directory.rglob("*"))
        else:
            entries = sorted(directory.glob("*"))

        for entry in entries:
            try:
                if entry.is_file():
                    files.append(entry)
            except PermissionError:
                # Skip entries where permission is denied during check
                continue
    except PermissionError as e:
        print(f"Permission denied accessing directory '{directory}': {e}", file=sys.stderr)
        raise

    return files


def generate_new_name(
    original_path: Path,
    options: RenameOptions,
    index: int = 0
) -> str:
    """
    Generate the new filename preserving the extension based on user options.
    """
    stem = original_path.stem
    ext = original_path.suffix

    date_str = ""
    if options.add_date:
        if options.custom_date:
            date_str = options.custom_date
        else:
            date_str = datetime.date.today().isoformat()

    number_str = ""
    if options.add_number:
        num = options.start_number + index
        number_str = f"{num:0{options.number_padding}d}"

    front_parts = []
    if date_str:
        front_parts.append(date_str)
    if options.prefix:
        p = options.prefix.rstrip("_-")
        if p:
            front_parts.append(p)
    if number_str:
        front_parts.append(number_str)

    back_parts = []
    if options.suffix:
        s = options.suffix.lstrip("_-")
        if s:
            back_parts.append(s)

    front = "_".join(front_parts)
    back = "_".join(back_parts)

    new_stem = stem
    if front:
        new_stem = f"{front}_{new_stem}"
    if back:
        new_stem = f"{new_stem}_{back}"

    return f"{new_stem}{ext}"


def build_rename_plan(files: List[Path], options: RenameOptions) -> List[RenameItem]:
    """
    Build initial list of planned renames without modifying any files.
    """
    plan: List[RenameItem] = []
    for i, file_path in enumerate(files):
        new_filename = generate_new_name(file_path, options, index=i)
        new_path = file_path.parent / new_filename

        if file_path == new_path:
            item = RenameItem(
                original_path=file_path,
                new_path=new_path,
                status="SKIP_UNCHANGED",
                message="Filename unchanged"
            )
        else:
            item = RenameItem(
                original_path=file_path,
                new_path=new_path,
                status="PENDING",
                message=""
            )
        plan.append(item)

    return plan


def detect_conflicts(plan: List[RenameItem]) -> Tuple[List[RenameItem], bool]:
    """
    Analyze rename plan for potential safety conflicts:
    1. Destination file already exists on disk (and is not part of the source set).
    2. Multiple source files target the exact same destination file.

    Returns:
        Updated plan list and a boolean flag indicating if any unresolvable conflicts exist.
    """
    has_critical_conflicts = False

    # Count occurrences of destination paths across the plan
    dest_counts: Dict[Path, int] = {}
    for item in plan:
        dest_counts[item.new_path] = dest_counts.get(item.new_path, 0) + 1

    source_paths = {item.original_path for item in plan}

    for item in plan:
        if item.status == "SKIP_UNCHANGED":
            continue

        # Conflict check 1: Duplicate destination target among source files
        if dest_counts[item.new_path] > 1:
            item.status = "COLLISION_DUPLICATE"
            item.message = f"Multiple files target the same destination name '{item.new_path.name}'"
            has_critical_conflicts = True
            continue

        # Conflict check 2: Destination path already exists on disk
        if item.new_path.exists():
            item.status = "CONFLICT_EXISTS"
            item.message = f"Destination file already exists on disk: '{item.new_path.name}'"
            has_critical_conflicts = True

    return plan, has_critical_conflicts


def display_preview(plan: List[RenameItem], target_folder: Path) -> None:
    """
    Display a clean preview table showing proposed changes and potential conflicts.
    """
    print("\n" + "=" * 80)
    print("PREVIEW OF RENAME OPERATIONS")
    print("=" * 80)
    print(f"Target Directory: {target_folder}\n")

    header = f"{'OLD FILENAME':<35} -> {'NEW FILENAME':<35} {'STATUS':<15}"
    print(header)
    print("-" * 80)

    pending_count = 0
    skipped_count = 0
    conflict_count = 0

    for item in plan:
        old_rel = item.original_path.name
        new_rel = item.new_path.name

        if item.status == "PENDING":
            status_display = "OK (Planned)"
            pending_count += 1
        elif item.status == "SKIP_UNCHANGED":
            status_display = "SKIPPED (Unchanged)"
            skipped_count += 1
        else:
            status_display = f"CONFLICT! ({item.status})"
            conflict_count += 1

        print(f"{old_rel:<35} -> {new_rel:<35} {status_display:<15}")
        if item.message and item.status not in ("PENDING", "SKIP_UNCHANGED"):
            print(f"  [ERROR] {item.message}")

    print("=" * 80)
    print(f"Total files analyzed : {len(plan)}")
    print(f"Files to rename      : {pending_count}")
    print(f"Files skipped        : {skipped_count}")
    print(f"Conflicts detected   : {conflict_count}")
    print("=" * 80 + "\n")


def apply_renames(plan: List[RenameItem], dry_run: bool = False) -> Dict[str, int]:
    """
    Execute the file renames defined in the plan.
    If dry_run is True, no filesystem operations are performed.
    """
    results = {
        "found": len(plan),
        "renamed": 0,
        "skipped": 0,
        "errors": 0
    }

    if dry_run:
        for item in plan:
            if item.status == "PENDING":
                results["renamed"] += 1
            elif item.status == "SKIP_UNCHANGED":
                results["skipped"] += 1
            else:
                results["errors"] += 1
        return results

    for item in plan:
        if item.status == "SKIP_UNCHANGED":
            results["skipped"] += 1
            continue

        if item.status != "PENDING":
            results["errors"] += 1
            print(f"Skipping unsafe rename for '{item.original_path.name}': {item.message}", file=sys.stderr)
            continue

        try:
            item.original_path.rename(item.new_path)
            results["renamed"] += 1
        except Exception as e:
            results["errors"] += 1
            item.status = "ERROR"
            item.message = str(e)
            print(f"Failed to rename '{item.original_path.name}' -> '{item.new_path.name}': {e}", file=sys.stderr)

    return results


def display_summary(results: Dict[str, int], target_folder: Path, dry_run: bool = False) -> None:
    """
    Display a clear summary of the renaming results.
    """
    print("\n" + "=" * 50)
    if dry_run:
        print("DRY RUN COMPLETE (No files were changed)")
    else:
        print("RENAME OPERATION COMPLETE")
    print("=" * 50)
    print(f"Files found:       {results['found']}")
    print(f"Files renamed:     {results['renamed']}")
    print(f"Files skipped:     {results['skipped']}")
    print(f"Errors encountered: {results['errors']}")
    print(f"Output directory:  {target_folder}")
    print("=" * 50 + "\n")


def parse_arguments(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Bulk File Renamer - Safely rename files with prefix, suffix, date, and numbers."
    )
    parser.add_argument(
        "--folder", "-f",
        type=str,
        help="Target folder containing files to rename"
    )
    parser.add_argument(
        "--prefix", "-p",
        type=str,
        default="",
        help="Prefix to add before filename stem"
    )
    parser.add_argument(
        "--suffix", "-s",
        type=str,
        default="",
        help="Suffix to add after filename stem (before extension)"
    )
    parser.add_argument(
        "--date", "-d",
        action="store_true",
        help="Add current date (YYYY-MM-DD) to filename"
    )
    parser.add_argument(
        "--number", "-n",
        action="store_true",
        help="Add sequential numbering to filename"
    )
    parser.add_argument(
        "--start",
        type=int,
        default=1,
        help="Starting number for sequential numbering (default: 1)"
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=3,
        help="Zero padding width for sequential numbering (default: 3)"
    )
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Process subdirectories recursively"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying any files"
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Automatically confirm renames without prompt"
    )

    return parser.parse_args(args)


def run_interactive_menu() -> Optional[RenameOptions]:
    """
    Guide the user through an interactive terminal menu if CLI arguments were not fully provided.
    """
    print("\n" + "=" * 50)
    print("      BULK FILE RENAMER - INTERACTIVE MODE      ")
    print("=" * 50)

    while True:
        folder_input = input("\nEnter target folder path (or 'q' to quit): ").strip()
        if folder_input.lower() == 'q':
            return None
        if not folder_input:
            print("Folder path cannot be empty.")
            continue
        try:
            folder_path = validate_directory(folder_input)
            break
        except (FileNotFoundError, NotADirectoryError) as e:
            print(f"Error: {e}")

    try:
        files = discover_files(folder_path, recursive=False)
    except PermissionError:
        return None

    print(f"\nFound {len(files)} file(s) in '{folder_path}'.")

    print("\nChoose an operation:")
    print("1. Add prefix")
    print("2. Add suffix")
    print("3. Add date")
    print("4. Add prefix + suffix")
    print("5. Add date + prefix")
    print("6. Add sequential numbering")
    print("7. Custom combination")
    print("8. Exit")

    choice = input("\nEnter choice [1-8]: ").strip()

    if choice == '8' or choice.lower() == 'q':
        return None

    prefix = ""
    suffix = ""
    add_date = False
    add_number = False
    start_number = 1
    number_padding = 3

    if choice == '1':
        prefix = input("Enter prefix: ").strip()
    elif choice == '2':
        suffix = input("Enter suffix: ").strip()
    elif choice == '3':
        add_date = True
    elif choice == '4':
        prefix = input("Enter prefix: ").strip()
        suffix = input("Enter suffix: ").strip()
    elif choice == '5':
        add_date = True
        prefix = input("Enter prefix: ").strip()
    elif choice == '6':
        add_number = True
        start_str = input("Enter starting number (default 1): ").strip()
        if start_str.isdigit():
            start_number = int(start_str)
        pad_str = input("Enter zero padding width (default 3): ").strip()
        if pad_str.isdigit():
            number_padding = int(pad_str)
    elif choice == '7':
        d_input = input("Add current date? (y/N): ").strip().lower()
        add_date = d_input in ('y', 'yes')

        prefix = input("Enter prefix (leave blank for none): ").strip()

        n_input = input("Add sequential numbering? (y/N): ").strip().lower()
        if n_input in ('y', 'yes'):
            add_number = True
            start_str = input("Enter starting number (default 1): ").strip()
            if start_str.isdigit():
                start_number = int(start_str)
            pad_str = input("Enter zero padding width (default 3): ").strip()
            if pad_str.isdigit():
                number_padding = int(pad_str)

        suffix = input("Enter suffix (leave blank for none): ").strip()
    else:
        print("Invalid choice selected. Exiting interactive mode.")
        return None

    rec_input = input("Process subdirectories recursively? (y/N): ").strip().lower()
    recursive = rec_input in ('y', 'yes')

    dry_input = input("Run as dry-run preview only? (y/N): ").strip().lower()
    dry_run = dry_input in ('y', 'yes')

    return RenameOptions(
        folder=folder_path,
        prefix=prefix,
        suffix=suffix,
        add_date=add_date,
        add_number=add_number,
        start_number=start_number,
        number_padding=number_padding,
        recursive=recursive,
        dry_run=dry_run
    )


def main(cli_args: Optional[List[str]] = None) -> int:
    """
    Main entry point for Bulk File Renamer.
    """
    try:
        parsed = parse_arguments(cli_args)

        # Determine mode: CLI flags or Interactive
        if parsed.folder:
            try:
                folder_path = validate_directory(parsed.folder)
            except (FileNotFoundError, NotADirectoryError) as e:
                print(f"Error: {e}", file=sys.stderr)
                return 1

            options = RenameOptions(
                folder=folder_path,
                prefix=parsed.prefix,
                suffix=parsed.suffix,
                add_date=parsed.date,
                add_number=parsed.number,
                start_number=parsed.start,
                number_padding=parsed.padding,
                recursive=parsed.recursive,
                dry_run=parsed.dry_run
            )
        else:
            options = run_interactive_menu()
            if options is None:
                print("Operation cancelled. Exiting.")
                return 0

        # Validate that at least one modification rule is specified
        if not any([options.prefix, options.suffix, options.add_date, options.add_number]):
            print("Notice: No modification options (prefix, suffix, date, number) were specified.")

        # Discover files
        try:
            files = discover_files(options.folder, recursive=options.recursive)
        except Exception as e:
            print(f"Error discovering files: {e}", file=sys.stderr)
            return 1

        if not files:
            print(f"No files found in '{options.folder}'. Nothing to rename.")
            return 0

        # Build plan and check for conflicts
        plan = build_rename_plan(files, options)
        plan, has_conflicts = detect_conflicts(plan)

        # Display preview
        display_preview(plan, options.folder)

        if has_conflicts:
            print("CONFLICT DETECTED: Cannot safely rename files due to errors shown above.")
            print("Operation aborted to prevent accidental data loss or file overwrites.")
            return 1

        if options.dry_run:
            results = apply_renames(plan, dry_run=True)
            display_summary(results, options.folder, dry_run=True)
            return 0

        # Ask for user confirmation if CLI --yes was not provided
        auto_yes = parsed.yes if parsed.folder else False
        if not auto_yes:
            confirm = input("Apply these changes? [y/N]: ").strip().lower()
            if confirm not in ("y", "yes"):
                print("\nOperation cancelled. No files were changed.")
                return 0

        # Apply renames
        results = apply_renames(plan, dry_run=False)
        display_summary(results, options.folder, dry_run=False)
        return 0

    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user (Ctrl+C). No further changes made.")
        return 130
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
