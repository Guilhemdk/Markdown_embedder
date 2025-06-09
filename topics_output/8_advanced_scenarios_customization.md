## 8. Advanced Scenarios & Customization

### 8.1. Example: Implementing a custom `DeepCrawlStrategy` by subclassing `DeepCrawlStrategy`.
This provides a skeleton for creating your own crawl logic.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DeepCrawlStrategy, CrawlResult
from typing import List, Set, Dict, AsyncGenerator, Tuple
from unittest.mock import patch

class MyCustomDeepCrawlStrategy(DeepCrawlStrategy):
    def __init__(self, max_depth=1, **kwargs):
        self.max_depth = max_depth
        # Potentially other custom init params
        super().__init__(**kwargs) # Pass along other kwargs if base class uses them
        print("MyCustomDeepCrawlStrategy Initialized")

    async def _arun_batch(self, start_url: str, crawler: AsyncWebCrawler, config: CrawlerRunConfig) -> List[CrawlResult]:
        print(f"[Custom Strategy] _arun_batch called for: {start_url}")
        # Implement batch crawling logic (e.g., BFS-like)
        # This is a simplified version. A real one needs queue, visited set, depth tracking etc.
        results = []
        initial_result_container = await crawler.arun(url=start_url, config=config.clone(deep_crawl_strategy=None))
        initial_result = initial_result_container[0] # arun returns a list

        if not initial_result.success: return [initial_result]
        results.append(initial_result)

        if self.max_depth > 0 and initial_result.links.get("internal"):
            for link_info in initial_result.links["internal"][:2]: # Crawl first 2 internal links
                link_url = link_info["href"]
                # Pass metadata for depth and parent
                link_config = config.clone(deep_crawl_strategy=None)

                # In a real strategy, you'd manage metadata directly or pass it for crawler.arun
                # For this mock, we simplify as crawler.arun normally doesn't take depth/parent for single page
                print(f"  [Custom Strategy] Crawling linked URL: {link_url} at depth 1")
                linked_result_container = await crawler.arun(url=link_url, config=link_config)
                linked_result = linked_result_container[0]
                # Manually add metadata for this example
                if linked_result.metadata is None: linked_result.metadata = {}
                linked_result.metadata['depth'] = 1
                linked_result.metadata['parent_url'] = start_url
                results.append(linked_result)
        return results

    async def _arun_stream(self, start_url: str, crawler: AsyncWebCrawler, config: CrawlerRunConfig) -> AsyncGenerator[CrawlResult, None]:
        print(f"[Custom Strategy] _arun_stream called for: {start_url}")
        # Implement streaming crawling logic
        # Simplified: yields results from a batch-like process for this example
        batch_results = await self._arun_batch(start_url, crawler, config)
        for result in batch_results:
            yield result

    async def can_process_url(self, url: str, depth: int) -> bool:
        # Example: only process URLs not containing "archive" and within max_depth
        print(f"[Custom Strategy] can_process_url called for: {url}, depth: {depth}")
        if "archive" in url:
            return False
        return depth <= self.max_depth

    async def link_discovery(
        self, result: CrawlResult, source_url: str, current_depth: int,
        visited: Set[str], next_level: List[Tuple[str, str]], depths: Dict[str, int]
    ) -> None:
        # This method is crucial for discovering and queuing new links.
        # The base class might have a default implementation, or you might need to call
        # crawler.arun to get links if result.links is not populated.
        # For this example, we'll assume result.links is populated by the crawler.
        print(f"[Custom Strategy] link_discovery for: {source_url} at depth {current_depth}")
        new_depth = current_depth + 1
        if new_depth > self.max_depth:
            return

        for link_info in result.links.get("internal", [])[:3]: # Limit for example
            link_url = link_info["href"]
            if link_url not in visited and await self.can_process_url(link_url, new_depth):
                next_level.append((link_url, source_url)) # (url, parent_url)
                depths[link_url] = new_depth
                print(f"  [Custom Strategy] Discovered and added to queue: {link_url}")

    async def shutdown(self):
        print("[Custom Strategy] Shutdown called.")
        # Implement any cleanup or signal to stop crawling loops


@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def custom_deep_crawl_strategy_example():
    custom_strategy = MyCustomDeepCrawlStrategy(max_depth=1)
    run_config = CrawlerRunConfig(deep_crawl_strategy=custom_strategy, cache_mode=CacheMode.BYPASS)

    print("--- Using Custom DeepCrawlStrategy ---")
    async with AsyncWebCrawler() as crawler: # This will be MockAsyncWebCrawler
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"\nCustom strategy crawled {len(results)} pages:")
        for r in results:
            print(f"  URL: {r.url}, Success: {r.success}, Depth: {r.metadata.get('depth') if r.metadata else 'N/A'}")

if __name__ == "__main__":
    asyncio.run(custom_deep_crawl_strategy_example())
```

### 8.2. Example: Implementing a custom `URLFilter`.
`URLFilter` itself is a concrete class, but you can create custom logic by making a callable class or function that adheres to the expected filter signature `(url: str) -> bool`. For more complex stateful filters, subclassing a base might be an option if one is provided or creating your own structure.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain
from unittest.mock import patch

class MyCustomURLFilter:
    def __init__(self, forbidden_keyword: str):
        self.forbidden_keyword = forbidden_keyword.lower()
        print(f"MyCustomURLFilter initialized to block URLs with '{self.forbidden_keyword}'")

    async def __call__(self, url: str) -> bool: # Filters must be async
        """Return True if URL should be allowed, False if blocked."""
        if self.forbidden_keyword in url.lower():
            print(f"[CustomFilter] Blocking URL: {url} (contains '{self.forbidden_keyword}')")
            return False # Block if keyword found
        print(f"[CustomFilter] Allowing URL: {url}")
        return True # Allow otherwise

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def custom_url_filter_example():
    custom_filter = MyCustomURLFilter(forbidden_keyword="archive")
    filter_chain = FilterChain(filters=[custom_filter])

    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    print("--- Using Custom URLFilter (blocking 'archive') ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"\nCustom filter crawl resulted in {len(results)} pages:")
        for r in results:
            print(f"  URL: {r.url}")
            assert "archive" not in r.url.lower(), f"Custom filter failed to block {r.url}"
        print("Successfully blocked URLs containing 'archive'.")

if __name__ == "__main__":
    asyncio.run(custom_url_filter_example())
```

### 8.3. Example: Implementing a custom `URLScorer` for `BestFirstCrawlingStrategy`.
Subclass `URLScorer` and implement the `score` method.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, URLScorer
from urllib.parse import urlparse
from unittest.mock import patch

class MyCustomURLScorer(URLScorer):
    def __init__(self, preferred_domain: str, weight: float = 1.0):
        super().__init__(weight)
        self.preferred_domain = preferred_domain
        print(f"MyCustomURLScorer initialized, preferring domain: {self.preferred_domain}")

    def score(self, url: str, **kwargs) -> float:
        """Scores URL based on whether it matches the preferred domain."""
        parsed_url = urlparse(url)
        score = 0.0
        if parsed_url.netloc == self.preferred_domain:
            score = 1.0 * self.weight
            print(f"[CustomScorer] URL {url} matches preferred domain. Score: {score}")
        else:
            score = 0.1 * self.weight # Lower score for other domains
            print(f"[CustomScorer] URL {url} does NOT match preferred domain. Score: {score}")
        return score

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def custom_url_scorer_example():
    custom_scorer = MyCustomURLScorer(preferred_domain="docs.crawl4ai.com", weight=2.0)

    strategy = BestFirstCrawlingStrategy(
        max_depth=1,
        url_scorer=custom_scorer,
        include_external=True, # To allow scoring external domains differently
        max_pages=5
    )
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- Using Custom URLScorer (preferring 'docs.crawl4ai.com') ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}")
    print("Pages from 'docs.crawl4ai.com' should generally have higher scores.")

if __name__ == "__main__":
    asyncio.run(custom_url_scorer_example())
```

### 8.4. Example: Deep crawling a site with very large number of pages efficiently using `max_pages` and streaming.
This combines `max_pages` to limit the scope and `stream=True` to process results incrementally, which is crucial for very large crawls to manage memory and get feedback sooner.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def deep_crawl_large_site_efficiently():
    # Simulate a large site by setting a high conceptual depth,
    # but limit actual work with max_pages.
    strategy = BFSDeePCrawlStrategy(
        max_depth=10,      # Imagine this could lead to thousands of pages
        max_pages=10,      # But we only want the first 10 found by BFS
        include_external=False
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=True,       # Process results as they come
        cache_mode=CacheMode.BYPASS # Or CacheMode.ENABLED for subsequent partial crawls
    )

    print("--- Efficiently Crawling a 'Large' Site (max_pages=10, stream=True) ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html" # Use our mock site

        crawled_count = 0
        async for result in await crawler.arun(url=start_url, config=run_config):
            crawled_count += 1
            if result.success:
                print(f"  Processed ({crawled_count}/{strategy.max_pages}): {result.url} at depth {result.metadata.get('depth')}")
            else:
                print(f"  Failed ({crawled_count}/{strategy.max_pages}): {result.url} - {result.error_message}")

            if crawled_count >= strategy.max_pages:
                print(f"Reached max_pages limit of {strategy.max_pages}. Stopping.")
                # In a real scenario, you might need to call strategy.shutdown() if the crawler
                # doesn't automatically stop precisely at max_pages when streaming.
                # However, strategies are designed to respect max_pages.
                break

        print(f"\nTotal pages processed: {crawled_count}")
        assert crawled_count <= strategy.max_pages

if __name__ == "__main__":
    asyncio.run(deep_crawl_large_site_efficiently())
```

### 8.5. Example: Combining deep crawling with `LLMExtractionStrategy` to extract structured data from each crawled page.
This example shows setting up a deep crawl where each successfully crawled page's content is then passed to an `LLMExtractionStrategy`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, LLMExtractionStrategy, LLMConfig
from pydantic import BaseModel, Field
from unittest.mock import patch

class PageSummary(BaseModel):
    title: str = Field(description="The main title of the page.")
    brief_summary: str = Field(description="A one-sentence summary of the page content.")

# Mock the LLM call within the extraction strategy for this example
async def mock_llm_extract(self, url: str, sections: list[str]):
    print(f"[Mock LLM] Extracting from {url}, first section: {sections[0][:50]}...")
    # Based on the URL from MOCK_SITE_DATA, return a plausible mock summary
    if "index.html" in url:
        return [{"title": "Index", "brief_summary": "This is the main page."}]
    elif "page1.html" in url:
        return [{"title": "Page 1", "brief_summary": "Content about crawl strategies."}]
    elif "page2.html" in url:
        return [{"title": "Page 2 - Feature Rich", "brief_summary": "Discusses a key feature."}]
    return [{"title": "Unknown Title", "brief_summary": "Could not summarize."}]

@patch('crawl4ai.extraction_strategy.LLMExtractionStrategy.run', side_effect=mock_llm_extract)
@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def deep_crawl_with_llm_extraction(mock_llm_run): # mock_llm_run is from the patch
    llm_config = LLMConfig(provider="mock/mock-model") # Mock provider

    extraction_strategy = LLMExtractionStrategy(
        llm_config=llm_config,
        schema=PageSummary.model_json_schema(), # Use Pydantic model for schema
        extraction_type="schema",
        instruction="Extract the title and a brief summary for the provided HTML content."
    )

    deep_crawl_config = BFSDeePCrawlStrategy(max_depth=1, max_pages=3)

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=deep_crawl_config,
        extraction_strategy=extraction_strategy, # Apply this to each crawled page
        cache_mode=CacheMode.BYPASS
    )

    print("--- Deep Crawl with LLM Extraction on Each Page ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        for result in results:
            if result.success:
                print(f"\nCrawled URL: {result.url}")
                if result.extracted_content:
                    print(f"  Extracted Data: {result.extracted_content}")
                else:
                    print("  No data extracted (or LLM mock returned empty).")
            else:
                print(f"\nFailed to crawl URL: {result.url} - {result.error_message}")

        assert mock_llm_run.called, "LLM Extraction strategy's run method was not called."

if __name__ == "__main__":
    asyncio.run(deep_crawl_with_llm_extraction())
```

### 8.6. Example: Scenario for using `can_process_url` within a strategy to dynamically decide if a URL should be added to the queue.
Override `can_process_url` in a custom strategy to implement dynamic filtering logic based on URL and current depth.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, CrawlResult
from typing import List, Set, Dict, Tuple
from unittest.mock import patch

class DepthAndPatternAwareBFSStrategy(BFSDeePCrawlStrategy):
    async def can_process_url(self, url: str, depth: int) -> bool:
        # Standard checks from parent (like filter_chain)
        if not await super().can_process_url(url, depth):
            print(f"[Custom can_process_url] Blocked by parent: {url}")
            return False

        # Custom logic: Do not process '/archive/' pages if depth is > 1
        if depth > 1 and "/archive/" in url:
            print(f"[Custom can_process_url] Blocking deep archive page: {url} at depth {depth}")
            return False

        print(f"[Custom can_process_url] Allowing: {url} at depth {depth}")
        return True

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def custom_can_process_url_example():
    # Add a deeper archive link for testing
    MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/page1.html"]["html_content"] += '<a href="archive/deep_archive.html">Deep Archive</a>'
    MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/archive/deep_archive.html"] = {
        "html_content": "<html><title>Deep Archive</title><body>Very old stuff.</body></html>",
        "response_headers": {"Content-Type": "text/html"}
    }

    custom_strategy = DepthAndPatternAwareBFSStrategy(max_depth=2) # Crawl up to depth 2
    run_config = CrawlerRunConfig(deep_crawl_strategy=custom_strategy, cache_mode=CacheMode.BYPASS)

    print("--- Custom Strategy with Dynamic can_process_url ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"\nCrawled {len(results)} pages:")
        archive_at_depth_1_crawled = False
        deep_archive_blocked = True

        for r in results:
            print(f"  URL: {r.url}, Depth: {r.metadata.get('depth')}")
            if "/archive/old_page.html" in r.url and r.metadata.get('depth') == 1:
                archive_at_depth_1_crawled = True
            if "/archive/deep_archive.html" in r.url and r.metadata.get('depth') == 2:
                 # This should not happen due to our custom can_process_url
                deep_archive_blocked = False

        assert archive_at_depth_1_crawled, "Archive page at depth 1 should have been crawled."
        assert deep_archive_blocked, "Deep archive page at depth 2 should have been blocked by custom can_process_url."
        print("Dynamic URL processing logic worked as expected.")

    # Clean up mock data
    MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/page1.html"]["html_content"] = MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/page1.html"]["html_content"].replace('<a href="archive/deep_archive.html">Deep Archive</a>', '')
    del MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/archive/deep_archive.html"]


if __name__ == "__main__":
    asyncio.run(custom_can_process_url_example())
    # Clean up dummy files after all examples run
    if (Path(os.getcwd()) / "test_local_index.html").exists():
        os.remove(Path(os.getcwd()) / "test_local_index.html")
    if (Path(os.getcwd()) / "test_local_page1.html").exists():
        os.remove(Path(os.getcwd()) / "test_local_page1.html")
    if Path("custom_deep_crawl.log").exists():
        os.remove("custom_deep_crawl.log")

```

---
