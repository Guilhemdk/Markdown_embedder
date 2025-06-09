## 2. Breadth-First Search (`BFSDeePCrawlStrategy`) Examples

`BFSDeePCrawlStrategy` explores the website level by level.

### 2.1. Example: Basic `BFSDeePCrawlStrategy` with default depth.
The default `max_depth` for `BFSDeePCrawlStrategy` is often 1 if not specified, meaning it crawls the start URL and its direct links.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_default_depth():
    # Default max_depth is typically 1 (start_url + its direct children)
    # but let's be explicit for clarity or test with a higher default if library changes
    strategy = BFSDeePCrawlStrategy() # Default max_depth is 1

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BFS with Default Depth (max_depth=1) ---")
        print(f"Crawled {len(results)} pages.")
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")

if __name__ == "__main__":
    asyncio.run(bfs_default_depth())
```

### 2.2. Example: `BFSDeePCrawlStrategy` - Setting `max_depth` to control crawl depth (e.g., 3 levels).
Control how many levels deep the BFS crawler will go from the start URL. `max_depth=0` means only the start URL. `max_depth=1` means start URL + its direct links.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_set_max_depth():
    strategy = BFSDeePCrawlStrategy(max_depth=2) # Start URL (0), its links (1), and their links (2)

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BFS with max_depth=2 ---")
        print(f"Crawled {len(results)} pages.")
        for result in sorted(results, key=lambda r: (r.metadata.get('depth', 0), r.url)):
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")

        # Verify that no pages with depth > 2 are present
        assert all(r.metadata.get('depth', 0) <= 2 for r in results if r.success)

if __name__ == "__main__":
    asyncio.run(bfs_set_max_depth())
```

### 2.3. Example: `BFSDeePCrawlStrategy` - Setting `max_pages` to limit the total number of pages crawled (e.g., 10 pages).
Limit the crawl to a maximum number of pages, regardless of depth.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch
import math # for math.inf

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_set_max_pages():
    strategy = BFSDeePCrawlStrategy(
        max_depth=math.inf, # Effectively no depth limit for this test
        max_pages=3         # Limit to 3 pages
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BFS with max_pages=3 ---")
        print(f"Crawled {len(results)} pages (should be at most 3).")
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")

        assert len(results) <= 3

if __name__ == "__main__":
    asyncio.run(bfs_set_max_pages())
```

### 2.4. Example: `BFSDeePCrawlStrategy` - Using `include_external=True` to follow links to external domains.
Allow the BFS crawler to follow links that lead to different domains than the start URL.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_include_external():
    strategy = BFSDeePCrawlStrategy(
        max_depth=1,
        include_external=True
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BFS with include_external=True (max_depth=1) ---")
        print(f"Crawled {len(results)} pages.")
        found_external = False
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
            if "external-site.com" in result.url:
                found_external = True

        assert found_external, "Expected to crawl an external link."

if __name__ == "__main__":
    asyncio.run(bfs_include_external())
```

### 2.5. Example: `BFSDeePCrawlStrategy` - Using `include_external=False` (default) to stay within the starting domain.
The default behavior is to only crawl links within the same domain as the start URL.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_exclude_external():
    strategy = BFSDeePCrawlStrategy(
        max_depth=1,
        include_external=False # Default, but explicit for clarity
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BFS with include_external=False (max_depth=1) ---")
        print(f"Crawled {len(results)} pages.")
        found_external = False
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
            if "external-site.com" in result.url:
                found_external = True

        assert not found_external, "Should not have crawled external links."

if __name__ == "__main__":
    asyncio.run(bfs_exclude_external())
```

### 2.6. Example: `BFSDeePCrawlStrategy` - Streaming results using `CrawlerRunConfig(stream=True)`.
Process results as they become available, useful for long crawls.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_streaming_results():
    strategy = BFSDeePCrawlStrategy(max_depth=1)

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=True, # Enable streaming
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        print(f"--- BFS with Streaming Results (max_depth=1) ---")
        count = 0
        async for result in await crawler.arun(url=start_url, config=run_config):
            count += 1
            if result.success:
                print(f"  Streamed Result {count}: {result.url}, Depth: {result.metadata.get('depth')}")
            else:
                print(f"  Streamed FAILED Result {count}: {result.url}, Error: {result.error_message}")
        print(f"Total results streamed: {count}")

if __name__ == "__main__":
    asyncio.run(bfs_streaming_results())
```

### 2.7. Example: `BFSDeePCrawlStrategy` - Batch results using `CrawlerRunConfig(stream=False)` (default).
The default behavior is to return all results as a list after the crawl completes.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_batch_results():
    strategy = BFSDeePCrawlStrategy(max_depth=1)

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=False, # Default, but explicit for clarity
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config) # Returns a list

        print(f"--- BFS with Batch Results (max_depth=1) ---")
        print(f"Received {len(results)} pages in a batch.")
        for result in results:
            if result.success:
                print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")

if __name__ == "__main__":
    asyncio.run(bfs_batch_results())
```

### 2.8. Example: `BFSDeePCrawlStrategy` - Integrating a `FilterChain` with `URLPatternFilter` to crawl specific paths.
Use filters to guide the crawler, for instance, to only explore URLs matching `/blog/*`.

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

### 2.9. Example: `BFSDeePCrawlStrategy` - Demonstrating `shutdown()` to gracefully stop an ongoing crawl.
Showcase how to stop a crawl prematurely using the strategy's `shutdown()` method.

```python
import asyncio
import time
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_demonstrate_shutdown():
    strategy = BFSDeePCrawlStrategy(
        max_depth=5, # A potentially long crawl
        max_pages=100
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=True, # Streaming is good to see partial results before shutdown
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html" # A site with enough links

        print(f"--- BFS with shutdown() demonstration ---")

        crawl_task = asyncio.create_task(crawler.arun(url=start_url, config=run_config))

        # Let the crawl run for a very short time
        await asyncio.sleep(0.1)

        print("Attempting to shut down the crawl...")
        await strategy.shutdown()

        results_list = []
        try:
            # Await the results from the crawl task
            # If streaming, this will iterate through what was processed before shutdown
            async for res in await crawl_task:
                results_list.append(res)
                print(f"  Collected result (post-shutdown signal): {res.url}")
        except asyncio.CancelledError:
            print("Crawl task was cancelled.")

        print(f"Crawl shut down. Processed {len(results_list)} pages before/during shutdown.")
        # The number of pages will be less than if it ran to completion
        assert len(results_list) < 10, "Crawl likely didn't shut down early enough or mock site too small."

if __name__ == "__main__":
    asyncio.run(bfs_demonstrate_shutdown())
```

### 2.10. Example: `BFSDeePCrawlStrategy` - Crawling with no `max_depth` limit but a `max_pages` limit.
Demonstrate a scenario where depth is unlimited (or very high) but the crawl stops after a certain number of pages.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch
import math

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_no_depth_limit_max_pages():
    strategy = BFSDeePCrawlStrategy(
        max_depth=math.inf, # Unlimited depth
        max_pages=4        # But only 4 pages
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BFS with no depth limit, max_pages=4 ---")
        print(f"Crawled {len(results)} pages.")
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")

        assert len(results) <= 4, "More pages crawled than max_pages limit."

if __name__ == "__main__":
    asyncio.run(bfs_no_depth_limit_max_pages())
```

---
