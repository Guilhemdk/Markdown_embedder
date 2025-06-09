---
id: memory_full_document_sec6.3
cluster: memory
topic: full_document
title: `ContentTypeScorer`
version_context: None
outline_date: None
section_hierarchy: ['Configuring Scorers (`URLScorer`) for `BestFirstCrawlingStrategy`', '`KeywordRelevanceScorer`', 'Example: `KeywordRelevanceScorer` with a list of keywords and default weight.', 'Example: `KeywordRelevanceScorer` adjusting the `weight` parameter to influence its importance.', 'Example: `KeywordRelevanceScorer` with `case_sensitive=True`.', '`PathDepthScorer`', 'Example: `PathDepthScorer` with default behavior (penalizing deeper paths).', 'Example: `PathDepthScorer` with custom `depth_penalty_factor`.', 'Example: `PathDepthScorer` with `higher_score_is_better=False` (to favor deeper paths).', '`ContentTypeScorer`', 'Example: `ContentTypeScorer` prioritizing `text/html` and penalizing `application/pdf`.']
keywords: ['AsyncWebCrawler', 'BestFirstCrawlingStrategy', 'CacheMode', 'Content', 'ContentTypeScorer', 'CrawlerRunConfig', 'Links']
description:
file_path: 6_configuring_scorers_urlscorer_for_bestfirstcrawlingstrategy.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, ContentTypeScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def scorer_content_type_html_vs_pdf():
    scorer = ContentTypeScorer(
        content_type_weights={"text/html": 1.0, "application/pdf": -1.0, "image/jpeg": 0.2}
    )
    strategy = BestFirstCrawlingStrategy(max_depth=1, url_scorer=scorer, max_pages=5)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- ContentTypeScorer (HTML: 1.0, PDF: -1.0) ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/page1.html" # Links to HTML and PDF
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                content_type = result.response_headers.get('Content-Type', 'unknown')
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}, Type: {content_type}")

if __name__ == "__main__":
    asyncio.run(scorer_content_type_html_vs_pdf())
```