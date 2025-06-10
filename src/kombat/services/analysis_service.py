import os
from collections import Counter


class AnalysisService:
    @staticmethod
    def analyze_hierarchy(hierarchy: dict) -> dict:
        """
        Analyze the hierarchy and provide summary statistics.

        Args:
            hierarchy: The hierarchy data to analyze.

        Returns:
            A dictionary containing summary statistics.
        """
        total_files = 0
        total_directories = 0
        disk_usage_by_extension = Counter()
        largest_files = []
        largest_folders = []
        empty_directories = []
        zero_byte_files = []

        def traverse(node: dict, current_path: str = ""):
            nonlocal total_files, total_directories, disk_usage_by_extension, largest_files, largest_folders, empty_directories, zero_byte_files

            if "files" in node:
                for ext, files in node["files"].items():
                    for file_name, metadata in files.items():
                        total_files += 1
                        disk_usage_by_extension[ext] += metadata["size_in_bytes"]
                        largest_files.append((os.path.join(current_path, file_name), metadata["size_in_bytes"]))
                        if metadata["size_in_bytes"] == 0:
                            zero_byte_files.append(os.path.join(current_path, file_name))

            if "directories" in node:
                total_directories += len(node["directories"])
                for dir_name, dir_data in node["directories"].items():
                    dir_path = os.path.join(current_path, dir_name)
                    if not dir_data["files"] and not dir_data["directories"]:
                        empty_directories.append(dir_path)
                    largest_folders.append((dir_path, dir_data["total_size_in_bytes"]))
                    traverse(dir_data, dir_path)

        # Start traversal from the root
        for root_name, root_data in hierarchy.items():
            traverse(root_data, root_name)

        # Calculate most and least used extensions
        most_used_extensions = disk_usage_by_extension.most_common(5)
        least_used_extensions = disk_usage_by_extension.most_common()[:-6:-1]

        # Sort largest files and folders
        largest_files = sorted(largest_files, key=lambda x: x[1], reverse=True)[:5]
        largest_folders = sorted(largest_folders, key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_files": total_files,
            "total_directories": total_directories,
            "disk_usage_by_extension": dict(disk_usage_by_extension),
            "most_used_extensions": most_used_extensions,
            "least_used_extensions": least_used_extensions,
            "largest_files": largest_files,
            "largest_folders": largest_folders,
            "empty_directories": empty_directories,
            "zero_byte_files": zero_byte_files,
        }
