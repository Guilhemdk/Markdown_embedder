---
id: memory_full_document_sec4.9
cluster: memory
topic: full_document
title: Example: `BestFirstCrawlingStrategy` - Integrating a `FilterChain` with `ContentTypeFilter` to only process HTML.
version_context: None
outline_date: None
section_hierarchy: ['Best-First Crawling (`BestFirstCrawlingStrategy`) Examples', 'Example: Basic `BestFirstCrawlingStrategy` with default parameters.', 'Example: `BestFirstCrawlingStrategy` - Setting `max_depth` to limit crawl depth.', 'Example: `BestFirstCrawlingStrategy` - Setting `max_pages` to limit total pages crawled.', 'Example: `BestFirstCrawlingStrategy` - Using `include_external=True`.', 'Example: `BestFirstCrawlingStrategy` - Using `KeywordRelevanceScorer` to prioritize URLs containing specific keywords.', 'Example: `BestFirstCrawlingStrategy` - Using `PathDepthScorer` to influence priority based on URL path depth.', 'Example: `BestFirstCrawlingStrategy` - Using `ContentTypeScorer` to prioritize HTML pages over PDFs.', 'Example: `BestFirstCrawlingStrategy` - Using `CompositeScorer` to combine `KeywordRelevanceScorer` and `PathDepthScorer`.', 'Example: `BestFirstCrawlingStrategy` - Integrating a `FilterChain` with `ContentTypeFilter` to only process HTML.']
keywords: ['AsyncWebCrawler', 'BestFirstCrawlingStrategy', 'CacheMode', 'Content', 'ContentTypeFilter', 'Crawled', 'CrawlerRunConfig']
description:
file_path: 4_best_first_crawling_bestfirstcrawlingstrategy_examples.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, FilterChain, ContentTypeFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_with_content_type_filter():
    content_filter = ContentTypeFilter(allowed_types=["text/html"])
    filter_chain = FilterChain(filters=[content_filter])

    # Scorer is optional here, just demonstrating filter integration
    strategy = BestFirstCrawlingStrategy(
        max_depth=1,
        filter_chain=filter_chain
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/page1.html" # This page links to HTML and PDF
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- BestFirstCrawlingStrategy with ContentTypeFilter (HTML only) ---")
        print(f"Crawled {len(results)} pages.")
        all_html = True
        for result in results:
            content_type = result.response_headers.get('Content-Type', '')
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}, Content-Type: {content_type}")
            if result.metadata.get('depth',0) > 0 and "text/html" not in content_type : # Start URL is not filtered
                 all_html = False

        discovered_pages = [r for r in results if r.metadata.get('depth',0) > 0]
        if discovered_pages:
            assert all("text/html" in r.response_headers.get('Content-Type','') for r in discovered_pages), "Non-HTML page found among discovered pages."
        print("Filter for HTML content type applied successfully to discovered pages.")

if __name__ == "__main__":
    asyncio.run(best_first_with_content_type_filter())
```