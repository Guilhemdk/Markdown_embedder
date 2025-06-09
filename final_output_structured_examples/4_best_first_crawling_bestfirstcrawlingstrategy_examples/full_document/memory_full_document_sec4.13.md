---
id: memory_full_document_sec4.13
cluster: memory
topic: full_document
title: Example: `BestFirstCrawlingStrategy` - Demonstrating `shutdown()` to stop an ongoing prioritized crawl.
version_context: None
outline_date: None
section_hierarchy: ['Best-First Crawling (`BestFirstCrawlingStrategy`) Examples', 'Example: Basic `BestFirstCrawlingStrategy` with default parameters.', 'Example: `BestFirstCrawlingStrategy` - Setting `max_depth` to limit crawl depth.', 'Example: `BestFirstCrawlingStrategy` - Setting `max_pages` to limit total pages crawled.', 'Example: `BestFirstCrawlingStrategy` - Using `include_external=True`.', 'Example: `BestFirstCrawlingStrategy` - Using `KeywordRelevanceScorer` to prioritize URLs containing specific keywords.', 'Example: `BestFirstCrawlingStrategy` - Using `PathDepthScorer` to influence priority based on URL path depth.', 'Example: `BestFirstCrawlingStrategy` - Using `ContentTypeScorer` to prioritize HTML pages over PDFs.', 'Example: `BestFirstCrawlingStrategy` - Using `CompositeScorer` to combine `KeywordRelevanceScorer` and `PathDepthScorer`.', 'Example: `BestFirstCrawlingStrategy` - Integrating a `FilterChain` with `ContentTypeFilter` to only process HTML.', 'Example: `BestFirstCrawlingStrategy` - Streaming results and observing the order based on scores.', 'Example: `BestFirstCrawlingStrategy` - Batch results and analyzing scores post-crawl.', 'Example: `BestFirstCrawlingStrategy` - Accessing and interpreting `score`, `depth`, and `parent_url` from `CrawlResult.metadata`.', 'Example: `BestFirstCrawlingStrategy` - Demonstrating `shutdown()` to stop an ongoing prioritized crawl.']
keywords: ['AsyncWebCrawler', 'Attempting', 'BestFirst', 'BestFirstCrawlingStrategy', 'CacheMode', 'CancelledError', 'Collected']
description:
file_path: 4_best_first_crawling_bestfirstcrawlingstrategy_examples.md::full_document
---

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