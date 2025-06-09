---
id: memory_full_document_sec2.7
cluster: memory
topic: full_document
title: Example: `BFSDeePCrawlStrategy` - Batch results using `CrawlerRunConfig(stream=False)` (default).
version_context: None
outline_date: None
section_hierarchy: ['Breadth-First Search (`BFSDeePCrawlStrategy`) Examples', 'Example: Basic `BFSDeePCrawlStrategy` with default depth.', 'Example: `BFSDeePCrawlStrategy` - Setting `max_depth` to control crawl depth (e.g., 3 levels).', 'Example: `BFSDeePCrawlStrategy` - Setting `max_pages` to limit the total number of pages crawled (e.g., 10 pages).', 'Example: `BFSDeePCrawlStrategy` - Using `include_external=True` to follow links to external domains.', 'Example: `BFSDeePCrawlStrategy` - Using `include_external=False` (default) to stay within the starting domain.', 'Example: `BFSDeePCrawlStrategy` - Streaming results using `CrawlerRunConfig(stream=True)`.', 'Example: `BFSDeePCrawlStrategy` - Batch results using `CrawlerRunConfig(stream=False)` (default).']
keywords: ['AsyncWebCrawler', 'Batch', 'CacheMode', 'CrawlerRunConfig', 'Default', 'Depth', 'False']
description:
file_path: 2_breadth_first_search_bfsdeepcrawlstrategy_examples.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_batch_results():
    strategy = BFSDeePCrawlStrategy(max_depth=1)

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=False, # Default, but explicit for clarity
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config) # Returns a list

        print(f"--- BFS with Batch Results (max_depth=1) ---")
        print(f"Received {len(results)} pages in a batch.")
        for result in results:
            if result.success:
                print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")

if __name__ == "__main__":
    asyncio.run(bfs_batch_results())
```