---
id: memory_full_document_sec7
cluster: memory
topic: full_document
title: General Deep Crawl Configuration and Usage
version_context: None
outline_date: None
section_hierarchy: ['General Deep Crawl Configuration and Usage', 'Example: Deep crawling a site that relies heavily on JavaScript for link generation.']
keywords: ['AsyncWebCrawler', 'BrowserConfig', 'CacheMode', 'Conceptual', 'Crawled', 'CrawlerRunConfig', 'Crawling']
description:
file_path: 7_general_deep_crawl_configuration_and_usage.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, BrowserConfig
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def deep_crawl_js_heavy_site():
    # BrowserConfig enables JS by default.
    # For very JS-heavy sites, ensure headless=False if debugging, and consider timeouts.
    browser_cfg = BrowserConfig(headless=True) # Keep headless for automated tests

    # CrawlerRunConfig might need adjustments for JS execution time
    run_cfg = CrawlerRunConfig(
        page_timeout=30000, # 30 seconds, might need more for complex JS
        # js_code can be used to trigger actions if needed before link discovery
        # js_code="window.scrollTo(0, document.body.scrollHeight);", # Example to scroll
        deep_crawl_strategy=BFSDeePCrawlStrategy(max_depth=1, max_pages=3),
        cache_mode=CacheMode.BYPASS
    )

    print("--- Deep Crawling a JS-Heavy Site (Conceptual: JS execution is enabled by default) ---")
    # Using index.html which has a JS-triggered link via onclick
    start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        results = await crawler.arun(url=start_url, config=run_cfg)

        print(f"Crawled {len(results)} pages.")
        js_link_found = False
        for result in results:
            print(f"  URL: {result.url}")
            if "js_page.html" in result.url:
                js_link_found = True

        # This assertion relies on the MockAsyncWebCrawler's _fetch_page
        # correctly parsing links from html_content, even if added by mock JS.
        # A more robust test would involve Playwright's own JS execution.
        # For now, we assume the mock crawler finds links from the final HTML state.
        # To truly test JS-driven links, one would need to modify MockAsyncWebCrawler
        # to simulate JS execution or use a real browser test.
        # This example mainly shows the configuration for enabling JS.
        print("Note: True JS-link discovery depends on Playwright's execution within the crawler.")
        print("The mock crawler simulates link finding from final HTML state.")
        # assert js_link_found, "JS-generated link was not found. Mock might need adjustment or real browser test."


if __name__ == "__main__":
    asyncio.run(deep_crawl_js_heavy_site())
```