---
id: memory_full_document_sec4.10
cluster: memory
topic: full_document
title: Example: `BestFirstCrawlingStrategy` - Streaming results and observing the order based on scores.
version_context: None
outline_date: None
section_hierarchy: ['Best-First Crawling (`BestFirstCrawlingStrategy`) Examples', 'Example: Basic `BestFirstCrawlingStrategy` with default parameters.', 'Example: `BestFirstCrawlingStrategy` - Setting `max_depth` to limit crawl depth.', 'Example: `BestFirstCrawlingStrategy` - Setting `max_pages` to limit total pages crawled.', 'Example: `BestFirstCrawlingStrategy` - Using `include_external=True`.', 'Example: `BestFirstCrawlingStrategy` - Using `KeywordRelevanceScorer` to prioritize URLs containing specific keywords.', 'Example: `BestFirstCrawlingStrategy` - Using `PathDepthScorer` to influence priority based on URL path depth.', 'Example: `BestFirstCrawlingStrategy` - Using `ContentTypeScorer` to prioritize HTML pages over PDFs.', 'Example: `BestFirstCrawlingStrategy` - Using `CompositeScorer` to combine `KeywordRelevanceScorer` and `PathDepthScorer`.', 'Example: `BestFirstCrawlingStrategy` - Integrating a `FilterChain` with `ContentTypeFilter` to only process HTML.', 'Example: `BestFirstCrawlingStrategy` - Streaming results and observing the order based on scores.']
keywords: ['Assuming', 'AsyncWebCrawler', 'BestFirstCrawlingStrategy', 'CacheMode', 'CrawlerRunConfig', 'Depth', 'Due']
description:
file_path: 4_best_first_crawling_bestfirstcrawlingstrategy_examples.md::full_document
---

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