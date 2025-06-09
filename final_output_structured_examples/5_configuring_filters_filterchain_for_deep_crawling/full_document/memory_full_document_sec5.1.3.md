---
id: memory_full_document_sec5.1.3
cluster: memory
topic: full_document
title: Example: `URLPatternFilter` with `case_sensitive=True` vs. `case_sensitive=False`.
version_context: None
outline_date: None
section_hierarchy: ['Configuring Filters (`FilterChain`) for Deep Crawling', '`URLPatternFilter`', 'Example: Using `URLPatternFilter` to allow URLs matching specific patterns (e.g., `/blog/*`).', 'Example: Using `URLPatternFilter` to block URLs matching specific patterns (e.g., `*/login/*`, `*/archive/*`).', 'Example: `URLPatternFilter` with `case_sensitive=True` vs. `case_sensitive=False`.']
keywords: ['Add', 'Allow', 'AsyncWebCrawler', 'CacheMode', 'Case', 'Check', 'Content']
description:
file_path: 5_configuring_filters_filterchain_for_deep_crawling.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, URLPatternFilter
from unittest.mock import patch

# Add a case-specific URL to MOCK_SITE_DATA
MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/Page1.html"] = {
    "html_content": "<html><head><title>Page 1 Case Test</title></head><body><p>Content for case test.</p></body></html>",
    "response_headers": {"Content-Type": "text/html"}
}
MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"] += '<a href="Page1.html">Page 1 Case Test</a>'


@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_pattern_case_sensitivity():
    start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"

    # Case-sensitive: should only match 'page1.html'
    print("\n--- URLPatternFilter: Case Sensitive (Allow '*/page1.html*') ---")
    url_filter_sensitive = URLPatternFilter(patterns=["*/page1.html*"], case_sensitive=True)
    filter_chain_sensitive = FilterChain(filters=[url_filter_sensitive])
    strategy_sensitive = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain_sensitive)
    run_config_sensitive = CrawlerRunConfig(deep_crawl_strategy=strategy_sensitive, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        results_sensitive = await crawler.arun(url=start_url, config=run_config_sensitive)
        print(f"Crawled {len(results_sensitive)} pages.")
        for r in results_sensitive:
            print(f"  URL: {r.url}")
            if r.metadata.get('depth',0) > 0:
                assert "page1.html" in r.url and "Page1.html" not in r.url, "Case-sensitive filter failed."

    # Case-insensitive: should match both 'page1.html' and 'Page1.html'
    print("\n--- URLPatternFilter: Case Insensitive (Allow '*/page1.html*') ---")
    url_filter_insensitive = URLPatternFilter(patterns=["*/page1.html*"], case_sensitive=False)
    filter_chain_insensitive = FilterChain(filters=[url_filter_insensitive])
    strategy_insensitive = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain_insensitive)
    run_config_insensitive = CrawlerRunConfig(deep_crawl_strategy=strategy_insensitive, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        results_insensitive = await crawler.arun(url=start_url, config=run_config_insensitive)
        print(f"Crawled {len(results_insensitive)} pages.")
        found_page1_lower = False
        found_page1_upper = False
        for r in results_insensitive:
            print(f"  URL: {r.url}")
            if "page1.html" in r.url.lower(): # Check lower to catch both
                 if "page1.html" == Path(r.url).name: found_page1_lower = True
                 if "Page1.html" == Path(r.url).name: found_page1_upper = True

        assert found_page1_lower and found_page1_upper, "Case-insensitive filter should have matched both cases."

if __name__ == "__main__":
    asyncio.run(filter_pattern_case_sensitivity())
```