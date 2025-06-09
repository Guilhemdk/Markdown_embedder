---
id: memory_full_document_sec4.7
cluster: memory
topic: full_document
title: Example: `BestFirstCrawlingStrategy` - Using `ContentTypeScorer` to prioritize HTML pages over PDFs.
version_context: None
outline_date: None
section_hierarchy: ['Best-First Crawling (`BestFirstCrawlingStrategy`) Examples', 'Example: Basic `BestFirstCrawlingStrategy` with default parameters.', 'Example: `BestFirstCrawlingStrategy` - Setting `max_depth` to limit crawl depth.', 'Example: `BestFirstCrawlingStrategy` - Setting `max_pages` to limit total pages crawled.', 'Example: `BestFirstCrawlingStrategy` - Using `include_external=True`.', 'Example: `BestFirstCrawlingStrategy` - Using `KeywordRelevanceScorer` to prioritize URLs containing specific keywords.', 'Example: `BestFirstCrawlingStrategy` - Using `PathDepthScorer` to influence priority based on URL path depth.', 'Example: `BestFirstCrawlingStrategy` - Using `ContentTypeScorer` to prioritize HTML pages over PDFs.']
keywords: ['AsyncWebCrawler', 'BestFirstCrawlingStrategy', 'CacheMode', 'Content', 'ContentTypeScorer', 'Could', 'CrawlerRunConfig']
description:
file_path: 4_best_first_crawling_bestfirstcrawlingstrategy_examples.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, ContentTypeScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_content_type_scorer():
    # Prioritize HTML, penalize PDF
    scorer = ContentTypeScorer(content_type_weights={"text/html": 1.0, "application/pdf": -0.5})
    strategy = BestFirstCrawlingStrategy(
        max_depth=1,
        url_scorer=scorer
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS,
        stream=True
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/page1.html" # This page links to HTML and PDF
        print(f"--- BestFirstCrawlingStrategy with ContentTypeScorer (HTML > PDF) ---")

        results_list = []
        async for result in await crawler.arun(url=start_url, config=run_config):
            results_list.append(result)
            if result.success:
                 print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}, Content-Type: {result.response_headers.get('Content-Type')}")

        html_page_score = next((r.metadata.get('score') for r in results_list if "page1_sub1.html" in r.url), None)
        pdf_page_score = next((r.metadata.get('score') for r in results_list if "page1_sub2.pdf" in r.url), None)

        print(f"HTML page score: {html_page_score}, PDF page score: {pdf_page_score}")
        if html_page_score is not None and pdf_page_score is not None:
            assert html_page_score > pdf_page_score, "HTML page should have a higher score than PDF."
        elif html_page_score is None or pdf_page_score is None:
            print("Warning: Could not find both HTML and PDF pages in results to compare scores.")


if __name__ == "__main__":
    asyncio.run(best_first_content_type_scorer())
```