---
id: memory_full_document_sec8.5
cluster: memory
topic: full_document
title: Example: Combining deep crawling with `LLMExtractionStrategy` to extract structured data from each crawled page.
version_context: None
outline_date: None
section_hierarchy: ['Advanced Scenarios & Customization', 'Example: Implementing a custom `DeepCrawlStrategy` by subclassing `DeepCrawlStrategy`.', 'Example: Implementing a custom `URLFilter`.', 'Example: Implementing a custom `URLScorer` for `BestFirstCrawlingStrategy`.', 'Example: Deep crawling a site with very large number of pages efficiently using `max_pages` and streaming.', 'Example: Combining deep crawling with `LLMExtractionStrategy` to extract structured data from each crawled page.']
keywords: ['Apply', 'AsyncWebCrawler', 'BaseModel', 'Based', 'CacheMode', 'Content', 'Could']
description:
file_path: 8_advanced_scenarios_customization.md::full_document
---

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, LLMExtractionStrategy, LLMConfig
from pydantic import BaseModel, Field
from unittest.mock import patch

class PageSummary(BaseModel):
    title: str = Field(description="The main title of the page.")
    brief_summary: str = Field(description="A one-sentence summary of the page content.")

# Mock the LLM call within the extraction strategy for this example
async def mock_llm_extract(self, url: str, sections: list[str]):
    print(f"[Mock LLM] Extracting from {url}, first section: {sections[0][:50]}...")
    # Based on the URL from MOCK_SITE_DATA, return a plausible mock summary
    if "index.html" in url:
        return [{"title": "Index", "brief_summary": "This is the main page."}]
    elif "page1.html" in url:
        return [{"title": "Page 1", "brief_summary": "Content about crawl strategies."}]
    elif "page2.html" in url:
        return [{"title": "Page 2 - Feature Rich", "brief_summary": "Discusses a key feature."}]
    return [{"title": "Unknown Title", "brief_summary": "Could not summarize."}]

@patch('crawl4ai.extraction_strategy.LLMExtractionStrategy.run', side_effect=mock_llm_extract)
@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def deep_crawl_with_llm_extraction(mock_llm_run): # mock_llm_run is from the patch
    llm_config = LLMConfig(provider="mock/mock-model") # Mock provider

    extraction_strategy = LLMExtractionStrategy(
        llm_config=llm_config,
        schema=PageSummary.model_json_schema(), # Use Pydantic model for schema
        extraction_type="schema",
        instruction="Extract the title and a brief summary for the provided HTML content."
    )

    deep_crawl_config = BFSDeePCrawlStrategy(max_depth=1, max_pages=3)

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=deep_crawl_config,
        extraction_strategy=extraction_strategy, # Apply this to each crawled page
        cache_mode=CacheMode.BYPASS
    )

    print("--- Deep Crawl with LLM Extraction on Each Page ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        for result in results:
            if result.success:
                print(f"\nCrawled URL: {result.url}")
                if result.extracted_content:
                    print(f"  Extracted Data: {result.extracted_content}")
                else:
                    print("  No data extracted (or LLM mock returned empty).")
            else:
                print(f"\nFailed to crawl URL: {result.url} - {result.error_message}")

        assert mock_llm_run.called, "LLM Extraction strategy's run method was not called."

if __name__ == "__main__":
    asyncio.run(deep_crawl_with_llm_extraction())
```