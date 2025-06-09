---
id: memory_full_document_sec3.7
cluster: memory
topic: full_document
title: Example: `DFSDeePCrawlStrategy` - Batch results.
version_context: None
outline_date: None
section_hierarchy: ['Depth-First Search (`DFSDeePCrawlStrategy`) Examples', 'Example: Basic `DFSDeePCrawlStrategy` with default depth.', 'Example: `DFSDeePCrawlStrategy` - Setting `max_depth` to control how deep each branch goes.', 'Example: `DFSDeePCrawlStrategy` - Setting `max_pages` to limit the total number of pages.', 'Example: `DFSDeePCrawlStrategy` - Following external links with `include_external=True`.', 'Example: `DFSDeePCrawlStrategy` - Staying within the domain with `include_external=False`.', 'Example: `DFSDeePCrawlStrategy` - Streaming results.', 'Example: `DFSDeePCrawlStrategy` - Batch results.']
keywords: ['AsyncWebCrawler', 'Batch', 'CacheMode', 'CrawlerRunConfig', 'Default', 'Depth', 'False']
description:
file_path: 3_depth_first_search_dfsdeepcrawlstrategy_examples.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def dfs_batch_results():
    strategy = DFSDeePCrawlStrategy(max_depth=1)

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=False, # Default
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- DFS with Batch Results (max_depth=1) ---")
        print(f"Received {len(results)} pages in a batch.")
        for result in results:
            if result.success:
                print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")

if __name__ == "__main__":
    asyncio.run(dfs_batch_results())
```