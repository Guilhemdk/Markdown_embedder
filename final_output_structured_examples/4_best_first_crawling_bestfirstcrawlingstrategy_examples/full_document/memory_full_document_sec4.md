---
id: memory_full_document_sec4
cluster: memory
topic: full_document
title: Best-First Crawling (`BestFirstCrawlingStrategy`) Examples
version_context: None
outline_date: None
section_hierarchy: ['Best-First Crawling (`BestFirstCrawlingStrategy`) Examples', 'Example: Basic `BestFirstCrawlingStrategy` with default parameters.']
keywords: ['AsyncWebCrawler', 'BestFirstCrawlingStrategy', 'CacheMode', 'Crawled', 'CrawlerRunConfig', 'Default', 'Depth']
description:
file_path: 4_best_first_crawling_bestfirstcrawlingstrategy_examples.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_default_params():
    strategy = BestFirstCrawlingStrategy(max_depth=1) # Default scorer (often scores 0)

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BestFirstCrawlingStrategy with default parameters (max_depth=1) ---")
        print(f"Crawled {len(results)} pages.")
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}, Score: {result.metadata.get('score', 0.0):.2f}")

if __name__ == "__main__":
    asyncio.run(best_first_default_params())
```