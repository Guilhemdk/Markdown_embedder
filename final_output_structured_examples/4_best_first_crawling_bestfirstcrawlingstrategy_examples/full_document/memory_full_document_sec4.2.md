---
id: memory_full_document_sec4.2
cluster: memory
topic: full_document
title: Example: `BestFirstCrawlingStrategy` - Setting `max_depth` to limit crawl depth.
version_context: None
outline_date: None
section_hierarchy: ['Best-First Crawling (`BestFirstCrawlingStrategy`) Examples', 'Example: Basic `BestFirstCrawlingStrategy` with default parameters.', 'Example: `BestFirstCrawlingStrategy` - Setting `max_depth` to limit crawl depth.']
keywords: ['AsyncWebCrawler', 'BestFirstCrawlingStrategy', 'CacheMode', 'Crawled', 'CrawlerRunConfig', 'Depth', 'MockAsyncWebCrawler']
description:
file_path: 4_best_first_crawling_bestfirstcrawlingstrategy_examples.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_max_depth():
    strategy = BestFirstCrawlingStrategy(max_depth=2)

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BestFirstCrawlingStrategy with max_depth=2 ---")
        print(f"Crawled {len(results)} pages.")
        for result in sorted(results, key=lambda r: (r.metadata.get('depth', 0), r.url)):
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}, Score: {result.metadata.get('score', 0.0):.2f}")
        assert all(r.metadata.get('depth', 0) <= 2 for r in results if r.success)

if __name__ == "__main__":
    asyncio.run(best_first_max_depth())
```