---
id: memory_full_document_sec5.6
cluster: memory
topic: full_document
title: `SEOFilter`
version_context: None
outline_date: None
section_hierarchy: ['Configuring Filters (`FilterChain`) for Deep Crawling', '`URLPatternFilter`', 'Example: Using `URLPatternFilter` to allow URLs matching specific patterns (e.g., `/blog/*`).', 'Example: Using `URLPatternFilter` to block URLs matching specific patterns (e.g., `*/login/*`, `*/archive/*`).', 'Example: `URLPatternFilter` with `case_sensitive=True` vs. `case_sensitive=False`.', '`DomainFilter`', 'Example: Using `DomainFilter` with `allowed_domains` to restrict crawling to a list of specific domains.', 'Example: Using `DomainFilter` with `blocked_domains` to avoid crawling certain domains.', 'Example: `DomainFilter` configured to allow subdomains (`allow_subdomains=True`).', 'Example: `DomainFilter` configured to disallow subdomains (`allow_subdomains=False`).', '`ContentTypeFilter`', 'Example: Using `ContentTypeFilter` to allow only `text/html` pages.', 'Example: Using `ContentTypeFilter` with multiple `allowed_types` (e.g., `text/html`, `application/json`).', 'Example: Using `ContentTypeFilter` with `blocked_types` (e.g., blocking `application/pdf`).', '`URLFilter` (Simple exact match)', 'Example: `URLFilter` to allow a specific list of exact URLs.', 'Example: `URLFilter` to block a specific list of exact URLs.', '`ContentRelevanceFilter`', 'Example: Setting up `ContentRelevanceFilter` with target keywords (conceptual, focusing on setup).', 'Example: `ContentRelevanceFilter` with a custom `threshold`.', '`SEOFilter`', 'Example: Basic `SEOFilter` with default SEO checks (conceptual, focusing on setup).']
keywords: ['Basic', 'Conceptual', 'DeepCrawlStrategy', 'Default', 'Description', 'FilterChain', 'Length']
description:
file_path: 5_configuring_filters_filterchain_for_deep_crawling.md::full_document
---

```python
import asyncio
from crawl4ai import SEOFilter

async def setup_basic_seo_filter():
    print("--- Basic SEOFilter with default checks (Conceptual Setup) ---")

    # Default checks might include missing title, short meta description, etc.
    seo_filter = SEOFilter()

    print(f"SEOFilter created with default settings:")
    print(f"  Min Title Length: {seo_filter.min_title_length}")
    print(f"  Max Title Length: {seo_filter.max_title_length}")
    print(f"  Min Meta Description Length: {seo_filter.min_meta_description_length}")
    # ... and other default parameters
    print("This filter would be added to a FilterChain and used in a DeepCrawlStrategy.")
    print("It would then check each page against these SEO criteria.")

if __name__ == "__main__":
    asyncio.run(setup_basic_seo_filter())
```