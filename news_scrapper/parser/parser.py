"""
This module contains the Parser component.
The Parser is responsible for transforming raw HTML/JSON into clean, structured data.
It uses multiple strategies: custom CSS selectors, Schema.org (via extruct),
general AI (crawl4ai), and can trigger LLM-based selector generation.
"""
import json
import re
from datetime import datetime, timezone, timedelta
import time
from urllib.parse import urljoin

try:
    from crawl4ai import WebCrawler, Url
except ImportError:
    WebCrawler = None # type: ignore
    Url = None # type: ignore
    print("WARNING: Parser: crawl4ai synchronous WebCrawler/Url not found, using placeholders. AI parsing will be affected.")

# JsonCssExtractionStrategy is not used directly (handled by commenting out its import block)

import feedparser # type: ignore[reportMissingImports]
import extruct
from bs4 import BeautifulSoup, Tag
from dateutil import parser as dateutil_parser

try:
    from ..analyzer.structure_analyzer import StructureAnalyzer
except ImportError:
    StructureAnalyzer = None

from typing import Any, Dict, List, Optional, Union


class Parser:
    def __init__(self, monitor_instance=None, planner_reference=None, structure_analyzer_instance=None):
        self.monitor = monitor_instance
        self.planner_ref = planner_reference
        self.structure_analyzer = structure_analyzer_instance

        if WebCrawler is None:
            self._log_event("ERROR", "Parser: crawl4ai.WebCrawler is not available. AI parsing will fail.")
            self.crawler = None
        else:
            try:
                self.crawler = WebCrawler()
                self._log_event("INFO", "Parser: crawl4ai WebCrawler initialized.")
            except Exception as e:
                self._log_event("ERROR", f"Parser: Failed to initialize crawl4ai WebCrawler: {e}")
                self.crawler = None

        if self.planner_ref is None: self._log_event("WARNING", "Parser: Planner reference not provided.")
        if self.structure_analyzer is None: self._log_event("WARNING", "Parser: StructureAnalyzer not provided.")

    def _log_event(self, level: str, message: str, details: Optional[Dict[str, Any]] = None):
        if self.monitor: self.monitor.log_event(level.upper(), message, details)
        else: print(f"[{level.upper()}] {message}{(' | ' + json.dumps(details)) if details else ''}")

    def _parse_generic_date_to_utc(self, date_input: Any) -> Optional[datetime]: # context_url removed
        if date_input is None: return None
        if isinstance(date_input, datetime):
            return date_input.astimezone(timezone.utc) if date_input.tzinfo else date_input.replace(tzinfo=timezone.utc)
        if isinstance(date_input, str):
            try:
                dt = dateutil_parser.parse(date_input)
                return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError, OverflowError): # Logged where this is called if context needed
                return None
        if isinstance(date_input, time.struct_time):
            try: return datetime.fromtimestamp(time.mktime(date_input), tz=timezone.utc)
            except Exception: return None
        return None


    def _is_data_sufficient(self, parsed_data_dict: Optional[Dict[str, Any]]) -> bool:
        if not parsed_data_dict: return False
        return bool(parsed_data_dict.get('title') and parsed_data_dict.get('text'))

    def _normalize_extracted_data(self, data_dict: Dict[str, Any], source_url: str, extraction_method_used: str) -> Dict[str, Any]:
        if not isinstance(data_dict, dict): data_dict = {}
        title = data_dict.get('title') or data_dict.get('headline')
        text = data_dict.get('text') or data_dict.get('content') or data_dict.get('articleBody')
        raw_date = data_dict.get('published_date_utc') or data_dict.get('datePublished') or \
                   data_dict.get('dateModified') or data_dict.get('date') or data_dict.get('published_time')
        published_date_utc = self._parse_generic_date_to_utc(raw_date) # context_url removed
        if raw_date and not published_date_utc: # Log if parsing failed with a value
            self._log_event("DEBUG", f"Date parsing failed for value '{raw_date}'", {"url": source_url, "method": extraction_method_used})

        authors_data: Union[List[Any], Dict[str, Any], str, None] = data_dict.get('authors') or data_dict.get('author')
        authors_list: List[str] = []
        if isinstance(authors_data, list):
            for auth in authors_data: authors_list.append(auth.get('name') if isinstance(auth, dict) else str(auth))
        elif isinstance(authors_data, dict): authors_list.append(authors_data.get('name', str(authors_data)))
        elif isinstance(authors_data, str): authors_list = [n.strip() for n in authors_data.split(',')]

        return {
            "title": str(title).strip() if title else None,
            "text": str(text).strip() if text else None,
            "published_date_utc": published_date_utc,
            "authors": [str(a).strip() for a in authors_list if str(a).strip()],
            "url": data_dict.get('url', source_url),
            "extraction_method": extraction_method_used,
        }

    def _parse_with_custom_selectors(self, html_content: str, url: str, source_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        selectors = source_config.get("extraction_selectors")
        if not selectors or not isinstance(selectors, dict): return None
        strategy_map = {"title": selectors.get("article_title_selector"), "text": selectors.get("article_content_selector"),
            "authors": selectors.get("article_author_selector"), "date": selectors.get("article_date_selector")}
        active_selectors = {k: v for k, v in strategy_map.items() if v and str(v).strip()}
        if not active_selectors: return None
        self._log_event("INFO", f"Attempting extraction with custom CSS for {url}", {"selectors_count": len(active_selectors)})
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            extracted_data: Dict[str, Any] = {}
            for field, selector in active_selectors.items():
                elements = soup.select(selector)
                if elements:
                    if field == "text": extracted_data[field] = "\n".join([el.get_text(separator="\n", strip=True) for el in elements])
                    elif field == "authors": extracted_data[field] = [el.get_text(strip=True) for el in elements]
                    elif field == "date": extracted_data[field] = elements[0].get('datetime', elements[0].get_text(strip=True))
                    else: extracted_data[field] = elements[0].get_text(strip=True)
            return self._normalize_extracted_data(extracted_data, url, "custom_css") if extracted_data else None
        except Exception as e: self._log_event("ERROR", f"Custom CSS parsing error: {e}", {"url": url}); return None

    def _parse_with_schema_org(self, html_content: str, url: str) -> Optional[Dict[str, Any]]:
        self._log_event("INFO", f"Attempting Schema.org (extruct) for {url}")
        try:
            data = extruct.extract(html_content, base_url=urljoin(url, "/"), syntaxes=['json-ld', 'microdata'], uniform=True)
            for entry_type in ['json-ld', 'microdata']:
                for item in data.get(entry_type, []):
                    item_type_val = item.get('@type')
                    item_type_str = str(item_type_val[0] if isinstance(item_type_val, list) else item_type_val).lower() if item_type_val else ""
                    if any(t in item_type_str for t in ['article', 'newsarticle', 'blogposting', 'webpage']):
                        mapped = {'title': item.get('headline') or item.get('name'), 'text': item.get('articleBody') or item.get('text'),
                                  'authors': item.get('author'), 'date': item.get('datePublished') or item.get('dateModified'), 'url': item.get('url')}
                        if mapped.get('title') or mapped.get('text'):
                            return self._normalize_extracted_data(mapped, url, f"schema_org_{item_type_str}")
        except Exception as e: self._log_event("ERROR", f"Schema.org parsing error: {e}", {"url":url});
        return None

    def _parse_with_general_ai(self, html_content: str, url: str) -> Optional[Dict[str, Any]]:
        if not self.crawler or WebCrawler is None or Url is None :
            self._log_event("ERROR", "crawl4ai not available for general AI parsing.", {"url": url}); return None
        self._log_event("INFO", f"Attempting general AI (crawl4ai) for {url}")
        try:
            res = self.crawler.read(Url(url=url, html_content=html_content))
            if res and (res.text or res.metadata):
                ai_data = {'title': res.metadata.get('title'), 'text': res.text, 'date': res.metadata.get('date'),
                           'authors': [res.metadata.get('author')] if res.metadata.get('author') else []}
                return self._normalize_extracted_data(ai_data, url, "general_ai")
        except Exception as e: self._log_event("ERROR", f"General AI parsing error: {e}", {"url":url});
        return None

    def parse_content(self, html_content: str, url: str, source_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        source_config = source_config or {}
        source_name = source_config.get("name", "UnknownSource")
        self._log_event("INFO", f"Multi-strategy parsing for {url}", {"source": source_name})
        final_result: Optional[Dict[str, Any]] = None
        result_custom = self._parse_with_custom_selectors(html_content, url, source_config)
        if self._is_data_sufficient(result_custom): final_result = result_custom
        else:
            result_schema = self._parse_with_schema_org(html_content, url)
            if self._is_data_sufficient(result_schema): final_result = result_schema
            elif result_schema and not final_result: final_result = result_schema
        result_general_ai = self._parse_with_general_ai(html_content, url)
        if not self._is_data_sufficient(final_result):
            if self._is_data_sufficient(result_general_ai): final_result = result_general_ai
            elif result_general_ai and not final_result: final_result = result_general_ai
        needs_llm = (not source_config.get("extraction_selectors") or \
                     source_config.get("extraction_selectors",{}).get("_isEmpty",False)) and \
                    source_config.get("llm_analysis_pending", True)
        if needs_llm and (not final_result or not self._is_data_sufficient(final_result)):
            self._log_event("INFO", f"Attempting LLM selector generation for {source_name} ({url}).")
            if self.structure_analyzer and self.planner_ref and StructureAnalyzer is not None:
                new_selectors = self.structure_analyzer.generate_extraction_selectors(url, html_content)
                if new_selectors:
                    self.planner_ref.update_source_extraction_selectors(source_name, new_selectors)
                    if hasattr(self.planner_ref, 'save_config'): self.planner_ref.save_config()
                    source_config["extraction_selectors"] = new_selectors
                    source_config["llm_analysis_pending"] = False
                    self._log_event("INFO", "Re-parsing with LLM-generated selectors.", {"url": url})
                    result_after_llm = self._parse_with_custom_selectors(html_content, url, source_config)
                    if self._is_data_sufficient(result_after_llm): final_result = result_after_llm
                else:
                    self.planner_ref.set_llm_analysis_flag(source_name, False)
                    if hasattr(self.planner_ref, 'save_config'): self.planner_ref.save_config()
            else: self._log_event("WARNING", "LLM components not available.", {"url": url})
        return final_result if final_result else self._normalize_extracted_data({}, url, "no_data_found")

    def find_rss_links_in_html(self, html_content: str, base_url: str) -> List[str]:
        rss_links: List[str] = []
        if not html_content:
            self._log_event("DEBUG", "No HTML content provided to find_rss_links_in_html.", {"base_url": base_url})
            return rss_links
        found_hrefs: set[str] = set()
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            all_link_tags = soup.find_all('link')
            for tag in all_link_tags:
                tag_type_attr = tag.get('type')
                tag_rel_attr = tag.get('rel', [])
                rel_values: set[str] = set()
                if isinstance(tag_rel_attr, str): rel_values = {tag_rel_attr.lower()}
                elif isinstance(tag_rel_attr, list): rel_values = {r.lower() for r in tag_rel_attr if isinstance(r, str)}
                is_rss_type = isinstance(tag_type_attr, str) and 'application/rss+xml' in tag_type_attr.lower()
                is_alternate_rel = 'alternate' in rel_values
                if is_rss_type and is_alternate_rel:
                    href_attr = tag.get('href')
                    if isinstance(href_attr, str) and href_attr.strip():
                        full_url = urljoin(base_url, href_attr.strip())
                        if full_url not in found_hrefs:
                            rss_links.append(full_url); found_hrefs.add(full_url)
            if not rss_links: self._log_event("DEBUG", "No RSS links matching primary criteria found.", {"base_url": base_url})
            else: self._log_event("DEBUG", f"Found {len(rss_links)} RSS links.", {"base_url": base_url, "links": rss_links})
        except Exception as e:
            self._log_event("ERROR", f"HTML RSS link parsing error: {e}", {"base_url": base_url, "exception_type": type(e).__name__})
        return rss_links

    def find_sitemap_links_in_robots(self, robots_txt_content: str) -> List[str]:
        sitemap_links: List[str] = []
        if not robots_txt_content: return sitemap_links
        try:
            for line in robots_txt_content.splitlines():
                if line.strip().lower().startswith('sitemap:'):
                    parts = line.split(':', 1)
                    if len(parts) > 1 and parts[1].strip(): sitemap_links.append(parts[1].strip())
        except Exception as e: self._log_event("ERROR", f"robots.txt sitemap link parsing error: {e}")
        return list(set(sitemap_links))

    def parse_rss_feed(self, feed_xml_content: str, feed_url: str) -> List[Dict[str, Any]]:
        if not feed_xml_content: return []
        parsed = feedparser.parse(feed_xml_content) # type: ignore[reportUnknownMemberType]
        if parsed.get("bozo", False): self._log_event("WARNING", f"Ill-formed RSS feed {feed_url}", {"exc": str(parsed.get("bozo_exception", "Unknown"))})
        items: List[Dict[str, Any]] = []
        for entry in parsed.entries:
            link = entry.get('link')
            if not link: continue
            date_struct = entry.get('published_parsed') or entry.get('updated_parsed')
            items.append({"id": entry.get('id', link), "link": link, "title": entry.get('title'),
                          "published_date_utc": self._parse_generic_date_to_utc(date_struct), # context_url removed
                          "source_feed_url": feed_url, "feed_entry_raw": dict(entry)})
        return items

    def parse_sitemap(self, sitemap_xml_content: str, sitemap_url: str) -> Optional[Dict[str, Any]]:
        if not sitemap_xml_content:
            self._log_event("WARNING", "Sitemap XML content is empty.", {"sitemap_url": sitemap_url})
            return None
        try:
            soup = BeautifulSoup(sitemap_xml_content, 'xml')
            sitemap_index_tag = soup.find('sitemapindex')
            if sitemap_index_tag:
                sitemap_urls: List[str] = []
                for sitemap_tag_entry in sitemap_index_tag.find_all('sitemap', recursive=False):
                    if not isinstance(sitemap_tag_entry, Tag): continue
                    loc_tag = sitemap_tag_entry.find('loc')
                    if loc_tag and isinstance(loc_tag, Tag) and loc_tag.string:
                        loc_text = loc_tag.string.strip()
                        if loc_text: sitemap_urls.append(loc_text)
                if sitemap_urls:
                    return {'type': 'sitemap_index', 'sitemap_urls': sitemap_urls, 'source_sitemap_url': sitemap_url}
                else: return None
            urlset_tag = soup.find('urlset')
            if urlset_tag:
                items_data: List[Dict[str, Any]] = []
                for url_tag_entry in urlset_tag.find_all('url', recursive=False):
                    if not isinstance(url_tag_entry, Tag): continue
                    loc_tag = url_tag_entry.find('loc')
                    if not (loc_tag and isinstance(loc_tag, Tag) and loc_tag.string and loc_tag.string.strip()):
                        continue
                    current_loc = loc_tag.string.strip()
                    lastmod_utc: Optional[datetime] = None
                    lastmod_tag = url_tag_entry.find('lastmod')
                    if lastmod_tag and isinstance(lastmod_tag, Tag) and lastmod_tag.string and lastmod_tag.string.strip():
                        lastmod_utc = self._parse_generic_date_to_utc(lastmod_tag.string.strip()) # context_url removed
                    items_data.append({'loc': current_loc, 'lastmod_utc': lastmod_utc, 'source_sitemap_url': sitemap_url})
                return {'type': 'urlset', 'items': items_data, 'source_sitemap_url': sitemap_url}
            self._log_event("WARNING", "Sitemap XML not recognized as index or urlset.", {"sitemap_url": sitemap_url})
            return None
        except Exception as e:
            self._log_event("ERROR", f"Exception parsing sitemap XML {sitemap_url}: {e}", {"exc_type": type(e).__name__})
            return None

    def parse_crawl_delay(self, robots_txt_content: str, target_user_agent:str ="*") -> Optional[float]:
        if not robots_txt_content: return None
        lines = robots_txt_content.splitlines(); specific_delay, wildcard_delay = None, None
        in_target_agent_block, in_wildcard_block = False, False
        for line in lines:
            line = line.strip().lower()
            if line.startswith('user-agent:'):
                agent = line.split(':',1)[1].strip()
                in_target_agent_block = (agent == target_user_agent.lower())
                in_wildcard_block = (agent == '*')
            elif line.startswith('crawl-delay:'):
                try:
                    delay = float(line.split(':',1)[1].strip())
                    if in_target_agent_block: specific_delay = delay; break
                    if in_wildcard_block: wildcard_delay = delay
                except ValueError: pass
        return specific_delay if specific_delay is not None else wildcard_delay

if __name__ == '__main__':
    pass
