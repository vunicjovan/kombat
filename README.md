# Kombat

A Python library for crawling and analyzing file system hierarchies.

## Installation

```bash
pip install kombat
```

## Usage

```python
from kombat import SystemCrawler

crawler = SystemCrawler()
crawler.build_hierarchy("/path/to/directory")
print(crawler.hierarchy)
```

