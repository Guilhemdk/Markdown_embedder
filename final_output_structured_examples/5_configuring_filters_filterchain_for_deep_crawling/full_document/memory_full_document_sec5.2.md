---
id: memory_full_document_sec5.2
cluster: memory
topic: full_document
title: `DomainFilter`
version_context: None
outline_date: None
section_hierarchy: ['Configuring Filters (`FilterChain`) for Deep Crawling', '`URLPatternFilter`', 'Example: Using `URLPatternFilter` to allow URLs matching specific patterns (e.g., `/blog/*`).', 'Example: Using `URLPatternFilter` to block URLs matching specific patterns (e.g., `*/login/*`, `*/archive/*`).', 'Example: `URLPatternFilter` with `case_sensitive=True` vs. `case_sensitive=False`.', '`DomainFilter`', 'Example: Using `DomainFilter` with `allowed_domains` to restrict crawling to a list of specific domains.']
keywords: ['All', 'Allowing', 'AsyncWebCrawler', 'CacheMode', 'Crawled', 'CrawlerRunConfig', 'DomainFilter']
description:
file_path: 5_configuring_filters_filterchain_for_deep_crawling.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, DomainFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_allowed_domains():
    # Only crawl within 'docs.crawl4ai.com'
    domain_filter = DomainFilter(allowed_domains=["docs.crawl4ai.com"])
    filter_chain = FilterChain(filters=[domain_filter])

    # include_external needs to be True for DomainFilter to even consider other domains for blocking/allowing
    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain, include_external=True)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html" # This links to external-site.com
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- DomainFilter: Allowing only 'docs.crawl4ai.com' ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            print(f"  URL: {r.url}")
            assert "docs.crawl4ai.com" in r.url, f"Page {r.url} is not from an allowed domain."
        print("All crawled pages are from 'docs.crawl4ai.com'.")

if __name__ == "__main__":
    asyncio.run(filter_allowed_domains())
```