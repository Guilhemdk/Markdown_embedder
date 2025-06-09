---
id: memory_full_document_sec5.3.3
cluster: memory
topic: full_document
title: Example: Using `ContentTypeFilter` with `blocked_types` (e.g., blocking `application/pdf`).
version_context: None
outline_date: None
section_hierarchy: ['Configuring Filters (`FilterChain`) for Deep Crawling', '`URLPatternFilter`', 'Example: Using `URLPatternFilter` to allow URLs matching specific patterns (e.g., `/blog/*`).', 'Example: Using `URLPatternFilter` to block URLs matching specific patterns (e.g., `*/login/*`, `*/archive/*`).', 'Example: `URLPatternFilter` with `case_sensitive=True` vs. `case_sensitive=False`.', '`DomainFilter`', 'Example: Using `DomainFilter` with `allowed_domains` to restrict crawling to a list of specific domains.', 'Example: Using `DomainFilter` with `blocked_domains` to avoid crawling certain domains.', 'Example: `DomainFilter` configured to allow subdomains (`allow_subdomains=True`).', 'Example: `DomainFilter` configured to disallow subdomains (`allow_subdomains=False`).', '`ContentTypeFilter`', 'Example: Using `ContentTypeFilter` to allow only `text/html` pages.', 'Example: Using `ContentTypeFilter` with multiple `allowed_types` (e.g., `text/html`, `application/json`).', 'Example: Using `ContentTypeFilter` with `blocked_types` (e.g., blocking `application/pdf`).']
keywords: ['AsyncWebCrawler', 'Blocking', 'CacheMode', 'Content', 'ContentTypeFilter', 'Crawled', 'CrawlerRunConfig']
description:
file_path: 5_configuring_filters_filterchain_for_deep_crawling.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, ContentTypeFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_block_pdf():
    content_filter = ContentTypeFilter(blocked_types=["application/pdf"])
    filter_chain = FilterChain(filters=[content_filter])

    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/page1.html" # Links to HTML and PDF
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- ContentTypeFilter: Blocking 'application/pdf' ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            content_type = r.response_headers.get('Content-Type', '')
            print(f"  URL: {r.url}, Content-Type: {content_type}")
            assert "application/pdf" not in content_type, f"PDF page {r.url} was not blocked."
        print("No 'application/pdf' pages were crawled (beyond start URL if it was PDF).")

if __name__ == "__main__":
    asyncio.run(filter_block_pdf())
```