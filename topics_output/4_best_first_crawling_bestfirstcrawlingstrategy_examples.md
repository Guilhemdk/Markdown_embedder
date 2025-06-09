## 4. Best-First Crawling (`BestFirstCrawlingStrategy`) Examples

`BestFirstCrawlingStrategy` uses a priority queue, guided by scorers, to decide which URLs to crawl next.

### 4.1. Example: Basic `BestFirstCrawlingStrategy` with default parameters.
If no `url_scorer` is provided, it behaves somewhat like BFS but might have different internal queue management.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_default_params():
    strategy = BestFirstCrawlingStrategy(max_depth=1) # Default scorer (often scores 0)

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BestFirstCrawlingStrategy with default parameters (max_depth=1) ---")
        print(f"Crawled {len(results)} pages.")
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}, Score: {result.metadata.get('score', 0.0):.2f}")

if __name__ == "__main__":
    asyncio.run(best_first_default_params())
```

### 4.2. Example: `BestFirstCrawlingStrategy` - Setting `max_depth` to limit crawl depth.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_max_depth():
    strategy = BestFirstCrawlingStrategy(max_depth=2)

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BestFirstCrawlingStrategy with max_depth=2 ---")
        print(f"Crawled {len(results)} pages.")
        for result in sorted(results, key=lambda r: (r.metadata.get('depth', 0), r.url)):
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}, Score: {result.metadata.get('score', 0.0):.2f}")
        assert all(r.metadata.get('depth', 0) <= 2 for r in results if r.success)

if __name__ == "__main__":
    asyncio.run(best_first_max_depth())
```

### 4.3. Example: `BestFirstCrawlingStrategy` - Setting `max_pages` to limit total pages crawled.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy
from unittest.mock import patch
import math

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_max_pages():
    strategy = BestFirstCrawlingStrategy(
        max_depth=math.inf,
        max_pages=3
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BestFirstCrawlingStrategy with max_pages=3 ---")
        print(f"Crawled {len(results)} pages.")
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}, Score: {result.metadata.get('score', 0.0):.2f}")
        assert len(results) <= 3

if __name__ == "__main__":
    asyncio.run(best_first_max_pages())
```

### 4.4. Example: `BestFirstCrawlingStrategy` - Using `include_external=True`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_include_external():
    strategy = BestFirstCrawlingStrategy(
        max_depth=1,
        include_external=True,
        max_pages=5 # To keep it manageable
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BestFirstCrawlingStrategy with include_external=True (max_depth=1) ---")
        print(f"Crawled {len(results)} pages.")
        found_external = False
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}, Score: {result.metadata.get('score', 0.0):.2f}")
            if "external-site.com" in result.url:
                found_external = True

        assert found_external, "Expected to crawl an external link."

if __name__ == "__main__":
    asyncio.run(best_first_include_external())
```

### 4.5. Example: `BestFirstCrawlingStrategy` - Using `KeywordRelevanceScorer` to prioritize URLs containing specific keywords.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_keyword_scorer():
    scorer = KeywordRelevanceScorer(keywords=["feature", "advanced", "core"])
    strategy = BestFirstCrawlingStrategy(
        max_depth=1,
        url_scorer=scorer,
        max_pages=4 # Limit for example clarity
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS,
        stream=True # Stream to see order
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        print(f"--- BestFirstCrawlingStrategy with KeywordRelevanceScorer ---")
        results_list = []
        async for result in await crawler.arun(url=start_url, config=run_config):
            results_list.append(result)
            if result.success:
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f} (Depth: {result.metadata.get('depth')})")

        # Check if pages with keywords like "feature" or "core" were prioritized (appeared earlier/higher score)
        # This is a soft check as actual order depends on many factors in a real crawl
        # and the mock site's link structure.
        print("\nNote: Higher scores should ideally correspond to URLs with keywords 'feature', 'advanced', 'core'.")
        feature_page_crawled = any("page2.html" in r.url for r in results_list) # page2 has "feature"
        assert feature_page_crawled, "Page with 'feature' keyword was expected."


if __name__ == "__main__":
    asyncio.run(best_first_keyword_scorer())
```

### 4.6. Example: `BestFirstCrawlingStrategy` - Using `PathDepthScorer` to influence priority based on URL path depth.
This scorer penalizes deeper paths by default.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, PathDepthScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_path_depth_scorer():
    # Penalizes deeper paths (lower score for deeper paths)
    scorer = PathDepthScorer(higher_score_is_better=False)
    strategy = BestFirstCrawlingStrategy(
        max_depth=2, # Allow some depth to see scorer effect
        url_scorer=scorer
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS,
        stream=True
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        print(f"--- BestFirstCrawlingStrategy with PathDepthScorer (favoring shallower paths) ---")

        results_list = []
        async for result in await crawler.arun(url=start_url, config=run_config):
            results_list.append(result)
            if result.success:
                 print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}, Depth: {result.metadata.get('depth')}")

        # A simple check: depth 1 pages should generally have higher (less negative) scores than depth 2
        # (if scores are negative due to penalty) or simply appear earlier if scores are positive.
        # With default scoring, higher score_is_better = True, so higher depth = lower score.
        # With higher_score_is_better=False, higher depth = higher (less negative) score.
        # The mock PathDepthScorer will need to be implemented or this test adjusted based on actual scorer logic.
        # For now, let's assume the scorer penalizes, so deeper paths have lower (more negative) scores.
        print("\nNote: Shallower pages should ideally have higher scores.")


if __name__ == "__main__":
    asyncio.run(best_first_path_depth_scorer())
```

### 4.7. Example: `BestFirstCrawlingStrategy` - Using `ContentTypeScorer` to prioritize HTML pages over PDFs.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, ContentTypeScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_content_type_scorer():
    # Prioritize HTML, penalize PDF
    scorer = ContentTypeScorer(content_type_weights={"text/html": 1.0, "application/pdf": -0.5})
    strategy = BestFirstCrawlingStrategy(
        max_depth=1,
        url_scorer=scorer
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS,
        stream=True
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/page1.html" # This page links to HTML and PDF
        print(f"--- BestFirstCrawlingStrategy with ContentTypeScorer (HTML > PDF) ---")

        results_list = []
        async for result in await crawler.arun(url=start_url, config=run_config):
            results_list.append(result)
            if result.success:
                 print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}, Content-Type: {result.response_headers.get('Content-Type')}")

        html_page_score = next((r.metadata.get('score') for r in results_list if "page1_sub1.html" in r.url), None)
        pdf_page_score = next((r.metadata.get('score') for r in results_list if "page1_sub2.pdf" in r.url), None)

        print(f"HTML page score: {html_page_score}, PDF page score: {pdf_page_score}")
        if html_page_score is not None and pdf_page_score is not None:
            assert html_page_score > pdf_page_score, "HTML page should have a higher score than PDF."
        elif html_page_score is None or pdf_page_score is None:
            print("Warning: Could not find both HTML and PDF pages in results to compare scores.")


if __name__ == "__main__":
    asyncio.run(best_first_content_type_scorer())
```

### 4.8. Example: `BestFirstCrawlingStrategy` - Using `CompositeScorer` to combine `KeywordRelevanceScorer` and `PathDepthScorer`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer, PathDepthScorer, CompositeScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_composite_scorer():
    keyword_scorer = KeywordRelevanceScorer(keywords=["feature", "core"], weight=0.7)
    path_scorer = PathDepthScorer(weight=0.3, higher_score_is_better=False) # Penalize depth slightly

    composite_scorer = CompositeScorer(scorers=[keyword_scorer, path_scorer])

    strategy = BestFirstCrawlingStrategy(
        max_depth=2,
        url_scorer=composite_scorer,
        max_pages=6
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS,
        stream=True
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        print(f"--- BestFirstCrawlingStrategy with CompositeScorer ---")

        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}, Depth: {result.metadata.get('depth')}")
        print("\nNote: Scores are a combination of keyword relevance and path depth penalty.")

if __name__ == "__main__":
    asyncio.run(best_first_composite_scorer())
```

### 4.9. Example: `BestFirstCrawlingStrategy` - Integrating a `FilterChain` with `ContentTypeFilter` to only process HTML.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, FilterChain, ContentTypeFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_with_content_type_filter():
    content_filter = ContentTypeFilter(allowed_types=["text/html"])
    filter_chain = FilterChain(filters=[content_filter])

    # Scorer is optional here, just demonstrating filter integration
    strategy = BestFirstCrawlingStrategy(
        max_depth=1,
        filter_chain=filter_chain
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/page1.html" # This page links to HTML and PDF
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BestFirstCrawlingStrategy with ContentTypeFilter (HTML only) ---")
        print(f"Crawled {len(results)} pages.")
        all_html = True
        for result in results:
            content_type = result.response_headers.get('Content-Type', '')
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}, Content-Type: {content_type}")
            if result.metadata.get('depth',0) > 0 and "text/html" not in content_type : # Start URL is not filtered
                 all_html = False

        discovered_pages = [r for r in results if r.metadata.get('depth',0) > 0]
        if discovered_pages:
            assert all("text/html" in r.response_headers.get('Content-Type','') for r in discovered_pages), "Non-HTML page found among discovered pages."
        print("Filter for HTML content type applied successfully to discovered pages.")

if __name__ == "__main__":
    asyncio.run(best_first_with_content_type_filter())
```

### 4.10. Example: `BestFirstCrawlingStrategy` - Streaming results and observing the order based on scores.
This example will use a scorer and stream results to demonstrate that higher-scored URLs are (generally) processed earlier.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_streaming_order():
    scorer = KeywordRelevanceScorer(keywords=["feature", "advanced"])
    strategy = BestFirstCrawlingStrategy(
        max_depth=1,
        url_scorer=scorer,
        max_pages=5
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=True,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        print(f"--- BestFirstCrawlingStrategy - Streaming and Observing Order ---")

        previous_score = float('inf') # Assuming scores are positive and higher is better
        processed_urls = []
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                current_score = result.metadata.get('score', 0.0)
                print(f"  Streamed: {result.url}, Score: {current_score:.2f}, Depth: {result.metadata.get('depth')}")
                # Note: Due to batching (BATCH_SIZE) and async nature, strict descending order isn't guaranteed
                # but generally higher scored items should appear earlier.
                # assert current_score <= previous_score + 1e-9, f"Scores not in generally descending order: {previous_score} then {current_score}"
                # previous_score = current_score
                processed_urls.append((result.url, current_score))

        print("\nProcessed URLs and their scores (order of processing):")
        for url, score in processed_urls:
            print(f"  {url} (Score: {score:.2f})")
        print("Note: Higher scored URLs are prioritized but strict order depends on batching and concurrency.")

if __name__ == "__main__":
    asyncio.run(best_first_streaming_order())
```

### 4.11. Example: `BestFirstCrawlingStrategy` - Batch results and analyzing scores post-crawl.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_batch_analysis():
    scorer = KeywordRelevanceScorer(keywords=["feature", "core"])
    strategy = BestFirstCrawlingStrategy(
        max_depth=1,
        url_scorer=scorer,
        max_pages=5
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=False, # Batch mode
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BestFirstCrawlingStrategy - Batch Results Analysis ---")
        print(f"Received {len(results)} pages.")

        # Sort by score for analysis (higher score first)
        sorted_results = sorted(results, key=lambda r: r.metadata.get('score', 0.0), reverse=True)

        for result in sorted_results:
            if result.success:
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}, Depth: {result.metadata.get('depth')}")

if __name__ == "__main__":
    asyncio.run(best_first_batch_analysis())
```

### 4.12. Example: `BestFirstCrawlingStrategy` - Accessing and interpreting `score`, `depth`, and `parent_url` from `CrawlResult.metadata`.
This explicitly shows how to get these specific metadata fields.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_access_metadata():
    scorer = KeywordRelevanceScorer(keywords=["feature"])
    strategy = BestFirstCrawlingStrategy(max_depth=1, url_scorer=scorer)

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BestFirstCrawlingStrategy - Accessing Metadata ---")
        for result in results:
            if result.success:
                url = result.url
                metadata = result.metadata
                depth = metadata.get('depth', 'N/A')
                parent_url = metadata.get('parent_url', 'N/A')
                score = metadata.get('score', 'N/A')

                print(f"URL: {url}")
                print(f"  Depth: {depth}")
                print(f"  Parent URL: {parent_url}")
                print(f"  Score: {score:.2f}" if isinstance(score, float) else f"  Score: {score}")
                print("-" * 10)

if __name__ == "__main__":
    asyncio.run(best_first_access_metadata())
```

### 4.13. Example: `BestFirstCrawlingStrategy` - Demonstrating `shutdown()` to stop an ongoing prioritized crawl.

```python
import asyncio
import time
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_demonstrate_shutdown():
    scorer = KeywordRelevanceScorer(keywords=["feature", "core", "example"])
    strategy = BestFirstCrawlingStrategy(
        max_depth=5, # A potentially long crawl
        max_pages=100,
        url_scorer=scorer
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=True,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"

        print(f"--- BestFirstCrawlingStrategy with shutdown() demonstration ---")

        crawl_task = asyncio.create_task(crawler.arun(url=start_url, config=run_config))

        await asyncio.sleep(0.1)

        print("Attempting to shut down the BestFirst crawl...")
        await strategy.shutdown()

        results_list = []
        try:
            async for res in await crawl_task:
                results_list.append(res)
                print(f"  Collected result (post-shutdown signal): {res.url} (Score: {res.metadata.get('score', 0.0):.2f})")
        except asyncio.CancelledError:
            print("Crawl task was cancelled.")

        print(f"Crawl shut down. Processed {len(results_list)} pages before/during shutdown.")
        assert len(results_list) < 10, "Crawl likely didn't shut down early enough or mock site too small."

if __name__ == "__main__":
    asyncio.run(best_first_demonstrate_shutdown())
```

### 4.14. Example: `BestFirstCrawlingStrategy` - Explaining the effect of `BATCH_SIZE` on `arun_many`.
`BATCH_SIZE` is an internal constant in `bbf_strategy.py` (typically 10). This example explains its role rather than making it directly configurable by the user through the strategy's constructor, as it's an internal implementation detail of how the strategy uses `crawler.arun_many`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer
from unittest.mock import patch

# Note: BATCH_SIZE is internal to BestFirstCrawlingStrategy, usually 10.
# We can't directly set it, but we can explain its effect.

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_batch_size_effect():
    print("--- Explaining BATCH_SIZE in BestFirstCrawlingStrategy ---")
    print("BestFirstCrawlingStrategy processes URLs in batches for efficiency.")
    print("Internally, it retrieves a batch of highest-priority URLs (typically up to BATCH_SIZE, e.g., 10) from its queue.")
    print("It then calls `crawler.arun_many()` with this batch.")
    print("This means that while URLs are prioritized, the order within a small batch might not be strictly descending by score,")
    print("especially if `stream=True`, as results from `arun_many` can arrive slightly out of strict submission order.")
    print("The overall crawl still heavily favors higher-scored URLs first over many batches.")

    # To simulate observing this, let's run a crawl and see if groups of results are processed.
    scorer = KeywordRelevanceScorer(keywords=["feature", "core", "page1", "page2"])
    strategy = BestFirstCrawlingStrategy(
        max_depth=2,
        url_scorer=scorer,
        max_pages=6 # Small enough to potentially see batching effects if BATCH_SIZE was smaller
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=True,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"

        print("\n--- Crawl Example (max_pages=6) ---")
        results_in_order = []
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                results_in_order.append(result.metadata.get('score',0.0))
                print(f"  Streamed: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}")

        # This assertion is hard to make definitively without knowing the exact internal BATCH_SIZE
        # and perfect mock site behavior. The print statements are more illustrative.
        print("\nScores in order of processing:", [f"{s:.2f}" for s in results_in_order])
        print("Observe if there are small groups where order might not be strictly descending due to batch processing.")


if __name__ == "__main__":
    asyncio.run(best_first_batch_size_effect())
```

---
