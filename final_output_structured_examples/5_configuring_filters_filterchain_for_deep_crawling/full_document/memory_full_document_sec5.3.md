---
id: memory_full_document_sec5.3
cluster: memory
topic: full_document
title: `ContentTypeFilter`
version_context: None
outline_date: None
section_hierarchy: ['Configuring Filters (`FilterChain`) for Deep Crawling', '`URLPatternFilter`', 'Example: Using `URLPatternFilter` to allow URLs matching specific patterns (e.g., `/blog/*`).', 'Example: Using `URLPatternFilter` to block URLs matching specific patterns (e.g., `*/login/*`, `*/archive/*`).', 'Example: `URLPatternFilter` with `case_sensitive=True` vs. `case_sensitive=False`.', '`DomainFilter`', 'Example: Using `DomainFilter` with `allowed_domains` to restrict crawling to a list of specific domains.', 'Example: Using `DomainFilter` with `blocked_domains` to avoid crawling certain domains.', 'Example: `DomainFilter` configured to allow subdomains (`allow_subdomains=True`).', 'Example: `DomainFilter` configured to disallow subdomains (`allow_subdomains=False`).', '`ContentTypeFilter`', 'Example: Using `ContentTypeFilter` to allow only `text/html` pages.']
keywords: ['All', 'Allowing', 'AsyncWebCrawler', 'CacheMode', 'Check', 'Content', 'ContentTypeFilter']
description:
file_path: 5_configuring_filters_filterchain_for_deep_crawling.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, ContentTypeFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_allow_html_only():
    content_filter = ContentTypeFilter(allowed_types=["text/html"])
    filter_chain = FilterChain(filters=[content_filter])

    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/page1.html" # Links to HTML and PDF
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- ContentTypeFilter: Allowing only 'text/html' ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            content_type = r.response_headers.get('Content-Type', '')
            print(f"  URL: {r.url}, Content-Type: {content_type}")
            if r.metadata.get('depth', 0) > 0: # Check discovered URLs
                assert "text/html" in content_type, f"Page {r.url} has wrong content type: {content_type}"
        print("All discovered pages are 'text/html'.")

if __name__ == "__main__":
    asyncio.run(filter_allow_html_only())
```