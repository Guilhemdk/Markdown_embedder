---
id: memory_full_document_sec6.1.2
cluster: memory
topic: full_document
title: Example: `KeywordRelevanceScorer` adjusting the `weight` parameter to influence its importance.
version_context: None
outline_date: None
section_hierarchy: ['Configuring Scorers (`URLScorer`) for `BestFirstCrawlingStrategy`', '`KeywordRelevanceScorer`', 'Example: `KeywordRelevanceScorer` with a list of keywords and default weight.', 'Example: `KeywordRelevanceScorer` adjusting the `weight` parameter to influence its importance.']
keywords: ['AsyncWebCrawler', 'BestFirstCrawlingStrategy', 'CacheMode', 'CompositeScorer', 'CrawlerRunConfig', 'False', 'High']
description:
file_path: 6_configuring_scorers_urlscorer_for_bestfirstcrawlingstrategy.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer, PathDepthScorer, CompositeScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def scorer_keyword_custom_weight():
    # High weight for keywords, low for path depth
    keyword_scorer = KeywordRelevanceScorer(keywords=["feature"], weight=2.0)
    path_scorer = PathDepthScorer(weight=0.1, higher_score_is_better=False) # Less penalty

    composite_scorer = CompositeScorer(scorers=[keyword_scorer, path_scorer])
    strategy = BestFirstCrawlingStrategy(max_depth=1, url_scorer=composite_scorer, max_pages=4)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- KeywordRelevanceScorer with adjusted weight (weight=2.0) in CompositeScorer ---")
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun("https://docs.crawl4ai.com/vibe-examples/index.html", config=run_config):
            if result.success:
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}")
    print("Keyword relevance should have a stronger impact on the final score.")

if __name__ == "__main__":
    asyncio.run(scorer_keyword_custom_weight())
```