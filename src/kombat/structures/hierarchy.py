import hashlib
import mimetypes
import os
import stat

from ..services.analysis_service import AnalysisService
from ..services.csv_service import CSVService
from ..services.html_service import HTMLService
from ..services.json_service import JSONService


class Hierarchy(dict):
    def __init__(self, root_path: str = None, extensions: set[str] = None, depth: int = -1):
        super().__init__()
        self.root_path = root_path
        self.extensions = extensions
        self.depth = depth
        self.hierarchy_root_path = None
        mimetypes.init()
        self.summary = {}

        if root_path:
            self.build_hierarchy()
            self.hierarchy_root_path = root_path
            self.summary = self.summarize()

    def build_hierarchy(self) -> None:
        """Build directory hierarchy with optional extension filtering and depth limit."""
        root_path = self.root_path
        extensions = self.extensions
        depth = self.depth
        formed_hierarchy = {}

        if not os.path.exists(root_path):
            print(f"Path '{root_path}' does not exist.")
            return

        if not os.path.isdir(root_path):
            print(f"Path '{root_path}' is not a directory.")
            return

        # Normalize extensions to lowercase if provided
        if extensions is not None:
            extensions = {ext.lower() if ext.startswith('.') else f'.{ext.lower()}'
                          for ext in extensions}

        root_dir_name = os.path.basename(root_path)
        formed_hierarchy[root_dir_name] = {
            "total_size_in_bytes": 0,
            "directories": {},
            "file_count": 0,
            "files": {}
        }

        if not os.listdir(root_path):
            self.update(formed_hierarchy)
            return

        # Track files by hash at root level
        hash_to_files = {}

        for item in os.listdir(root_path):
            path = os.path.join(root_path, item)
            if os.path.isdir(path):
                # Skip directory if we've reached depth limit
                if depth == 0:
                    continue

                dir_name = os.path.basename(path)
                formed_hierarchy[root_dir_name]["directories"][dir_name] = {
                    "total_size_in_bytes": 0,
                    "file_count": 0,
                    "files": {}
                }
                # Pass decremented depth for next level
                self._process_directory(
                    path,
                    formed_hierarchy[root_dir_name]["directories"][dir_name],
                    extensions,
                    depth - 1 if depth > 0 else -1
                )
            else:
                # Skip if extension filtering is enabled and file doesn't match
                if extensions is not None:
                    ext = os.path.splitext(item)[1].lower()
                    if ext not in extensions:
                        continue

                metadata = self._get_file_metadata(path)
                file_hash = metadata["hash"]

                if file_hash not in hash_to_files:
                    hash_to_files[file_hash] = []
                hash_to_files[file_hash].append(item)

                self._add_file_to_hierarchy(path, formed_hierarchy[root_dir_name])
                formed_hierarchy[root_dir_name]["total_size_in_bytes"] += metadata["size_in_bytes"]
                formed_hierarchy[root_dir_name]["file_count"] += 1

        # Add duplicates section at root level if duplicates exist
        duplicates = {h: files for h, files in hash_to_files.items() if len(files) > 1}
        if duplicates:
            formed_hierarchy[root_dir_name]["duplicates"] = duplicates

        # Sort files and update total size
        for ext, files in formed_hierarchy[root_dir_name]["files"].items():
            formed_hierarchy[root_dir_name]["files"][ext] = dict(sorted(files.items()))

        # Sort files in subdirectories and update root size
        for dir_info in formed_hierarchy[root_dir_name]["directories"].values():
            for ext, files in dir_info["files"].items():
                dir_info["files"][ext] = dict(sorted(files.items()))
            formed_hierarchy[root_dir_name]["total_size_in_bytes"] += dir_info["total_size_in_bytes"]

        self.update(formed_hierarchy)

    def _process_directory(self, path: str, dir_hierarchy: dict, extensions: set[str] = None, depth: int = -1) -> None:
        """Process directory contents with optional extension filtering and depth limit."""
        hash_to_files = {}

        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                # Skip subdirectories if we've reached depth limit
                if depth == 0:
                    continue

                dir_name = os.path.basename(item_path)
                dir_hierarchy["directories"] = dir_hierarchy.get("directories", {})
                dir_hierarchy["directories"][dir_name] = {
                    "total_size_in_bytes": 0,
                    "file_count": 0,
                    "files": {}
                }
                # Pass decremented depth for next level
                self._process_directory(
                    item_path,
                    dir_hierarchy["directories"][dir_name],
                    extensions,
                    depth - 1 if depth > 0 else -1
                )
            else:
                if extensions is not None:
                    ext = os.path.splitext(item)[1].lower()
                    if ext not in extensions:
                        continue

                metadata = self._get_file_metadata(item_path)
                file_hash = metadata["hash"]

                if file_hash not in hash_to_files:
                    hash_to_files[file_hash] = []
                hash_to_files[file_hash].append(item)

                self._add_file_to_hierarchy(item_path, dir_hierarchy)
                dir_hierarchy["total_size_in_bytes"] += metadata["size_in_bytes"]
                dir_hierarchy["file_count"] += 1

        duplicates = {h: files for h, files in hash_to_files.items() if len(files) > 1}
        if duplicates:
            dir_hierarchy["duplicates"] = duplicates

        for ext, files in dir_hierarchy["files"].items():
            dir_hierarchy["files"][ext] = dict(sorted(files.items()))

    def _add_file_to_hierarchy(self, file_path: str, hierarchy_section: dict) -> None:
        file_name = os.path.basename(file_path)
        ext = os.path.splitext(file_name)[1].lower()

        if ext not in hierarchy_section["files"]:
            hierarchy_section["files"][ext] = {}

        hierarchy_section["files"][ext][file_name] = self._get_file_metadata(file_path)

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

    def export(self, location: str = "hierarchy.json", export_type: str = "json") -> None:
        """Export the hierarchy to a specified format using the appropriate service."""
        if export_type.lower() == "json":
            JSONService.export_to_json(self, location)
        elif export_type.lower() == "csv":
            CSVService.export_to_csv(self, location)
        else:
            raise ValueError(f"Unsupported export type: {export_type}")

    def html_tree(self, output_path: str = "hierarchy.html") -> None:
        """Visualize the hierarchy using HTMLService."""
        HTMLService.visualize_with_html(self, output_path, self.summary)

    def summarize(self) -> dict:
        """
        Generate summary statistics for the hierarchy.

        Returns:
            A dictionary containing summary statistics.
        """
        return AnalysisService.analyze_hierarchy(self)
