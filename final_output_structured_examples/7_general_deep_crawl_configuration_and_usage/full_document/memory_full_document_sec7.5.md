---
id: memory_full_document_sec7.5
cluster: memory
topic: full_document
title: Example: Deep crawling starting from a local HTML file that contains links to other local files or web URLs.
version_context: None
outline_date: None
section_hierarchy: ['General Deep Crawl Configuration and Usage', 'Example: Deep crawling a site that relies heavily on JavaScript for link generation.', 'Example: How `CrawlerRunConfig` parameters (e.g., `page_timeout`) and `BrowserConfig` (e.g., `user_agent`, `proxy_config`) affect underlying page fetches.', 'Example: Iterating through deep crawl results and handling cases where some pages failed to crawl or were filtered out.', 'Example: Using a custom `logger` instance passed to a `DeepCrawlStrategy`.', 'Example: Deep crawling starting from a local HTML file that contains links to other local files or web URLs.']
keywords: ['Allow', 'AsyncWebCrawler', 'CacheMode', 'Clean', 'Crawled', 'CrawlerRunConfig', 'Crawling']
description:
file_path: 7_general_deep_crawl_configuration_and_usage.md::full_document
---

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