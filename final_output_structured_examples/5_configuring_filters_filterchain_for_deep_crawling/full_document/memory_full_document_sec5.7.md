---
id: memory_full_document_sec5.7
cluster: memory
topic: full_document
title: `FilterChain`
version_context: None
outline_date: None
section_hierarchy: ['Configuring Filters (`FilterChain`) for Deep Crawling', '`URLPatternFilter`', 'Example: Using `URLPatternFilter` to allow URLs matching specific patterns (e.g., `/blog/*`).', 'Example: Using `URLPatternFilter` to block URLs matching specific patterns (e.g., `*/login/*`, `*/archive/*`).', 'Example: `URLPatternFilter` with `case_sensitive=True` vs. `case_sensitive=False`.', '`DomainFilter`', 'Example: Using `DomainFilter` with `allowed_domains` to restrict crawling to a list of specific domains.', 'Example: Using `DomainFilter` with `blocked_domains` to avoid crawling certain domains.', 'Example: `DomainFilter` configured to allow subdomains (`allow_subdomains=True`).', 'Example: `DomainFilter` configured to disallow subdomains (`allow_subdomains=False`).', '`ContentTypeFilter`', 'Example: Using `ContentTypeFilter` to allow only `text/html` pages.', 'Example: Using `ContentTypeFilter` with multiple `allowed_types` (e.g., `text/html`, `application/json`).', 'Example: Using `ContentTypeFilter` with `blocked_types` (e.g., blocking `application/pdf`).', '`URLFilter` (Simple exact match)', 'Example: `URLFilter` to allow a specific list of exact URLs.', 'Example: `URLFilter` to block a specific list of exact URLs.', '`ContentRelevanceFilter`', 'Example: Setting up `ContentRelevanceFilter` with target keywords (conceptual, focusing on setup).', 'Example: `ContentRelevanceFilter` with a custom `threshold`.', '`SEOFilter`', 'Example: Basic `SEOFilter` with default SEO checks (conceptual, focusing on setup).', 'Example: `SEOFilter` configuring specific checks like `min_title_length`, `max_meta_description_length`, or `keyword_in_title_check` (conceptual).', '`FilterChain`', 'Example: Combining `URLPatternFilter` (allow `/products/*`) and `DomainFilter` (only `example.com`) in a `FilterChain`.']
keywords: ['Add', 'All', 'AsyncWebCrawler', 'CacheMode', 'Clean', 'Content', 'Crawled']
description:
file_path: 5_configuring_filters_filterchain_for_deep_crawling.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, URLPatternFilter, DomainFilter
from unittest.mock import patch

# Add mock data for this scenario
MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/products/productA.html"] = {
    "html_content": "<html><title>Product A</title><body>Product A details</body></html>",
    "response_headers": {"Content-Type": "text/html"}
}
MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"] += '<a href="products/productA.html">Product A</a>'


@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_chain_combination():
    product_filter = URLPatternFilter(patterns=["*/products/*"])
    domain_filter = DomainFilter(allowed_domains=["docs.crawl4ai.com"])

    combined_filter_chain = FilterChain(filters=[product_filter, domain_filter])

    strategy = BFSDeePCrawlStrategy(max_depth=2, filter_chain=combined_filter_chain, include_external=True)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- FilterChain: URLPatternFilter + DomainFilter ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            print(f"  URL: {r.url}")
            if r.metadata.get('depth', 0) > 0: # Discovered URLs
                assert "docs.crawl4ai.com" in r.url, "Domain filter failed."
                assert "/products/" in r.url, "URL pattern filter failed."
        print("All discovered pages are from 'docs.crawl4ai.com' and match '*/products/*'.")

        # Clean up mock data
        del MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/products/productA.html"]
        MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"] = MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"].replace('<a href="products/productA.html">Product A</a>', '')


if __name__ == "__main__":
    asyncio.run(filter_chain_combination())
```