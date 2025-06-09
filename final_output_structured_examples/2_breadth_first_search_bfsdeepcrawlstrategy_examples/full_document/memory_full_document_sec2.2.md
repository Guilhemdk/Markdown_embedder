---
id: memory_full_document_sec2.2
cluster: memory
topic: full_document
title: Example: `BFSDeePCrawlStrategy` - Setting `max_depth` to control crawl depth (e.g., 3 levels).
version_context: None
outline_date: None
section_hierarchy: ['Breadth-First Search (`BFSDeePCrawlStrategy`) Examples', 'Example: Basic `BFSDeePCrawlStrategy` with default depth.', 'Example: `BFSDeePCrawlStrategy` - Setting `max_depth` to control crawl depth (e.g., 3 levels).']
keywords: ['AsyncWebCrawler', 'CacheMode', 'Crawled', 'CrawlerRunConfig', 'Depth', 'MockAsyncWebCrawler', 'Start']
description:
file_path: 2_breadth_first_search_bfsdeepcrawlstrategy_examples.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_set_max_depth():
    strategy = BFSDeePCrawlStrategy(max_depth=2) # Start URL (0), its links (1), and their links (2)

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BFS with max_depth=2 ---")
        print(f"Crawled {len(results)} pages.")
        for result in sorted(results, key=lambda r: (r.metadata.get('depth', 0), r.url)):
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")

        # Verify that no pages with depth > 2 are present
        assert all(r.metadata.get('depth', 0) <= 2 for r in results if r.success)

if __name__ == "__main__":
    asyncio.run(bfs_set_max_depth())
```