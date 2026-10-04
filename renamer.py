import os
import argparse
from pathlib import Path

def rename_files(target_folder, prefix, suffix, replace, with_text, dry_run):
    folder_path = Path(target_folder)
    
    if not folder_path.is_dir():
        print(f"Error: The directory '{target_folder}' does not exist or is not a directory.")
        return

    print(f"Scanning directory: {folder_path.resolve()}")
    if dry_run:
        print("--- DRY RUN MODE: No files will be modified ---\n")

    files_renamed = 0

    for file_path in folder_path.iterdir():
        if file_path.is_file():
            old_name = file_path.name
            new_name = old_name

            if replace and with_text is not None:
                new_name = new_name.replace(replace, with_text)
            
            # Extract stem and suffix for prefix/suffix addition
            stem = Path(new_name).stem
            extension = Path(new_name).suffix

            if prefix:
                stem = f"{prefix}{stem}"
            if suffix:
                stem = f"{stem}{suffix}"
            
            new_name = f"{stem}{extension}"

            if old_name != new_name:
                new_file_path = folder_path / new_name
                
                if dry_run:
                    print(f"DRY RUN: '{old_name}' -> '{new_name}'")
                else:
                    file_path.rename(new_file_path)
                    print(f"Renamed: '{old_name}' -> '{new_name}'")
                
                files_renamed += 1

    if files_renamed == 0:
        print("No files were renamed.")
    else:
        print(f"\nTotal files processed: {files_renamed}")

def main():
    parser = argparse.ArgumentParser(description="Bulk File Renamer CLI")
    parser.add_argument("target_folder", help="The folder containing files to rename")
    parser.add_argument("--prefix", type=str, help="String to add to the beginning of the filename")
    parser.add_argument("--suffix", type=str, help="String to add to the end of the filename (before extension)")
    parser.add_argument("--replace", type=str, help="String to replace in the filename")
    parser.add_argument("--with_text", type=str, default="", help="String to replace with (used with --replace)")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without renaming any files")

    args = parser.parse_args()

    # Validate that replace and with_text logic makes sense
    if args.with_text and not args.replace:
        parser.error("--with_text requires --replace to be specified.")

    rename_files(
        target_folder=args.target_folder,
        prefix=args.prefix,
        suffix=args.suffix,
        replace=args.replace,
        with_text=args.with_text,
        dry_run=args.dry_run
    )

if __name__ == "__main__":
    main()
