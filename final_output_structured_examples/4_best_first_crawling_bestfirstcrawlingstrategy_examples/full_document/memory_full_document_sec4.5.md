---
id: memory_full_document_sec4.5
cluster: memory
topic: full_document
title: Example: `BestFirstCrawlingStrategy` - Using `KeywordRelevanceScorer` to prioritize URLs containing specific keywords.
version_context: None
outline_date: None
section_hierarchy: ['Best-First Crawling (`BestFirstCrawlingStrategy`) Examples', 'Example: Basic `BestFirstCrawlingStrategy` with default parameters.', 'Example: `BestFirstCrawlingStrategy` - Setting `max_depth` to limit crawl depth.', 'Example: `BestFirstCrawlingStrategy` - Setting `max_pages` to limit total pages crawled.', 'Example: `BestFirstCrawlingStrategy` - Using `include_external=True`.', 'Example: `BestFirstCrawlingStrategy` - Using `KeywordRelevanceScorer` to prioritize URLs containing specific keywords.']
keywords: ['AsyncWebCrawler', 'BestFirstCrawlingStrategy', 'CacheMode', 'Check', 'CrawlerRunConfig', 'Depth', 'Higher']
description:
file_path: 4_best_first_crawling_bestfirstcrawlingstrategy_examples.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_keyword_scorer():
    scorer = KeywordRelevanceScorer(keywords=["feature", "advanced", "core"])
    strategy = BestFirstCrawlingStrategy(
        max_depth=1,
        url_scorer=scorer,
        max_pages=4 # Limit for example clarity
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS,
        stream=True # Stream to see order
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        print(f"--- BestFirstCrawlingStrategy with KeywordRelevanceScorer ---")
        results_list = []
        async for result in await crawler.arun(url=start_url, config=run_config):
            results_list.append(result)
            if result.success:
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f} (Depth: {result.metadata.get('depth')})")

        # Check if pages with keywords like "feature" or "core" were prioritized (appeared earlier/higher score)
        # This is a soft check as actual order depends on many factors in a real crawl
        # and the mock site's link structure.
        print("\nNote: Higher scores should ideally correspond to URLs with keywords 'feature', 'advanced', 'core'.")
        feature_page_crawled = any("page2.html" in r.url for r in results_list) # page2 has "feature"
        assert feature_page_crawled, "Page with 'feature' keyword was expected."


if __name__ == "__main__":
    asyncio.run(best_first_keyword_scorer())
```