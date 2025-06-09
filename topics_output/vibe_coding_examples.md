## Vibe Coding - Examples
Source: crawl4ai_vibe_examples_content.llm.md

# Examples Outline for crawl4ai - vibe Component

**Target Document Type:** Examples Collection
**Target Output Filename Suggestion:** `llm_examples_vibe.md`
**Library Version Context:** 0.6.3
**Outline Generation Date:** 2024-05-24
---

This document provides a collection of runnable code examples for the `vibe` component of the `crawl4ai` library, focusing on its deep crawling capabilities, filtering, and scoring mechanisms.

**Note on URLs:** Most examples use placeholder URLs like `https://docs.crawl4ai.com/vibe-examples/pageN.html`. These are for demonstration and will be mocked to return predefined content. Replace them with actual URLs for real-world use.

**Common Imports (assumed for many examples below, but will be included in each runnable block):**
```python
import asyncio
import time
import re
from pathlib import Path
import os # For local file examples
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    CrawlResult,
    BrowserConfig,
    CacheMode,
    # Deep Crawling Strategies
    BFSDeePCrawlStrategy,
    DFSDeePCrawlStrategy,
    BestFirstCrawlingStrategy,
    DeepCrawlStrategy, # For custom strategy
    # Filters
    FilterChain,
    URLPatternFilter,
    DomainFilter,
    ContentTypeFilter,
    URLFilter,
    ContentRelevanceFilter, # Conceptual
    SEOFilter,            # Conceptual
    FilterStats,
    # Scorers
    URLScorer, # For custom scorer
    KeywordRelevanceScorer,
    PathDepthScorer,
    ContentTypeScorer,
    DomainAuthorityScorer, # Conceptual
    FreshnessScorer,       # Conceptual
    CompositeScorer,
    # Other
    LLMExtractionStrategy, # For combination example
    AsyncLogger          # For custom logger example
)
from unittest.mock import patch, AsyncMock # For mocking network calls

# --- Mock Website Data ---
# This data will be used by the MockAsyncWebCrawler to simulate a website
MOCK_SITE_DATA = {
    "https://docs.crawl4ai.com/vibe-examples/index.html": {
        "html_content": """
            <html><head><title>Index</title></head><body>
                <h1>Main Page</h1>
                <a href="page1.html">Page 1</a>
                <a href="page2.html">Page 2 (Feature)</a>
                <a href="https://external-site.com/pageA.html">External Site</a>
                <a href="/vibe-examples/archive/old_page.html">Archive</a>
                <a href="/vibe-examples/blog/post1.html">Blog Post 1</a>
                <a href="/vibe-examples/login.html">Login</a>
                <a href="javascript:void(0);" onclick="document.body.innerHTML += '<a href=js_page.html>JS Link</a>'">Load JS Link</a>
            </body></html>
        """,
        "response_headers": {"Content-Type": "text/html"}
    },
    "https://docs.crawl4ai.com/vibe-examples/page1.html": {
        "html_content": """
            <html><head><title>Page 1</title></head><body>
                <h2>Page One</h2>
                <p>This is page 1. It has some core content about crawl strategies.</p>
                <a href="page1_sub1.html">Sub Page 1.1</a>
                <a href="page1_sub2.pdf">Sub Page 1.2 (PDF)</a>
                <a href="index.html">Back to Index</a>
            </body></html>
        """,
        "response_headers": {"Content-Type": "text/html"}
    },
    "https://docs.crawl4ai.com/vibe-examples/page1_sub1.html": {
        "html_content": "<html><head><title>Sub Page 1.1</title></head><body><p>Sub page 1.1 content. More on core concepts.</p></body></html>",
        "response_headers": {"Content-Type": "text/html"}
    },
    "https://docs.crawl4ai.com/vibe-examples/page1_sub2.pdf": {
        "html_content": "%PDF-1.4 ... (Mock PDF Content: Crawl examples)", # Mock PDF content
        "response_headers": {"Content-Type": "application/pdf"}
    },
    "https://docs.crawl4ai.com/vibe-examples/page2.html": {
        "html_content": """
            <html><head><title>Page 2 - Feature Rich</title></head><body>
                <h2>Page Two with Feature</h2>
                <p>This page discusses a key feature and advanced configuration for async tasks.</p>
                <a href="page2_sub1.html">Sub Page 2.1</a>
            </body></html>
        """,
        "response_headers": {"Content-Type": "text/html"}
    },
    "https://docs.crawl4ai.com/vibe-examples/page2_sub1.html": {
        "html_content": "<html><head><title>Sub Page 2.1</title></head><body><p>More about the feature and JavaScript interaction.</p></body></html>",
        "response_headers": {"Content-Type": "text/html"}
    },
    "https://docs.crawl4ai.com/vibe-examples/archive/old_page.html": {
        "html_content": "<html><head><title>Old Page</title></head><body><p>Archived content, less relevant.</p></body></html>",
        "response_headers": {"Content-Type": "text/html"}
    },
    "https://docs.crawl4ai.com/vibe-examples/blog/post1.html": {
        "html_content": "<html><head><title>Blog Post 1</title></head><body><p>This is a blog post about core ideas and examples.</p></body></html>",
        "response_headers": {"Content-Type": "text/html"}
    },
     "https://docs.crawl4ai.com/vibe-examples/login.html": {
        "html_content": "<html><head><title>Login</title></head><body><form>...</form></body></html>",
        "response_headers": {"Content-Type": "text/html"}
    },
    "https://docs.crawl4ai.com/vibe-examples/js_page.html": {
        "html_content": "<html><head><title>JS Page</title></head><body><p>Content loaded by JavaScript.</p></body></html>",
        "response_headers": {"Content-Type": "text/html"}
    },
    "https://external-site.com/pageA.html": {
        "html_content": "<html><head><title>External Page A</title></head><body><p>Content from external site about other topics.</p></body></html>",
        "response_headers": {"Content-Type": "text/html"}
    },
    # For local file examples
    "file:" + str(Path(os.getcwd()) / "test_local_index.html"): {
         "html_content": """
            <html><head><title>Local Index</title></head><body>
                <h1>Local Main Page</h1>
                <a href="test_local_page1.html">Local Page 1</a>
                <a href="https://docs.crawl4ai.com/vibe-examples/index.html">Web Index</a>
            </body></html>
        """,
        "response_headers": {"Content-Type": "text/html"}
    },
    "file:" + str(Path(os.getcwd()) / "test_local_page1.html"): {
        "html_content": "<html><head><title>Local Page 1</title></head><body><p>Local page 1 content.</p></body></html>",
        "response_headers": {"Content-Type": "text/html"}
    }
}

# Create a dummy local file for testing
Path("test_local_index.html").write_text(MOCK_SITE_DATA["file:" + str(Path(os.getcwd()) / "test_local_index.html")]["html_content"])
Path("test_local_page1.html").write_text(MOCK_SITE_DATA["file:" + str(Path(os.getcwd()) / "test_local_page1.html")]["html_content"])


# --- Mock AsyncWebCrawler ---
# This mock crawler will simulate fetching pages from MOCK_SITE_DATA
class MockAsyncWebCrawler(AsyncWebCrawler):
    async def _fetch_page(self, url: str, config: CrawlerRunConfig):
        # Simulate network delay
        await asyncio.sleep(0.01)

        # Normalize URL for lookup (e.g. relative to absolute)
        if not url.startswith("file:") and not url.startswith("http"):
            # This is a simplified relative URL resolver for the mock
            base_parts = self.current_url.split('/')[:-1] if hasattr(self, 'current_url') and self.current_url else []
            normalized_url = "/".join(base_parts + [url])
            if "docs.crawl4ai.com" not in normalized_url and not normalized_url.startswith("file:"): # ensure base domain
                 normalized_url = "https://docs.crawl4ai.com/vibe-examples/" + url.lstrip("/")
        else:
            normalized_url = url

        if normalized_url in MOCK_SITE_DATA:
            page_data = MOCK_SITE_DATA[normalized_url]
            self.current_url = normalized_url # Store for relative path resolution

            # Basic link extraction for deep crawling
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_data["html_content"], 'html.parser')
            links = []
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                # Simple relative to absolute conversion for mock
                if not href.startswith("http") and not href.startswith("file:") and not href.startswith("javascript:"):
                    abs_href = "/".join(normalized_url.split('/')[:-1]) + "/" + href.lstrip("./")
                     # Further simplify to ensure it hits mock data, very basic
                    if "docs.crawl4ai.com" in abs_href: # if it's a vibe-example page
                        abs_href = "https://docs.crawl4ai.com/vibe-examples/" + Path(href).name
                    elif "external-site.com" in abs_href:
                        abs_href = "https://external-site.com/" + Path(href).name

                elif href.startswith("file:"): # Keep file URLs as is
                    abs_href = href
                elif href.startswith("javascript:"):
                    abs_href = None # Skip JS links for this mock
                else:
                    abs_href = href

                if abs_href:
                    links.append({"href": abs_href, "text": a_tag.get_text(strip=True)})

            return CrawlResult(
                url=normalized_url,
                html_content=page_data["html_content"],
                success=True,
                status_code=200,
                response_headers=page_data.get("response_headers", {"Content-Type": "text/html"}),
                links={"internal": [l for l in links if "docs.crawl4ai.com/vibe-examples" in l["href"] or l["href"].startswith("file:")],
                       "external": [l for l in links if "external-site.com" in l["href"]]}
            )
        else:
            # print(f"Mock Warning: URL not found in MOCK_SITE_DATA: {normalized_url} (Original: {url})")
            return CrawlResult(
                url=url, html_content="", success=False, status_code=404, error_message="Mock URL not found"
            )

    async def arun(self, url: str, config: CrawlerRunConfig = None, **kwargs):
        # This is the method called by DeepCrawlStrategy instances
        # For deep crawls, the strategy itself calls this multiple times.
        # For a single arun call with a deep_crawl_strategy, the decorator handles it.

        if config and config.deep_crawl_strategy:
             # The decorator usually handles this part. For direct strategy.arun() tests:
            return await config.deep_crawl_strategy.arun(
                crawler=self, # Pass the mock crawler instance
                start_url=url,
                config=config
            )

        # Fallback to single page fetch if no deep crawl strategy
        self.current_url = url # Set for relative path resolution in _fetch_page
        return await self._fetch_page(url, config)

    async def arun_many(self, urls: list[str], config: CrawlerRunConfig = None, **kwargs):
        results = []
        for url_item in urls:
            # In BestFirst, arun_many is called with tuples of (score, depth, url, parent_url)
            # For simplicity in mock, we assume url_item is just the URL string here or a tuple where url is at index 2
            current_url_to_crawl = url_item
            if isinstance(url_item, tuple) and len(url_item) >=3 :
                 current_url_to_crawl = url_item[2]

            self.current_url = current_url_to_crawl # Set for relative path resolution
            result = await self._fetch_page(current_url_to_crawl, config)
            results.append(result)
        if config and config.stream:
            async def result_generator():
                for res in results:
                    yield res
            return result_generator()
        return results

    async def __aenter__(self):
        # print("MockAsyncWebCrawler entered")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # print("MockAsyncWebCrawler exited")
        pass

    async def start(self): # Add start method
        # print("MockAsyncWebCrawler started")
        self.ready = True
        return self

    async def close(self): # Add close method
        # print("MockAsyncWebCrawler closed")
        self.ready = False

# --- End Mock ---
```

---
