## 5. Configuring Filters (`FilterChain`) for Deep Crawling

Filters allow you to control which URLs are processed during a deep crawl. They are applied *before* a URL is added to the crawl queue (except for the start URL).

### 5.1. `URLPatternFilter`

#### 5.1.1. Example: Using `URLPatternFilter` to allow URLs matching specific patterns (e.g., `/blog/*`).

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, URLPatternFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_allow_pattern():
    # Allow only URLs containing '/blog/'
    url_filter = URLPatternFilter(patterns=["*/blog/*"])
    filter_chain = FilterChain(filters=[url_filter])

    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- URLPatternFilter: Allowing '*/blog/*' ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            print(f"  URL: {r.url} (Depth: {r.metadata.get('depth')})")
            if r.metadata.get('depth', 0) > 0: # Check discovered URLs
                assert "/blog/" in r.url, f"Page {r.url} does not match pattern."
        print("All discovered pages match the allowed pattern.")

if __name__ == "__main__":
    asyncio.run(filter_allow_pattern())
```

#### 5.1.2. Example: Using `URLPatternFilter` to block URLs matching specific patterns (e.g., `*/login/*`, `*/archive/*`).

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, URLPatternFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_block_pattern():
    # Block URLs containing '/login/' or '/archive/'
    url_filter = URLPatternFilter(patterns=["*/login/*", "*/archive/*"], block_list=True)
    filter_chain = FilterChain(filters=[url_filter])

    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- URLPatternFilter: Blocking '*/login/*' and '*/archive/*' ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            print(f"  URL: {r.url} (Depth: {r.metadata.get('depth')})")
            assert "/login/" not in r.url, f"Page {r.url} should have been blocked (login)."
            assert "/archive/" not in r.url, f"Page {r.url} should have been blocked (archive)."
        print("No pages matching blocked patterns were crawled.")

if __name__ == "__main__":
    asyncio.run(filter_block_pattern())
```

#### 5.1.3. Example: `URLPatternFilter` with `case_sensitive=True` vs. `case_sensitive=False`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, URLPatternFilter
from unittest.mock import patch

# Add a case-specific URL to MOCK_SITE_DATA
MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/Page1.html"] = {
    "html_content": "<html><head><title>Page 1 Case Test</title></head><body><p>Content for case test.</p></body></html>",
    "response_headers": {"Content-Type": "text/html"}
}
MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"] += '<a href="Page1.html">Page 1 Case Test</a>'


@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_pattern_case_sensitivity():
    start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"

    # Case-sensitive: should only match 'page1.html'
    print("\n--- URLPatternFilter: Case Sensitive (Allow '*/page1.html*') ---")
    url_filter_sensitive = URLPatternFilter(patterns=["*/page1.html*"], case_sensitive=True)
    filter_chain_sensitive = FilterChain(filters=[url_filter_sensitive])
    strategy_sensitive = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain_sensitive)
    run_config_sensitive = CrawlerRunConfig(deep_crawl_strategy=strategy_sensitive, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        results_sensitive = await crawler.arun(url=start_url, config=run_config_sensitive)
        print(f"Crawled {len(results_sensitive)} pages.")
        for r in results_sensitive:
            print(f"  URL: {r.url}")
            if r.metadata.get('depth',0) > 0:
                assert "page1.html" in r.url and "Page1.html" not in r.url, "Case-sensitive filter failed."

    # Case-insensitive: should match both 'page1.html' and 'Page1.html'
    print("\n--- URLPatternFilter: Case Insensitive (Allow '*/page1.html*') ---")
    url_filter_insensitive = URLPatternFilter(patterns=["*/page1.html*"], case_sensitive=False)
    filter_chain_insensitive = FilterChain(filters=[url_filter_insensitive])
    strategy_insensitive = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain_insensitive)
    run_config_insensitive = CrawlerRunConfig(deep_crawl_strategy=strategy_insensitive, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        results_insensitive = await crawler.arun(url=start_url, config=run_config_insensitive)
        print(f"Crawled {len(results_insensitive)} pages.")
        found_page1_lower = False
        found_page1_upper = False
        for r in results_insensitive:
            print(f"  URL: {r.url}")
            if "page1.html" in r.url.lower(): # Check lower to catch both
                 if "page1.html" == Path(r.url).name: found_page1_lower = True
                 if "Page1.html" == Path(r.url).name: found_page1_upper = True

        assert found_page1_lower and found_page1_upper, "Case-insensitive filter should have matched both cases."

if __name__ == "__main__":
    asyncio.run(filter_pattern_case_sensitivity())
```

### 5.2. `DomainFilter`

#### 5.2.1. Example: Using `DomainFilter` with `allowed_domains` to restrict crawling to a list of specific domains.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, DomainFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_allowed_domains():
    # Only crawl within 'docs.crawl4ai.com'
    domain_filter = DomainFilter(allowed_domains=["docs.crawl4ai.com"])
    filter_chain = FilterChain(filters=[domain_filter])

    # include_external needs to be True for DomainFilter to even consider other domains for blocking/allowing
    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain, include_external=True)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html" # This links to external-site.com
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- DomainFilter: Allowing only 'docs.crawl4ai.com' ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            print(f"  URL: {r.url}")
            assert "docs.crawl4ai.com" in r.url, f"Page {r.url} is not from an allowed domain."
        print("All crawled pages are from 'docs.crawl4ai.com'.")

if __name__ == "__main__":
    asyncio.run(filter_allowed_domains())
```

#### 5.2.2. Example: Using `DomainFilter` with `blocked_domains` to avoid crawling certain domains.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, DomainFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_blocked_domains():
    # Block 'external-site.com'
    domain_filter = DomainFilter(blocked_domains=["external-site.com"])
    filter_chain = FilterChain(filters=[domain_filter])

    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain, include_external=True)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- DomainFilter: Blocking 'external-site.com' ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            print(f"  URL: {r.url}")
            assert "external-site.com" not in r.url, f"Page {r.url} from blocked domain was crawled."
        print("No pages from 'external-site.com' were crawled.")

if __name__ == "__main__":
    asyncio.run(filter_blocked_domains())
```

#### 5.2.3. Example: `DomainFilter` configured to allow subdomains (`allow_subdomains=True`).
(Conceptual as MOCK_SITE_DATA doesn't have subdomains for `docs.crawl4ai.com`.)

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, DomainFilter
from unittest.mock import patch

# Imagine MOCK_SITE_DATA also has:
# "https://blog.docs.crawl4ai.com/vibe-examples/post.html": { ... }
# And index.html links to it.

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_allow_subdomains():
    domain_filter = DomainFilter(allowed_domains=["docs.crawl4ai.com"], allow_subdomains=True)
    filter_chain = FilterChain(filters=[domain_filter])

    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain, include_external=True)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- DomainFilter: Allowing subdomains of 'docs.crawl4ai.com' (Conceptual) ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            print(f"  URL: {r.url}")
            # In a real test, you'd check if blog.docs.crawl4ai.com was included
        print("This example is conceptual; for a real test, ensure mock data includes subdomains.")

if __name__ == "__main__":
    asyncio.run(filter_allow_subdomains())
```

#### 5.2.4. Example: `DomainFilter` configured to disallow subdomains (`allow_subdomains=False`).
(Conceptual as MOCK_SITE_DATA doesn't have subdomains for `docs.crawl4ai.com`.)

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, DomainFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_disallow_subdomains():
    domain_filter = DomainFilter(allowed_domains=["docs.crawl4ai.com"], allow_subdomains=False) # Default
    filter_chain = FilterChain(filters=[domain_filter])

    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain, include_external=True)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- DomainFilter: Disallowing subdomains of 'docs.crawl4ai.com' (Conceptual) ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            print(f"  URL: {r.url}")
            # In a real test, you'd check if blog.docs.crawl4ai.com was NOT included
        print("This example is conceptual; for a real test, ensure mock data includes subdomains to be excluded.")

if __name__ == "__main__":
    asyncio.run(filter_disallow_subdomains())
```

### 5.3. `ContentTypeFilter`

#### 5.3.1. Example: Using `ContentTypeFilter` to allow only `text/html` pages.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, ContentTypeFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_allow_html_only():
    content_filter = ContentTypeFilter(allowed_types=["text/html"])
    filter_chain = FilterChain(filters=[content_filter])

    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/page1.html" # Links to HTML and PDF
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- ContentTypeFilter: Allowing only 'text/html' ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            content_type = r.response_headers.get('Content-Type', '')
            print(f"  URL: {r.url}, Content-Type: {content_type}")
            if r.metadata.get('depth', 0) > 0: # Check discovered URLs
                assert "text/html" in content_type, f"Page {r.url} has wrong content type: {content_type}"
        print("All discovered pages are 'text/html'.")

if __name__ == "__main__":
    asyncio.run(filter_allow_html_only())
```

#### 5.3.2. Example: Using `ContentTypeFilter` with multiple `allowed_types` (e.g., `text/html`, `application/json`).
(Conceptual, as MOCK_SITE_DATA only has html/pdf)

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, ContentTypeFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_allow_multiple_types():
    content_filter = ContentTypeFilter(allowed_types=["text/html", "application/json"])
    filter_chain = FilterChain(filters=[content_filter])

    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/page1.html"
        # Imagine page1.html also links to a page1_sub3.json
        MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/page1_sub3.json"] = {
            "html_content": '{"key": "value"}',
            "response_headers": {"Content-Type": "application/json"}
        }
        MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/page1.html"]["html_content"] += '<a href="page1_sub3.json">JSON Data</a>'


        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- ContentTypeFilter: Allowing 'text/html', 'application/json' ---")
        print(f"Crawled {len(results)} pages.")
        found_json = False
        for r in results:
            content_type = r.response_headers.get('Content-Type', '')
            print(f"  URL: {r.url}, Content-Type: {content_type}")
            if r.metadata.get('depth',0) > 0:
                assert "text/html" in content_type or "application/json" in content_type
            if "application/json" in content_type:
                found_json = True
        assert found_json, "Expected to find a JSON page."
        print("All discovered pages are either 'text/html' or 'application/json'.")

        # Clean up mock data
        del MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/page1_sub3.json"]
        MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/page1.html"]["html_content"] = MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/page1.html"]["html_content"].replace('<a href="page1_sub3.json">JSON Data</a>', '')


if __name__ == "__main__":
    asyncio.run(filter_allow_multiple_types())
```

#### 5.3.3. Example: Using `ContentTypeFilter` with `blocked_types` (e.g., blocking `application/pdf`).

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, ContentTypeFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_block_pdf():
    content_filter = ContentTypeFilter(blocked_types=["application/pdf"])
    filter_chain = FilterChain(filters=[content_filter])

    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/page1.html" # Links to HTML and PDF
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- ContentTypeFilter: Blocking 'application/pdf' ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            content_type = r.response_headers.get('Content-Type', '')
            print(f"  URL: {r.url}, Content-Type: {content_type}")
            assert "application/pdf" not in content_type, f"PDF page {r.url} was not blocked."
        print("No 'application/pdf' pages were crawled (beyond start URL if it was PDF).")

if __name__ == "__main__":
    asyncio.run(filter_block_pdf())
```

### 5.4. `URLFilter` (Simple exact match)

#### 5.4.1. Example: `URLFilter` to allow a specific list of exact URLs.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, URLFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_allow_exact_urls():
    allowed_urls = [
        "https://docs.crawl4ai.com/vibe-examples/page1.html",
        "https://docs.crawl4ai.com/vibe-examples/page1_sub1.html"
    ]
    url_filter = URLFilter(urls=allowed_urls, block_list=False) # Allow list
    filter_chain = FilterChain(filters=[url_filter])

    strategy = BFSDeePCrawlStrategy(max_depth=2, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- URLFilter: Allowing specific URLs ---")
        print(f"Crawled {len(results)} pages.")
        crawled_urls = {r.url for r in results}
        # The start URL is always crawled initially, then its links are filtered.
        # So we check that all *other* crawled URLs are in the allowed list.
        for r_url in crawled_urls:
            if r_url != start_url: # Exclude start_url from this assertion
                 assert r_url in allowed_urls, f"URL {r_url} was not in the allowed list."
        print("Only URLs from the allowed list (plus start_url) were crawled.")

if __name__ == "__main__":
    asyncio.run(filter_allow_exact_urls())
```

#### 5.4.2. Example: `URLFilter` to block a specific list of exact URLs.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, URLFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_block_exact_urls():
    blocked_urls = [
        "https://docs.crawl4ai.com/vibe-examples/page2.html",
        "https://docs.crawl4ai.com/vibe-examples/archive/old_page.html"
    ]
    url_filter = URLFilter(urls=blocked_urls, block_list=True) # Block list
    filter_chain = FilterChain(filters=[url_filter])

    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)

        print(f"--- URLFilter: Blocking specific URLs ---")
        print(f"Crawled {len(results)} pages.")
        crawled_urls = {r.url for r in results}
        for blocked_url in blocked_urls:
            assert blocked_url not in crawled_urls, f"URL {blocked_url} should have been blocked."
        print("Blocked URLs were not crawled.")

if __name__ == "__main__":
    asyncio.run(filter_block_exact_urls())
```

### 5.5. `ContentRelevanceFilter`
This filter uses an LLM to determine relevance. The example focuses on setup, as a full run requires an LLM.

#### 5.5.1. Example: Setting up `ContentRelevanceFilter` with target keywords (conceptual, focusing on setup).

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

#### 5.5.2. Example: `ContentRelevanceFilter` with a custom `threshold`.

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

### 5.6. `SEOFilter`
This filter checks for common SEO issues. The example is conceptual, focusing on setup.

#### 5.6.1. Example: Basic `SEOFilter` with default SEO checks (conceptual, focusing on setup).

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

#### 5.6.2. Example: `SEOFilter` configuring specific checks like `min_title_length`, `max_meta_description_length`, or `keyword_in_title_check` (conceptual).

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

### 5.7. `FilterChain`

#### 5.7.1. Example: Combining `URLPatternFilter` (allow `/products/*`) and `DomainFilter` (only `example.com`) in a `FilterChain`.

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

#### 5.7.2. Example: Using `FilterChain` with `FilterStats` to retrieve and display statistics about filtered URLs.

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

#### 5.7.3. Example: `FilterChain` with `allow_empty=True` vs `allow_empty=False`.
This shows how `allow_empty` on the `FilterChain` itself works. If `allow_empty=True` (default), an empty chain allows all URLs. If `False`, an empty chain blocks all.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_chain_allow_empty():
    start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"

    # Case 1: allow_empty=True (default) - empty chain allows all
    print("\n--- FilterChain with allow_empty=True (empty chain) ---")
    empty_chain_allow = FilterChain(filters=[], allow_empty=True)
    strategy_allow = BFSDeePCrawlStrategy(max_depth=1, filter_chain=empty_chain_allow)
    run_config_allow = CrawlerRunConfig(deep_crawl_strategy=strategy_allow, cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler() as crawler:
        results_allow = await crawler.arun(url=start_url, config=run_config_allow)
        print(f"Crawled {len(results_allow)} pages. (Expected > 1 as all links from index should be allowed)")
        assert len(results_allow) > 1 # Start URL + its links

    # Case 2: allow_empty=False - empty chain blocks all (except start URL)
    print("\n--- FilterChain with allow_empty=False (empty chain) ---")
    empty_chain_block = FilterChain(filters=[], allow_empty=False)
    strategy_block = BFSDeePCrawlStrategy(max_depth=1, filter_chain=empty_chain_block)
    run_config_block = CrawlerRunConfig(deep_crawl_strategy=strategy_block, cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler() as crawler:
        results_block = await crawler.arun(url=start_url, config=run_config_block)
        print(f"Crawled {len(results_block)} pages. (Expected 1, only start URL)")
        assert len(results_block) == 1 # Only start_url, as all its links are blocked by empty chain


if __name__ == "__main__":
    asyncio.run(filter_chain_allow_empty())
```

---
