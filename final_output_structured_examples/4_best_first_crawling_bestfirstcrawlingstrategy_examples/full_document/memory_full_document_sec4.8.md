---
id: memory_full_document_sec4.8
cluster: memory
topic: full_document
title: Example: `BestFirstCrawlingStrategy` - Using `CompositeScorer` to combine `KeywordRelevanceScorer` and `PathDepthScorer`.
version_context: None
outline_date: None
section_hierarchy: ['Best-First Crawling (`BestFirstCrawlingStrategy`) Examples', 'Example: Basic `BestFirstCrawlingStrategy` with default parameters.', 'Example: `BestFirstCrawlingStrategy` - Setting `max_depth` to limit crawl depth.', 'Example: `BestFirstCrawlingStrategy` - Setting `max_pages` to limit total pages crawled.', 'Example: `BestFirstCrawlingStrategy` - Using `include_external=True`.', 'Example: `BestFirstCrawlingStrategy` - Using `KeywordRelevanceScorer` to prioritize URLs containing specific keywords.', 'Example: `BestFirstCrawlingStrategy` - Using `PathDepthScorer` to influence priority based on URL path depth.', 'Example: `BestFirstCrawlingStrategy` - Using `ContentTypeScorer` to prioritize HTML pages over PDFs.', 'Example: `BestFirstCrawlingStrategy` - Using `CompositeScorer` to combine `KeywordRelevanceScorer` and `PathDepthScorer`.']
keywords: ['AsyncWebCrawler', 'BestFirstCrawlingStrategy', 'CacheMode', 'CompositeScorer', 'CrawlerRunConfig', 'Depth', 'False']
description:
file_path: 4_best_first_crawling_bestfirstcrawlingstrategy_examples.md::full_document
---

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