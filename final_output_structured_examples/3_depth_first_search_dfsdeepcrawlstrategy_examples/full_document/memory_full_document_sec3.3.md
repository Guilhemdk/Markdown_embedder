---
id: memory_full_document_sec3.3
cluster: memory
topic: full_document
title: Example: `DFSDeePCrawlStrategy` - Setting `max_pages` to limit the total number of pages.
version_context: None
outline_date: None
section_hierarchy: ['Depth-First Search (`DFSDeePCrawlStrategy`) Examples', 'Example: Basic `DFSDeePCrawlStrategy` with default depth.', 'Example: `DFSDeePCrawlStrategy` - Setting `max_depth` to control how deep each branch goes.', 'Example: `DFSDeePCrawlStrategy` - Setting `max_pages` to limit the total number of pages.']
keywords: ['AsyncWebCrawler', 'CacheMode', 'Crawled', 'CrawlerRunConfig', 'Depth', 'MockAsyncWebCrawler', 'python\nimport asyncio\nfrom crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy\nfrom unittest.mock import patch\nimport math\n\n@patch(\'crawl4ai.AsyncWebCrawler\', MockAsyncWebCrawler)\nasync def dfs_set_max_pages():\n    strategy = DFSDeePCrawlStrategy(\n        max_depth=math.inf, # No depth limit for this test\n        max_pages=3\n    )\n    \n    run_config = CrawlerRunConfig(\n        deep_crawl_strategy=strategy,\n        cache_mode=CacheMode.BYPASS\n    )\n\n    async with AsyncWebCrawler() as crawler:\n        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"\n        results = await crawler.arun(url=start_url, config=run_config)\n        \n        print(f"--- DFS with max_pages=3 ---")\n        print(f"Crawled {len(results)} pages (should be at most 3).")\n        for result in results:\n            print(f"  URL: {result.url}, Depth: {result.metadata.get(\'depth\')}")\n        assert len(results) <= 3\n\nif __name__ == "__main__":\n    asyncio.run(dfs_set_max_pages())\n']
description:
file_path: 3_depth_first_search_dfsdeepcrawlstrategy_examples.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy
from unittest.mock import patch
import math

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def dfs_set_max_pages():
    strategy = DFSDeePCrawlStrategy(
        max_depth=math.inf, # No depth limit for this test
        max_pages=3
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- DFS with max_pages=3 ---")
        print(f"Crawled {len(results)} pages (should be at most 3).")
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
        assert len(results) <= 3

if __name__ == "__main__":
    asyncio.run(dfs_set_max_pages())
```