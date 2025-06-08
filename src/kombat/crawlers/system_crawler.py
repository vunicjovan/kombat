import csv
import hashlib
import json
import mimetypes
import os
import stat


class SystemCrawler:
    def __init__(self):
        self.hierarchy = {}
        mimetypes.init()

    def export_to_json(self, output_path: str = "hierarchy.json") -> None:
        """Export the hierarchy to a JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.hierarchy, f, indent=4, ensure_ascii=False)

    def export_to_csv(self, output_path: str = "hierarchy.csv") -> None:
        """Export the hierarchy to a CSV file with flattened structure."""
        # Prepare data for CSV format
        rows = []

        def process_files(directory_path: str, files_data: dict) -> None:
            for ext_info in files_data["by_extension"].values():
                for file_name, metadata in ext_info["items"].items():
                    rows.append({
                        "directory": directory_path,
                        "file_name": file_name,
                        "size_bytes": metadata["size_in_bytes"],
                        "modified_timestamp": metadata["timestamps"]["modified"],
                        "created_timestamp": metadata["timestamps"]["created"],
                        "mime_type": metadata["mime_type"],
                        "hash": metadata["hash"],
                        "readable": metadata["security"]["readable"],
                        "writable": metadata["security"]["writable"],
                        "executable": metadata["security"]["executable"]
                    })

        # Process root level files and directories
        for root_dir, root_data in self.hierarchy.items():
            # Process files in root directory
            if "files" in root_data:
                process_files(root_dir, root_data["files"])

            # Process files in subdirectories
            if "directories" in root_data:
                for dir_name, dir_data in root_data["directories"].items():
                    dir_path = f"{root_dir}/{dir_name}"
                    process_files(dir_path, dir_data["files"])

        # Write to CSV file
        if rows:
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)

    def build_hierarchy(self, root_path: str) -> None:
        formed_hierarchy = {}

        if not os.path.exists(root_path):
            print(f"Path '{root_path}' does not exist.")
            self.hierarchy = formed_hierarchy
            return

        if not os.path.isdir(root_path):
            print(f"Path '{root_path}' is not a directory.")
            self.hierarchy = formed_hierarchy
            return

        root_dir_name = os.path.basename(root_path)
        formed_hierarchy[root_dir_name] = {
            "total_size_in_bytes": 0,
            "directories": {},
            "files": {
                "count": 0,
                "by_extension": {}
            }
        }

        if not os.listdir(root_path):
            self.hierarchy = formed_hierarchy
            return

        # Track files by hash at root level
        hash_to_files = {}

        for item in os.listdir(root_path):
            path = os.path.join(root_path, item)
            if os.path.isdir(path):
                dir_name = os.path.basename(path)
                formed_hierarchy[root_dir_name]["directories"][dir_name] = {
                    "total_size_in_bytes": 0,
                    "files": {
                        "count": 0,
                        "by_extension": {}
                    }
                }
                self._process_directory(path, formed_hierarchy[root_dir_name]["directories"][dir_name])
            else:
                metadata = self._get_file_metadata(path)
                file_hash = metadata["hash"]

                # Track files by hash for duplicate detection at root level
                if file_hash not in hash_to_files:
                    hash_to_files[file_hash] = []
                hash_to_files[file_hash].append(item)

                self._add_file_to_hierarchy(path, formed_hierarchy[root_dir_name]["files"])
                formed_hierarchy[root_dir_name]["total_size_in_bytes"] += metadata["size_in_bytes"]

        # Add duplicates section at root level if duplicates exist
        duplicates = {h: files for h, files in hash_to_files.items() if len(files) > 1}
        if duplicates:
            formed_hierarchy[root_dir_name]["duplicates"] = duplicates

        # Sort files and update total size
        for ext_info in formed_hierarchy[root_dir_name]["files"]["by_extension"].values():
            ext_info["items"] = dict(sorted(ext_info["items"].items()))

        # Sort files in subdirectories and update root size
        for dir_info in formed_hierarchy[root_dir_name]["directories"].values():
            for ext_info in dir_info["files"]["by_extension"].values():
                ext_info["items"] = dict(sorted(ext_info["items"].items()))
            formed_hierarchy[root_dir_name]["total_size_in_bytes"] += dir_info["total_size_in_bytes"]

        self.hierarchy = formed_hierarchy

    def _calculate_file_hash(self, file_path: str, algorithm: str = 'sha256') -> str:  # noqa
        """Calculate hash of a file using specified algorithm."""
        hash_func = getattr(hashlib, algorithm)()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()

    def _get_file_metadata(self, file_path: str) -> dict:
        stats = os.stat(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)

        # Calculate file hash
        file_hash = self._calculate_file_hash(file_path)

        return {
            "size_in_bytes": stats.st_size,
            "timestamps": {
                "modified": int(stats.st_mtime),
                "created": int(stats.st_ctime)
            },
            "security": {
                "mode": oct(stat.S_IMODE(stats.st_mode)),
                "readable": os.access(file_path, os.R_OK),
                "writable": os.access(file_path, os.W_OK),
                "executable": os.access(file_path, os.X_OK)
            },
            "mime_type": mime_type or "application/octet-stream",
            "hash": file_hash
        }

    def _process_directory(self, path: str, dir_hierarchy: dict) -> None:
        # Dictionary to track files by their hash
        hash_to_files = {}

        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if not os.path.isdir(item_path):
                metadata = self._get_file_metadata(item_path)
                file_hash = metadata["hash"]

                # Track files by hash for duplicate detection
                if file_hash not in hash_to_files:
                    hash_to_files[file_hash] = []
                hash_to_files[file_hash].append(item)

                self._add_file_to_hierarchy(item_path, dir_hierarchy["files"])
                dir_hierarchy["total_size_in_bytes"] += metadata["size_in_bytes"]

        # Add duplicates section only if duplicates exist
        duplicates = {h: files for h, files in hash_to_files.items() if len(files) > 1}
        if duplicates:
            dir_hierarchy["duplicates"] = duplicates

    def _add_file_to_hierarchy(self, file_path: str, hierarchy_section: dict) -> None:
        file_name = os.path.basename(file_path)
        ext = os.path.splitext(file_name)[1].lower()

        if ext not in hierarchy_section["by_extension"]:
            hierarchy_section["by_extension"][ext] = {
                "count": 0,
                "items": {}
            }

        hierarchy_section["count"] += 1
        hierarchy_section["by_extension"][ext]["count"] += 1
        hierarchy_section["by_extension"][ext]["items"][file_name] = self._get_file_metadata(file_path)


if __name__ == '__main__':
    crawler = SystemCrawler()
    crawler.build_hierarchy(r"C:\Users\jovan\Downloads")
    crawler.export_to_json("hierarchy.json")
    crawler.export_to_csv("hierarchy.csv")
