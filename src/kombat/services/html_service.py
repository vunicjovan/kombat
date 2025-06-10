import json
import os
from typing import Any


class HTMLService:
    @staticmethod
    def visualize_with_html(hierarchy: Any, output_path: str = "hierarchy.html", summary: dict = None) -> None:
        """
        Create an HTML visualization of the hierarchy with expandable/collapsible nodes using external HTML and CSS files.

        Args:
            hierarchy: The hierarchy data to visualize.
            output_path: Path where the HTML file will be saved.
            summary: The summary statistics to display.
        """

        # Load HTML template
        template_path = os.path.join(os.path.dirname(__file__), "resources/html/html_tree_template.html")
        with open(template_path, 'r', encoding='utf-8') as f:
            html_template = f.read()

        # Load CSS styles
        css_path = os.path.join(os.path.dirname(__file__), "resources/css/html_tree_style.css")
        with open(css_path, 'r', encoding='utf-8') as f:
            css_styles = f.read()

        # Prepare data for HTML
        hierarchy_root_path = hierarchy.hierarchy_root_path
        hierarchy_json = json.dumps(hierarchy)

        # Prepare summary for HTML
        summary_html = ""
        if summary:
            summary_html += "<h2>Summary Statistics</h2><ul>"
            summary_html += f"<li>Total Files: {summary['total_files']}</li>"
            summary_html += f"<li>Total Directories: {summary['total_directories']}</li>"
            summary_html += "<li>Disk Usage by Extension:<ul>"
            for ext, size in summary["disk_usage_by_extension"].items():
                summary_html += f"<li>{ext}: {size} bytes</li>"
            summary_html += "</ul></li>"
            summary_html += "<li>Most Used Extensions:<ul>"
            for ext, size in summary["most_used_extensions"]:
                summary_html += f"<li>{ext}: {size} bytes</li>"
            summary_html += "</ul></li>"
            summary_html += "<li>Least Used Extensions:<ul>"
            for ext, size in summary["least_used_extensions"]:
                summary_html += f"<li>{ext}: {size} bytes</li>"
            summary_html += "</ul></li>"
            summary_html += "<li>Largest Files:<ul>"
            for file, size in summary["largest_files"]:
                summary_html += f"<li>{file}: {size} bytes</li>"
            summary_html += "</ul></li>"
            summary_html += "<li>Largest Folders:<ul>"
            for folder, size in summary["largest_folders"]:
                summary_html += f"<li>{folder}: {size} bytes</li>"
            summary_html += "</ul></li>"
            summary_html += f"<li>Empty Directories: {len(summary['empty_directories'])}</li>"
            summary_html += f"<li>Zero-Byte Files: {len(summary['zero_byte_files'])}</li>"
            summary_html += "</ul>"

        # Replace placeholders in HTML template
        html_content = html_template.replace("ROOT_PATH", hierarchy_root_path)
        html_content = html_content.replace("CSS_STYLES", css_styles)
        html_content = html_content.replace("HIERARCHY_DATA_PLACEHOLDER", hierarchy_json)
        html_content = html_content.replace("SUMMARY_STATISTICS_PLACEHOLDER", summary_html)

        # Write the HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
