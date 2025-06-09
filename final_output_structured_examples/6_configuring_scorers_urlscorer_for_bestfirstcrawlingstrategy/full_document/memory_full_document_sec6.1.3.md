---
id: memory_full_document_sec6.1.3
cluster: memory
topic: full_document
title: Example: `KeywordRelevanceScorer` with `case_sensitive=True`.
version_context: None
outline_date: None
section_hierarchy: ['Configuring Scorers (`URLScorer`) for `BestFirstCrawlingStrategy`', '`KeywordRelevanceScorer`', 'Example: `KeywordRelevanceScorer` with a list of keywords and default weight.', 'Example: `KeywordRelevanceScorer` adjusting the `weight` parameter to influence its importance.', 'Example: `KeywordRelevanceScorer` with `case_sensitive=True`.']
keywords: ['AsyncWebCrawler', 'BestFirstCrawlingStrategy', 'CacheMode', 'Case', 'Clean', 'Contains', 'Content']
description:
file_path: 6_configuring_scorers_urlscorer_for_bestfirstcrawlingstrategy.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer
from unittest.mock import patch

# Modify mock data to have case-specific keywords in URLs
MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/FEATUREpage.html"] = {
    "html_content": "<html><title>FEATURE Page</title><body>Uppercase FEATURE</body></html>",
    "response_headers": {"Content-Type": "text/html"}
}
MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"] += '<a href="FEATUREpage.html">FEATURE Page</a>'


@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def scorer_keyword_case_sensitive():
    # Case-sensitive: will only score URLs with 'feature' (lowercase)
    scorer_sensitive = KeywordRelevanceScorer(keywords=["feature"], case_sensitive=True)
    strategy_sensitive = BestFirstCrawlingStrategy(max_depth=1, url_scorer=scorer_sensitive, max_pages=5)
    run_config_sensitive = CrawlerRunConfig(deep_crawl_strategy=strategy_sensitive, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- KeywordRelevanceScorer with case_sensitive=True (keyword: 'feature') ---")
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun("https://docs.crawl4ai.com/vibe-examples/index.html", config=run_config_sensitive):
            if result.success:
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}")
                if "FEATUREpage.html" in result.url: # Uppercase 'FEATURE'
                    assert result.metadata.get('score', 0.0) == 0.0, "Uppercase keyword should not be scored."
                elif "page2.html" in result.url: # Contains lowercase 'feature' in title/mock
                     assert result.metadata.get('score', 0.0) > 0.0, "Lowercase keyword should be scored."

    # Clean up mock data
    del MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/FEATUREpage.html"]
    MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"] = MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"].replace('<a href="FEATUREpage.html">FEATURE Page</a>', '')


if __name__ == "__main__":
    asyncio.run(scorer_keyword_case_sensitive())
```