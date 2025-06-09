---
id: memory_full_document_sec5.4
cluster: memory
topic: full_document
title: `URLFilter` (Simple exact match)
version_context: None
outline_date: None
section_hierarchy: ['Configuring Filters (`FilterChain`) for Deep Crawling', '`URLPatternFilter`', 'Example: Using `URLPatternFilter` to allow URLs matching specific patterns (e.g., `/blog/*`).', 'Example: Using `URLPatternFilter` to block URLs matching specific patterns (e.g., `*/login/*`, `*/archive/*`).', 'Example: `URLPatternFilter` with `case_sensitive=True` vs. `case_sensitive=False`.', '`DomainFilter`', 'Example: Using `DomainFilter` with `allowed_domains` to restrict crawling to a list of specific domains.', 'Example: Using `DomainFilter` with `blocked_domains` to avoid crawling certain domains.', 'Example: `DomainFilter` configured to allow subdomains (`allow_subdomains=True`).', 'Example: `DomainFilter` configured to disallow subdomains (`allow_subdomains=False`).', '`ContentTypeFilter`', 'Example: Using `ContentTypeFilter` to allow only `text/html` pages.', 'Example: Using `ContentTypeFilter` with multiple `allowed_types` (e.g., `text/html`, `application/json`).', 'Example: Using `ContentTypeFilter` with `blocked_types` (e.g., blocking `application/pdf`).', '`URLFilter` (Simple exact match)', 'Example: `URLFilter` to allow a specific list of exact URLs.']
keywords: ['Allow', 'Allowing', 'AsyncWebCrawler', 'CacheMode', 'Crawled', 'CrawlerRunConfig', 'Exclude']
description:
file_path: 5_configuring_filters_filterchain_for_deep_crawling.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, URLFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_allow_exact_urls():
    allowed_urls = [
        "https://docs.crawl4ai.com/vibe-examples/page1.html",
        "https://docs.crawl4ai.com/vibe-examples/page1_sub1.html"
    ]
    url_filter = URLFilter(urls=allowed_urls, block_list=False) # Allow list
    filter_chain = FilterChain(filters=[url_filter])

    strategy = BFSDeePCrawlStrategy(max_depth=2, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- URLFilter: Allowing specific URLs ---")
        print(f"Crawled {len(results)} pages.")
        crawled_urls = {r.url for r in results}
        # The start URL is always crawled initially, then its links are filtered.
        # So we check that all *other* crawled URLs are in the allowed list.
        for r_url in crawled_urls:
            if r_url != start_url: # Exclude start_url from this assertion
                 assert r_url in allowed_urls, f"URL {r_url} was not in the allowed list."
        print("Only URLs from the allowed list (plus start_url) were crawled.")

if __name__ == "__main__":
    asyncio.run(filter_allow_exact_urls())
```