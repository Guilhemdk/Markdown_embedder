## 6. Configuring Scorers (`URLScorer`) for `BestFirstCrawlingStrategy`

Scorers are used by `BestFirstCrawlingStrategy` to prioritize URLs in its crawl queue.

### 6.1. `KeywordRelevanceScorer`

#### 6.1.1. Example: `KeywordRelevanceScorer` with a list of keywords and default weight.

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

#### 6.1.2. Example: `KeywordRelevanceScorer` adjusting the `weight` parameter to influence its importance.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer, PathDepthScorer, CompositeScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def scorer_keyword_custom_weight():
    # High weight for keywords, low for path depth
    keyword_scorer = KeywordRelevanceScorer(keywords=["feature"], weight=2.0)
    path_scorer = PathDepthScorer(weight=0.1, higher_score_is_better=False) # Less penalty

    composite_scorer = CompositeScorer(scorers=[keyword_scorer, path_scorer])
    strategy = BestFirstCrawlingStrategy(max_depth=1, url_scorer=composite_scorer, max_pages=4)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- KeywordRelevanceScorer with adjusted weight (weight=2.0) in CompositeScorer ---")
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun("https://docs.crawl4ai.com/vibe-examples/index.html", config=run_config):
            if result.success:
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}")
    print("Keyword relevance should have a stronger impact on the final score.")

if __name__ == "__main__":
    asyncio.run(scorer_keyword_custom_weight())
```

#### 6.1.3. Example: `KeywordRelevanceScorer` with `case_sensitive=True`.

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

### 6.2. `PathDepthScorer`

#### 6.2.1. Example: `PathDepthScorer` with default behavior (penalizing deeper paths).
By default, `PathDepthScorer` gives higher scores to shallower paths (depth 0 > depth 1 > depth 2).

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, PathDepthScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def scorer_path_depth_default():
    scorer = PathDepthScorer() # Default: higher_score_is_better=True, depth_penalty_factor=0.1
    strategy = BestFirstCrawlingStrategy(max_depth=2, url_scorer=scorer, max_pages=6)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- PathDepthScorer with default behavior (shallower is better) ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"

        depth_scores = {}
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                depth = result.metadata.get('depth')
                score = result.metadata.get('score', 0.0)
                print(f"  URL: {result.url}, Depth: {depth}, Score: {score:.2f}")
                if depth not in depth_scores:
                    depth_scores[depth] = []
                depth_scores[depth].append(score)

        if 1 in depth_scores and 2 in depth_scores and depth_scores[1] and depth_scores[2]:
           avg_score_depth1 = sum(depth_scores[1]) / len(depth_scores[1])
           avg_score_depth2 = sum(depth_scores[2]) / len(depth_scores[2])
           print(f"Avg score depth 1: {avg_score_depth1:.2f}, Avg score depth 2: {avg_score_depth2:.2f}")
           assert avg_score_depth1 > avg_score_depth2, "Shallower paths should have higher scores."

if __name__ == "__main__":
    asyncio.run(scorer_path_depth_default())
```

#### 6.2.2. Example: `PathDepthScorer` with custom `depth_penalty_factor`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, PathDepthScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def scorer_path_depth_custom_penalty():
    # Higher penalty factor means deeper paths are penalized more severely
    scorer = PathDepthScorer(depth_penalty_factor=0.5, higher_score_is_better=True)
    strategy = BestFirstCrawlingStrategy(max_depth=2, url_scorer=scorer, max_pages=6)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- PathDepthScorer with custom depth_penalty_factor=0.5 ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"

        depth_scores = {}
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                depth = result.metadata.get('depth')
                score = result.metadata.get('score', 0.0)
                print(f"  URL: {result.url}, Depth: {depth}, Score: {score:.2f}")
                if depth not in depth_scores:
                    depth_scores[depth] = []
                depth_scores[depth].append(score)

        if 1 in depth_scores and 2 in depth_scores and depth_scores[1] and depth_scores[2]:
           avg_score_depth1 = sum(depth_scores[1]) / len(depth_scores[1])
           avg_score_depth2 = sum(depth_scores[2]) / len(depth_scores[2])
           print(f"Avg score depth 1: {avg_score_depth1:.2f}, Avg score depth 2: {avg_score_depth2:.2f}")
           # Expect a larger difference due to higher penalty
           assert (avg_score_depth1 - avg_score_depth2) > 0.05, "Higher penalty factor should result in a larger score drop for deeper paths."


if __name__ == "__main__":
    asyncio.run(scorer_path_depth_custom_penalty())
```

#### 6.2.3. Example: `PathDepthScorer` with `higher_score_is_better=False` (to favor deeper paths).

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, PathDepthScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def scorer_path_depth_favor_deep():
    # Now, deeper paths will get higher (less negative or more positive) scores
    scorer = PathDepthScorer(higher_score_is_better=False)
    strategy = BestFirstCrawlingStrategy(max_depth=2, url_scorer=scorer, max_pages=6)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- PathDepthScorer with higher_score_is_better=False (favoring deeper paths) ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"

        depth_scores = {}
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                depth = result.metadata.get('depth')
                score = result.metadata.get('score', 0.0)
                print(f"  URL: {result.url}, Depth: {depth}, Score: {score:.2f}")
                if depth not in depth_scores:
                    depth_scores[depth] = []
                depth_scores[depth].append(score)

        if 1 in depth_scores and 2 in depth_scores and depth_scores[1] and depth_scores[2]:
           avg_score_depth1 = sum(depth_scores[1]) / len(depth_scores[1])
           avg_score_depth2 = sum(depth_scores[2]) / len(depth_scores[2])
           print(f"Avg score depth 1: {avg_score_depth1:.2f}, Avg score depth 2: {avg_score_depth2:.2f}")
           assert avg_score_depth2 > avg_score_depth1, "Deeper paths should have higher scores with higher_score_is_better=False."

if __name__ == "__main__":
    asyncio.run(scorer_path_depth_favor_deep())
```

### 6.3. `ContentTypeScorer`

#### 6.3.1. Example: `ContentTypeScorer` prioritizing `text/html` and penalizing `application/pdf`.

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

#### 6.3.2. Example: `ContentTypeScorer` with custom `content_type_weights`.

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

### 6.4. `DomainAuthorityScorer`

#### 6.4.1. Example: Setting up `DomainAuthorityScorer` (conceptual, as DA often requires an external API or dataset).
This example shows how to instantiate and potentially use it, but actual scoring depends on external data.

```python
import asyncio
from crawl4ai import DomainAuthorityScorer

async def setup_domain_authority_scorer():
    print("--- DomainAuthorityScorer (Conceptual Setup) ---")

    # Conceptual: imagine you have a way to get DA scores
    # da_scores = {"example.com": 90, "anotherexample.net": 70}
    # scorer = DomainAuthorityScorer(domain_authority_map=da_scores, weight=1.5)

    # For this example, we'll just instantiate it
    scorer = DomainAuthorityScorer(weight=1.5)
    print(f"DomainAuthorityScorer created with weight: {scorer.weight}")
    print("To use this scorer effectively, you'd need a 'domain_authority_map' or a way to fetch DA scores.")
    print("Example URL score (conceptual): ", scorer.score("https://highly-authoritative-site.com/page"))

if __name__ == "__main__":
    asyncio.run(setup_domain_authority_scorer())
```

### 6.5. `FreshnessScorer`

#### 6.5.1. Example: Setting up `FreshnessScorer` (conceptual, as freshness often requires parsing dates from content or headers).
This example focuses on instantiation. Actual scoring would need date extraction.

```python
import asyncio
from crawl4ai import FreshnessScorer
from datetime import datetime, timedelta

async def setup_freshness_scorer():
    print("--- FreshnessScorer (Conceptual Setup) ---")

    # Conceptual: the scorer would need a way to get the publication date of a URL
    # For this example, we'll just instantiate it
    scorer = FreshnessScorer(
        max_age_days=30,      # Pages older than 30 days get lower scores
        date_penalty_factor=0.1 # How much to penalize per day older
    )
    print(f"FreshnessScorer created with max_age_days: {scorer.max_age_days}")
    print("To use this, the crawling process or a pre-processor would need to extract and provide publication dates for URLs.")

    # Conceptual scoring:
    # recent_date = datetime.now() - timedelta(days=5)
    # old_date = datetime.now() - timedelta(days=60)
    # print(f"Score for recent page (mock date): {scorer.score('https://example.com/recent', publication_date=recent_date)}")
    # print(f"Score for old page (mock date): {scorer.score('https://example.com/old', publication_date=old_date)}")


if __name__ == "__main__":
    asyncio.run(setup_freshness_scorer())
```

### 6.6. `CompositeScorer`

#### 6.6.1. Example: Combining `KeywordRelevanceScorer` and `PathDepthScorer` using `CompositeScorer` with equal weights.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy
from crawl4ai import KeywordRelevanceScorer, PathDepthScorer, CompositeScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def composite_scorer_equal_weights():
    keyword_scorer = KeywordRelevanceScorer(keywords=["feature"]) # Default weight 1.0
    path_scorer = PathDepthScorer(higher_score_is_better=False)  # Default weight 1.0, penalizes depth

    # Equal weighting by default if weights list not provided or all weights are same
    composite_scorer = CompositeScorer(scorers=[keyword_scorer, path_scorer])

    strategy = BestFirstCrawlingStrategy(max_depth=1, url_scorer=composite_scorer, max_pages=5)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- CompositeScorer with equal weights for Keyword and PathDepth ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}, Depth: {result.metadata.get('depth')}")
    print("Scores are an equal combination of keyword relevance and path depth penalty.")

if __name__ == "__main__":
    asyncio.run(composite_scorer_equal_weights())
```

#### 6.6.2. Example: `CompositeScorer` assigning different `weights` to prioritize one scorer over another.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy
from crawl4ai import KeywordRelevanceScorer, PathDepthScorer, CompositeScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def composite_scorer_different_weights():
    # Keyword relevance is more important
    keyword_scorer = KeywordRelevanceScorer(keywords=["feature"])
    path_scorer = PathDepthScorer(higher_score_is_better=False)

    composite_scorer = CompositeScorer(
        scorers=[keyword_scorer, path_scorer],
        weights=[0.8, 0.2] # Keyword scorer has 80% influence, PathDepth 20%
    )

    strategy = BestFirstCrawlingStrategy(max_depth=1, url_scorer=composite_scorer, max_pages=5)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- CompositeScorer with different weights (Keyword: 0.8, PathDepth: 0.2) ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}, Depth: {result.metadata.get('depth')}")
    print("Keyword relevance should more heavily influence scores.")

if __name__ == "__main__":
    asyncio.run(composite_scorer_different_weights())
```

#### 6.6.3. Example: Nesting `CompositeScorer` for more complex scoring logic.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy
from crawl4ai import KeywordRelevanceScorer, PathDepthScorer, ContentTypeScorer, CompositeScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def composite_scorer_nesting():
    keyword_scorer = KeywordRelevanceScorer(keywords=["feature"])
    path_scorer = PathDepthScorer(higher_score_is_better=False)
    content_type_scorer = ContentTypeScorer(content_type_weights={"text/html": 1.0, "application/pdf": -1.0})

    # First level composite: keyword and path
    relevance_and_structure_scorer = CompositeScorer(
        scorers=[keyword_scorer, path_scorer],
        weights=[0.7, 0.3]
    )

    # Second level composite: combine above with content type
    final_scorer = CompositeScorer(
        scorers=[relevance_and_structure_scorer, content_type_scorer],
        weights=[0.8, 0.2] # Relevance/structure is 80%, content type 20%
    )

    strategy = BestFirstCrawlingStrategy(max_depth=1, url_scorer=final_scorer, max_pages=5)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- Nested CompositeScorer ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                 print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}, Depth: {result.metadata.get('depth')}, Type: {result.response_headers.get('Content-Type')}")
    print("Scores reflect a nested combination of keyword, path, and content type.")

if __name__ == "__main__":
    asyncio.run(composite_scorer_nesting())
```

---
