import os
import shutil
import tempfile
import unittest

from kombat.crawlers.system_crawler import SystemCrawler


class TestSystemCrawler(unittest.TestCase):
    def setUp(self):
        self.crawler = SystemCrawler()
        self.test_dir = tempfile.mkdtemp()

        # Create test files and directories
        self.create_test_environment()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_test_environment(self):
        """Create a test directory structure with various files for testing."""
        # Create files in root
        self.create_file("file1.txt", "content1")
        self.create_file("file2.txt", "content1")  # Duplicate of file1
        self.create_file("doc.pdf", "pdf content")

        # Create subdirectory with files
        os.makedirs(os.path.join(self.test_dir, "subdir"))
        self.create_file(os.path.join("subdir", "sub_file.txt"), "subcontent")
        self.create_file(os.path.join("subdir", "another.pdf"), "pdf content")  # Duplicate of doc.pdf

        # Create empty directory
        os.makedirs(os.path.join(self.test_dir, "empty_dir"))

    def create_file(self, relative_path: str, content: str):
        """Helper method to create a file with content."""
        full_path = os.path.join(self.test_dir, relative_path)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

    def test_initialization(self):
        """Test crawler initialization."""
        self.assertIsInstance(self.crawler.hierarchy, dict)
        self.assertEqual(len(self.crawler.hierarchy), 0)

    def test_nonexistent_path(self):
        """Test handling of nonexistent paths."""
        self.crawler.build_hierarchy("nonexistent_path_xyz")
        self.assertEqual(self.crawler.hierarchy, {})

    def test_file_instead_of_directory(self):
        """Test handling when path points to a file instead of directory."""
        file_path = os.path.join(self.test_dir, "file1.txt")
        self.crawler.build_hierarchy(file_path)
        self.assertEqual(self.crawler.hierarchy, {})

    def test_empty_directory(self):
        """Test scanning an empty directory."""
        empty_dir = os.path.join(self.test_dir, "empty_dir")
        self.crawler.build_hierarchy(empty_dir)

        dir_name = os.path.basename(empty_dir)
        self.assertIn(dir_name, self.crawler.hierarchy)
        self.assertEqual(self.crawler.hierarchy[dir_name]["total_size_in_bytes"], 0)
        self.assertEqual(self.crawler.hierarchy[dir_name]["files"]["count"], 0)
        self.assertEqual(len(self.crawler.hierarchy[dir_name]["directories"]), 0)

    def test_duplicate_detection(self):
        """Test detection of duplicate files."""
        self.crawler.build_hierarchy(self.test_dir)
        root_dir = os.path.basename(self.test_dir)

        # Check root level duplicates
        self.assertIn("duplicates", self.crawler.hierarchy[root_dir])
        duplicates = self.crawler.hierarchy[root_dir]["duplicates"]
        self.assertGreater(len(duplicates), 0)

        # Verify duplicate content across different directories
        has_cross_directory_duplicate = any(
            len(files) > 1 for files in duplicates.values()
        )
        self.assertTrue(has_cross_directory_duplicate)

    def test_file_metadata(self):
        """Test file metadata collection."""
        self.crawler.build_hierarchy(self.test_dir)
        root_dir = os.path.basename(self.test_dir)

        file_data = self.crawler.hierarchy[root_dir]["files"]["by_extension"][".txt"]["items"]["file1.txt"]

        # Check metadata fields
        self.assertIn("size_in_bytes", file_data)
        self.assertIn("timestamps", file_data)
        self.assertIn("security", file_data)
        self.assertIn("mime_type", file_data)
        self.assertIn("hash", file_data)

        # Verify security attributes
        security = file_data["security"]
        self.assertIn("readable", security)
        self.assertIn("writable", security)
        self.assertIn("executable", security)

    def test_directory_structure(self):
        """Test correct directory structure creation."""
        self.crawler.build_hierarchy(self.test_dir)
        root_dir = os.path.basename(self.test_dir)

        # Check root structure
        self.assertIn("directories", self.crawler.hierarchy[root_dir])
        self.assertIn("files", self.crawler.hierarchy[root_dir])
        self.assertIn("total_size_in_bytes", self.crawler.hierarchy[root_dir])

        # Check subdirectory
        self.assertIn("subdir", self.crawler.hierarchy[root_dir]["directories"])
        subdir = self.crawler.hierarchy[root_dir]["directories"]["subdir"]
        self.assertIn("files", subdir)
        self.assertIn("total_size_in_bytes", subdir)

    def test_export_json(self):
        """Test JSON export functionality."""
        self.crawler.build_hierarchy(self.test_dir)
        json_path = os.path.join(self.test_dir, "test_export.json")

        self.crawler.export_to_json(json_path)
        self.assertTrue(os.path.exists(json_path))

        # Verify file is valid JSON
        import json
        with open(json_path, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        self.assertEqual(exported_data, self.crawler.hierarchy)

    def test_export_csv(self):
        """Test CSV export functionality."""
        self.crawler.build_hierarchy(self.test_dir)
        csv_path = os.path.join(self.test_dir, "test_export.csv")

        self.crawler.export_to_csv(csv_path)
        self.assertTrue(os.path.exists(csv_path))

        # Verify CSV structure
        import csv
        with open(csv_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            rows = list(reader)

        expected_headers = [
            "directory", "file_name", "size_bytes", "modified_timestamp",
            "created_timestamp", "mime_type", "hash", "readable",
            "writable", "executable"
        ]
        self.assertEqual(sorted(headers), sorted(expected_headers))
        self.assertGreater(len(rows), 0)


if __name__ == "__main__":
    unittest.main()
