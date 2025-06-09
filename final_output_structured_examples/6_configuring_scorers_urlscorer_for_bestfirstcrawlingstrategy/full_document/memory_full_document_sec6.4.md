---
id: memory_full_document_sec6.4
cluster: memory
topic: full_document
title: `DomainAuthorityScorer`
version_context: None
outline_date: None
section_hierarchy: ['Configuring Scorers (`URLScorer`) for `BestFirstCrawlingStrategy`', '`KeywordRelevanceScorer`', 'Example: `KeywordRelevanceScorer` with a list of keywords and default weight.', 'Example: `KeywordRelevanceScorer` adjusting the `weight` parameter to influence its importance.', 'Example: `KeywordRelevanceScorer` with `case_sensitive=True`.', '`PathDepthScorer`', 'Example: `PathDepthScorer` with default behavior (penalizing deeper paths).', 'Example: `PathDepthScorer` with custom `depth_penalty_factor`.', 'Example: `PathDepthScorer` with `higher_score_is_better=False` (to favor deeper paths).', '`ContentTypeScorer`', 'Example: `ContentTypeScorer` prioritizing `text/html` and penalizing `application/pdf`.', 'Example: `ContentTypeScorer` with custom `content_type_weights`.', '`DomainAuthorityScorer`', 'Example: Setting up `DomainAuthorityScorer` (conceptual, as DA often requires an external API or dataset).']
keywords: ['Conceptual', 'DomainAuthorityScorer', 'Example', 'For', 'Setup', 'python\nimport asyncio\nfrom crawl4ai import DomainAuthorityScorer\n\nasync def setup_domain_authority_scorer():\n    print("--- DomainAuthorityScorer (Conceptual Setup) ---")\n    \n    # Conceptual: imagine you have a way to get DA scores\n    # da_scores = {"example.com": 90, "anotherexample.net": 70}\n    # scorer = DomainAuthorityScorer(domain_authority_map=da_scores, weight=1.5)\n    \n    # For this example, we\'ll just instantiate it\n    scorer = DomainAuthorityScorer(weight=1.5)\n    print(f"DomainAuthorityScorer created with weight: {scorer.weight}")\n    print("To use this scorer effectively, you\'d need a \'domain_authority_map\' or a way to fetch DA scores.")\n    print("Example URL score (conceptual): ", scorer.score("https://highly-authoritative-site.com/page"))\n\nif __name__ == "__main__":\n    asyncio.run(setup_domain_authority_scorer())\n']
description:
file_path: 6_configuring_scorers_urlscorer_for_bestfirstcrawlingstrategy.md::full_document
---

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