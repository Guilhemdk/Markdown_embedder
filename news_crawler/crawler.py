"""High level orchestration for crawling news sites."""

from __future__ import annotations

import asyncio
from typing import List

from .fetcher import Fetcher
from .interpreters import ArticleLinkInterpreter, ArticleInterpreter, ArticleInfo


class NewsCrawler:
    """Crawl a news site and extract articles."""

    def __init__(
        self,
        fetcher: Fetcher,
        link_interpreter: ArticleLinkInterpreter,
        article_interpreter: ArticleInterpreter,
    ) -> None:
        self.fetcher = fetcher
        self.link_interpreter = link_interpreter
        self.article_interpreter = article_interpreter

    async def crawl(self, url: str, depth: int = 0) -> List[ArticleInfo]:
        html = await self.fetcher.fetch(url)
        news_div = await self.article_interpreter.get_sample_news_div(html)
        div_schema = await self.article_interpreter.generate_div(url, news_div)

        #TODO: implement the loop for going through the home page html and retrieve the links of each identified schema
        
        #TODO: implement the generate div for 1 retrieved article link

        #TODO: implement the for loop for fetching the title, description, content, author, date and type of each article


class SitePoller:
    """Periodically poll a news site for new articles."""

    def __init__(self, crawler: NewsCrawler, interval: float = 300.0) -> None:
        self.crawler = crawler
        self.interval = interval
        self._seen: set[str] = set()
        self._running = False

    async def start(self, url: str) -> None:
        self._running = True
        while self._running:
            articles = await self.crawler.crawl(url)
            for art in articles:
                if art.url not in self._seen:
                    self._seen.add(art.url)
                    self.handle_new_article(art)
            await asyncio.sleep(self.interval)

    def stop(self) -> None:
        self._running = False

    def handle_new_article(self, article: ArticleInfo) -> None:
        """Override to integrate with storage or downstream pipelines."""
        print(f"New article: {article.title} ({article.date})")
