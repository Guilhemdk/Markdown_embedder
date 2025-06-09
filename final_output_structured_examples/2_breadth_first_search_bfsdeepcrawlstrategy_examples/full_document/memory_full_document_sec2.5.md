---
id: memory_full_document_sec2.5
cluster: memory
topic: full_document
title: Example: `BFSDeePCrawlStrategy` - Using `include_external=False` (default) to stay within the starting domain.
version_context: None
outline_date: None
section_hierarchy: ['Breadth-First Search (`BFSDeePCrawlStrategy`) Examples', 'Example: Basic `BFSDeePCrawlStrategy` with default depth.', 'Example: `BFSDeePCrawlStrategy` - Setting `max_depth` to control crawl depth (e.g., 3 levels).', 'Example: `BFSDeePCrawlStrategy` - Setting `max_pages` to limit the total number of pages crawled (e.g., 10 pages).', 'Example: `BFSDeePCrawlStrategy` - Using `include_external=True` to follow links to external domains.', 'Example: `BFSDeePCrawlStrategy` - Using `include_external=False` (default) to stay within the starting domain.']
keywords: ['AsyncWebCrawler', 'CacheMode', 'Crawled', 'CrawlerRunConfig', 'Default', 'Depth', 'False']
description:
file_path: 2_breadth_first_search_bfsdeepcrawlstrategy_examples.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_exclude_external():
    strategy = BFSDeePCrawlStrategy(
        max_depth=1,
        include_external=False # Default, but explicit for clarity
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BFS with include_external=False (max_depth=1) ---")
        print(f"Crawled {len(results)} pages.")
        found_external = False
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
            if "external-site.com" in result.url:
                found_external = True

        assert not found_external, "Should not have crawled external links."

if __name__ == "__main__":
    asyncio.run(bfs_exclude_external())
```