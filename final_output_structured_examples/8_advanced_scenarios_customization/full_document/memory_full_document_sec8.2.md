---
id: memory_full_document_sec8.2
cluster: memory
topic: full_document
title: Example: Implementing a custom `URLFilter`.
version_context: None
outline_date: None
section_hierarchy: ['Advanced Scenarios & Customization', 'Example: Implementing a custom `DeepCrawlStrategy` by subclassing `DeepCrawlStrategy`.', 'Example: Implementing a custom `URLFilter`.']
keywords: ['Allow', 'Allowing', 'AsyncWebCrawler', 'Block', 'Blocking', 'CacheMode', 'CrawlerRunConfig']
description:
file_path: 8_advanced_scenarios_customization.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain
from unittest.mock import patch

class MyCustomURLFilter:
    def __init__(self, forbidden_keyword: str):
        self.forbidden_keyword = forbidden_keyword.lower()
        print(f"MyCustomURLFilter initialized to block URLs with '{self.forbidden_keyword}'")

    async def __call__(self, url: str) -> bool: # Filters must be async
        """Return True if URL should be allowed, False if blocked."""
        if self.forbidden_keyword in url.lower():
            print(f"[CustomFilter] Blocking URL: {url} (contains '{self.forbidden_keyword}')")
            return False # Block if keyword found
        print(f"[CustomFilter] Allowing URL: {url}")
        return True # Allow otherwise

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def custom_url_filter_example():
    custom_filter = MyCustomURLFilter(forbidden_keyword="archive")
    filter_chain = FilterChain(filters=[custom_filter])

    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    print("--- Using Custom URLFilter (blocking 'archive') ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"\nCustom filter crawl resulted in {len(results)} pages:")
        for r in results:
            print(f"  URL: {r.url}")
            assert "archive" not in r.url.lower(), f"Custom filter failed to block {r.url}"
        print("Successfully blocked URLs containing 'archive'.")

if __name__ == "__main__":
    asyncio.run(custom_url_filter_example())
```