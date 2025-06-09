---
id: memory_full_document_sec3.4
cluster: memory
topic: full_document
title: Example: `DFSDeePCrawlStrategy` - Following external links with `include_external=True`.
version_context: None
outline_date: None
section_hierarchy: ['Depth-First Search (`DFSDeePCrawlStrategy`) Examples', 'Example: Basic `DFSDeePCrawlStrategy` with default depth.', 'Example: `DFSDeePCrawlStrategy` - Setting `max_depth` to control how deep each branch goes.', 'Example: `DFSDeePCrawlStrategy` - Setting `max_pages` to limit the total number of pages.', 'Example: `DFSDeePCrawlStrategy` - Following external links with `include_external=True`.']
keywords: ['AsyncWebCrawler', 'CacheMode', 'Crawled', 'CrawlerRunConfig', 'Depth', 'Expected', 'False']
description:
file_path: 3_depth_first_search_dfsdeepcrawlstrategy_examples.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def dfs_include_external():
    strategy = DFSDeePCrawlStrategy(
        max_depth=1,
        include_external=True,
        max_pages=5 # Limit pages as external can be vast
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- DFS with include_external=True (max_depth=1, max_pages=5) ---")
        print(f"Crawled {len(results)} pages.")
        found_external = False
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
            if "external-site.com" in result.url:
                found_external = True

        assert found_external, "Expected to crawl an external link."

if __name__ == "__main__":
    asyncio.run(dfs_include_external())
```