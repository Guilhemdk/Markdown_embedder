"""
This module contains the Parser component.
The Parser is responsible for transforming raw HTML/JSON into clean, structured data.
It uses crawl4ai for intelligent content extraction and BeautifulSoup/feedparser for specific tasks,
and provides utilities for parsing robots.txt directives like Crawl-delay.
"""
from crawl4ai import WebCrawler
from crawl4ai.web_crawler import Url
from bs4 import BeautifulSoup
import urllib.parse
import feedparser
from datetime import datetime, timezone, timedelta
import time
from dateutil import parser as dateutil_parser


class Parser:
    """
    Parses HTML, RSS feeds, sitemaps, and provides robots.txt parsing utilities.
    """
    def __init__(self, monitor_instance=None):
        # ... (existing __init__) ...
        self.monitor = monitor_instance
        try:
            self.crawler = WebCrawler()
            self._log_event("INFO", "crawl4ai WebCrawler initialized successfully.")
        except Exception as e:
            self._log_event("ERROR", f"Failed to initialize crawl4ai WebCrawler: {e}")
            self.crawler = None

    def _log_event(self, level, message, details=None):
        # ... (existing _log_event) ...
        if self.monitor:
            self.monitor.log_event(level, message, details)
        else:
            details_str = f" | Details: {details}" if details else ""
            print(f"[{level}] {message}{details_str}")

    def _parse_generic_date_to_utc(self, date_input, context_url="N/A"):
        # ... (existing _parse_generic_date_to_utc) ...
        if date_input is None: return None
        if isinstance(date_input, datetime):
            return date_input.astimezone(timezone.utc) if date_input.tzinfo else date_input.replace(tzinfo=timezone.utc)
        if isinstance(date_input, str):
            try:
                dt = dateutil_parser.parse(date_input)
                return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except Exception: return None
        if isinstance(date_input, time.struct_time):
            try: return datetime.fromtimestamp(time.mktime(date_input), tz=timezone.utc)
            except Exception: return None
        return None

    def parse_content(self, html_content, url):
        # ... (existing parse_content, ensure it uses _parse_generic_date_to_utc) ...
        if not self.crawler: self._log_event("ERROR", "Crawler not init.", {"url": url}); return None
        if not html_content: self._log_event("INFO", "No HTML for parsing.", {"url": url}); return None
        try:
            res = self.crawler.read(Url(url=url, html_content=html_content))
            if res and (res.text or res.metadata):
                date_val = next((res.metadata.get(k) for k in ["date", "publish_date", "published_time", "created_at", "updated_at"] if res.metadata.get(k)), None)
                return {"url": url, "title": res.metadata.get("title", "N/A"), "text": res.text or None,
                        "published_date_utc": self._parse_generic_date_to_utc(date_val, url), "raw_metadata": res.metadata}
        except Exception as e: self._log_event("ERROR", f"crawl4ai parsing error: {e}", {"url": url});
        return None

    def find_rss_links_in_html(self, html_content, base_url):
        # ... (existing find_rss_links_in_html) ...
        rss_links = []
        if not html_content: return rss_links
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            for tag in soup.find_all('link', attrs={'rel': 'alternate', 'type': lambda t: t and 'application/rss+xml' in t.lower()}):
                if href := tag.get('href'): rss_links.append(urllib.parse.urljoin(base_url, href.strip()))
            for tag in soup.find_all('link', attrs={'type': lambda t: t and 'application/rss+xml' in t.lower()}):
                if href := tag.get('href'):
                    full_url = urllib.parse.urljoin(base_url, href.strip())
                    if full_url not in rss_links: rss_links.append(full_url)
        except Exception as e: self._log_event("ERROR", f"HTML RSS link parsing error: {e}", {"base_url": base_url})
        return list(set(rss_links))

    def find_sitemap_links_in_robots(self, robots_txt_content):
        # ... (existing find_sitemap_links_in_robots) ...
        sitemap_links = []
        if not robots_txt_content: return sitemap_links
        try:
            for line in robots_txt_content.splitlines():
                if line.strip().lower().startswith('sitemap:'):
                    if parts := line.split(':', 1):
                        if len(parts) > 1 and parts[1].strip(): sitemap_links.append(parts[1].strip())
        except Exception as e: self._log_event("ERROR", f"robots.txt sitemap link parsing error: {e}")
        return list(set(sitemap_links))

    def parse_rss_feed(self, feed_xml_content, feed_url):
        # ... (existing parse_rss_feed, ensure it uses _parse_generic_date_to_utc) ...
        if not feed_xml_content: return []
        parsed = feedparser.parse(feed_xml_content)
        if parsed.bozo: self._log_event("WARNING", f"Ill-formed RSS feed {feed_url}", {"exc": str(parsed.get("bozo_exception"))})
        items = []
        for entry in parsed.entries:
            link = entry.get('link')
            if not link: continue
            date_struct = entry.get('published_parsed') or entry.get('updated_parsed')
            items.append({"id": entry.get('id', link), "link": link, "title": entry.get('title'),
                          "published_date_utc": self._parse_generic_date_to_utc(date_struct, feed_url),
                          "source_feed_url": feed_url, "feed_entry_raw": entry})
        return items

    def parse_sitemap(self, sitemap_xml_content, sitemap_url):
        # ... (existing parse_sitemap, ensure it uses _parse_generic_date_to_utc) ...
        if not sitemap_xml_content: return None
        try:
            soup = BeautifulSoup(sitemap_xml_content, 'xml')
            if soup.find('sitemapindex'):
                urls = [tag.text.strip() for s_tag in soup.find_all('sitemap') if (tag := s_tag.find('loc')) and tag.text]
                return {'type': 'sitemap_index', 'sitemap_urls': urls, 'source_sitemap_url': sitemap_url} if urls else None
            elif soup.find('urlset'):
                items = []
                for url_tag in soup.find_all('url'):
                    loc_tag, mod_tag = url_tag.find('loc'), url_tag.find('lastmod')
                    if loc_tag and loc_tag.text:
                        items.append({'loc': loc_tag.text.strip(),
                                      'lastmod_utc': self._parse_generic_date_to_utc(mod_tag.text.strip() if mod_tag and mod_tag.text else None, sitemap_url),
                                      'source_sitemap_url': sitemap_url})
                return {'type': 'urlset', 'items': items, 'source_sitemap_url': sitemap_url}
        except Exception as e: self._log_event("ERROR", f"Sitemap parsing error {sitemap_url}: {e}")
        return None

    def parse_crawl_delay(self, robots_txt_content, target_user_agent="*"):
        """
        Parses robots.txt content to find Crawl-delay for a specific user-agent.
        Args:
            robots_txt_content (str): The content of the robots.txt file.
            target_user_agent (str): The user-agent string to look for. Defaults to "*".
        Returns:
            float: The crawl delay in seconds, or None if not found.
        """
        if not robots_txt_content:
            return None

        lines = robots_txt_content.splitlines()
        current_agent_match = False
        target_agent_lower = target_user_agent.lower()
        wildcard_agent_match = False
        crawl_delay = None
        wildcard_crawl_delay = None

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split(':', 1)
            if len(parts) != 2:
                continue

            directive = parts[0].strip().lower()
            value = parts[1].strip()

            if directive == 'user-agent':
                # New user-agent block starts, reset current match state
                current_agent_match = (value.lower() == target_agent_lower)
                wildcard_agent_match = (value == '*')
                if current_agent_match: # Specific agent matched, reset wildcard delay if it was set for a previous block
                    wildcard_crawl_delay = None

            elif directive == 'crawl-delay':
                try:
                    delay_value = float(value)
                    if current_agent_match: # Matches specific target_user_agent
                        crawl_delay = delay_value
                        # Specific agent delay found, this takes precedence. We can even break if we only care about the first match.
                        # For thoroughness, one might continue to see if other specific blocks redefine it, but usually first one counts.
                        # For now, let's say the first specific match is taken.
                        break
                    elif wildcard_agent_match: # Matches '*'
                        wildcard_crawl_delay = delay_value
                except ValueError:
                    self._log_event("WARNING", f"Invalid Crawl-delay value '{value}' in robots.txt.")

        final_delay = crawl_delay if crawl_delay is not None else wildcard_crawl_delay
        if final_delay is not None:
            self._log_event("INFO", f"Found Crawl-delay: {final_delay}s for agent '{target_user_agent if crawl_delay is not None else '*'}'")
        return final_delay


if __name__ == '__main__':
    monitor_dummy = None
    parser = Parser(monitor_instance=monitor_dummy)

    print("\n--- Testing Parser: Crawl-delay parsing ---")
    robots_example_content = """
    # Example robots.txt
    User-agent: SpecificBot
    Crawl-delay: 10
    Disallow: /private/

    User-agent: *
    Crawl-delay: 5
    Disallow: /tmp/
    Sitemap: http://example.com/sitemap.xml

    User-agent: AnotherSpecificBot
    Crawl-delay: 15
    """
    delay1 = parser.parse_crawl_delay(robots_example_content, "SpecificBot")
    print(f"  Delay for SpecificBot: {delay1} (Expected: 10.0)")
    assert delay1 == 10.0

    delay2 = parser.parse_crawl_delay(robots_example_content, "OtherBot") # Should use wildcard
    print(f"  Delay for OtherBot (uses *): {delay2} (Expected: 5.0)")
    assert delay2 == 5.0

    delay3 = parser.parse_crawl_delay(robots_example_content, "*") # Explicitly wildcard
    print(f"  Delay for *: {delay3} (Expected: 5.0)")
    assert delay3 == 5.0

    delay4 = parser.parse_crawl_delay(robots_example_content, "AnotherSpecificBot")
    print(f"  Delay for AnotherSpecificBot: {delay4} (Expected: 15.0)")
    assert delay4 == 15.0

    robots_no_delay = "User-agent: *\nDisallow: /"
    delay_none = parser.parse_crawl_delay(robots_no_delay, "*")
    print(f"  Delay for no_delay robots: {delay_none} (Expected: None)")
    assert delay_none is None

    print("\n--- Parser __main__ tests (including crawl-delay) finished ---")
