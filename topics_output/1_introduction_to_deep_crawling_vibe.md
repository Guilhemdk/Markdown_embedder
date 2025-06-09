## 1. Introduction to Deep Crawling (`vibe`)

The `vibe` component of Crawl4ai provides powerful deep crawling capabilities, allowing you to traverse websites by following links and processing multiple pages.

### 1.1. Example: Enabling Basic Deep Crawl with `BFSDeePCrawlStrategy` via `CrawlerRunConfig`.
This example demonstrates how to enable a basic Breadth-First Search (BFS) deep crawl by setting the `deep_crawl_strategy` in `CrawlerRunConfig`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

# Using the MockAsyncWebCrawler defined in the preamble
@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def basic_bfs_deep_crawl():
    # Configure BFS to crawl up to 1 level deep from the start URL
    bfs_strategy = BFSDeePCrawlStrategy(max_depth=1)

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=bfs_strategy,
        # For mock, ensure cache is bypassed to see fresh mock results
        cache_mode=CacheMode.BYPASS
    )

    # The actual AsyncWebCrawler is replaced by MockAsyncWebCrawler via @patch
    async with AsyncWebCrawler() as crawler: # This will be MockAsyncWebCrawler
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- Basic BFS Deep Crawl (max_depth=1) ---")
        print(f"Crawled {len(results)} pages starting from {start_url}:")
        for i, result in enumerate(results):
            if result.success:
                print(f"  {i+1}. URL: {result.url}, Depth: {result.metadata.get('depth')}, Parent: {result.metadata.get('parent_url')}")
            else:
                print(f"  {i+1}. FAILED: {result.url}, Error: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(basic_bfs_deep_crawl())
```

### 1.2. Example: Understanding `CrawlResult.metadata` (depth, parent_url, score) in Deep Crawl Results.
Each `CrawlResult` from a deep crawl contains useful metadata like the crawl `depth`, the `parent_url` from which it was discovered, and a `score` (if applicable, e.g., with `BestFirstCrawlingStrategy`).

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, KeywordRelevanceScorer, BestFirstCrawlingStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def understand_metadata():
    # Using BestFirstCrawlingStrategy to demonstrate scores
    scorer = KeywordRelevanceScorer(keywords=["feature", "core"])
    strategy = BestFirstCrawlingStrategy(max_depth=1, url_scorer=scorer)

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- Understanding CrawlResult.metadata ---")
        for result in results:
            if result.success:
                depth = result.metadata.get('depth', 'N/A')
                parent = result.metadata.get('parent_url', 'N/A')
                score = result.metadata.get('score', 'N/A') # Score comes from BestFirst strategy
                print(f"URL: {result.url}")
                print(f"  Depth: {depth}")
                print(f"  Parent URL: {parent}")
                print(f"  Score: {score if score != 'N/A' else 'N/A (not scored or BFS/DFS)'}")
                print("-" * 20)

if __name__ == "__main__":
    asyncio.run(understand_metadata())
```

### 1.3. Example: Minimal setup for deep crawling a single level deep.
This demonstrates the most straightforward way to perform a shallow deep crawl (depth 1).

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def minimal_single_level_deep_crawl():
    # BFS strategy, max_depth=1 means start_url + its direct links
    strategy = BFSDeePCrawlStrategy(max_depth=1)
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- Minimal Single Level Deep Crawl (max_depth=1) ---")
        print(f"Total pages crawled: {len(results)}")
        for result in results:
            if result.success:
                print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")

if __name__ == "__main__":
    asyncio.run(minimal_single_level_deep_crawl())
```

---
