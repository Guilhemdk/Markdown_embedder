---
id: memory_full_document_sec4.11
cluster: memory
topic: full_document
title: Example: `BestFirstCrawlingStrategy` - Batch results and analyzing scores post-crawl.
version_context: None
outline_date: None
section_hierarchy: ['Best-First Crawling (`BestFirstCrawlingStrategy`) Examples', 'Example: Basic `BestFirstCrawlingStrategy` with default parameters.', 'Example: `BestFirstCrawlingStrategy` - Setting `max_depth` to limit crawl depth.', 'Example: `BestFirstCrawlingStrategy` - Setting `max_pages` to limit total pages crawled.', 'Example: `BestFirstCrawlingStrategy` - Using `include_external=True`.', 'Example: `BestFirstCrawlingStrategy` - Using `KeywordRelevanceScorer` to prioritize URLs containing specific keywords.', 'Example: `BestFirstCrawlingStrategy` - Using `PathDepthScorer` to influence priority based on URL path depth.', 'Example: `BestFirstCrawlingStrategy` - Using `ContentTypeScorer` to prioritize HTML pages over PDFs.', 'Example: `BestFirstCrawlingStrategy` - Using `CompositeScorer` to combine `KeywordRelevanceScorer` and `PathDepthScorer`.', 'Example: `BestFirstCrawlingStrategy` - Integrating a `FilterChain` with `ContentTypeFilter` to only process HTML.', 'Example: `BestFirstCrawlingStrategy` - Streaming results and observing the order based on scores.', 'Example: `BestFirstCrawlingStrategy` - Batch results and analyzing scores post-crawl.']
keywords: ['Analysis', 'AsyncWebCrawler', 'Batch', 'BestFirstCrawlingStrategy', 'CacheMode', 'CrawlerRunConfig', 'Depth']
description:
file_path: 4_best_first_crawling_bestfirstcrawlingstrategy_examples.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_batch_analysis():
    scorer = KeywordRelevanceScorer(keywords=["feature", "core"])
    strategy = BestFirstCrawlingStrategy(
        max_depth=1,
        url_scorer=scorer,
        max_pages=5
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=False, # Batch mode
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BestFirstCrawlingStrategy - Batch Results Analysis ---")
        print(f"Received {len(results)} pages.")

        # Sort by score for analysis (higher score first)
        sorted_results = sorted(results, key=lambda r: r.metadata.get('score', 0.0), reverse=True)

        for result in sorted_results:
            if result.success:
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}, Depth: {result.metadata.get('depth')}")

if __name__ == "__main__":
    asyncio.run(best_first_batch_analysis())
```