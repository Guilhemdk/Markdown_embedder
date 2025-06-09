---
id: memory_full_document_sec6.6.2
cluster: memory
topic: full_document
title: Example: `CompositeScorer` assigning different `weights` to prioritize one scorer over another.
version_context: None
outline_date: None
section_hierarchy: ['Configuring Scorers (`URLScorer`) for `BestFirstCrawlingStrategy`', '`KeywordRelevanceScorer`', 'Example: `KeywordRelevanceScorer` with a list of keywords and default weight.', 'Example: `KeywordRelevanceScorer` adjusting the `weight` parameter to influence its importance.', 'Example: `KeywordRelevanceScorer` with `case_sensitive=True`.', '`PathDepthScorer`', 'Example: `PathDepthScorer` with default behavior (penalizing deeper paths).', 'Example: `PathDepthScorer` with custom `depth_penalty_factor`.', 'Example: `PathDepthScorer` with `higher_score_is_better=False` (to favor deeper paths).', '`ContentTypeScorer`', 'Example: `ContentTypeScorer` prioritizing `text/html` and penalizing `application/pdf`.', 'Example: `ContentTypeScorer` with custom `content_type_weights`.', '`DomainAuthorityScorer`', 'Example: Setting up `DomainAuthorityScorer` (conceptual, as DA often requires an external API or dataset).', '`FreshnessScorer`', 'Example: Setting up `FreshnessScorer` (conceptual, as freshness often requires parsing dates from content or headers).', '`CompositeScorer`', 'Example: Combining `KeywordRelevanceScorer` and `PathDepthScorer` using `CompositeScorer` with equal weights.', 'Example: `CompositeScorer` assigning different `weights` to prioritize one scorer over another.']
keywords: ['AsyncWebCrawler', 'BestFirstCrawlingStrategy', 'CacheMode', 'CompositeScorer', 'CrawlerRunConfig', 'Depth', 'False']
description:
file_path: 6_configuring_scorers_urlscorer_for_bestfirstcrawlingstrategy.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy
from crawl4ai import KeywordRelevanceScorer, PathDepthScorer, CompositeScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def composite_scorer_different_weights():
    # Keyword relevance is more important
    keyword_scorer = KeywordRelevanceScorer(keywords=["feature"])
    path_scorer = PathDepthScorer(higher_score_is_better=False)

    composite_scorer = CompositeScorer(
        scorers=[keyword_scorer, path_scorer],
        weights=[0.8, 0.2] # Keyword scorer has 80% influence, PathDepth 20%
    )

    strategy = BestFirstCrawlingStrategy(max_depth=1, url_scorer=composite_scorer, max_pages=5)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- CompositeScorer with different weights (Keyword: 0.8, PathDepth: 0.2) ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}, Depth: {result.metadata.get('depth')}")
    print("Keyword relevance should more heavily influence scores.")

if __name__ == "__main__":
    asyncio.run(composite_scorer_different_weights())
```