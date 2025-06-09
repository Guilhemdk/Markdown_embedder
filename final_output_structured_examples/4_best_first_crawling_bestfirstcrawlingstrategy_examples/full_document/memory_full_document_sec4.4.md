---
id: memory_full_document_sec4.4
cluster: memory
topic: full_document
title: Example: `BestFirstCrawlingStrategy` - Using `include_external=True`.
version_context: None
outline_date: None
section_hierarchy: ['Best-First Crawling (`BestFirstCrawlingStrategy`) Examples', 'Example: Basic `BestFirstCrawlingStrategy` with default parameters.', 'Example: `BestFirstCrawlingStrategy` - Setting `max_depth` to limit crawl depth.', 'Example: `BestFirstCrawlingStrategy` - Setting `max_pages` to limit total pages crawled.', 'Example: `BestFirstCrawlingStrategy` - Using `include_external=True`.']
keywords: ['AsyncWebCrawler', 'BestFirstCrawlingStrategy', 'CacheMode', 'Crawled', 'CrawlerRunConfig', 'Depth', 'Expected']
description:
file_path: 4_best_first_crawling_bestfirstcrawlingstrategy_examples.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_include_external():
    strategy = BestFirstCrawlingStrategy(
        max_depth=1,
        include_external=True,
        max_pages=5 # To keep it manageable
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BestFirstCrawlingStrategy with include_external=True (max_depth=1) ---")
        print(f"Crawled {len(results)} pages.")
        found_external = False
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}, Score: {result.metadata.get('score', 0.0):.2f}")
            if "external-site.com" in result.url:
                found_external = True

        assert found_external, "Expected to crawl an external link."

if __name__ == "__main__":
    asyncio.run(best_first_include_external())
```