"""News crawler skeleton using Crawl4AI components."""

from .fetcher import Fetcher, FetchResult
from .interpreters import ArticleLinkInterpreter, ArticleInterpreter, ArticleInfo
from .crawler import NewsCrawler, SitePoller
from .policy import DomainScanner, DomainRegistry, PermissionLevel, DomainInfo

__all__ = [
    "Fetcher",
    "FetchResult",
    "ArticleLinkInterpreter",
    "ArticleInterpreter",
    "ArticleInfo",
    "NewsCrawler",
    "SitePoller",
    "DomainScanner",
    "DomainRegistry",
    "PermissionLevel",
    "DomainInfo",
]
