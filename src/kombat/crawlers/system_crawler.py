import csv
import hashlib
import json
import mimetypes
import os
import stat


class SystemCrawler:
    def __init__(self):
        self.hierarchy = {}
        self.hierarchy_root_path = None
        mimetypes.init()

    def visualize_with_html(self, output_path: str = "hierarchy.html") -> None:
        """
        Create an HTML visualization of the hierarchy with expandable/collapsible nodes.

        Args:
            output_path: Path where the HTML file will be saved
        """
        html_template = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Hierarchy Visualization: ROOT_PATH}</title>
            <style>
                .tree-node {
                    margin-left: 20px;
                }
                .expandable {
                    cursor: pointer;
                    user-select: none;
                }
                .expandable::before {
                    content: "▶";
                    display: inline-block;
                    margin-right: 6px;
                    transition: transform 0.2s;
                }
                .expanded::before {
                    transform: rotate(90deg);
                }
                .hidden {
                    display: none;
                }
                .file-node {
                    margin-left: 26px;
                }
                .directory {
                    color: #2c3e50;
                    font-weight: bold;
                }
                .file {
                    color: #34495e;
                }
                .file-ext {
                    color: #7f8c8d;
                }
                .metadata {
                    font-size: 0.9em;
                    color: #95a5a6;
                    margin-left: 10px;
                }
                .duplicate {
                    color: #e74c3c;
                }
                .container {
                    font-family: Arial, sans-serif;
                    padding: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Hierarchy Visualization: ROOT_PATH</h1>
                <div id="hierarchy"></div>
            </div>

            <script>
                function toggleNode(element) {
                    element.classList.toggle('expanded');
                    const content = element.nextElementSibling;
                    if (content) {
                        content.classList.toggle('hidden');
                    }
                }

                function formatSize(bytes) {
                    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
                    let size = bytes;
                    let unitIndex = 0;
                    while (size >= 1024 && unitIndex < units.length - 1) {
                        size /= 1024;
                        unitIndex++;
                    }
                    return `${size.toFixed(2)} ${units[unitIndex]}`;
                }

                function formatTimestamp(timestamp) {
                    return new Date(timestamp * 1000).toLocaleString();
                }

                const hierarchyData = HIERARCHY_DATA_PLACEHOLDER;

                function createTreeNode(data, name, isRoot = false) {
                    const container = document.createElement('div');

                    if (data.files || data.directories) {
                        const header = document.createElement('div');
                        header.className = 'expandable directory';
                        if (!isRoot) header.classList.add('tree-node');
                        header.textContent = name;
                        header.onclick = () => toggleNode(header);
                        container.appendChild(header);

                        const content = document.createElement('div');
                        content.className = 'tree-node';

                        // Add files
                        if (data.files && data.files.by_extension) {
                            Object.entries(data.files.by_extension).forEach(([ext, extData]) => {
                                Object.entries(extData.items).forEach(([fileName, fileData]) => {
                                    const fileNode = document.createElement('div');
                                    fileNode.className = 'file file-node';
                                    fileNode.innerHTML = `
                                        ${fileName}
                                        <span class="file-ext">${ext}</span>
                                        <span class="metadata">
                                            (${formatSize(fileData.size_in_bytes)},
                                            Created: ${formatTimestamp(fileData.timestamps.created)},
                                            Modified: ${formatTimestamp(fileData.timestamps.modified)})
                                        </span>
                                    `;
                                    content.appendChild(fileNode);
                                });
                            });
                        }

                        // Add duplicates section if exists
                        if (data.duplicates) {
                            const duplicatesNode = document.createElement('div');
                            duplicatesNode.className = 'tree-node';
                            Object.entries(data.duplicates).forEach(([hash, files]) => {
                                if (files.length > 1) {
                                    const dupNode = document.createElement('div');
                                    dupNode.className = 'duplicate';
                                    dupNode.textContent = `Duplicates: ${files.join(', ')}`;
                                    duplicatesNode.appendChild(dupNode);
                                }
                            });
                            content.appendChild(duplicatesNode);
                        }

                        // Add subdirectories
                        if (data.directories) {
                            Object.entries(data.directories).forEach(([dirName, dirData]) => {
                                content.appendChild(createTreeNode(dirData, dirName));
                            });
                        }

                        container.appendChild(content);
                    }

                    return container;
                }

                const hierarchyContainer = document.getElementById('hierarchy');
                Object.entries(hierarchyData).forEach(([rootName, rootData]) => {
                    hierarchyContainer.appendChild(createTreeNode(rootData, rootName, true));
                });

                // Expand root nodes by default
                document.querySelectorAll('.expandable').forEach(node => {
                    if (!node.classList.contains('tree-node')) {
                        toggleNode(node);
                    }
                });
            </script>
        </body>
        </html>
        '''

        # Convert hierarchy to JSON for JavaScript
        hierarchy_json = json.dumps(self.hierarchy)
        html_content = html_template.replace("HIERARCHY_DATA_PLACEHOLDER", hierarchy_json)
        html_content = html_content.replace("ROOT_PATH", self.hierarchy_root_path)

        # Write the HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

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

    def build_hierarchy(self, root_path: str, extensions: set[str] = None, depth: int = -1) -> None:
        """
        Build directory hierarchy with optional extension filtering and depth limit.

        Args:
            root_path: Path to the root directory
            extensions: Set of file extensions to include (e.g. {'.txt', '.pdf'}).
                       If None, include all extensions.
            depth: Maximum depth to crawl (-1 for unlimited, 0 for root only,
                   1 for first level subdirectories, etc.)
        """
        formed_hierarchy = {}

        if not os.path.exists(root_path):
            print(f"Path '{root_path}' does not exist.")
            self.hierarchy = formed_hierarchy
            return

        if not os.path.isdir(root_path):
            print(f"Path '{root_path}' is not a directory.")
            self.hierarchy = formed_hierarchy
            return

        # Normalize extensions to lowercase if provided
        if extensions is not None:
            extensions = {ext.lower() if ext.startswith('.') else f'.{ext.lower()}'
                          for ext in extensions}

        self.hierarchy_root_path = root_path
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
                # Skip directory if we've reached depth limit
                if depth == 0:
                    continue

                dir_name = os.path.basename(path)
                formed_hierarchy[root_dir_name]["directories"][dir_name] = {
                    "total_size_in_bytes": 0,
                    "files": {
                        "count": 0,
                        "by_extension": {}
                    }
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

    def _process_directory(self, path: str, dir_hierarchy: dict, extensions: set[str] = None, depth: int = -1) -> None:
        """
        Process directory contents with optional extension filtering and depth limit.

        Args:
            path: Directory path to process
            dir_hierarchy: Dictionary to store the hierarchy
            extensions: Set of allowed file extensions
            depth: Remaining depth to process (-1 for unlimited)
        """
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
                    "files": {
                        "count": 0,
                        "by_extension": {}
                    }
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

                self._add_file_to_hierarchy(item_path, dir_hierarchy["files"])
                dir_hierarchy["total_size_in_bytes"] += metadata["size_in_bytes"]

        duplicates = {h: files for h, files in hash_to_files.items() if len(files) > 1}
        if duplicates:
            dir_hierarchy["duplicates"] = duplicates

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
