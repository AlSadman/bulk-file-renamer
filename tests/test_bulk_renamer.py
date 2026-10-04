"""
Unit test suite for Bulk File Renamer application.
Tests all renaming options, conflict detection, dry run, and recursive operations safely
using temporary isolated directories.
"""

import datetime
import tempfile
import unittest
from pathlib import Path

from src.bulk_renamer import (
    RenameOptions,
    validate_directory,
    discover_files,
    generate_new_name,
    build_rename_plan,
    detect_conflicts,
    apply_renames,
    main,
)


class TestBulkRenamer(unittest.TestCase):

    def setUp(self):
        """Create a temporary directory for safe test operations."""
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_dir = Path(self.temp_dir_obj.name)

    def tearDown(self):
        """Clean up the temporary directory after tests."""
        self.temp_dir_obj.cleanup()

    def _create_sample_file(self, filename: str, content: str = "dummy content") -> Path:
        """Helper method to create dummy files inside the temporary directory."""
        path = self.temp_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_validate_directory_valid(self):
        """Verify that validate_directory returns resolved path for valid directory."""
        validated = validate_directory(self.temp_dir)
        self.assertEqual(validated, self.temp_dir.resolve())

    def test_validate_directory_non_existent(self):
        """Verify FileNotFoundError raised for non-existent path."""
        non_existent = self.temp_dir / "does_not_exist"
        with self.assertRaises(FileNotFoundError):
            validate_directory(non_existent)

    def test_validate_directory_file(self):
        """Verify NotADirectoryError raised when path points to a file."""
        file_path = self._create_sample_file("test.txt")
        with self.assertRaises(NotADirectoryError):
            validate_directory(file_path)

    def test_prefix_renaming(self):
        """Test adding a prefix to filenames."""
        f1 = self._create_sample_file("photo1.jpg")
        f2 = self._create_sample_file("photo2.jpg")

        options = RenameOptions(folder=self.temp_dir, prefix="Trip_")
        files = discover_files(self.temp_dir)
        plan = build_rename_plan(files, options)
        plan, has_conflicts = detect_conflicts(plan)

        self.assertFalse(has_conflicts)
        apply_renames(plan, dry_run=False)

        self.assertTrue((self.temp_dir / "Trip_photo1.jpg").exists())
        self.assertTrue((self.temp_dir / "Trip_photo2.jpg").exists())
        self.assertFalse(f1.exists())
        self.assertFalse(f2.exists())

    def test_suffix_renaming(self):
        """Test adding a suffix to filenames before extension."""
        f1 = self._create_sample_file("report.pdf")

        options = RenameOptions(folder=self.temp_dir, suffix="_final")
        files = discover_files(self.temp_dir)
        plan = build_rename_plan(files, options)

        apply_renames(plan, dry_run=False)

        self.assertTrue((self.temp_dir / "report_final.pdf").exists())
        self.assertFalse(f1.exists())

    def test_extension_preservation(self):
        """Ensure file extension is preserved unchanged across operations."""
        f1 = self._create_sample_file("document.docx")

        options = RenameOptions(folder=self.temp_dir, prefix="Archive_", suffix="_v2")
        files = discover_files(self.temp_dir)
        plan = build_rename_plan(files, options)

        apply_renames(plan, dry_run=False)

        renamed = self.temp_dir / "Archive_document_v2.docx"
        self.assertTrue(renamed.exists())

    def test_date_generation(self):
        """Test adding date to filename."""
        self._create_sample_file("notes.txt")
        today_str = datetime.date.today().isoformat()

        options = RenameOptions(folder=self.temp_dir, add_date=True)
        files = discover_files(self.temp_dir)
        plan = build_rename_plan(files, options)

        apply_renames(plan, dry_run=False)

        expected = self.temp_dir / f"{today_str}_notes.txt"
        self.assertTrue(expected.exists())

    def test_sequential_numbering(self):
        """Test sequential numbering with padding and custom start."""
        self._create_sample_file("img_a.png")
        self._create_sample_file("img_b.png")

        options = RenameOptions(
            folder=self.temp_dir,
            add_number=True,
            start_number=10,
            number_padding=3
        )
        files = discover_files(self.temp_dir)
        plan = build_rename_plan(files, options)

        apply_renames(plan, dry_run=False)

        self.assertTrue((self.temp_dir / "010_img_a.png").exists())
        self.assertTrue((self.temp_dir / "011_img_b.png").exists())

    def test_dry_run_behavior(self):
        """Test that dry-run mode does not modify files on disk."""
        f1 = self._create_sample_file("original.txt")

        options = RenameOptions(folder=self.temp_dir, prefix="New_")
        files = discover_files(self.temp_dir)
        plan = build_rename_plan(files, options)

        results = apply_renames(plan, dry_run=True)

        self.assertEqual(results["renamed"], 1)
        self.assertTrue(f1.exists())
        self.assertFalse((self.temp_dir / "New_original.txt").exists())

    def test_existing_destination_conflict(self):
        """Detect conflict when target filename already exists on disk."""
        self._create_sample_file("file1.txt")
        self._create_sample_file("Prefix_file1.txt")  # Collision on disk

        options = RenameOptions(folder=self.temp_dir, prefix="Prefix_")
        files = discover_files(self.temp_dir)
        plan = build_rename_plan(files, options)
        plan, has_conflicts = detect_conflicts(plan)

        self.assertTrue(has_conflicts)
        conflict_items = [item for item in plan if item.status == "CONFLICT_EXISTS"]
        self.assertEqual(len(conflict_items), 1)
        self.assertEqual(conflict_items[0].original_path.name, "file1.txt")

    def test_duplicate_destination_conflict(self):
        """Detect collision when two source files target the exact same new filename."""
        # Setup files that would collide when suffix is added if logic forced them to same target
        f1 = self._create_sample_file("a.txt")
        f2 = self._create_sample_file("b.txt")

        # Manually construct a plan where both target the same file
        target = self.temp_dir / "same_target.txt"
        item1 = build_rename_plan([f1], RenameOptions(folder=self.temp_dir, prefix="temp"))[0]
        item1.new_path = target
        item1.status = "PENDING"

        item2 = build_rename_plan([f2], RenameOptions(folder=self.temp_dir, prefix="temp"))[0]
        item2.new_path = target
        item2.status = "PENDING"

        plan, has_conflicts = detect_conflicts([item1, item2])
        self.assertTrue(has_conflicts)
        self.assertEqual(plan[0].status, "COLLISION_DUPLICATE")
        self.assertEqual(plan[1].status, "COLLISION_DUPLICATE")

    def test_unchanged_filename(self):
        """Verify that unchanged filenames are flagged as SKIP_UNCHANGED."""
        f1 = self._create_sample_file("sample.txt")

        options = RenameOptions(folder=self.temp_dir)  # No prefix, suffix, date, number
        files = discover_files(self.temp_dir)
        plan = build_rename_plan(files, options)

        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0].status, "SKIP_UNCHANGED")

    def test_non_recursive_mode(self):
        """Verify that non-recursive mode ignores files in subdirectories."""
        self._create_sample_file("root.txt")
        self._create_sample_file("sub/nested.txt")

        files = discover_files(self.temp_dir, recursive=False)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "root.txt")

    def test_recursive_mode(self):
        """Verify that recursive mode finds files in subdirectories and preserves structure."""
        self._create_sample_file("root.txt")
        sub_file = self._create_sample_file("sub/nested.txt")

        options = RenameOptions(folder=self.temp_dir, prefix="Rec_", recursive=True)
        files = discover_files(self.temp_dir, recursive=True)
        self.assertEqual(len(files), 2)

        plan = build_rename_plan(files, options)
        apply_renames(plan, dry_run=False)

        self.assertTrue((self.temp_dir / "Rec_root.txt").exists())
        self.assertTrue((self.temp_dir / "sub" / "Rec_nested.txt").exists())
        self.assertFalse(sub_file.exists())

    def test_cli_main_dry_run(self):
        """Test end-to-end execution of main() using CLI flags with --dry-run."""
        self._create_sample_file("cli_test.txt")

        exit_code = main([
            "--folder", str(self.temp_dir),
            "--prefix", "CLI_",
            "--dry-run"
        ])

        self.assertEqual(exit_code, 0)
        self.assertTrue((self.temp_dir / "cli_test.txt").exists())


if __name__ == "__main__":
    unittest.main()
