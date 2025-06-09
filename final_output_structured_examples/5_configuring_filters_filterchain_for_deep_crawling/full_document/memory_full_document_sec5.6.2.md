---
id: memory_full_document_sec5.6.2
cluster: memory
topic: full_document
title: Example: `SEOFilter` configuring specific checks like `min_title_length`, `max_meta_description_length`, or `keyword_in_title_check` (conceptual).
version_context: None
outline_date: None
section_hierarchy: ['Configuring Filters (`FilterChain`) for Deep Crawling', '`URLPatternFilter`', 'Example: Using `URLPatternFilter` to allow URLs matching specific patterns (e.g., `/blog/*`).', 'Example: Using `URLPatternFilter` to block URLs matching specific patterns (e.g., `*/login/*`, `*/archive/*`).', 'Example: `URLPatternFilter` with `case_sensitive=True` vs. `case_sensitive=False`.', '`DomainFilter`', 'Example: Using `DomainFilter` with `allowed_domains` to restrict crawling to a list of specific domains.', 'Example: Using `DomainFilter` with `blocked_domains` to avoid crawling certain domains.', 'Example: `DomainFilter` configured to allow subdomains (`allow_subdomains=True`).', 'Example: `DomainFilter` configured to disallow subdomains (`allow_subdomains=False`).', '`ContentTypeFilter`', 'Example: Using `ContentTypeFilter` to allow only `text/html` pages.', 'Example: Using `ContentTypeFilter` with multiple `allowed_types` (e.g., `text/html`, `application/json`).', 'Example: Using `ContentTypeFilter` with `blocked_types` (e.g., blocking `application/pdf`).', '`URLFilter` (Simple exact match)', 'Example: `URLFilter` to allow a specific list of exact URLs.', 'Example: `URLFilter` to block a specific list of exact URLs.', '`ContentRelevanceFilter`', 'Example: Setting up `ContentRelevanceFilter` with target keywords (conceptual, focusing on setup).', 'Example: `ContentRelevanceFilter` with a custom `threshold`.', '`SEOFilter`', 'Example: Basic `SEOFilter` with default SEO checks (conceptual, focusing on setup).', 'Example: `SEOFilter` configuring specific checks like `min_title_length`, `max_meta_description_length`, or `keyword_in_title_check` (conceptual).']
keywords: ['Check', 'Conceptual', 'Custom', 'Description', 'Keyword', 'Keywords', 'Length']
description:
file_path: 5_configuring_filters_filterchain_for_deep_crawling.md::full_document
---

```python
import asyncio
from crawl4ai import SEOFilter

async def setup_custom_seo_filter():
    print("--- SEOFilter with custom checks (Conceptual Setup) ---")

    custom_seo_filter = SEOFilter(
        min_title_length=20,
        max_meta_description_length=150,
        keyword_in_title_check=True,
        target_keywords_for_seo=["crawl4ai", "web scraping"] # if keyword_in_title_check is True
    )

    print(f"Custom SEOFilter created with:")
    print(f"  Min Title Length: {custom_seo_filter.min_title_length}")
    print(f"  Max Meta Description Length: {custom_seo_filter.max_meta_description_length}")
    print(f"  Keyword in Title Check: {custom_seo_filter.keyword_in_title_check}")
    print(f"  Target SEO Keywords: {custom_seo_filter.target_keywords_for_seo}")
    print("This filter would apply these specific criteria during a crawl.")

if __name__ == "__main__":
    asyncio.run(setup_custom_seo_filter())
```