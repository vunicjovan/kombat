import json


class JSONService:
    @staticmethod
    def export_to_json(hierarchy: dict, output_path: str = "hierarchy.json") -> None:
        """Export the hierarchy to a JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(hierarchy, f, indent=4, ensure_ascii=False)
