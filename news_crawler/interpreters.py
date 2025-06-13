"""LLM-based interpreters for link discovery and article parsing."""

from __future__ import annotations

from typing import List, Optional

from collections import Counter
from bs4 import BeautifulSoup

from pydantic import BaseModel, Field
from crawl4ai import LLMExtractionStrategy, LLMConfig


class LinkList(BaseModel):
    """Schema for a list of article links."""

    links: List[str] = Field(description="Absolute URLs of article pages")


class ArticleInfo(BaseModel):
    """Structured information extracted from an article."""

    title: str = Field(description="Headline of the article")
    date: Optional[str] = Field(default=None, description="Publication date if available")
    description: Optional[str] = Field(default=None, description="Short description or summary")


class ArticleLinkInterpreter:
    """Use ``LLMExtractionStrategy`` to identify article links from HTML."""

    def __init__(self, llm_config: LLMConfig) -> None:
        self.strategy = LLMExtractionStrategy(
            llm_config=llm_config,
            schema=LinkList.model_json_schema(),
            extraction_type="schema",
            instruction=(
                "Inspect the HTML and return a JSON list of absolute URLs that represent news articles."
            ),
        )
        self.strategy.input_format = "html"

    async def extract_links(self, url: str, html: str) -> List[str]:
        results = self.strategy.extract(url=url, html_content=html)
        if not results:
            return []
        data = results[0] if isinstance(results, list) else results
        return data.get("links", [])

    def find_recurrent_news_class(self, html: str) -> Optional[str]:
        """Return the most common ``div`` class inside ``<main>`` if repeated."""
        soup = BeautifulSoup(html, "lxml")
        main = soup.find("main")
        if not main:
            return None
        class_counter: Counter[str] = Counter()
        for div in main.find_all("div", class_=True):
            classes = div.get("class") or []
            for cls in classes:
                class_counter[cls] += 1
        if not class_counter:
            return None
        cls, count = class_counter.most_common(1)[0]
        return cls if count > 1 else None

    def get_sample_news_div(self, html: str) -> Optional[str]:
        """Return HTML of a sample news ``div`` using the recurrent class."""
        cls = self.find_recurrent_news_class(html)
        if not cls:
            return None
        soup = BeautifulSoup(html, "lxml")
        main = soup.find("main")
        if not main:
            return None
        div = main.find("div", class_=cls)
        return str(div) if div else None


class ArticleInterpreter:
    """Extract structured article data using ``LLMExtractionStrategy``."""

    def __init__(self, llm_config: LLMConfig) -> None:
        self.strategy = LLMExtractionStrategy(
            llm_config=llm_config,
            schema=ArticleInfo.model_json_schema(),
            extraction_type="schema",
            instruction="Extract the title, publication date, and description from the article.",
        )
        self.strategy.input_format = "html"

    async def extract(self, url: str, html: str) -> ArticleInfo:
        result = self.strategy.extract(url=url, html_content=html)
        if isinstance(result, list) and result:
            return ArticleInfo(**result[0])
        if isinstance(result, dict):
            return ArticleInfo(**result)
        raise ValueError("No article data extracted")
