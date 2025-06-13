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
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import httpx

try:
    from crawl4ai import AsyncWebCrawler, Url, CrawlerRunConfig
    from crawl4ai.filters import URLPatternFilter, ContentTypeFilter
    from crawl4ai.scorers import KeywordRelevanceScorer, PathDepthScorer, CompositeScorer
except ImportError:
    AsyncWebCrawler = None # type: ignore
    Url = None # type: ignore
    CrawlerRunConfig = None # type: ignore
    URLPatternFilter = None # type: ignore
    ContentTypeFilter = None # type: ignore
    KeywordRelevanceScorer = None # type: ignore
    PathDepthScorer = None # type: ignore
    CompositeScorer = None # type: ignore
    print("WARNING: Parser: crawl4ai components (AsyncWebCrawler, Url, CrawlerRunConfig, Filters, Scorers) not found, using placeholders. Functionality will be affected.")

# JsonCssExtractionStrategy is not used directly (handled by commenting out its import block)

import feedparser # type: ignore[reportMissingImports]
import extruct
from bs4 import BeautifulSoup, Tag
from dateutil import parser as dateutil_parser

try:
    from ..analyzer.structure_analyzer import StructureAnalyzer
except ImportError:
    StructureAnalyzer = None

from typing import Any, Dict, List, Optional, Union, Set # RobotFileParser is already imported


class Parser:
    def __init__(self, monitor_instance=None, planner_reference=None, structure_analyzer_instance=None):
        self.monitor = monitor_instance
        self.planner_ref = planner_reference
        self.structure_analyzer = structure_analyzer_instance
        self.robot_parsers: Dict[str, RobotFileParser] = {}

        if AsyncWebCrawler is None:
            self._log_event("ERROR", "Parser: crawl4ai.AsyncWebCrawler is not available. AI parsing will fail.")
            self.crawler = None
        else:
            try:
                self.crawler = AsyncWebCrawler()
                self._log_event("INFO", "Parser: crawl4ai AsyncWebCrawler initialized.")
            except Exception as e:
                self._log_event("ERROR", f"Parser: Failed to initialize crawl4ai AsyncWebCrawler: {e}")
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

    async def _parse_with_general_ai(self, html_content: str, url: str) -> Optional[Dict[str, Any]]:
        if not self.crawler or AsyncWebCrawler is None or Url is None or CrawlerRunConfig is None:
            self._log_event("ERROR", "crawl4ai components not available for general AI parsing.", {"url": url}); return None
        self._log_event("INFO", f"Attempting general AI (crawl4ai) for {url}")
        try:
            # Configure for single-page processing, not deep crawling.
            # Assuming max_depth=0 or similar tells it to only process the provided content.
            # The exact parameters for CrawlerRunConfig might need adjustment based on crawl4ai's API.
            config = CrawlerRunConfig(max_depth=0, max_pages=1)
            # AsyncWebCrawler's equivalent of 'read' is often 'arun' or similar.
            # It likely returns a list of results, even for a single URL.
            results = await self.crawler.arun(seed_url=Url(url=url, html_content=html_content), crawler_run_config=config)

            # Process the first result if available
            if results and results.results and (results.results[0].text or results.results[0].metadata):
                res = results.results[0]
                ai_data = {'title': res.metadata.get('title'), 'text': res.text, 'date': res.metadata.get('date'),
                           'authors': [res.metadata.get('author')] if res.metadata.get('author') else []}
                return self._normalize_extracted_data(ai_data, url, "general_ai")
            elif results and not results.results:
                 self._log_event("DEBUG", "General AI parsing returned no results.", {"url":url})
            else:
                 self._log_event("DEBUG", "General AI parsing result was empty or lacked text/metadata.", {"url":url})

        except Exception as e: self._log_event("ERROR", f"General AI parsing error: {e}", {"url":url});
        return None

    async def parse_content(self, html_content: str, url: str, source_config: Dict[str, Any]) -> Dict[str, Any]:
        source_config = source_config or {}
        source_name = source_config.get("name", "UnknownSource")
        self._log_event("INFO", f"Starting new article extraction strategy for {url}", {"source": source_name})

        final_result: Optional[Dict[str, Any]] = None
        extraction_schema_used: Optional[Any] = None # Can be selectors dict or string like "schema.org"

        # 1. Schema.org First
        self._log_event("DEBUG", f"Attempting Schema.org parsing for {url}")
        result_schema = self._parse_with_schema_org(html_content, url)
        if self._is_data_sufficient(result_schema):
            final_result = result_schema
            extraction_schema_used = "schema.org"
            self._log_event("INFO", f"Sufficient data extracted using Schema.org for {url}")
        else:
            self._log_event("DEBUG", f"Schema.org parsing did not yield sufficient data for {url}")

        # 2. Custom/LLM Selectors (if Schema.org failed or was insufficient)
        if not self._is_data_sufficient(final_result):
            self._log_event("DEBUG", f"Schema.org insufficient, proceeding to custom/LLM selectors for {url}")
            custom_selectors = source_config.get("extraction_selectors")
            # Determine if LLM analysis should be considered
            # It's needed if:
            #   - No custom selectors exist OR custom selectors are marked as empty (e.g. from a previous failed LLM run)
            #   - AND llm_analysis_pending flag is true for the source
            #   (StructureAnalyzer and planner_ref must be available for LLM to run)
            llm_can_run = bool(self.structure_analyzer and self.planner_ref and StructureAnalyzer is not None)

            needs_llm_analysis = (not custom_selectors or custom_selectors.get("_isEmpty", False)) and \
                                 source_config.get("llm_analysis_pending", True)

            if custom_selectors and not custom_selectors.get("_isEmpty", False):
                self._log_event("INFO", f"Attempting extraction with existing custom CSS selectors for {url}")
                result_custom = self._parse_with_custom_selectors(html_content, url, source_config)
                if self._is_data_sufficient(result_custom):
                    final_result = result_custom
                    extraction_schema_used = custom_selectors # Store the actual selectors used
                    self._log_event("INFO", f"Sufficient data extracted using existing custom CSS for {url}")
                else:
                    self._log_event("DEBUG", f"Existing custom CSS selectors did not yield sufficient data for {url}")

            # If current selectors (if any) failed, and LLM is an option and hasn't failed permanently before for this source
            if not self._is_data_sufficient(final_result) and needs_llm_analysis:
                if llm_can_run:
                    self._log_event("INFO", f"Attempting LLM selector generation for {source_name} ({url}).")
                    # Placeholder for potentially checking/using domain-specific selectors from planner_ref first
                    # e.g., domain_specific_selectors = self.planner_ref.get_domain_specific_selectors(url)
                    # if domain_specific_selectors: new_selectors = domain_specific_selectors ...
                    new_selectors = self.structure_analyzer.generate_extraction_selectors(url, html_content)

                    if new_selectors and not new_selectors.get("_isEmpty", False) : # Check if new_selectors are valid
                        self._log_event("INFO", f"LLM generated new selectors for {url}. Re-parsing.", {"url": url})
                        if self.planner_ref:
                             self.planner_ref.update_source_extraction_selectors(source_name, new_selectors)
                             # Also mark llm_analysis_pending as False because we have new selectors
                             self.planner_ref.set_llm_analysis_flag(source_name, False, generated_new_selectors=True)
                             if hasattr(self.planner_ref, 'save_config'): self.planner_ref.save_config()

                        current_source_config_for_llm_parse = {**source_config, "extraction_selectors": new_selectors}
                        result_after_llm = self._parse_with_custom_selectors(html_content, url, current_source_config_for_llm_parse)

                        if self._is_data_sufficient(result_after_llm):
                            final_result = result_after_llm
                            extraction_schema_used = new_selectors # Store the new selectors
                            self._log_event("INFO", f"Sufficient data extracted using LLM-generated selectors for {url}")
                        else:
                            self._log_event("DEBUG", f"LLM-generated selectors did not yield sufficient data for {url}")
                            # Optional: If LLM selectors fail immediately, consider them "bad"
                            # and potentially revert or mark them as _isEmpty. For now, they are saved.
                    elif new_selectors and new_selectors.get("_isEmpty", False):
                        self._log_event("WARNING", f"LLM indicated no good selectors could be generated for {url}. Marking to prevent retries.")
                        if self.planner_ref:
                            self.planner_ref.update_source_extraction_selectors(source_name, new_selectors) # Save the _isEmpty state
                            self.planner_ref.set_llm_analysis_flag(source_name, False, generated_new_selectors=False)
                            if hasattr(self.planner_ref, 'save_config'): self.planner_ref.save_config()
                    else: # new_selectors is None or some other falsey value
                        self._log_event("WARNING", f"LLM selector generation failed or returned no selectors for {url}. Marking to prevent retries.")
                        if self.planner_ref:
                            self.planner_ref.set_llm_analysis_flag(source_name, False, generated_new_selectors=False)
                            if hasattr(self.planner_ref, 'save_config'): self.planner_ref.save_config()
                else: # llm_can_run is false
                     self._log_event("WARNING", f"LLM components (StructureAnalyzer or Planner reference) not available for {url}. Cannot generate selectors.", {"url": url})
            elif not self._is_data_sufficient(final_result) and needs_llm_analysis and not llm_can_run:
                 self._log_event("WARNING", f"LLM analysis was needed for {url} but components are not available.", {"url": url})


        # 3. Fallback to General AI (if other methods failed or were insufficient)
        if not self._is_data_sufficient(final_result):
            self._log_event("INFO", f"Falling back to General AI parsing for {url} as other methods were insufficient.")
            result_general_ai = await self._parse_with_general_ai(html_content, url)
            if self._is_data_sufficient(result_general_ai):
                final_result = result_general_ai
                extraction_schema_used = "general_ai"
                self._log_event("INFO", f"Sufficient data extracted using General AI for {url}")
            elif result_general_ai and not final_result: # Some data, even if not "sufficient" by main criteria
                final_result = result_general_ai # Use partial data if nothing else was better
                extraction_schema_used = "general_ai_partial"
                self._log_event("DEBUG", f"Partial data extracted using General AI for {url} (used as best available).")
            else:
                self._log_event("DEBUG", f"General AI parsing did not yield sufficient data for {url}")

        # 4. Finalize and Return
        timestamp = datetime.now(timezone.utc).isoformat()

        if final_result and self._is_data_sufficient(final_result):
            # _normalize_extracted_data adds 'extraction_method'. We add more specific schema and timestamp.
            output = {
                **final_result,
                "extraction_schema_details": extraction_schema_used, # Renamed for clarity
                "timestamp_utc": timestamp
            }
            self._log_event("INFO", f"Successfully extracted sufficient data for {url}", {"method_used_final": final_result.get('extraction_method'), "schema_details": extraction_schema_used})
            return output
        else:
            self._log_event("WARNING", f"No sufficient data extracted for {url} after all attempts.", {"url": url})
            # Return a standardized empty/error structure, including the method from the best partial result if available
            base_method = final_result.get('extraction_method') if final_result else "no_data_found"
            return {
                "title": final_result.get('title') if final_result else None,
                "text": final_result.get('text') if final_result else None,
                "published_date_utc": final_result.get('published_date_utc') if final_result else None,
                "authors": final_result.get('authors', []) if final_result else [],
                "url": url,
                "extraction_method": base_method,
                "extraction_schema_details": extraction_schema_used if final_result else None, # Renamed
                "timestamp_utc": timestamp
            }

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

    async def fetch_robots_txt(self, domain_url: str) -> Optional[str]:
        """
        Fetches the robots.txt file for a given domain.
        """
        robots_url = urljoin(domain_url, "/robots.txt")
        self._log_event("INFO", f"Fetching robots.txt from {robots_url}")
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
                response = await client.get(robots_url)
                if response.status_code == 200:
                    self._log_event("INFO", f"Successfully fetched robots.txt for {domain_url}", {"status_code": response.status_code})
                    return response.text
                elif response.status_code == 404:
                    self._log_event("INFO", f"robots.txt not found for {domain_url}", {"status_code": response.status_code})
                    return None
                else:
                    self._log_event("WARNING", f"Failed to fetch robots.txt for {domain_url}", {"status_code": response.status_code})
                    return None
        except httpx.RequestError as e:
            self._log_event("ERROR", f"Network error fetching robots.txt for {domain_url}: {e}", {"url": robots_url})
            return None
        except Exception as e:
            self._log_event("ERROR", f"Unexpected error fetching robots.txt for {domain_url}: {e}", {"url": robots_url, "exc_type": type(e).__name__})
            return None

    def parse_robots_content(self, robots_content: str, domain_url: str) -> RobotFileParser:
        """
        Parses the content of a robots.txt file.
        """
        rfp = RobotFileParser(url=domain_url) # Provide domain_url as per documentation for context
        rfp.parse(robots_content.splitlines())
        self._log_event("INFO", f"Parsed robots.txt content for {domain_url}")
        # Further analysis like rfp.disallow_all or rfp.allow_all can be logged if needed
        return rfp

    async def handle_robots_txt(self, seed_url: str) -> Optional[RobotFileParser]:
        """
        Fetches, parses, and stores the RobotFileParser instance for a given URL's domain.
        """
        try:
            parsed_url = urlparse(seed_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                self._log_event("ERROR", "Invalid seed_url for robots.txt handling", {"seed_url": seed_url})
                return None
            domain_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        except Exception as e:
            self._log_event("ERROR", f"Error parsing seed_url for robots.txt handling: {e}", {"seed_url": seed_url})
            return None

        if domain_url in self.robot_parsers:
            self._log_event("DEBUG", f"Reusing cached RobotFileParser for {domain_url}")
            return self.robot_parsers[domain_url]

        robots_content = await self.fetch_robots_txt(domain_url)
        if robots_content:
            try:
                rfp = self.parse_robots_content(robots_content, domain_url)
                self.robot_parsers[domain_url] = rfp
                # Example: Log disallowed paths for common user-agent
                # This is illustrative; can_fetch will be the primary use.
                # For now, just confirm it's parsed.
                self._log_event("INFO", f"robots.txt processed for {domain_url}. Rules now available.", {"disallow_all": rfp.disallow_all("*"), "allow_all": rfp.allow_all("*")})
                return rfp
            except Exception as e:
                self._log_event("ERROR", f"Error parsing robots.txt content for {domain_url}: {e}")
                return None
        else:
            # Store a default permissive parser or None if robots.txt is absent or errored
            # For now, if robots.txt is not found or error, we assume allow all by not having specific rules.
            # A more robust approach might be to create a default RobotFileParser that allows everything.
            # For now, we'll just log and return None, implying no restrictions found or error.
            # Or, we can cache a "None" to indicate it was checked and not found.
            # self.robot_parsers[domain_url] = None # Cache the fact that it was not found/errored
            self._log_event("INFO", f"No robots.txt found or error fetching for {domain_url}. Assuming permissive access.", {"domain": domain_url})
            # Create a default, permissive RobotFileParser instance
            default_rfp = RobotFileParser(url=domain_url)
            default_rfp.allow_all = True # Explicitly set allow all
            self.robot_parsers[domain_url] = default_rfp # Cache this default one
            return default_rfp

    def extract_and_filter_links(
        self,
        base_url: str,
        html_content: str,
        robot_parser: Optional[RobotFileParser],
        respect_robots: bool = True
    ) -> List[str]:
        """
        Extracts links from HTML content, resolves them to absolute URLs,
        and filters them based on robots.txt rules and predefined patterns.
        """
        if not html_content:
            self._log_event("DEBUG", "No HTML content provided to extract_and_filter_links.", {"base_url": base_url})
            return []

        initial_links: List[str] = []
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            for anchor_tag in soup.find_all('a', href=True):
                href = anchor_tag['href']
                if href and isinstance(href, str) and not href.startswith(('javascript:', 'mailto:', '#')):
                    try:
                        absolute_url = urljoin(base_url, href.strip())
                        # Basic validation of the joined URL structure
                        parsed_absolute_url = urlparse(absolute_url)
                        if parsed_absolute_url.scheme and parsed_absolute_url.netloc:
                             initial_links.append(absolute_url)
                        else:
                            self._log_event("DEBUG", f"Skipping malformed URL after join: {absolute_url}", {"original_href": href, "base_url": base_url})
                    except Exception as e: # Catch errors during urljoin or parsing
                        self._log_event("DEBUG", f"Error joining or parsing URL: {href}", {"base_url": base_url, "error": str(e)})
        except Exception as e:
            self._log_event("ERROR", f"Error parsing HTML content for link extraction: {e}", {"base_url": base_url})
            return [] # Return empty if HTML parsing fails

        # Deduplicate after initial extraction
        extracted_links = sorted(list(set(initial_links)))
        self._log_event("DEBUG", f"Extracted {len(extracted_links)} unique links initially.", {"base_url": base_url, "count_before_robots": len(extracted_links)})

        # Filter links based on robots.txt
        links_after_robots = []
        if respect_robots and robot_parser:
            for link in extracted_links:
                try:
                    if robot_parser.can_fetch("*", link):
                        links_after_robots.append(link)
                    else:
                        self._log_event("DEBUG", f"Link disallowed by robots.txt: {link}", {"base_url": base_url})
                except Exception as e: # Catch potential errors in can_fetch implementations
                    self._log_event("WARNING", f"Error during robots.txt can_fetch for link {link}: {e}", {"base_url": base_url})
                    links_after_robots.append(link) # Default to allowing if can_fetch errors
            self._log_event("DEBUG", f"Retained {len(links_after_robots)} links after robots.txt filtering.", {"base_url": base_url, "count_after_robots": len(links_after_robots)})
        else:
            links_after_robots = extracted_links
            if respect_robots and not robot_parser:
                 self._log_event("DEBUG", "robots.txt respect enabled but no parser provided. Skipping robots filter.", {"base_url": base_url})


        # Filter links with URLPatternFilter
        links_after_pattern_filter = []
        if URLPatternFilter is not None: # Check if class was imported
            # Define a list of exclusion patterns
            exclude_patterns = [
                r"/login", r"/signin", r"/register", r"/signup",
                r"/tag/", r"/user/", r"/profile/", r"/account/",
                r"/search", r"/privacy", r"/terms", r"/contact", r"/about",
                r"/\?replytocom=", r"/wp-json/", r"/feed/$", r"/comments/feed/$",
                r"\.pdf$", r"\.zip$", r"\.jpg$", r"\.jpeg$", r"\.png$", r"\.gif$", r"\.css$", r"\.js$",
                r"archive\.org/web/" # Example: exclude archive.org wayback machine links
            ]
            try:
                # Assuming URLPatternFilter expects list of strings. If it needs Url objects:
                # url_objects_to_filter = [Url(url=link_str) for link_str in links_after_robots]
                # filtered_url_objects = url_filter.filter(url_objects_to_filter)
                # links_after_pattern_filter = [uo.url for uo in filtered_url_objects]

                # Current assumption: URLPatternFilter takes list of strings and returns list of strings
                url_filter = URLPatternFilter(patterns=exclude_patterns, exclude=True) # exclude=True means remove matching patterns
                links_after_pattern_filter = url_filter.filter(links_after_robots)
                self._log_event("DEBUG", f"Retained {len(links_after_pattern_filter)} links after URLPatternFilter.", {"base_url": base_url, "count_after_pattern": len(links_after_pattern_filter)})
            except Exception as e:
                self._log_event("ERROR", f"Error applying URLPatternFilter: {e}", {"base_url": base_url})
                links_after_pattern_filter = links_after_robots # Fallback to pre-filter list
        else:
            self._log_event("WARNING", "URLPatternFilter not available, skipping pattern filtering.", {"base_url": base_url})
            links_after_pattern_filter = links_after_robots


        # Final deduplication
        final_links = sorted(list(set(links_after_pattern_filter)))
        self._log_event("INFO", f"Link extraction complete for {base_url}. Initial: {len(extracted_links)}, After robots: {len(links_after_robots)}, After patterns: {len(links_after_pattern_filter)}, Final: {len(final_links)}",
                        {"base_url": base_url})

        return final_links

    def score_and_select_links(
        self,
        links: List[str],
        top_n: Optional[int] = 10,
        relevance_threshold: Optional[float] = None
    ) -> List[str]:
        """
        Scores links based on keywords and path depth, then selects a subset.
        """
        if not links:
            self._log_event("DEBUG", "No links provided to score_and_select_links.")
            return []

        num_initial_links = len(links)
        self._log_event("DEBUG", f"Starting link scoring for {num_initial_links} links.", {"top_n": top_n, "relevance_threshold": relevance_threshold})

        # Check if crawl4ai components are available
        if not all([Url, KeywordRelevanceScorer, PathDepthScorer, CompositeScorer]):
            self._log_event("WARNING", "crawl4ai scorer components not available. Skipping scoring.",
                            {"available": {"Url": Url is not None, "KeywordRelevanceScorer": KeywordRelevanceScorer is not None,
                                           "PathDepthScorer": PathDepthScorer is not None, "CompositeScorer": CompositeScorer is not None}})
            # Fallback: return top_n links without scoring if top_n is specified, else all links
            return links[:top_n] if top_n is not None else links

        try:
            # Convert URL strings to Url objects
            try:
                url_objects = [Url(url=link_str) for link_str in links]
            except Exception as e:
                self._log_event("ERROR", f"Failed to convert link strings to Url objects: {e}", {"links_sample": links[:5]})
                # Fallback if Url object creation fails
                return links[:top_n] if top_n is not None else links

            # Initialize Scorers
            # Keywords can be expanded or customized based on typical content sought
            keyword_scorer = KeywordRelevanceScorer(
                keywords=["news", "article", "story", "post", "blog", "report", "update", "analysis", "breaking", "latest",
                          "headline", "summary", "release", "bulletin", "journal", "chronicle", "review", "insight",
                          # Date related keywords could be useful if they appear in paths
                          "2023", "2024", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
                weight=0.6
            )
            path_depth_scorer = PathDepthScorer(weight=0.4) # Favor shallower paths
            composite_scorer = CompositeScorer(scorers=[keyword_scorer, path_depth_scorer])

            # Score Links
            # Assuming composite_scorer.score modifies Url objects in-place by adding a .score attribute
            # or returns new Url objects with .score. If it returns (score, Url_object) tuples, this needs adjustment.
            # For now, let's assume it returns a list of Url objects, each with a .score attribute.
            # Based on typical crawl4ai patterns, score() might return a list of the same Url objects, now scored.
            scored_url_objects = composite_scorer.score(url_objects) # This might modify url_objects or return a new list

            # Sort Url objects by score in descending order
            # Ensure objects have a 'score' attribute; provide default if not
            for uo in scored_url_objects:
                if not hasattr(uo, 'score') or uo.score is None:
                    uo.score = 0.0 # Default score if not set by scorer

            scored_url_objects.sort(key=lambda uo: uo.score, reverse=True)

            selected_urls = scored_url_objects
            num_after_scoring = len(selected_urls)

            # Filter by relevance_threshold
            if relevance_threshold is not None:
                selected_urls = [uo for uo in selected_urls if uo.score >= relevance_threshold]
                self._log_event("DEBUG", f"{len(selected_urls)} links after relevance threshold ({relevance_threshold}). Originally {num_after_scoring}.",
                                {"threshold": relevance_threshold, "retained_count": len(selected_urls)})

            num_after_threshold = len(selected_urls)

            # Select top_n
            if top_n is not None:
                selected_urls = selected_urls[:top_n]
                self._log_event("DEBUG", f"Selected top {len(selected_urls)} links (max {top_n}). Originally {num_after_threshold}.",
                                {"top_n": top_n, "final_selected_count": len(selected_urls)})


            # Convert selected Url objects back to URL strings
            final_link_strings = [uo.url for uo in selected_urls]

            self._log_event("INFO", f"Link scoring and selection complete. Initial: {num_initial_links}, Scored: {num_after_scoring}, After threshold: {num_after_threshold}, Final selected: {len(final_link_strings)}",
                            {"top_n": top_n, "relevance_threshold": relevance_threshold})

            return final_link_strings

        except Exception as e:
            self._log_event("ERROR", f"Error during link scoring and selection: {e}",
                            {"exc_type": type(e).__name__, "initial_link_count": num_initial_links})
            # Fallback in case of any other error during scoring
            return links[:top_n] if top_n is not None else links

    async def filter_by_content_type(self, links: List[str]) -> List[str]:
        """
        Filters a list of URLs based on their Content-Type header.
        Only allows types like 'text/html' or 'text/plain'.
        """
        if not links:
            self._log_event("DEBUG", "No links provided to filter_by_content_type.")
            return []

        num_initial_links = len(links)
        self._log_event("DEBUG", f"Starting content-type filtering for {num_initial_links} links.")

        if ContentTypeFilter is None:
            self._log_event("WARNING", "ContentTypeFilter not available. Skipping content-type filtering.")
            return links

        # Initialize ContentTypeFilter with allowed types
        # These are common types for web pages; can be expanded (e.g., application/xhtml+xml)
        try:
            content_type_filter = ContentTypeFilter(allowed_types=["text/html", "text/plain", "application/xhtml+xml"])
        except Exception as e:
            self._log_event("ERROR", f"Failed to initialize ContentTypeFilter: {e}. Skipping content-type filtering.")
            return links

        valid_links: List[str] = []

        # Using a single AsyncClient for all requests
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            for link_url_str in links:
                try:
                    self._log_event("DEBUG", f"Checking content-type for: {link_url_str}")
                    response = await client.head(link_url_str)
                    response.raise_for_status() # Raise an exception for 4XX or 5XX status codes

                    content_type_header = response.headers.get('content-type')
                    if not content_type_header:
                        self._log_event("DEBUG", f"No content-type header for {link_url_str}. Skipping.", {"url": link_url_str})
                        continue

                    # Normalize content type: lowercase and take the part before any semicolon (e.g., charset)
                    normalized_content_type = content_type_header.lower().split(';')[0].strip()

                    # Use ContentTypeFilter.is_allowed_by_type (or similar method)
                    # Assuming is_allowed_by_type takes the string content type.
                    # If ContentTypeFilter is designed to work on Url objects with pre-fetched headers,
                    # the call might be different, e.g., content_type_filter.filter([Url(url=link_url_str, headers=response.headers)])
                    # For now, proceeding with the assumption of a direct check method.
                    if content_type_filter.is_allowed_by_type(normalized_content_type):
                        valid_links.append(link_url_str)
                        self._log_event("DEBUG", f"Allowed content-type '{normalized_content_type}' for {link_url_str}", {"url": link_url_str})
                    else:
                        self._log_event("DEBUG", f"Disallowed content-type '{normalized_content_type}' for {link_url_str}", {"url": link_url_str})

                except httpx.HTTPStatusError as e:
                    self._log_event("DEBUG", f"HTTP status error checking content-type for {link_url_str}: {e.response.status_code}", {"url": link_url_str, "error": str(e)})
                except httpx.RequestError as e: # Covers network errors, timeouts, etc.
                    self._log_event("DEBUG", f"Request error checking content-type for {link_url_str}: {type(e).__name__}", {"url": link_url_str, "error": str(e)})
                except Exception as e: # Catch any other unexpected errors
                    self._log_event("WARNING", f"Unexpected error checking content-type for {link_url_str}: {e}", {"url": link_url_str, "exc_type": type(e).__name__})

        num_final_links = len(valid_links)
        self._log_event("INFO", f"Content-type filtering complete. Initial: {num_initial_links}, Final allowed: {num_final_links}",
                        {"initial_count": num_initial_links, "final_count": num_final_links})

        return valid_links

    async def process_seed_url(
        self,
        seed_url_str: str,
        source_config: Dict[str, Any],
        respect_robots: bool = True,
        top_n_links: Optional[int] = 10,
        relevance_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Orchestrates the full processing pipeline for a single seed URL:
        - Fetches and parses robots.txt.
        - Fetches the seed URL.
        - Extracts, filters, scores, and selects links from the seed URL's content.
        - Fetches and parses content from these selected article links.
        Returns a list of extracted article data.
        """
        extracted_articles: List[Dict[str, Any]] = []
        self._log_event("INFO", f"Starting processing for seed URL: {seed_url_str}",
                        {"source_name": source_config.get("name", "Unknown"), "respect_robots": respect_robots,
                         "top_n_links": top_n_links, "relevance_threshold": relevance_threshold})

        if not self.crawler:
            self._log_event("ERROR", "AsyncWebCrawler (self.crawler) not initialized. Cannot process seed URL.", {"seed_url": seed_url_str})
            return extracted_articles

        # 1. Handle robots.txt
        robot_parser: Optional[RobotFileParser] = await self.handle_robots_txt(seed_url_str)
        if respect_robots and robot_parser and not robot_parser.can_fetch("*", seed_url_str):
            self._log_event("WARNING", f"Seed URL {seed_url_str} is disallowed by robots.txt. Skipping processing.", {"seed_url": seed_url_str})
            return extracted_articles

        # 2. Fetch content of seed_url_str
        seed_html_content: Optional[str] = None
        try:
            self._log_event("DEBUG", f"Fetching content for seed URL: {seed_url_str}")
            # Assuming CrawlerRunConfig for a single page, non-recursive fetch
            run_config = CrawlerRunConfig(max_depth=0, max_pages=1, store_content=True, allow_redirects=True)
            page_data_list = await self.crawler.arun(seed_url=Url(url=seed_url_str), crawler_run_config=run_config)

            if page_data_list and page_data_list.results and page_data_list.results[0].content:
                seed_html_content = page_data_list.results[0].content
                # Update seed_url_str to the final URL after redirects, if any
                final_url_after_redirect = page_data_list.results[0].url
                if final_url_after_redirect != seed_url_str:
                    self._log_event("INFO", f"Seed URL redirected from {seed_url_str} to {final_url_after_redirect}", {"original_seed": seed_url_str, "final_url": final_url_after_redirect})
                    seed_url_str = final_url_after_redirect # Use the final URL as the base for further operations
                self._log_event("DEBUG", f"Successfully fetched content for seed URL: {seed_url_str}")
            else:
                self._log_event("WARNING", f"Failed to fetch content or content was empty for seed URL: {seed_url_str}", {"seed_url": seed_url_str})
                return extracted_articles
        except Exception as e:
            self._log_event("ERROR", f"Exception while fetching content for seed URL {seed_url_str}: {e}", {"seed_url": seed_url_str, "exc_type": type(e).__name__})
            return extracted_articles

        if not seed_html_content: # Should be caught by previous block, but as a safeguard
            self._log_event("ERROR", f"Seed HTML content is None after fetch attempt for {seed_url_str}. Aborting.", {"seed_url": seed_url_str})
            return extracted_articles

        # 3. Link Discovery and Filtering from Seed Page
        self._log_event("DEBUG", f"Extracting links from seed page: {seed_url_str}")
        candidate_links = self.extract_and_filter_links(
            base_url=seed_url_str,  # Use potentially updated seed_url_str after redirects
            html_content=seed_html_content,
            robot_parser=robot_parser,
            respect_robots=respect_robots
        )
        self._log_event("INFO", f"Extracted {len(candidate_links)} candidate links from {seed_url_str}.", {"count": len(candidate_links)})

        scored_links = self.score_and_select_links(
            links=candidate_links,
            top_n=top_n_links,
            relevance_threshold=relevance_threshold
        )
        self._log_event("INFO", f"Scored and selected {len(scored_links)} links (top_n={top_n_links}, threshold={relevance_threshold}).", {"count": len(scored_links)})

        final_article_urls = await self.filter_by_content_type(links=scored_links)
        self._log_event("INFO", f"Content-type filtering resulted in {len(final_article_urls)} final article URLs.", {"count": len(final_article_urls)})

        if not final_article_urls:
            self._log_event("INFO", f"No suitable article links found or selected from seed URL {seed_url_str} after all filtering stages.")
            # Option: Parse the seed URL itself as an article if no links are found/selected
            # This behavior can be added if desired. For now, we only process discovered links.

        # 4. Process Selected Article Links
        for article_url_str in final_article_urls:
            try:
                self._log_event("INFO", f"Processing discovered article link: {article_url_str}", {"source_seed": seed_url_str})

                # Check robots.txt for each article_url_str individually as well if respect_robots is True
                # This is because extract_and_filter_links already does this, but good for defense-in-depth
                # or if links came from a source not yet checked by robots.txt (not the case here).
                # For this flow, links are already robot-checked by extract_and_filter_links.

                article_html_content: Optional[str] = None
                article_final_url = article_url_str # Initialize with the URL to be processed

                article_page_data_list = await self.crawler.arun(
                    seed_url=Url(url=article_url_str),
                    crawler_run_config=CrawlerRunConfig(max_depth=0, max_pages=1, store_content=True, allow_redirects=True)
                )

                if article_page_data_list and article_page_data_list.results and article_page_data_list.results[0].content:
                    article_html_content = article_page_data_list.results[0].content
                    article_final_url = article_page_data_list.results[0].url # Update URL if redirected
                    if article_final_url != article_url_str:
                         self._log_event("DEBUG", f"Article URL redirected from {article_url_str} to {article_final_url}")
                else:
                    self._log_event("WARNING", f"Failed to fetch content for article link: {article_url_str}", {"url": article_url_str})
                    continue # Skip to next article if content fetch fails

                if article_html_content:
                    article_data = await self.parse_content(
                        html_content=article_html_content,
                        url=article_final_url, # Use the final URL after potential redirects
                        source_config=source_config
                    )
                    # Check for sufficiency based on primary fields (title and text)
                    if article_data and article_data.get("title") and article_data.get("text"):
                        extracted_articles.append(article_data)
                        self._log_event("INFO", f"Successfully extracted article from {article_final_url}",
                                        {"title": article_data.get("title"), "original_url": article_url_str})
                    else:
                        self._log_event("WARNING", f"No sufficient data extracted from {article_final_url} after parsing.",
                                        {"url": article_final_url, "original_url": article_url_str})
            except Exception as e:
                self._log_event("ERROR", f"Error processing article link {article_url_str}: {e}",
                                {"url": article_url_str, "exc_type": type(e).__name__, "error_details": str(e)})

        self._log_event("INFO", f"Completed processing for seed URL {seed_url_str}. Extracted {len(extracted_articles)} articles from discovered links.",
                        {"seed_url": seed_url_str, "extracted_count": len(extracted_articles)})
        return extracted_articles


if __name__ == '__main__':
    pass
