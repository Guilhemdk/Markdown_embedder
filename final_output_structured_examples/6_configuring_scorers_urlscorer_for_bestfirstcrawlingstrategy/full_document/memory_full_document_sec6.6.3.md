---
id: memory_full_document_sec6.6.3
cluster: memory
topic: full_document
title: Example: Nesting `CompositeScorer` for more complex scoring logic.
version_context: None
outline_date: None
section_hierarchy: ['Configuring Scorers (`URLScorer`) for `BestFirstCrawlingStrategy`', '`KeywordRelevanceScorer`', 'Example: `KeywordRelevanceScorer` with a list of keywords and default weight.', 'Example: `KeywordRelevanceScorer` adjusting the `weight` parameter to influence its importance.', 'Example: `KeywordRelevanceScorer` with `case_sensitive=True`.', '`PathDepthScorer`', 'Example: `PathDepthScorer` with default behavior (penalizing deeper paths).', 'Example: `PathDepthScorer` with custom `depth_penalty_factor`.', 'Example: `PathDepthScorer` with `higher_score_is_better=False` (to favor deeper paths).', '`ContentTypeScorer`', 'Example: `ContentTypeScorer` prioritizing `text/html` and penalizing `application/pdf`.', 'Example: `ContentTypeScorer` with custom `content_type_weights`.', '`DomainAuthorityScorer`', 'Example: Setting up `DomainAuthorityScorer` (conceptual, as DA often requires an external API or dataset).', '`FreshnessScorer`', 'Example: Setting up `FreshnessScorer` (conceptual, as freshness often requires parsing dates from content or headers).', '`CompositeScorer`', 'Example: Combining `KeywordRelevanceScorer` and `PathDepthScorer` using `CompositeScorer` with equal weights.', 'Example: `CompositeScorer` assigning different `weights` to prioritize one scorer over another.', 'Example: Nesting `CompositeScorer` for more complex scoring logic.']
keywords: []
description:
file_path: 6_configuring_scorers_urlscorer_for_bestfirstcrawlingstrategy.md::full_document
---

---