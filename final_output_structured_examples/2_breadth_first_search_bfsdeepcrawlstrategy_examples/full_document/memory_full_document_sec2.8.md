---
id: memory_full_document_sec2.8
cluster: memory
topic: full_document
title: Example: `BFSDeePCrawlStrategy` - Integrating a `FilterChain` with `URLPatternFilter` to crawl specific paths.
version_context: None
outline_date: None
section_hierarchy: ['Breadth-First Search (`BFSDeePCrawlStrategy`) Examples', 'Example: Basic `BFSDeePCrawlStrategy` with default depth.', 'Example: `BFSDeePCrawlStrategy` - Setting `max_depth` to control crawl depth (e.g., 3 levels).', 'Example: `BFSDeePCrawlStrategy` - Setting `max_pages` to limit the total number of pages crawled (e.g., 10 pages).', 'Example: `BFSDeePCrawlStrategy` - Using `include_external=True` to follow links to external domains.', 'Example: `BFSDeePCrawlStrategy` - Using `include_external=False` (default) to stay within the starting domain.', 'Example: `BFSDeePCrawlStrategy` - Streaming results using `CrawlerRunConfig(stream=True)`.', 'Example: `BFSDeePCrawlStrategy` - Batch results using `CrawlerRunConfig(stream=False)` (default).', 'Example: `BFSDeePCrawlStrategy` - Integrating a `FilterChain` with `URLPatternFilter` to crawl specific paths.']
keywords: ['AsyncWebCrawler', 'CacheMode', 'Crawled', 'CrawlerRunConfig', 'Depth', 'False', 'Filter']
description:
file_path: 2_breadth_first_search_bfsdeepcrawlstrategy_examples.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, URLPatternFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_with_url_pattern_filter():
    # Only crawl URLs containing '/blog/'
    url_filter = URLPatternFilter(patterns=["*/blog/*"])
    filter_chain = FilterChain(filters=[url_filter])

    strategy = BFSDeePCrawlStrategy(
        max_depth=1,
        filter_chain=filter_chain
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BFS with URLPatternFilter ('*/blog/*') ---")
        print(f"Crawled {len(results)} pages.")
        all_match_pattern = True
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
            # The start URL itself might not match, but discovered links should
            if result.metadata.get('depth', 0) > 0 and "/blog/" not in result.url:
                all_match_pattern = False

        # The start_url itself is always processed, then its links are filtered.
        # So, we check if all *discovered* pages match the pattern.
        discovered_pages = [r for r in results if r.metadata.get('depth',0) > 0]
        if discovered_pages: # only assert if any pages beyond start_url were processed
            assert all("/blog/" in r.url for r in discovered_pages), "Not all crawled pages matched the /blog/ pattern"
        print("Filter applied successfully (start URL is always processed, subsequent links are filtered).")


if __name__ == "__main__":
    asyncio.run(bfs_with_url_pattern_filter())
```