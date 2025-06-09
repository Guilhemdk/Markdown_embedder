---
id: memory_full_document_sec5
cluster: memory
topic: full_document
title: Configuring Filters (`FilterChain`) for Deep Crawling
version_context: None
outline_date: None
section_hierarchy: ['Configuring Filters (`FilterChain`) for Deep Crawling', '`URLPatternFilter`', 'Example: Using `URLPatternFilter` to allow URLs matching specific patterns (e.g., `/blog/*`).']
keywords: ['All', 'Allow', 'Allowing', 'AsyncWebCrawler', 'CacheMode', 'Check', 'Crawled']
description:
file_path: 5_configuring_filters_filterchain_for_deep_crawling.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, URLPatternFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_allow_pattern():
    # Allow only URLs containing '/blog/'
    url_filter = URLPatternFilter(patterns=["*/blog/*"])
    filter_chain = FilterChain(filters=[url_filter])

    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- URLPatternFilter: Allowing '*/blog/*' ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            print(f"  URL: {r.url} (Depth: {r.metadata.get('depth')})")
            if r.metadata.get('depth', 0) > 0: # Check discovered URLs
                assert "/blog/" in r.url, f"Page {r.url} does not match pattern."
        print("All discovered pages match the allowed pattern.")

if __name__ == "__main__":
    asyncio.run(filter_allow_pattern())
```