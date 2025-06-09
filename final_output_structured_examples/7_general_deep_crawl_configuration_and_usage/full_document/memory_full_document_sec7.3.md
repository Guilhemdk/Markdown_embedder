---
id: memory_full_document_sec7.3
cluster: memory
topic: full_document
title: Example: Iterating through deep crawl results and handling cases where some pages failed to crawl or were filtered out.
version_context: None
outline_date: None
section_hierarchy: ['General Deep Crawl Configuration and Usage', 'Example: Deep crawling a site that relies heavily on JavaScript for link generation.', 'Example: How `CrawlerRunConfig` parameters (e.g., `page_timeout`) and `BrowserConfig` (e.g., `user_agent`, `proxy_config`) affect underlying page fetches.', 'Example: Iterating through deep crawl results and handling cases where some pages failed to crawl or were filtered out.']
keywords: ['Add', 'AsyncWebCrawler', 'CacheMode', 'Clean', 'Crawl', 'CrawlerRunConfig', 'Deep']
description:
file_path: 7_general_deep_crawl_configuration_and_usage.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, URLPatternFilter
from unittest.mock import patch

# Add a URL that will "fail" in our mock
MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/failing_page.html"] = {
    "html_content": None, # Simulate failure by not providing content
    "success": False,
    "status_code": 500,
    "error_message": "Mock Server Error"
}
MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"] += '<a href="failing_page.html">Failing Page</a>'


@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def deep_crawl_handling_failures():
    # Filter out '/archive/' pages, and one page will fail
    url_filter = URLPatternFilter(patterns=["*/archive/*"], block_list=True)
    filter_chain = FilterChain(filters=[url_filter])

    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- Deep Crawl - Handling Failures and Filtered Pages ---")
        successful_pages = 0
        failed_pages = 0

        for result in results:
            if result.success:
                successful_pages += 1
                print(f"  SUCCESS: {result.url} (Depth: {result.metadata.get('depth')})")
                assert "/archive/" not in result.url
            else:
                failed_pages += 1
                print(f"  FAILURE: {result.url} (Error: {result.error_message}, Status: {result.status_code})")

        print(f"\nTotal Successful: {successful_pages}, Total Failed/Filtered Out by crawler: {failed_pages}")
        # Start URL + index links (page1, page2, external, blog, login, failing) = 7 initial candidates
        # - external might be skipped by default include_external=False (depends on strategy)
        # - /archive/ is filtered by URLPatternFilter
        # - failing_page.html will fail
        # So, we expect start_url + page1, page2, blog, login. Failing page is in results but success=False.
        # The number of results includes the start_url and pages that were attempted.
        # Filters apply to links *discovered* from a page.

        # One page (/archive/old_page.html) should be filtered by the filter chain.
        # One page (failing_page.html) should be in results but with success=False.
        assert any("failing_page.html" in r.url and not r.success for r in results)
        assert not any("/archive/" in r.url for r in results)

    # Clean up mock data
    del MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/failing_page.html"]
    MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"] = MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"].replace('<a href="failing_page.html">Failing Page</a>', '')

if __name__ == "__main__":
    asyncio.run(deep_crawl_handling_failures())
```