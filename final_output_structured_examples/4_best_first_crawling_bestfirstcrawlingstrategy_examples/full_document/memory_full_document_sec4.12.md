---
id: memory_full_document_sec4.12
cluster: memory
topic: full_document
title: Example: `BestFirstCrawlingStrategy` - Accessing and interpreting `score`, `depth`, and `parent_url` from `CrawlResult.metadata`.
version_context: None
outline_date: None
section_hierarchy: ['Best-First Crawling (`BestFirstCrawlingStrategy`) Examples', 'Example: Basic `BestFirstCrawlingStrategy` with default parameters.', 'Example: `BestFirstCrawlingStrategy` - Setting `max_depth` to limit crawl depth.', 'Example: `BestFirstCrawlingStrategy` - Setting `max_pages` to limit total pages crawled.', 'Example: `BestFirstCrawlingStrategy` - Using `include_external=True`.', 'Example: `BestFirstCrawlingStrategy` - Using `KeywordRelevanceScorer` to prioritize URLs containing specific keywords.', 'Example: `BestFirstCrawlingStrategy` - Using `PathDepthScorer` to influence priority based on URL path depth.', 'Example: `BestFirstCrawlingStrategy` - Using `ContentTypeScorer` to prioritize HTML pages over PDFs.', 'Example: `BestFirstCrawlingStrategy` - Using `CompositeScorer` to combine `KeywordRelevanceScorer` and `PathDepthScorer`.', 'Example: `BestFirstCrawlingStrategy` - Integrating a `FilterChain` with `ContentTypeFilter` to only process HTML.', 'Example: `BestFirstCrawlingStrategy` - Streaming results and observing the order based on scores.', 'Example: `BestFirstCrawlingStrategy` - Batch results and analyzing scores post-crawl.', 'Example: `BestFirstCrawlingStrategy` - Accessing and interpreting `score`, `depth`, and `parent_url` from `CrawlResult.metadata`.']
keywords: ['Accessing', 'AsyncWebCrawler', 'BestFirstCrawlingStrategy', 'CacheMode', 'CrawlerRunConfig', 'Depth', 'KeywordRelevanceScorer']
description:
file_path: 4_best_first_crawling_bestfirstcrawlingstrategy_examples.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_access_metadata():
    scorer = KeywordRelevanceScorer(keywords=["feature"])
    strategy = BestFirstCrawlingStrategy(max_depth=1, url_scorer=scorer)

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BestFirstCrawlingStrategy - Accessing Metadata ---")
        for result in results:
            if result.success:
                url = result.url
                metadata = result.metadata
                depth = metadata.get('depth', 'N/A')
                parent_url = metadata.get('parent_url', 'N/A')
                score = metadata.get('score', 'N/A')

                print(f"URL: {url}")
                print(f"  Depth: {depth}")
                print(f"  Parent URL: {parent_url}")
                print(f"  Score: {score:.2f}" if isinstance(score, float) else f"  Score: {score}")
                print("-" * 10)

if __name__ == "__main__":
    asyncio.run(best_first_access_metadata())
```