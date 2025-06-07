"""HTML fetching utilities built on Crawl4AI."""

from dataclasses import dataclass
from typing import Optional, Any, Dict

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode


@dataclass
class FetchResult:
    """Container for fetched HTML and metadata."""

    url: str
    html: str
    metadata: Dict[str, Any]


class Fetcher:
    """Thin wrapper around ``AsyncWebCrawler`` for retrieving HTML."""

    def __init__(self, browser_config: Optional[BrowserConfig] | None = None) -> None:
        self.browser_config = browser_config or BrowserConfig(headless=True)

    async def fetch(self, url: str, run_config: Optional[CrawlerRunConfig] | None = None) -> FetchResult:
        """Retrieve the given URL and return the cleaned HTML."""
        run_cfg = run_config or CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            result = await crawler.arun(url=url, config=run_cfg)
        if not result.success:
            raise RuntimeError(f"Failed to fetch {url}: {result.error_message}")
        html = result.cleaned_html or result.html or ""
        return FetchResult(url=result.url, html=html, metadata=result.metadata)
