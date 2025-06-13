"""LLM-based interpreters for link discovery and article parsing."""

from __future__ import annotations
import os, json
from typing import List, Optional
from collections import Counter
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from crawl4ai import LLMExtractionStrategy, LLMConfig, JsonCssExtractionStrategy

llm_config = LLMConfig(provider="openai/gpt-4o-mini",
                       api_token=os.getenv("OPENAI_API_KEY"))

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

    #TODO: implement the logic to retrieve the content of a link fetched through ArticleInterpreter




class ArticleInterpreter:
    """Extract structured article div using ``LLMExtractionStrategy``."""

    #TODO: modify the __init__ accordingly to the new updated functions
    def __init__(self, llm_config: LLMConfig) -> None:
        self.strategy = LLMExtractionStrategy(
            llm_config=llm_config,
            schema=ArticleInfo.model_json_schema(),
            extraction_type="schema",
            instruction="Extract the title, publication date, and description from the article.",
        )
        self.strategy.input_format = "html"

    async def find_recurrent_news_class(self, html: str) -> Optional[str]:
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

    async def get_sample_news_div(self, html: str) -> Optional[str]:
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

    async def generate_div(self, url: str, html: str):
        """ Generate a schema for the most recurrent div class in the <main> """
        schema = JsonCssExtractionStrategy.generate_schema(
            html=html,
            llm_config=llm_config,
            query=f"From {url} I have shared a sample of one news article div class with a title, description and date. Please generate a schema for this news div",
        )
        print(f"Generated schema: {json.dumps(schema, indent=2)}")
    
    # TODO: save to domain structure 

