---
id: memory_full_document_sec6
cluster: memory
topic: full_document
title: Configuring Scorers (`URLScorer`) for `BestFirstCrawlingStrategy`
version_context: None
outline_date: None
section_hierarchy: ['Configuring Scorers (`URLScorer`) for `BestFirstCrawlingStrategy`', '`KeywordRelevanceScorer`', 'Example: `KeywordRelevanceScorer` with a list of keywords and default weight.']
keywords: ['AsyncWebCrawler', 'BestFirstCrawlingStrategy', 'CacheMode', 'CrawlerRunConfig', 'Default', 'KeywordRelevanceScorer', 'MockAsyncWebCrawler']
description:
file_path: 6_configuring_scorers_urlscorer_for_bestfirstcrawlingstrategy.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def scorer_keyword_default_weight():
    scorer = KeywordRelevanceScorer(keywords=["feature", "core concepts"]) # Default weight is 1.0
    strategy = BestFirstCrawlingStrategy(max_depth=1, url_scorer=scorer, max_pages=4)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- KeywordRelevanceScorer with default weight ---")
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun("https://docs.crawl4ai.com/vibe-examples/index.html", config=run_config):
            if result.success:
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}")
    print("Pages containing 'feature' or 'core concepts' in their URL should have higher scores.")

if __name__ == "__main__":
    asyncio.run(scorer_keyword_default_weight())
```