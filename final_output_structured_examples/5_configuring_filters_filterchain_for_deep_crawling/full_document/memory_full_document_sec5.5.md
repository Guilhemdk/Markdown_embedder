---
id: memory_full_document_sec5.5
cluster: memory
topic: full_document
title: `ContentRelevanceFilter`
version_context: None
outline_date: None
section_hierarchy: ['Configuring Filters (`FilterChain`) for Deep Crawling', '`URLPatternFilter`', 'Example: Using `URLPatternFilter` to allow URLs matching specific patterns (e.g., `/blog/*`).', 'Example: Using `URLPatternFilter` to block URLs matching specific patterns (e.g., `*/login/*`, `*/archive/*`).', 'Example: `URLPatternFilter` with `case_sensitive=True` vs. `case_sensitive=False`.', '`DomainFilter`', 'Example: Using `DomainFilter` with `allowed_domains` to restrict crawling to a list of specific domains.', 'Example: Using `DomainFilter` with `blocked_domains` to avoid crawling certain domains.', 'Example: `DomainFilter` configured to allow subdomains (`allow_subdomains=True`).', 'Example: `DomainFilter` configured to disallow subdomains (`allow_subdomains=False`).', '`ContentTypeFilter`', 'Example: Using `ContentTypeFilter` to allow only `text/html` pages.', 'Example: Using `ContentTypeFilter` with multiple `allowed_types` (e.g., `text/html`, `application/json`).', 'Example: Using `ContentTypeFilter` with `blocked_types` (e.g., blocking `application/pdf`).', '`URLFilter` (Simple exact match)', 'Example: `URLFilter` to allow a specific list of exact URLs.', 'Example: `URLFilter` to block a specific list of exact URLs.', '`ContentRelevanceFilter`', 'Example: Setting up `ContentRelevanceFilter` with target keywords (conceptual, focusing on setup).']
keywords: ['Adjust', 'Articles', 'AsyncWebCrawler', 'Attempting', 'CacheMode', 'Conceptual', 'Configure']
description:
file_path: 5_configuring_filters_filterchain_for_deep_crawling.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, ContentRelevanceFilter, LLMConfig

# This is a conceptual example showing setup.
# A real run would require an LLM provider to be configured.
async def setup_content_relevance_filter():
    print("--- Setting up ContentRelevanceFilter (Conceptual) ---")

    # Define keywords and context for relevance
    keywords = ["artificial intelligence", "web crawling", "data extraction"]
    context_query = "Articles related to AI-powered web scraping tools and techniques."

    # Configure LLM (replace with your actual provider and API key)
    llm_config = LLMConfig(provider="openai/gpt-3.5-turbo", api_token="YOUR_OPENAI_API_KEY")

    relevance_filter = ContentRelevanceFilter(
        llm_config=llm_config,
        keywords=keywords,
        context_query=context_query,
        threshold=0.6 # Adjust threshold as needed
    )
    filter_chain = FilterChain(filters=[relevance_filter])

    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    print("ContentRelevanceFilter configured. To run this example:")
    print("1. Replace 'YOUR_OPENAI_API_KEY' with your actual OpenAI API key.")
    print("2. (Optional) Install OpenAI client: pip install openai")
    print("3. Uncomment the crawler execution part below.")

    # # Example of how it would be used (requires actual LLM call)
    # async with AsyncWebCrawler() as crawler:
    #     # Mock or use a real URL that would trigger the LLM
    #     start_url = "https://docs.crawl4ai.com/vibe-examples/page1.html"
    #     print(f"Attempting to crawl {start_url} with ContentRelevanceFilter...")
    #     # results = await crawler.arun(url=start_url, config=run_config)
    #     # print(f"Crawled {len(results)} pages after relevance filtering.")
    #     # for r in results:
    #     #     print(f"  URL: {r.url}, Relevance Score: {r.metadata.get('relevance_score')}")
    print("Conceptual setup complete.")

if __name__ == "__main__":
    asyncio.run(setup_content_relevance_filter())
```