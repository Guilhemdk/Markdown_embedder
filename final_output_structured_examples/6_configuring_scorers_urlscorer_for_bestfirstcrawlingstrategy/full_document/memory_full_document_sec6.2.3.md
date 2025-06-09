---
id: memory_full_document_sec6.2.3
cluster: memory
topic: full_document
title: Example: `PathDepthScorer` with `higher_score_is_better=False` (to favor deeper paths).
version_context: None
outline_date: None
section_hierarchy: ['Configuring Scorers (`URLScorer`) for `BestFirstCrawlingStrategy`', '`KeywordRelevanceScorer`', 'Example: `KeywordRelevanceScorer` with a list of keywords and default weight.', 'Example: `KeywordRelevanceScorer` adjusting the `weight` parameter to influence its importance.', 'Example: `KeywordRelevanceScorer` with `case_sensitive=True`.', '`PathDepthScorer`', 'Example: `PathDepthScorer` with default behavior (penalizing deeper paths).', 'Example: `PathDepthScorer` with custom `depth_penalty_factor`.', 'Example: `PathDepthScorer` with `higher_score_is_better=False` (to favor deeper paths).']
keywords: ['AsyncWebCrawler', 'Avg', 'BestFirstCrawlingStrategy', 'CacheMode', 'CrawlerRunConfig', 'Deeper', 'Depth']
description:
file_path: 6_configuring_scorers_urlscorer_for_bestfirstcrawlingstrategy.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, PathDepthScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def scorer_path_depth_favor_deep():
    # Now, deeper paths will get higher (less negative or more positive) scores
    scorer = PathDepthScorer(higher_score_is_better=False)
    strategy = BestFirstCrawlingStrategy(max_depth=2, url_scorer=scorer, max_pages=6)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- PathDepthScorer with higher_score_is_better=False (favoring deeper paths) ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"

        depth_scores = {}
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                depth = result.metadata.get('depth')
                score = result.metadata.get('score', 0.0)
                print(f"  URL: {result.url}, Depth: {depth}, Score: {score:.2f}")
                if depth not in depth_scores:
                    depth_scores[depth] = []
                depth_scores[depth].append(score)

        if 1 in depth_scores and 2 in depth_scores and depth_scores[1] and depth_scores[2]:
           avg_score_depth1 = sum(depth_scores[1]) / len(depth_scores[1])
           avg_score_depth2 = sum(depth_scores[2]) / len(depth_scores[2])
           print(f"Avg score depth 1: {avg_score_depth1:.2f}, Avg score depth 2: {avg_score_depth2:.2f}")
           assert avg_score_depth2 > avg_score_depth1, "Deeper paths should have higher scores with higher_score_is_better=False."

if __name__ == "__main__":
    asyncio.run(scorer_path_depth_favor_deep())
```