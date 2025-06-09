---
id: memory_full_document_sec5.2.4
cluster: memory
topic: full_document
title: Example: `DomainFilter` configured to disallow subdomains (`allow_subdomains=False`).
version_context: None
outline_date: None
section_hierarchy: ['Configuring Filters (`FilterChain`) for Deep Crawling', '`URLPatternFilter`', 'Example: Using `URLPatternFilter` to allow URLs matching specific patterns (e.g., `/blog/*`).', 'Example: Using `URLPatternFilter` to block URLs matching specific patterns (e.g., `*/login/*`, `*/archive/*`).', 'Example: `URLPatternFilter` with `case_sensitive=True` vs. `case_sensitive=False`.', '`DomainFilter`', 'Example: Using `DomainFilter` with `allowed_domains` to restrict crawling to a list of specific domains.', 'Example: Using `DomainFilter` with `blocked_domains` to avoid crawling certain domains.', 'Example: `DomainFilter` configured to allow subdomains (`allow_subdomains=True`).', 'Example: `DomainFilter` configured to disallow subdomains (`allow_subdomains=False`).']
keywords: ['AsyncWebCrawler', 'CacheMode', 'Conceptual', 'Crawled', 'CrawlerRunConfig', 'Default', 'Disallowing']
description:
file_path: 5_configuring_filters_filterchain_for_deep_crawling.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, DomainFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_disallow_subdomains():
    domain_filter = DomainFilter(allowed_domains=["docs.crawl4ai.com"], allow_subdomains=False) # Default
    filter_chain = FilterChain(filters=[domain_filter])

    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain, include_external=True)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- DomainFilter: Disallowing subdomains of 'docs.crawl4ai.com' (Conceptual) ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            print(f"  URL: {r.url}")
            # In a real test, you'd check if blog.docs.crawl4ai.com was NOT included
        print("This example is conceptual; for a real test, ensure mock data includes subdomains to be excluded.")

if __name__ == "__main__":
    asyncio.run(filter_disallow_subdomains())
```