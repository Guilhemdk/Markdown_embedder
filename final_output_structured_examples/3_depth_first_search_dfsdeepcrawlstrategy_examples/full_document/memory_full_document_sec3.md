---
id: memory_full_document_sec3
cluster: memory
topic: full_document
title: Depth-First Search (`DFSDeePCrawlStrategy`) Examples
version_context: None
outline_date: None
section_hierarchy: ['Depth-First Search (`DFSDeePCrawlStrategy`) Examples', 'Example: Basic `DFSDeePCrawlStrategy` with default depth.']
keywords: ['AsyncWebCrawler', 'CacheMode', 'Crawled', 'CrawlerRunConfig', 'Default', 'Depth', 'Limit']
description:
file_path: 3_depth_first_search_dfsdeepcrawlstrategy_examples.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def dfs_default_depth():
    # Default max_depth for DFS is typically higher (e.g., 10)
    strategy = DFSDeePCrawlStrategy()

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        max_pages=5, # Limit pages to keep example short with default depth
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- DFS with Default Depth (max_pages=5 to limit output) ---")
        print(f"Crawled {len(results)} pages.")
        for result in results: # Order might be less predictable than BFS for small mock
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")

if __name__ == "__main__":
    asyncio.run(dfs_default_depth())
```