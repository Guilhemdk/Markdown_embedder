"""Domain policy scanning and registry utilities for the news crawler."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

import aiohttp


REQUEST_DELAY = 1.0  # seconds between requests
USER_AGENT = "NewsCrawler v1.0; contact: youremail@example.com"

logging.basicConfig(level=logging.INFO)


class PermissionLevel(str, Enum):
    """Classification for a site's scraping policy."""

    GREEN = "green"  # Has API or CC licensed feed
    YELLOW = "yellow"  # No explicit ban
    RED = "red"  # Explicitly forbids scraping


@dataclass
class DomainInfo:
    domain: str
    permission: PermissionLevel = PermissionLevel.YELLOW
    feed_urls: List[str] = field(default_factory=list)
    api_endpoints: List[str] = field(default_factory=list)
    contact: Optional[str] = None
    license_info: Optional[str] = None
    last_checked: Optional[str] = None
    etag: Optional[str] = None
    last_modified: Optional[str] = None


class DomainRegistry:
    """Persist and manage ``DomainInfo`` records."""

    def __init__(self, path: str) -> None:
        self.path = path
        self._data: Dict[str, DomainInfo] = {}
        self.load()

    def load(self) -> None:
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                raw = json.load(f)
                self._data = {item["domain"]: DomainInfo(**item) for item in raw}
        else:
            self._data = {}

    def save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump([asdict(d) for d in self._data.values()], f, indent=2)

    def update(self, info: DomainInfo) -> None:
        self._data[info.domain] = info
        self.save()

    def get(self, domain: str) -> Optional[DomainInfo]:
        return self._data.get(domain)


class DomainScanner:
    """Scan domains and classify scraping permission."""

    def __init__(self, registry: DomainRegistry) -> None:
        self.registry = registry
        self._semaphore = asyncio.Semaphore(1)
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "DomainScanner":
        self._session = aiohttp.ClientSession(headers={"User-Agent": USER_AGENT})
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._session:
            await self._session.close()

    async def _throttled_get(
        self, url: str, etag: Optional[str] = None, last_modified: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        assert self._session is not None
        headers = {}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified
        async with self._semaphore:
            await asyncio.sleep(REQUEST_DELAY)
            try:
                async with self._session.get(url, headers=headers, timeout=30) as resp:
                    if resp.status == 304:
                        logging.info("Not modified: %s", url)
                        return None, resp.headers.get("ETag"), resp.headers.get("Last-Modified")
                    if resp.status >= 400:
                        logging.warning("Failed request %s: %s", url, resp.status)
                        return None, None, None
                    text = await resp.text()
                    return text, resp.headers.get("ETag"), resp.headers.get("Last-Modified")
            except Exception as exc:
                logging.error("Error fetching %s: %s", url, exc)
                return None, None, None

    async def scan_domain(self, domain: str) -> DomainInfo:
        base = domain if domain.startswith("http") else f"https://{domain}"
        info = self.registry.get(domain) or DomainInfo(domain=domain)

        robots_url = base.rstrip("/") + "/robots.txt"
        robots, etag, lm = await self._throttled_get(robots_url, info.etag, info.last_modified)
        if robots is not None:
            info.etag, info.last_modified = etag, lm
            if re.search(r"disallow:\s*/", robots, re.I):
                info.permission = PermissionLevel.RED

        sitemap_url = base.rstrip("/") + "/sitemap.xml"
        sitemap, _, _ = await self._throttled_get(sitemap_url)
        if sitemap:
            feed_urls = re.findall(r"<loc>([^<]+)</loc>", sitemap)
            info.feed_urls.extend(feed_urls)

        home, _, _ = await self._throttled_get(base)
        if home:
            rss_links = re.findall(r'<link[^>]+type=["\']application/rss\+xml["\'][^>]+href=["\']([^"\']+)["\']', home, re.I)
            info.feed_urls.extend(rss_links)
            if re.search(r"api", home, re.I):
                info.api_endpoints.append(base)
            tos_match = re.search(r"href=[\"\']([^\"\']*(terms|tos)[^\"\']*)[\"\']", home, re.I)
            if tos_match:
                tos_url = tos_match.group(1)
                if not tos_url.startswith("http"):
                    tos_url = base.rstrip("/") + "/" + tos_url.lstrip("/")
                tos_page, _, _ = await self._throttled_get(tos_url)
                if tos_page and re.search(r"scrap|no scraping", tos_page, re.I):
                    info.permission = PermissionLevel.RED
                if tos_page and re.search(r"creative\s+commons", tos_page, re.I):
                    info.permission = PermissionLevel.GREEN

        if info.permission is PermissionLevel.YELLOW:
            if info.api_endpoints or any("creativecommons" in f.lower() for f in info.feed_urls):
                info.permission = PermissionLevel.GREEN

        info.feed_urls = list({u for u in info.feed_urls})
        info.last_checked = asyncio.get_event_loop().time().__str__()
        self.registry.update(info)
        return info


async def scan_from_file(domain_file: str, registry_path: str) -> None:
    registry = DomainRegistry(registry_path)
    async with DomainScanner(registry) as scanner:
        with open(domain_file, "r", encoding="utf-8") as f:
            domains = [line.strip() for line in f if line.strip()]
        for dom in domains:
            await scanner.scan_domain(dom)


def main() -> None:
    import asyncio as _asyncio
    domain_file = os.path.join(os.path.dirname(__file__), "candidate_domains.txt")
    registry_path = os.path.join(os.path.dirname(__file__), "domain_registry.json")
    _asyncio.run(scan_from_file(domain_file, registry_path))


if __name__ == "__main__":
    main()
