---
id: memory_full_document_sec7.2
cluster: memory
topic: full_document
title: Example: How `CrawlerRunConfig` parameters (e.g., `page_timeout`) and `BrowserConfig` (e.g., `user_agent`, `proxy_config`) affect underlying page fetches.
version_context: None
outline_date: None
section_hierarchy: ['General Deep Crawl Configuration and Usage', 'Example: Deep crawling a site that relies heavily on JavaScript for link generation.', 'Example: How `CrawlerRunConfig` parameters (e.g., `page_timeout`) and `BrowserConfig` (e.g., `user_agent`, `proxy_config`) affect underlying page fetches.']
keywords: [' to truly verify user_agent/proxy.\n        # For this example, we\'ll conceptually check based on setup.\n        print(f"Browser User-Agent set to: {crawler.browser_config.user_agent}")\n        if crawler.browser_config.proxy_config:\n            print(f"Browser Proxy set to: {crawler.browser_config.proxy_config.server}")\n        \n        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"\n        results = await crawler.arun(url=start_url, config=run_cfg)\n        \n        if results and results[0].success:\n            print(f"Crawled {results[0].url} successfully with page_timeout={run_cfg.page_timeout}ms")\n            # In a real scenario with a proxy, you\'d verify the source IP.\n            # For mock:\n            # perceived_ip = await mock_check_ip_via_proxy(start_url, browser_cfg) \n            # print(f"Perceived IP (mocked): {perceived_ip}")\n            # assert perceived_ip == "1.2.3.4" # Assuming proxy was used\n        else:\n            print(f"Crawl failed for {start_url}")\n\nif __name__ == "__main__":\n    asyncio.run(deep_crawl_with_configs())\n', 'Agent', 'Assuming', 'AsyncWebCrawler', 'Browser', 'BrowserConfig', 'CacheMode']
description:
file_path: 7_general_deep_crawl_configuration_and_usage.md::full_document
---

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