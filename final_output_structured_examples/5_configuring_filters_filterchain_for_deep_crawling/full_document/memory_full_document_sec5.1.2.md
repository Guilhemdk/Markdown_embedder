---
id: memory_full_document_sec5.1.2
cluster: memory
topic: full_document
title: Example: Using `URLPatternFilter` to block URLs matching specific patterns (e.g., `*/login/*`, `*/archive/*`).
version_context: None
outline_date: None
section_hierarchy: ['Configuring Filters (`FilterChain`) for Deep Crawling', '`URLPatternFilter`', 'Example: Using `URLPatternFilter` to allow URLs matching specific patterns (e.g., `/blog/*`).', 'Example: Using `URLPatternFilter` to block URLs matching specific patterns (e.g., `*/login/*`, `*/archive/*`).']
keywords: ['AsyncWebCrawler', 'Block', 'Blocking', 'CacheMode', 'Crawled', 'CrawlerRunConfig', 'Depth']
description:
file_path: 5_configuring_filters_filterchain_for_deep_crawling.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, URLPatternFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_block_pattern():
    # Block URLs containing '/login/' or '/archive/'
    url_filter = URLPatternFilter(patterns=["*/login/*", "*/archive/*"], block_list=True)
    filter_chain = FilterChain(filters=[url_filter])

    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- URLPatternFilter: Blocking '*/login/*' and '*/archive/*' ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            print(f"  URL: {r.url} (Depth: {r.metadata.get('depth')})")
            assert "/login/" not in r.url, f"Page {r.url} should have been blocked (login)."
            assert "/archive/" not in r.url, f"Page {r.url} should have been blocked (archive)."
        print("No pages matching blocked patterns were crawled.")

if __name__ == "__main__":
    asyncio.run(filter_block_pattern())
```