---
id: memory_full_document_sec5.7.2
cluster: memory
topic: full_document
title: Example: Using `FilterChain` with `FilterStats` to retrieve and display statistics about filtered URLs.
version_context: None
outline_date: None
section_hierarchy: ['Configuring Filters (`FilterChain`) for Deep Crawling', '`URLPatternFilter`', 'Example: Using `URLPatternFilter` to allow URLs matching specific patterns (e.g., `/blog/*`).', 'Example: Using `URLPatternFilter` to block URLs matching specific patterns (e.g., `*/login/*`, `*/archive/*`).', 'Example: `URLPatternFilter` with `case_sensitive=True` vs. `case_sensitive=False`.', '`DomainFilter`', 'Example: Using `DomainFilter` with `allowed_domains` to restrict crawling to a list of specific domains.', 'Example: Using `DomainFilter` with `blocked_domains` to avoid crawling certain domains.', 'Example: `DomainFilter` configured to allow subdomains (`allow_subdomains=True`).', 'Example: `DomainFilter` configured to disallow subdomains (`allow_subdomains=False`).', '`ContentTypeFilter`', 'Example: Using `ContentTypeFilter` to allow only `text/html` pages.', 'Example: Using `ContentTypeFilter` with multiple `allowed_types` (e.g., `text/html`, `application/json`).', 'Example: Using `ContentTypeFilter` with `blocked_types` (e.g., blocking `application/pdf`).', '`URLFilter` (Simple exact match)', 'Example: `URLFilter` to allow a specific list of exact URLs.', 'Example: `URLFilter` to block a specific list of exact URLs.', '`ContentRelevanceFilter`', 'Example: Setting up `ContentRelevanceFilter` with target keywords (conceptual, focusing on setup).', 'Example: `ContentRelevanceFilter` with a custom `threshold`.', '`SEOFilter`', 'Example: Basic `SEOFilter` with default SEO checks (conceptual, focusing on setup).', 'Example: `SEOFilter` configuring specific checks like `min_title_length`, `max_meta_description_length`, or `keyword_in_title_check` (conceptual).', '`FilterChain`', 'Example: Combining `URLPatternFilter` (allow `/products/*`) and `DomainFilter` (only `example.com`) in a `FilterChain`.', 'Example: Using `FilterChain` with `FilterStats` to retrieve and display statistics about filtered URLs.']
keywords: ['Allow', 'AsyncWebCrawler', 'Based', 'CacheMode', 'Crawled', 'CrawlerRunConfig', 'Create']
description:
file_path: 5_configuring_filters_filterchain_for_deep_crawling.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, URLPatternFilter, FilterStats
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_chain_with_stats():
    url_filter = URLPatternFilter(patterns=["*/blog/*"], block_list=False) # Allow only blog
    filter_stats = FilterStats() # Create a stats object
    filter_chain = FilterChain(filters=[url_filter], stats=filter_stats) # Pass stats to chain

    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- FilterChain with FilterStats ---")
        print(f"Crawled {len(results)} pages.")

        print("\nFilter Statistics:")
        print(f"  Total URLs considered by filters: {filter_stats.total_considered}")
        print(f"  Total URLs allowed: {filter_stats.total_allowed}")
        print(f"  Total URLs blocked: {filter_stats.total_blocked}")

        # Based on MOCK_SITE_DATA, index links to one /blog/ page and several non-blog pages.
        # Start URL itself is not subject to filter_chain in this strategy logic.
        # Links from start URL: page1, page2, external, archive, blog, login
        # Only /blog/post1.html should pass. 5 should be blocked.
        assert filter_stats.total_considered >= 5 # Links from index.html
        assert filter_stats.total_allowed >= 1    # /blog/post1.html
        assert filter_stats.total_blocked >= 4    # page1, page2, external (if not implicitly blocked), archive, login

if __name__ == "__main__":
    asyncio.run(filter_chain_with_stats())
```