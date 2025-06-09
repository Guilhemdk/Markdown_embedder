---
id: memory_full_document_sec5.5.2
cluster: memory
topic: full_document
title: Example: `ContentRelevanceFilter` with a custom `threshold`.
version_context: None
outline_date: None
section_hierarchy: ['Configuring Filters (`FilterChain`) for Deep Crawling', '`URLPatternFilter`', 'Example: Using `URLPatternFilter` to allow URLs matching specific patterns (e.g., `/blog/*`).', 'Example: Using `URLPatternFilter` to block URLs matching specific patterns (e.g., `*/login/*`, `*/archive/*`).', 'Example: `URLPatternFilter` with `case_sensitive=True` vs. `case_sensitive=False`.', '`DomainFilter`', 'Example: Using `DomainFilter` with `allowed_domains` to restrict crawling to a list of specific domains.', 'Example: Using `DomainFilter` with `blocked_domains` to avoid crawling certain domains.', 'Example: `DomainFilter` configured to allow subdomains (`allow_subdomains=True`).', 'Example: `DomainFilter` configured to disallow subdomains (`allow_subdomains=False`).', '`ContentTypeFilter`', 'Example: Using `ContentTypeFilter` to allow only `text/html` pages.', 'Example: Using `ContentTypeFilter` with multiple `allowed_types` (e.g., `text/html`, `application/json`).', 'Example: Using `ContentTypeFilter` with `blocked_types` (e.g., blocking `application/pdf`).', '`URLFilter` (Simple exact match)', 'Example: `URLFilter` to allow a specific list of exact URLs.', 'Example: `URLFilter` to block a specific list of exact URLs.', '`ContentRelevanceFilter`', 'Example: Setting up `ContentRelevanceFilter` with target keywords (conceptual, focusing on setup).', 'Example: `ContentRelevanceFilter` with a custom `threshold`.']
keywords: ['Actual', 'Conceptual', 'ContentRelevanceFilter', 'Lenient', 'Note', 'Replace', 'Setup']
description:
file_path: 5_configuring_filters_filterchain_for_deep_crawling.md::full_document
---

```python
import asyncio
from crawl4ai import ContentRelevanceFilter, LLMConfig

async def content_relevance_custom_threshold():
    print("--- ContentRelevanceFilter with custom threshold (Conceptual Setup) ---")
    llm_config = LLMConfig(provider="openai/gpt-3.5-turbo", api_token="YOUR_OPENAI_API_KEY") # Replace

    # A higher threshold means stricter relevance checking
    strict_filter = ContentRelevanceFilter(
        llm_config=llm_config,
        keywords=["specific technical term"],
        threshold=0.8
    )
    print(f"Strict filter created with threshold: {strict_filter.threshold}")

    # A lower threshold is more lenient
    lenient_filter = ContentRelevanceFilter(
        llm_config=llm_config,
        keywords=["general topic"],
        threshold=0.4
    )
    print(f"Lenient filter created with threshold: {lenient_filter.threshold}")
    print("Note: Actual filtering behavior depends on LLM responses to content.")

if __name__ == "__main__":
    asyncio.run(content_relevance_custom_threshold())
```