## 3. Depth-First Search (`DFSDeePCrawlStrategy`) Examples

`DFSDeePCrawlStrategy` explores as far down one branch as possible before backtracking.

### 3.1. Example: Basic `DFSDeePCrawlStrategy` with default depth.
The default `max_depth` for `DFSDeePCrawlStrategy` is typically 10 if not specified.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def dfs_default_depth():
    # Default max_depth for DFS is typically higher (e.g., 10)
    strategy = DFSDeePCrawlStrategy()

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        max_pages=5, # Limit pages to keep example short with default depth
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- DFS with Default Depth (max_pages=5 to limit output) ---")
        print(f"Crawled {len(results)} pages.")
        for result in results: # Order might be less predictable than BFS for small mock
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")

if __name__ == "__main__":
    asyncio.run(dfs_default_depth())
```

### 3.2. Example: `DFSDeePCrawlStrategy` - Setting `max_depth` to control how deep each branch goes.
Set `max_depth` to 2 for a DFS crawl.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def dfs_set_max_depth():
    strategy = DFSDeePCrawlStrategy(max_depth=2)

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- DFS with max_depth=2 ---")
        print(f"Crawled {len(results)} pages.")
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
        assert all(r.metadata.get('depth', 0) <= 2 for r in results if r.success)


if __name__ == "__main__":
    asyncio.run(dfs_set_max_depth())
```

### 3.3. Example: `DFSDeePCrawlStrategy` - Setting `max_pages` to limit the total number of pages.
Limit the total number of pages crawled by DFS to 3.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy
from unittest.mock import patch
import math

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def dfs_set_max_pages():
    strategy = DFSDeePCrawlStrategy(
        max_depth=math.inf, # No depth limit for this test
        max_pages=3
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- DFS with max_pages=3 ---")
        print(f"Crawled {len(results)} pages (should be at most 3).")
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
        assert len(results) <= 3

if __name__ == "__main__":
    asyncio.run(dfs_set_max_pages())
```

### 3.4. Example: `DFSDeePCrawlStrategy` - Following external links with `include_external=True`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def dfs_include_external():
    strategy = DFSDeePCrawlStrategy(
        max_depth=1,
        include_external=True,
        max_pages=5 # Limit pages as external can be vast
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- DFS with include_external=True (max_depth=1, max_pages=5) ---")
        print(f"Crawled {len(results)} pages.")
        found_external = False
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
            if "external-site.com" in result.url:
                found_external = True

        assert found_external, "Expected to crawl an external link."

if __name__ == "__main__":
    asyncio.run(dfs_include_external())
```

### 3.5. Example: `DFSDeePCrawlStrategy` - Staying within the domain with `include_external=False`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def dfs_exclude_external():
    strategy = DFSDeePCrawlStrategy(
        max_depth=1,
        include_external=False # Default
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- DFS with include_external=False (max_depth=1) ---")
        print(f"Crawled {len(results)} pages.")
        found_external = False
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
            if "external-site.com" in result.url:
                found_external = True

        assert not found_external, "Should not have crawled external links."

if __name__ == "__main__":
    asyncio.run(dfs_exclude_external())
```

### 3.6. Example: `DFSDeePCrawlStrategy` - Streaming results.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def dfs_streaming_results():
    strategy = DFSDeePCrawlStrategy(max_depth=1)

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=True,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        print(f"--- DFS with Streaming Results (max_depth=1) ---")
        count = 0
        async for result in await crawler.arun(url=start_url, config=run_config):
            count +=1
            if result.success:
                print(f"  Streamed Result {count}: {result.url}, Depth: {result.metadata.get('depth')}")
        print(f"Total results streamed: {count}")


if __name__ == "__main__":
    asyncio.run(dfs_streaming_results())
```

### 3.7. Example: `DFSDeePCrawlStrategy` - Batch results.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def dfs_batch_results():
    strategy = DFSDeePCrawlStrategy(max_depth=1)

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=False, # Default
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- DFS with Batch Results (max_depth=1) ---")
        print(f"Received {len(results)} pages in a batch.")
        for result in results:
            if result.success:
                print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")

if __name__ == "__main__":
    asyncio.run(dfs_batch_results())
```

### 3.8. Example: `DFSDeePCrawlStrategy` - Integrating a `FilterChain` with `DomainFilter` to restrict to subdomains.
This example is conceptual for subdomains as MOCK_SITE_DATA doesn't have distinct subdomains. The filter setup is key.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy, FilterChain, DomainFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def dfs_with_domain_filter_subdomains():
    # Allow only the start domain and its subdomains
    # For this mock, 'docs.crawl4ai.com' will be the main domain.
    # If we had e.g., 'blog.docs.crawl4ai.com', this filter would allow it.
    domain_filter = DomainFilter(
        allowed_domains=["docs.crawl4ai.com"],
        allow_subdomains=True
    )
    filter_chain = FilterChain(filters=[domain_filter])

    strategy = DFSDeePCrawlStrategy(
        max_depth=1,
        filter_chain=filter_chain,
        include_external=True # Necessary to even consider other (sub)domains
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- DFS with DomainFilter (allow subdomains of docs.crawl4ai.com) ---")
        print(f"Crawled {len(results)} pages.")
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
            # In a real scenario, you'd assert that only allowed domains/subdomains are present.
            # Our mock data doesn't have true subdomains to test this effectively.
            assert "docs.crawl4ai.com" in result.url or "external-site.com" not in result.url

if __name__ == "__main__":
    asyncio.run(dfs_with_domain_filter_subdomains())
```

---
