---
id: memory_full_document_sec6.5
cluster: memory
topic: full_document
title: `FreshnessScorer`
version_context: None
outline_date: None
section_hierarchy: ['Configuring Scorers (`URLScorer`) for `BestFirstCrawlingStrategy`', '`KeywordRelevanceScorer`', 'Example: `KeywordRelevanceScorer` with a list of keywords and default weight.', 'Example: `KeywordRelevanceScorer` adjusting the `weight` parameter to influence its importance.', 'Example: `KeywordRelevanceScorer` with `case_sensitive=True`.', '`PathDepthScorer`', 'Example: `PathDepthScorer` with default behavior (penalizing deeper paths).', 'Example: `PathDepthScorer` with custom `depth_penalty_factor`.', 'Example: `PathDepthScorer` with `higher_score_is_better=False` (to favor deeper paths).', '`ContentTypeScorer`', 'Example: `ContentTypeScorer` prioritizing `text/html` and penalizing `application/pdf`.', 'Example: `ContentTypeScorer` with custom `content_type_weights`.', '`DomainAuthorityScorer`', 'Example: Setting up `DomainAuthorityScorer` (conceptual, as DA often requires an external API or dataset).', '`FreshnessScorer`', 'Example: Setting up `FreshnessScorer` (conceptual, as freshness often requires parsing dates from content or headers).']
keywords: ['Conceptual', 'For', 'FreshnessScorer', 'How', 'Pages', 'Score', 'Setup']
description:
file_path: 6_configuring_scorers_urlscorer_for_bestfirstcrawlingstrategy.md::full_document
---

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