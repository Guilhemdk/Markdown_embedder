---
id: memory_full_document_sec3.5
cluster: memory
topic: full_document
title: Example: `DFSDeePCrawlStrategy` - Staying within the domain with `include_external=False`.
version_context: None
outline_date: None
section_hierarchy: ['Depth-First Search (`DFSDeePCrawlStrategy`) Examples', 'Example: Basic `DFSDeePCrawlStrategy` with default depth.', 'Example: `DFSDeePCrawlStrategy` - Setting `max_depth` to control how deep each branch goes.', 'Example: `DFSDeePCrawlStrategy` - Setting `max_pages` to limit the total number of pages.', 'Example: `DFSDeePCrawlStrategy` - Following external links with `include_external=True`.', 'Example: `DFSDeePCrawlStrategy` - Staying within the domain with `include_external=False`.']
keywords: ['AsyncWebCrawler', 'CacheMode', 'Crawled', 'CrawlerRunConfig', 'Default', 'Depth', 'False']
description:
file_path: 3_depth_first_search_dfsdeepcrawlstrategy_examples.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def dfs_exclude_external():
    strategy = DFSDeePCrawlStrategy(
        max_depth=1,
        include_external=False # Default
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- DFS with include_external=False (max_depth=1) ---")
        print(f"Crawled {len(results)} pages.")
        found_external = False
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
            if "external-site.com" in result.url:
                found_external = True

        assert not found_external, "Should not have crawled external links."

if __name__ == "__main__":
    asyncio.run(dfs_exclude_external())
```