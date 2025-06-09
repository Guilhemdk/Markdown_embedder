---
id: memory_full_document_sec3.2
cluster: memory
topic: full_document
title: Example: `DFSDeePCrawlStrategy` - Setting `max_depth` to control how deep each branch goes.
version_context: None
outline_date: None
section_hierarchy: ['Depth-First Search (`DFSDeePCrawlStrategy`) Examples', 'Example: Basic `DFSDeePCrawlStrategy` with default depth.', 'Example: `DFSDeePCrawlStrategy` - Setting `max_depth` to control how deep each branch goes.']
keywords: ['AsyncWebCrawler', 'CacheMode', 'Crawled', 'CrawlerRunConfig', 'Depth', 'MockAsyncWebCrawler', 'python\nimport asyncio\nfrom crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy\nfrom unittest.mock import patch\n\n@patch(\'crawl4ai.AsyncWebCrawler\', MockAsyncWebCrawler)\nasync def dfs_set_max_depth():\n    strategy = DFSDeePCrawlStrategy(max_depth=2)\n    \n    run_config = CrawlerRunConfig(\n        deep_crawl_strategy=strategy,\n        cache_mode=CacheMode.BYPASS\n    )\n\n    async with AsyncWebCrawler() as crawler:\n        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"\n        results = await crawler.arun(url=start_url, config=run_config)\n        \n        print(f"--- DFS with max_depth=2 ---")\n        print(f"Crawled {len(results)} pages.")\n        for result in results:\n            print(f"  URL: {result.url}, Depth: {result.metadata.get(\'depth\')}")\n        assert all(r.metadata.get(\'depth\', 0) <= 2 for r in results if r.success)\n\n\nif __name__ == "__main__":\n    asyncio.run(dfs_set_max_depth())\n']
description:
file_path: 3_depth_first_search_dfsdeepcrawlstrategy_examples.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def dfs_set_max_depth():
    strategy = DFSDeePCrawlStrategy(max_depth=2)

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- DFS with max_depth=2 ---")
        print(f"Crawled {len(results)} pages.")
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
        assert all(r.metadata.get('depth', 0) <= 2 for r in results if r.success)


if __name__ == "__main__":
    asyncio.run(dfs_set_max_depth())
```