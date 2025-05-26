# Kombat

A Python library for crawling and analyzing file system hierarchies.

NOTE: [Kombat](https://pypi.org/project/kombat/0.1.0/) can be found on PyPI.

## Installation

```bash
pip install kombat
```

## Usage

```python
from kombat.crawlers.system_crawler import SystemCrawler

crawler = SystemCrawler()
crawler.build_hierarchy("/path/to/directory")
print(crawler.hierarchy)
```

