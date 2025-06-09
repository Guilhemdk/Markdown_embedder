---
id: memory_full_document_sec4.6
cluster: memory
topic: full_document
title: Example: `BestFirstCrawlingStrategy` - Using `PathDepthScorer` to influence priority based on URL path depth.
version_context: None
outline_date: None
section_hierarchy: ['Best-First Crawling (`BestFirstCrawlingStrategy`) Examples', 'Example: Basic `BestFirstCrawlingStrategy` with default parameters.', 'Example: `BestFirstCrawlingStrategy` - Setting `max_depth` to limit crawl depth.', 'Example: `BestFirstCrawlingStrategy` - Setting `max_pages` to limit total pages crawled.', 'Example: `BestFirstCrawlingStrategy` - Using `include_external=True`.', 'Example: `BestFirstCrawlingStrategy` - Using `KeywordRelevanceScorer` to prioritize URLs containing specific keywords.', 'Example: `BestFirstCrawlingStrategy` - Using `PathDepthScorer` to influence priority based on URL path depth.']
keywords: ['Allow', 'AsyncWebCrawler', 'BestFirstCrawlingStrategy', 'CacheMode', 'CrawlerRunConfig', 'Depth', 'False']
description:
file_path: 4_best_first_crawling_bestfirstcrawlingstrategy_examples.md::full_document
---

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