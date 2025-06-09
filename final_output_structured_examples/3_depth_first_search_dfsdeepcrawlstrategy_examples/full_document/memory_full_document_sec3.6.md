---
id: memory_full_document_sec3.6
cluster: memory
topic: full_document
title: Example: `DFSDeePCrawlStrategy` - Streaming results.
version_context: None
outline_date: None
section_hierarchy: ['Depth-First Search (`DFSDeePCrawlStrategy`) Examples', 'Example: Basic `DFSDeePCrawlStrategy` with default depth.', 'Example: `DFSDeePCrawlStrategy` - Setting `max_depth` to control how deep each branch goes.', 'Example: `DFSDeePCrawlStrategy` - Setting `max_pages` to limit the total number of pages.', 'Example: `DFSDeePCrawlStrategy` - Following external links with `include_external=True`.', 'Example: `DFSDeePCrawlStrategy` - Staying within the domain with `include_external=False`.', 'Example: `DFSDeePCrawlStrategy` - Streaming results.']
keywords: ['AsyncWebCrawler', 'CacheMode', 'CrawlerRunConfig', 'Depth', 'MockAsyncWebCrawler', 'Result', 'Results']
description:
file_path: 3_depth_first_search_dfsdeepcrawlstrategy_examples.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def dfs_streaming_results():
    strategy = DFSDeePCrawlStrategy(max_depth=1)

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=True,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        print(f"--- DFS with Streaming Results (max_depth=1) ---")
        count = 0
        async for result in await crawler.arun(url=start_url, config=run_config):
            count +=1
            if result.success:
                print(f"  Streamed Result {count}: {result.url}, Depth: {result.metadata.get('depth')}")
        print(f"Total results streamed: {count}")


if __name__ == "__main__":
    asyncio.run(dfs_streaming_results())
```