---
id: memory_full_document_sec8.4
cluster: memory
topic: full_document
title: Example: Deep crawling a site with very large number of pages efficiently using `max_pages` and streaming.
version_context: None
outline_date: None
section_hierarchy: ['Advanced Scenarios & Customization', 'Example: Implementing a custom `DeepCrawlStrategy` by subclassing `DeepCrawlStrategy`.', 'Example: Implementing a custom `URLFilter`.', 'Example: Implementing a custom `URLScorer` for `BestFirstCrawlingStrategy`.', 'Example: Deep crawling a site with very large number of pages efficiently using `max_pages` and streaming.']
keywords: ['AsyncWebCrawler', 'But', 'CacheMode', 'CrawlerRunConfig', 'Crawling', 'Efficiently', 'Failed']
description:
file_path: 8_advanced_scenarios_customization.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def deep_crawl_large_site_efficiently():
    # Simulate a large site by setting a high conceptual depth,
    # but limit actual work with max_pages.
    strategy = BFSDeePCrawlStrategy(
        max_depth=10,      # Imagine this could lead to thousands of pages
        max_pages=10,      # But we only want the first 10 found by BFS
        include_external=False
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=True,       # Process results as they come
        cache_mode=CacheMode.BYPASS # Or CacheMode.ENABLED for subsequent partial crawls
    )

    print("--- Efficiently Crawling a 'Large' Site (max_pages=10, stream=True) ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html" # Use our mock site

        crawled_count = 0
        async for result in await crawler.arun(url=start_url, config=run_config):
            crawled_count += 1
            if result.success:
                print(f"  Processed ({crawled_count}/{strategy.max_pages}): {result.url} at depth {result.metadata.get('depth')}")
            else:
                print(f"  Failed ({crawled_count}/{strategy.max_pages}): {result.url} - {result.error_message}")

            if crawled_count >= strategy.max_pages:
                print(f"Reached max_pages limit of {strategy.max_pages}. Stopping.")
                # In a real scenario, you might need to call strategy.shutdown() if the crawler
                # doesn't automatically stop precisely at max_pages when streaming.
                # However, strategies are designed to respect max_pages.
                break

        print(f"\nTotal pages processed: {crawled_count}")
        assert crawled_count <= strategy.max_pages

if __name__ == "__main__":
    asyncio.run(deep_crawl_large_site_efficiently())
```