---
id: memory_full_document_sec2.3
cluster: memory
topic: full_document
title: Example: `BFSDeePCrawlStrategy` - Setting `max_pages` to limit the total number of pages crawled (e.g., 10 pages).
version_context: None
outline_date: None
section_hierarchy: ['Breadth-First Search (`BFSDeePCrawlStrategy`) Examples', 'Example: Basic `BFSDeePCrawlStrategy` with default depth.', 'Example: `BFSDeePCrawlStrategy` - Setting `max_depth` to control crawl depth (e.g., 3 levels).', 'Example: `BFSDeePCrawlStrategy` - Setting `max_pages` to limit the total number of pages crawled (e.g., 10 pages).']
keywords: ['AsyncWebCrawler', 'CacheMode', 'Crawled', 'CrawlerRunConfig', 'Depth', 'Effectively', 'Limit']
description:
file_path: 2_breadth_first_search_bfsdeepcrawlstrategy_examples.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch
import math # for math.inf

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_set_max_pages():
    strategy = BFSDeePCrawlStrategy(
        max_depth=math.inf, # Effectively no depth limit for this test
        max_pages=3         # Limit to 3 pages
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BFS with max_pages=3 ---")
        print(f"Crawled {len(results)} pages (should be at most 3).")
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")

        assert len(results) <= 3

if __name__ == "__main__":
    asyncio.run(bfs_set_max_pages())
```