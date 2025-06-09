---
id: memory_full_document_sec2
cluster: memory
topic: full_document
title: Breadth-First Search (`BFSDeePCrawlStrategy`) Examples
version_context: None
outline_date: None
section_hierarchy: ['Breadth-First Search (`BFSDeePCrawlStrategy`) Examples', 'Example: Basic `BFSDeePCrawlStrategy` with default depth.']
keywords: ['AsyncWebCrawler', 'CacheMode', 'Crawled', 'CrawlerRunConfig', 'Default', 'Depth', 'MockAsyncWebCrawler']
description:
file_path: 2_breadth_first_search_bfsdeepcrawlstrategy_examples.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_default_depth():
    # Default max_depth is typically 1 (start_url + its direct children)
    # but let's be explicit for clarity or test with a higher default if library changes
    strategy = BFSDeePCrawlStrategy() # Default max_depth is 1

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BFS with Default Depth (max_depth=1) ---")
        print(f"Crawled {len(results)} pages.")
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")

if __name__ == "__main__":
    asyncio.run(bfs_default_depth())
```