---
id: memory_full_document_sec6.3.2
cluster: memory
topic: full_document
title: Example: `ContentTypeScorer` with custom `content_type_weights`.
version_context: None
outline_date: None
section_hierarchy: ['Configuring Scorers (`URLScorer`) for `BestFirstCrawlingStrategy`', '`KeywordRelevanceScorer`', 'Example: `KeywordRelevanceScorer` with a list of keywords and default weight.', 'Example: `KeywordRelevanceScorer` adjusting the `weight` parameter to influence its importance.', 'Example: `KeywordRelevanceScorer` with `case_sensitive=True`.', '`PathDepthScorer`', 'Example: `PathDepthScorer` with default behavior (penalizing deeper paths).', 'Example: `PathDepthScorer` with custom `depth_penalty_factor`.', 'Example: `PathDepthScorer` with `higher_score_is_better=False` (to favor deeper paths).', '`ContentTypeScorer`', 'Example: `ContentTypeScorer` prioritizing `text/html` and penalizing `application/pdf`.', 'Example: `ContentTypeScorer` with custom `content_type_weights`.']
keywords: ['Add', 'AsyncWebCrawler', 'BestFirstCrawlingStrategy', 'CacheMode', 'Content', 'ContentTypeScorer', 'CrawlerRunConfig']
description:
file_path: 6_configuring_scorers_urlscorer_for_bestfirstcrawlingstrategy.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, ContentTypeScorer
from unittest.mock import patch

# Add a JSON page to mock data
MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/data.json"] = {
    "html_content": '{"data": "sample"}', "response_headers": {"Content-Type": "application/json"}
}
MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"] += '<a href="data.json">JSON Data</a>'


@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def scorer_content_type_custom_weights():
    scorer = ContentTypeScorer(
        content_type_weights={
            "application/json": 2.0, # Highly prioritize JSON
            "text/html": 0.5,
            "application/pdf": -2.0 # Strongly penalize PDF
        }
    )
    strategy = BestFirstCrawlingStrategy(max_depth=1, url_scorer=scorer, max_pages=5)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- ContentTypeScorer with custom weights (JSON: 2.0, HTML: 0.5, PDF: -2.0) ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/page1.html" # Links to HTML, PDF. Index links to JSON.

        # We'll crawl index to ensure JSON is discoverable
        async for result in await crawler.arun("https://docs.crawl4ai.com/vibe-examples/index.html", config=run_config):
            if result.success:
                content_type = result.response_headers.get('Content-Type', 'unknown')
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}, Type: {content_type}")

    del MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/data.json"]
    MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"] = MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"].replace('<a href="data.json">JSON Data</a>', '')

if __name__ == "__main__":
    asyncio.run(scorer_content_type_custom_weights())
```