---
id: memory_full_document_sec4.14
cluster: memory
topic: full_document
title: Example: `BestFirstCrawlingStrategy` - Explaining the effect of `BATCH_SIZE` on `arun_many`.
version_context: None
outline_date: None
section_hierarchy: ['Best-First Crawling (`BestFirstCrawlingStrategy`) Examples', 'Example: Basic `BestFirstCrawlingStrategy` with default parameters.', 'Example: `BestFirstCrawlingStrategy` - Setting `max_depth` to limit crawl depth.', 'Example: `BestFirstCrawlingStrategy` - Setting `max_pages` to limit total pages crawled.', 'Example: `BestFirstCrawlingStrategy` - Using `include_external=True`.', 'Example: `BestFirstCrawlingStrategy` - Using `KeywordRelevanceScorer` to prioritize URLs containing specific keywords.', 'Example: `BestFirstCrawlingStrategy` - Using `PathDepthScorer` to influence priority based on URL path depth.', 'Example: `BestFirstCrawlingStrategy` - Using `ContentTypeScorer` to prioritize HTML pages over PDFs.', 'Example: `BestFirstCrawlingStrategy` - Using `CompositeScorer` to combine `KeywordRelevanceScorer` and `PathDepthScorer`.', 'Example: `BestFirstCrawlingStrategy` - Integrating a `FilterChain` with `ContentTypeFilter` to only process HTML.', 'Example: `BestFirstCrawlingStrategy` - Streaming results and observing the order based on scores.', 'Example: `BestFirstCrawlingStrategy` - Batch results and analyzing scores post-crawl.', 'Example: `BestFirstCrawlingStrategy` - Accessing and interpreting `score`, `depth`, and `parent_url` from `CrawlResult.metadata`.', 'Example: `BestFirstCrawlingStrategy` - Demonstrating `shutdown()` to stop an ongoing prioritized crawl.', 'Example: `BestFirstCrawlingStrategy` - Explaining the effect of `BATCH_SIZE` on `arun_many`.']
keywords: []
description:
file_path: 4_best_first_crawling_bestfirstcrawlingstrategy_examples.md::full_document
---

---