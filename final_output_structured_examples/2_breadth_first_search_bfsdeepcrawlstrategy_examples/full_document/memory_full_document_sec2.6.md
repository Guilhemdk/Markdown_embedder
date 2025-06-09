---
id: memory_full_document_sec2.6
cluster: memory
topic: full_document
title: Example: `BFSDeePCrawlStrategy` - Streaming results using `CrawlerRunConfig(stream=True)`.
version_context: None
outline_date: None
section_hierarchy: ['Breadth-First Search (`BFSDeePCrawlStrategy`) Examples', 'Example: Basic `BFSDeePCrawlStrategy` with default depth.', 'Example: `BFSDeePCrawlStrategy` - Setting `max_depth` to control crawl depth (e.g., 3 levels).', 'Example: `BFSDeePCrawlStrategy` - Setting `max_pages` to limit the total number of pages crawled (e.g., 10 pages).', 'Example: `BFSDeePCrawlStrategy` - Using `include_external=True` to follow links to external domains.', 'Example: `BFSDeePCrawlStrategy` - Using `include_external=False` (default) to stay within the starting domain.', 'Example: `BFSDeePCrawlStrategy` - Streaming results using `CrawlerRunConfig(stream=True)`.']
keywords: ['AsyncWebCrawler', 'CacheMode', 'CrawlerRunConfig', 'Depth', 'Enable', 'Error', 'MockAsyncWebCrawler']
description:
file_path: 2_breadth_first_search_bfsdeepcrawlstrategy_examples.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_streaming_results():
    strategy = BFSDeePCrawlStrategy(max_depth=1)

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=True, # Enable streaming
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        print(f"--- BFS with Streaming Results (max_depth=1) ---")
        count = 0
        async for result in await crawler.arun(url=start_url, config=run_config):
            count += 1
            if result.success:
                print(f"  Streamed Result {count}: {result.url}, Depth: {result.metadata.get('depth')}")
            else:
                print(f"  Streamed FAILED Result {count}: {result.url}, Error: {result.error_message}")
        print(f"Total results streamed: {count}")

if __name__ == "__main__":
    asyncio.run(bfs_streaming_results())
```