---
id: memory_full_document_sec2.9
cluster: memory
topic: full_document
title: Example: `BFSDeePCrawlStrategy` - Demonstrating `shutdown()` to gracefully stop an ongoing crawl.
version_context: None
outline_date: None
section_hierarchy: ['Breadth-First Search (`BFSDeePCrawlStrategy`) Examples', 'Example: Basic `BFSDeePCrawlStrategy` with default depth.', 'Example: `BFSDeePCrawlStrategy` - Setting `max_depth` to control crawl depth (e.g., 3 levels).', 'Example: `BFSDeePCrawlStrategy` - Setting `max_pages` to limit the total number of pages crawled (e.g., 10 pages).', 'Example: `BFSDeePCrawlStrategy` - Using `include_external=True` to follow links to external domains.', 'Example: `BFSDeePCrawlStrategy` - Using `include_external=False` (default) to stay within the starting domain.', 'Example: `BFSDeePCrawlStrategy` - Streaming results using `CrawlerRunConfig(stream=True)`.', 'Example: `BFSDeePCrawlStrategy` - Batch results using `CrawlerRunConfig(stream=False)` (default).', 'Example: `BFSDeePCrawlStrategy` - Integrating a `FilterChain` with `URLPatternFilter` to crawl specific paths.', 'Example: `BFSDeePCrawlStrategy` - Demonstrating `shutdown()` to gracefully stop an ongoing crawl.']
keywords: ['AsyncWebCrawler', 'Attempting', 'Await', 'CacheMode', 'CancelledError', 'Collected', 'Crawl']
description:
file_path: 2_breadth_first_search_bfsdeepcrawlstrategy_examples.md::full_document
---

```python
import asyncio
import time
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_demonstrate_shutdown():
    strategy = BFSDeePCrawlStrategy(
        max_depth=5, # A potentially long crawl
        max_pages=100
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=True, # Streaming is good to see partial results before shutdown
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html" # A site with enough links

        print(f"--- BFS with shutdown() demonstration ---")

        crawl_task = asyncio.create_task(crawler.arun(url=start_url, config=run_config))

        # Let the crawl run for a very short time
        await asyncio.sleep(0.1)

        print("Attempting to shut down the crawl...")
        await strategy.shutdown()

        results_list = []
        try:
            # Await the results from the crawl task
            # If streaming, this will iterate through what was processed before shutdown
            async for res in await crawl_task:
                results_list.append(res)
                print(f"  Collected result (post-shutdown signal): {res.url}")
        except asyncio.CancelledError:
            print("Crawl task was cancelled.")

        print(f"Crawl shut down. Processed {len(results_list)} pages before/during shutdown.")
        # The number of pages will be less than if it ran to completion
        assert len(results_list) < 10, "Crawl likely didn't shut down early enough or mock site too small."

if __name__ == "__main__":
    asyncio.run(bfs_demonstrate_shutdown())
```