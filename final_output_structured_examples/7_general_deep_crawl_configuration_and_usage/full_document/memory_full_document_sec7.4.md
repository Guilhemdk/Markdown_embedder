---
id: memory_full_document_sec7.4
cluster: memory
topic: full_document
title: Example: Using a custom `logger` instance passed to a `DeepCrawlStrategy`.
version_context: None
outline_date: None
section_hierarchy: ['General Deep Crawl Configuration and Usage', 'Example: Deep crawling a site that relies heavily on JavaScript for link generation.', 'Example: How `CrawlerRunConfig` parameters (e.g., `page_timeout`) and `BrowserConfig` (e.g., `user_agent`, `proxy_config`) affect underlying page fetches.', 'Example: Iterating through deep crawl results and handling cases where some pages failed to crawl or were filtered out.', 'Example: Using a custom `logger` instance passed to a `DeepCrawlStrategy`.']
keywords: ['AsyncLogger', 'AsyncWebCrawler', 'CacheMode', 'Check', 'Crawl', 'CrawlerRunConfig', 'Custom']
description:
file_path: 7_general_deep_crawl_configuration_and_usage.md::full_document
---

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