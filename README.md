# Kombat

A Python library for crawling and analyzing file system hierarchies.

NOTE: [Kombat](https://pypi.org/project/kombat/) can be found on PyPI.

## Installation

```bash
pip install kombat
```

## Features

- **Rich File System Metadata**
  - File and directory size tracking with aggregation
  - Modification and access timestamps
  - File permissions and security attributes
  - MIME type detection
  - File hash calculation (SHA256) for duplicate detection
  
- **Multiple Export Formats**
  - Interactive HTML visualization with expandable tree view
  - JSON export for structured data analysis
  - CSV export for spreadsheet compatibility

## Usage

Basic crawling:
```python
from kombat.crawlers.system_crawler import SystemCrawler

crawler = SystemCrawler()
crawler.build_hierarchy("/path/to/directory")
```

Export and visualization:
```python
# Generate interactive HTML view
crawler.visualize_with_html("output.html")

# Export to JSON
crawler.export_to_json("hierarchy.json")

# Export to CSV
crawler.export_to_csv("hierarchy.csv")
```

Advanced options:
```python
# Filter by extensions and limit depth
crawler.build_hierarchy(
    "/path/to/directory",
    extensions={'.txt', '.pdf'},
    depth=2
)
```
