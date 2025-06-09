---
id: memory_full_document_sec5.3.2
cluster: memory
topic: full_document
title: Example: Using `ContentTypeFilter` with multiple `allowed_types` (e.g., `text/html`, `application/json`).
version_context: None
outline_date: None
section_hierarchy: ['Configuring Filters (`FilterChain`) for Deep Crawling', '`URLPatternFilter`', 'Example: Using `URLPatternFilter` to allow URLs matching specific patterns (e.g., `/blog/*`).', 'Example: Using `URLPatternFilter` to block URLs matching specific patterns (e.g., `*/login/*`, `*/archive/*`).', 'Example: `URLPatternFilter` with `case_sensitive=True` vs. `case_sensitive=False`.', '`DomainFilter`', 'Example: Using `DomainFilter` with `allowed_domains` to restrict crawling to a list of specific domains.', 'Example: Using `DomainFilter` with `blocked_domains` to avoid crawling certain domains.', 'Example: `DomainFilter` configured to allow subdomains (`allow_subdomains=True`).', 'Example: `DomainFilter` configured to disallow subdomains (`allow_subdomains=False`).', '`ContentTypeFilter`', 'Example: Using `ContentTypeFilter` to allow only `text/html` pages.', 'Example: Using `ContentTypeFilter` with multiple `allowed_types` (e.g., `text/html`, `application/json`).']
keywords: ['All', 'Allowing', 'AsyncWebCrawler', 'CacheMode', 'Clean', 'Content', 'ContentTypeFilter']
description:
file_path: 5_configuring_filters_filterchain_for_deep_crawling.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, ContentTypeFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_allow_multiple_types():
    content_filter = ContentTypeFilter(allowed_types=["text/html", "application/json"])
    filter_chain = FilterChain(filters=[content_filter])

    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/page1.html"
        # Imagine page1.html also links to a page1_sub3.json
        MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/page1_sub3.json"] = {
            "html_content": '{"key": "value"}',
            "response_headers": {"Content-Type": "application/json"}
        }
        MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/page1.html"]["html_content"] += '<a href="page1_sub3.json">JSON Data</a>'


        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- ContentTypeFilter: Allowing 'text/html', 'application/json' ---")
        print(f"Crawled {len(results)} pages.")
        found_json = False
        for r in results:
            content_type = r.response_headers.get('Content-Type', '')
            print(f"  URL: {r.url}, Content-Type: {content_type}")
            if r.metadata.get('depth',0) > 0:
                assert "text/html" in content_type or "application/json" in content_type
            if "application/json" in content_type:
                found_json = True
        assert found_json, "Expected to find a JSON page."
        print("All discovered pages are either 'text/html' or 'application/json'.")

        # Clean up mock data
        del MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/page1_sub3.json"]
        MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/page1.html"]["html_content"] = MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/page1.html"]["html_content"].replace('<a href="page1_sub3.json">JSON Data</a>', '')


if __name__ == "__main__":
    asyncio.run(filter_allow_multiple_types())
```