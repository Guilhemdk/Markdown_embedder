---
id: memory_full_document_sec5.4.2
cluster: memory
topic: full_document
title: Example: `URLFilter` to block a specific list of exact URLs.
version_context: None
outline_date: None
section_hierarchy: ['Configuring Filters (`FilterChain`) for Deep Crawling', '`URLPatternFilter`', 'Example: Using `URLPatternFilter` to allow URLs matching specific patterns (e.g., `/blog/*`).', 'Example: Using `URLPatternFilter` to block URLs matching specific patterns (e.g., `*/login/*`, `*/archive/*`).', 'Example: `URLPatternFilter` with `case_sensitive=True` vs. `case_sensitive=False`.', '`DomainFilter`', 'Example: Using `DomainFilter` with `allowed_domains` to restrict crawling to a list of specific domains.', 'Example: Using `DomainFilter` with `blocked_domains` to avoid crawling certain domains.', 'Example: `DomainFilter` configured to allow subdomains (`allow_subdomains=True`).', 'Example: `DomainFilter` configured to disallow subdomains (`allow_subdomains=False`).', '`ContentTypeFilter`', 'Example: Using `ContentTypeFilter` to allow only `text/html` pages.', 'Example: Using `ContentTypeFilter` with multiple `allowed_types` (e.g., `text/html`, `application/json`).', 'Example: Using `ContentTypeFilter` with `blocked_types` (e.g., blocking `application/pdf`).', '`URLFilter` (Simple exact match)', 'Example: `URLFilter` to allow a specific list of exact URLs.', 'Example: `URLFilter` to block a specific list of exact URLs.']
keywords: ['AsyncWebCrawler', 'Block', 'Blocked', 'Blocking', 'CacheMode', 'Crawled', 'CrawlerRunConfig']
description:
file_path: 5_configuring_filters_filterchain_for_deep_crawling.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, URLFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_block_exact_urls():
    blocked_urls = [
        "https://docs.crawl4ai.com/vibe-examples/page2.html",
        "https://docs.crawl4ai.com/vibe-examples/archive/old_page.html"
    ]
    url_filter = URLFilter(urls=blocked_urls, block_list=True) # Block list
    filter_chain = FilterChain(filters=[url_filter])

    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- URLFilter: Blocking specific URLs ---")
        print(f"Crawled {len(results)} pages.")
        crawled_urls = {r.url for r in results}
        for blocked_url in blocked_urls:
            assert blocked_url not in crawled_urls, f"URL {blocked_url} should have been blocked."
        print("Blocked URLs were not crawled.")

if __name__ == "__main__":
    asyncio.run(filter_block_exact_urls())
```