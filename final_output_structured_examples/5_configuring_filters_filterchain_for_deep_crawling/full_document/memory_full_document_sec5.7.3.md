---
id: memory_full_document_sec5.7.3
cluster: memory
topic: full_document
title: Example: `FilterChain` with `allow_empty=True` vs `allow_empty=False`.
version_context: None
outline_date: None
section_hierarchy: ['Configuring Filters (`FilterChain`) for Deep Crawling', '`URLPatternFilter`', 'Example: Using `URLPatternFilter` to allow URLs matching specific patterns (e.g., `/blog/*`).', 'Example: Using `URLPatternFilter` to block URLs matching specific patterns (e.g., `*/login/*`, `*/archive/*`).', 'Example: `URLPatternFilter` with `case_sensitive=True` vs. `case_sensitive=False`.', '`DomainFilter`', 'Example: Using `DomainFilter` with `allowed_domains` to restrict crawling to a list of specific domains.', 'Example: Using `DomainFilter` with `blocked_domains` to avoid crawling certain domains.', 'Example: `DomainFilter` configured to allow subdomains (`allow_subdomains=True`).', 'Example: `DomainFilter` configured to disallow subdomains (`allow_subdomains=False`).', '`ContentTypeFilter`', 'Example: Using `ContentTypeFilter` to allow only `text/html` pages.', 'Example: Using `ContentTypeFilter` with multiple `allowed_types` (e.g., `text/html`, `application/json`).', 'Example: Using `ContentTypeFilter` with `blocked_types` (e.g., blocking `application/pdf`).', '`URLFilter` (Simple exact match)', 'Example: `URLFilter` to allow a specific list of exact URLs.', 'Example: `URLFilter` to block a specific list of exact URLs.', '`ContentRelevanceFilter`', 'Example: Setting up `ContentRelevanceFilter` with target keywords (conceptual, focusing on setup).', 'Example: `ContentRelevanceFilter` with a custom `threshold`.', '`SEOFilter`', 'Example: Basic `SEOFilter` with default SEO checks (conceptual, focusing on setup).', 'Example: `SEOFilter` configuring specific checks like `min_title_length`, `max_meta_description_length`, or `keyword_in_title_check` (conceptual).', '`FilterChain`', 'Example: Combining `URLPatternFilter` (allow `/products/*`) and `DomainFilter` (only `example.com`) in a `FilterChain`.', 'Example: Using `FilterChain` with `FilterStats` to retrieve and display statistics about filtered URLs.', 'Example: `FilterChain` with `allow_empty=True` vs `allow_empty=False`.']
keywords: []
description:
file_path: 5_configuring_filters_filterchain_for_deep_crawling.md::full_document
---

---