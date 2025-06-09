---
id: memory_full_document_sec8.3
cluster: memory
topic: full_document
title: Example: Implementing a custom `URLScorer` for `BestFirstCrawlingStrategy`.
version_context: None
outline_date: None
section_hierarchy: ['Advanced Scenarios & Customization', 'Example: Implementing a custom `DeepCrawlStrategy` by subclassing `DeepCrawlStrategy`.', 'Example: Implementing a custom `URLFilter`.', 'Example: Implementing a custom `URLScorer` for `BestFirstCrawlingStrategy`.']
keywords: ['AsyncWebCrawler', 'BestFirstCrawlingStrategy', 'CacheMode', 'CrawlerRunConfig', 'Custom', 'CustomScorer', 'Lower']
description:
file_path: 8_advanced_scenarios_customization.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, URLScorer
from urllib.parse import urlparse
from unittest.mock import patch

class MyCustomURLScorer(URLScorer):
    def __init__(self, preferred_domain: str, weight: float = 1.0):
        super().__init__(weight)
        self.preferred_domain = preferred_domain
        print(f"MyCustomURLScorer initialized, preferring domain: {self.preferred_domain}")

    def score(self, url: str, **kwargs) -> float:
        """Scores URL based on whether it matches the preferred domain."""
        parsed_url = urlparse(url)
        score = 0.0
        if parsed_url.netloc == self.preferred_domain:
            score = 1.0 * self.weight
            print(f"[CustomScorer] URL {url} matches preferred domain. Score: {score}")
        else:
            score = 0.1 * self.weight # Lower score for other domains
            print(f"[CustomScorer] URL {url} does NOT match preferred domain. Score: {score}")
        return score

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def custom_url_scorer_example():
    custom_scorer = MyCustomURLScorer(preferred_domain="docs.crawl4ai.com", weight=2.0)

    strategy = BestFirstCrawlingStrategy(
        max_depth=1,
        url_scorer=custom_scorer,
        include_external=True, # To allow scoring external domains differently
        max_pages=5
    )
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- Using Custom URLScorer (preferring 'docs.crawl4ai.com') ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}")
    print("Pages from 'docs.crawl4ai.com' should generally have higher scores.")

if __name__ == "__main__":
    asyncio.run(custom_url_scorer_example())
```