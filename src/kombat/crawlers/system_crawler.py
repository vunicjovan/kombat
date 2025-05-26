import os
from typing import Any


class SystemCrawler:
    """
    A class for analyzing directory structures and file distributions.

    Creates a hierarchical representation of directories and their contents,
    including statistics about subdirectories and files grouped by extension.
    """

    def __init__(self):
        self.hierarchy = {}

    def build_hierarchy(self, root_path: str, indent: str = "") -> None:
        """
        Build a hierarchical representation of the given directory.

        Args:
            root_path (str): Path to the directory to analyze
            indent (str, optional): Indentation for pretty printing. Defaults to "".
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

        root_dir_name = os.path.basename(root_path)
        formed_hierarchy[root_dir_name] = {
            "directories": {
                "count": 0,
                "names": []
            },
            "files": {
                "count": 0,
                "by_extension": {}
            }
        }

        # Handle empty directory case
        if not os.listdir(root_path):
            self.hierarchy = formed_hierarchy
            return

        # Iterate through directory contents
        for item in os.listdir(root_path):
            path = os.path.join(root_path, item)
            if os.path.isdir(path):
                # Recursively process subdirectories
                sub_hierarchy = self._process_directory(path, indent + "    ")
                formed_hierarchy[root_dir_name].update(sub_hierarchy)
                # Update directory information
                formed_hierarchy[root_dir_name]["directories"]["count"] += 1
                formed_hierarchy[root_dir_name]["directories"]["names"].append(os.path.basename(path))
            else:
                # Update file information
                formed_hierarchy[root_dir_name]["files"]["count"] += 1
                ext = os.path.splitext(item)[1].lower()
                if ext not in formed_hierarchy[root_dir_name]["files"]["by_extension"]:
                    formed_hierarchy[root_dir_name]["files"]["by_extension"][ext] = {
                        "count": 0,
                        "names": []
                    }
                formed_hierarchy[root_dir_name]["files"]["by_extension"][ext]["count"] += 1
                formed_hierarchy[root_dir_name]["files"]["by_extension"][ext]["names"].append(item)

        # Sort lists for better readability
        formed_hierarchy[root_dir_name]["directories"]["names"].sort()
        for ext_info in formed_hierarchy[root_dir_name]["files"]["by_extension"].values():
            ext_info["names"].sort()

        self.hierarchy = formed_hierarchy

    def _process_directory(self, path: str, indent: str) -> dict[str, Any]:
        """Helper method to process directories recursively"""
        dir_name = os.path.basename(path)
        result = {
            dir_name: {
                "directories": {
                    "count": 0,
                    "names": []
                },
                "files": {
                    "count": 0,
                    "by_extension": {}
                }
            }
        }

        if os.listdir(path):
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    sub_hierarchy = self._process_directory(item_path, indent + "    ")
                    result[dir_name].update(sub_hierarchy)
                    # Update directory information
                    result[dir_name]["directories"]["count"] += 1
                    result[dir_name]["directories"]["names"].append(os.path.basename(item_path))
                else:
                    # Update file information
                    result[dir_name]["files"]["count"] += 1
                    ext = os.path.splitext(item)[1].lower()
                    if ext not in result[dir_name]["files"]["by_extension"]:
                        result[dir_name]["files"]["by_extension"][ext] = {
                            "count": 0,
                            "names": []
                        }
                    result[dir_name]["files"]["by_extension"][ext]["count"] += 1
                    result[dir_name]["files"]["by_extension"][ext]["names"].append(item)

            # Sort lists for better readability
            result[dir_name]["directories"]["names"].sort()
            for ext_info in result[dir_name]["files"]["by_extension"].values():
                ext_info["names"].sort()

        return result
