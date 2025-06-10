import csv


class CSVService:
    @staticmethod
    def export_to_csv(hierarchy: dict, output_path: str = "hierarchy.csv") -> None:
        """Export the hierarchy to a CSV file with flattened structure."""
        # Prepare data for CSV format
        rows = []

        def process_files(directory_path: str, files_data: dict) -> None:
            for ext, files in files_data.items():
                for file_name, metadata in files.items():
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
        for root_dir, root_data in hierarchy.items():
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
