## 7. General Deep Crawl Configuration and Usage

### 7.1. Example: Deep crawling a site that relies heavily on JavaScript for link generation.
This example demonstrates the setup. A real JS-heavy site would be needed for full verification.

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

### 7.2. Example: How `CrawlerRunConfig` parameters (e.g., `page_timeout`) and `BrowserConfig` (e.g., `user_agent`, `proxy_config`) affect underlying page fetches.
This shows how `BrowserConfig` (passed to `AsyncWebCrawler`) and `CrawlerRunConfig` (passed to `arun`) influence individual page fetches.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, BrowserConfig, ProxyConfig
from unittest.mock import patch

# Mocking a proxy server check - in reality, you'd use a real proxy
async def mock_check_ip_via_proxy(url, config):
    # This function would normally make a request through the proxy
    # and return the perceived IP. For mock, we'll just simulate.
    if config and config.proxy_config and config.proxy_config.server == "http://mockproxy.com:8080":
        return "1.2.3.4" # Mocked IP if proxy is used
    return "9.8.7.6" # Mocked direct IP

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def deep_crawl_with_configs():
    browser_cfg = BrowserConfig(
        user_agent="MyCustomDeepCrawler/1.0",
        proxy_config=ProxyConfig(server="http://mockproxy.com:8080") # This should be used by crawler
    )

    # For deep crawl, the page_timeout in CrawlerRunConfig applies to each page fetch
    run_cfg = CrawlerRunConfig(
        page_timeout=15000, # 15s timeout for each page in the deep crawl
        deep_crawl_strategy=BFSDeePCrawlStrategy(max_depth=0), # Just the start URL
        cache_mode=CacheMode.BYPASS
    )

    print("--- Deep Crawl with Custom Browser & Run Configs ---")
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        # The crawler instance now has the browser_cfg settings.
        # We expect its internal page fetches to use these.

        # We'd need to inspect logs or mock `crawler.strategy._fetch_page` to truly verify user_agent/proxy.
        # For this example, we'll conceptually check based on setup.
        print(f"Browser User-Agent set to: {crawler.browser_config.user_agent}")
        if crawler.browser_config.proxy_config:
            print(f"Browser Proxy set to: {crawler.browser_config.proxy_config.server}")

        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_cfg)

        if results and results[0].success:
            print(f"Crawled {results[0].url} successfully with page_timeout={run_cfg.page_timeout}ms")
            # In a real scenario with a proxy, you'd verify the source IP.
            # For mock:
            # perceived_ip = await mock_check_ip_via_proxy(start_url, browser_cfg)
            # print(f"Perceived IP (mocked): {perceived_ip}")
            # assert perceived_ip == "1.2.3.4" # Assuming proxy was used
        else:
            print(f"Crawl failed for {start_url}")

if __name__ == "__main__":
    asyncio.run(deep_crawl_with_configs())
```

### 7.3. Example: Iterating through deep crawl results and handling cases where some pages failed to crawl or were filtered out.
A robust deep crawl should handle partial failures gracefully.

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

### 7.4. Example: Using a custom `logger` instance passed to a `DeepCrawlStrategy`.

```python
import asyncio
import logging
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, AsyncLogger
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def deep_crawl_custom_logger():
    # Setup a custom logger
    custom_logger = AsyncLogger(log_file="custom_deep_crawl.log", name="MyDeepCrawler", level="DEBUG")

    strategy = BFSDeePCrawlStrategy(max_depth=0, logger=custom_logger) # Pass logger to strategy
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    print("--- Deep Crawl with Custom Logger ---")
    async with AsyncWebCrawler() as crawler: # Main crawler logger can be default
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        await crawler.arun(url=start_url, config=run_config)

    print("Crawl complete. Check 'custom_deep_crawl.log' for logs from the strategy.")
    # You can verify the log file content here if needed
    # e.g., with open("custom_deep_crawl.log", "r") as f: assert "MyDeepCrawler" in f.read()
    # For this example, just visual confirmation is sufficient.

if __name__ == "__main__":
    asyncio.run(deep_crawl_custom_logger())
```

### 7.5. Example: Deep crawling starting from a local HTML file that contains links to other local files or web URLs.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch
from pathlib import Path
import os

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def deep_crawl_from_local_file():
    # Ensure the mock local files exist for the test
    local_index_path = Path(os.getcwd()) / "test_local_index.html"
    local_page1_path = Path(os.getcwd()) / "test_local_page1.html"

    # If not created by preamble, create them
    if not local_index_path.exists():
        local_index_path.write_text(MOCK_SITE_DATA[f"file://{local_index_path}"]["html_content"])
    if not local_page1_path.exists():
        local_page1_path.write_text(MOCK_SITE_DATA[f"file://{local_page1_path}"]["html_content"])

    start_file_url = f"file://{local_index_path.resolve()}"

    strategy = BFSDeePCrawlStrategy(max_depth=1, include_external=True) # Allow following to web URLs
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    print(f"--- Deep Crawling from Local File: {start_file_url} ---")
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun(url=start_file_url, config=run_config)

        print(f"Crawled {len(results)} pages.")
        found_local_link = False
        found_web_link = False
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
            if result.url == f"file://{local_page1_path.resolve()}":
                found_local_link = True
            if result.url == "https://docs.crawl4ai.com/vibe-examples/index.html":
                found_web_link = True

        assert found_local_link, "Did not follow local file link."
        assert found_web_link, "Did not follow web link from local file."

    # Clean up dummy files
    if local_index_path.exists(): os.remove(local_index_path)
    if local_page1_path.exists(): os.remove(local_page1_path)


if __name__ == "__main__":
    asyncio.run(deep_crawl_from_local_file())
```

### 7.6. Example: Comparing outputs from `BFSDeePCrawlStrategy`, `DFSDeePCrawlStrategy`, and `BestFirstCrawlingStrategy`.
This example runs all three main strategies with similar settings to highlight differences in traversal and results.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai import BFSDeePCrawlStrategy, DFSDeePCrawlStrategy, BestFirstCrawlingStrategy, KeywordRelevanceScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def compare_deep_crawl_strategies():
    start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
    max_depth = 2
    max_pages = 7 # Keep it manageable for comparison

    common_config_params = {
        "max_depth": max_depth,
        "max_pages": max_pages,
        "include_external": False, # Keep it simple for comparison
    }

    scorer = KeywordRelevanceScorer(keywords=["feature", "core"])

    strategies_to_compare = {
        "BFS": BFSDeePCrawlStrategy(**common_config_params),
        "DFS": DFSDeePCrawlStrategy(**common_config_params),
        "Best-First": BestFirstCrawlingStrategy(**common_config_params, url_scorer=scorer)
    }

    print(f"--- Comparing Deep Crawl Strategies (max_depth={max_depth}, max_pages={max_pages}) ---")

    async with AsyncWebCrawler() as crawler:
        for name, strategy_instance in strategies_to_compare.items():
            print(f"\n-- Running {name} Strategy --")
            run_config = CrawlerRunConfig(
                deep_crawl_strategy=strategy_instance,
                cache_mode=CacheMode.BYPASS,
                stream=False # Batch for easier comparison of final set
            )

            start_time = time.perf_counter()
            results = await crawler.arun(url=start_url, config=run_config)
            duration = time.perf_counter() - start_time

            print(f"  {name} crawled {len(results)} pages in {duration:.2f}s.")
            # Sort by depth then URL for consistent output for BFS/DFS
            # For Best-First, sort by score (desc) then depth then URL
            if name == "Best-First":
                 sorted_results = sorted(results, key=lambda r: (r.metadata.get('score', 0.0), -r.metadata.get('depth', 0), r.url), reverse=True)
            else:
                 sorted_results = sorted(results, key=lambda r: (r.metadata.get('depth', 0), r.url))


            for i, r in enumerate(sorted_results):
                if i < 5 or i > len(sorted_results) - 3 : # Show first 5 and last 2
                    score_str = f", Score: {r.metadata.get('score', 0.0):.2f}" if name == "Best-First" else ""
                    print(f"    URL: {r.url} (Depth: {r.metadata.get('depth')}{score_str})")
                elif i == 5:
                    print(f"    ... ({len(sorted_results) - 5 -2 } more results) ...")
            print("-" * 30)

if __name__ == "__main__":
    asyncio.run(compare_deep_crawl_strategies())
```

---
