---
id: memory_full_document_sec8
cluster: memory
topic: full_document
title: Advanced Scenarios & Customization
version_context: None
outline_date: None
section_hierarchy: ['Advanced Scenarios & Customization', 'Example: Implementing a custom `DeepCrawlStrategy` by subclassing `DeepCrawlStrategy`.']
keywords: ['AsyncGenerator', 'AsyncWebCrawler', 'CacheMode', 'Crawl', 'CrawlResult', 'CrawlerRunConfig', 'Crawling']
description:
file_path: 8_advanced_scenarios_customization.md::full_document
---

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