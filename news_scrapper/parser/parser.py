"""
This module contains the Parser component.
The Parser is responsible for transforming raw HTML/JSON into clean, structured data.
It uses multiple strategies: custom CSS selectors, Schema.org (via extruct),
general AI (crawl4ai), and can trigger LLM-based selector generation.
"""
import json
import extruct # For Schema.org and other microdata
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import urllib.parse # For urljoin if needed by schema data
import time # For time.mktime for feedparser date conversion

from crawl4ai import WebCrawler
from crawl4ai.web_crawler import Url
# JsonCssExtractionStrategy might not be used directly if WebCrawler.read doesn't take it for pre-fetched HTML
# from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

try:
    from ..analyzer.structure_analyzer import StructureAnalyzer
    # from ..planner.planner import Planner # Avoid full import for type hint if possible
except ImportError:
    StructureAnalyzer = None
    # Planner = None

from dateutil import parser as dateutil_parser


class Parser:
    def __init__(self, monitor_instance=None, planner_reference=None, structure_analyzer_instance=None):
        self.monitor = monitor_instance
        self.planner_ref = planner_reference
        self.structure_analyzer = structure_analyzer_instance

        try:
            self.crawler = WebCrawler()
            self._log_event("INFO", "Parser: crawl4ai WebCrawler initialized.")
        except Exception as e:
            self._log_event("ERROR", f"Parser: Failed to initialize crawl4ai WebCrawler: {e}")
            self.crawler = None

        if self.planner_ref is None:
            self._log_event("WARNING", "Parser: Planner reference not provided. Cannot update source configs with LLM selectors.")
        if self.structure_analyzer is None:
            self._log_event("WARNING", "Parser: StructureAnalyzer not provided. LLM selector generation disabled.")

    def _log_event(self, level, message, details=None):
        if self.monitor: self.monitor.log_event(level.upper(), message, details)
        else: print(f"[{level.upper()}] {message}{(' | ' + json.dumps(details)) if details else ''}")

    def _parse_generic_date_to_utc(self, date_input, context_url="N/A"):
        if date_input is None: return None
        if isinstance(date_input, datetime):
            return date_input.astimezone(timezone.utc) if date_input.tzinfo else date_input.replace(tzinfo=timezone.utc)
        if isinstance(date_input, str):
            try:
                dt = dateutil_parser.parse(date_input)
                return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError, OverflowError): return None
        if isinstance(date_input, time.struct_time):
            try: return datetime.fromtimestamp(time.mktime(date_input), tz=timezone.utc)
            except Exception: return None
        return None

    def _is_data_sufficient(self, parsed_data_dict):
        if not parsed_data_dict: return False
        return bool(parsed_data_dict.get('title') and parsed_data_dict.get('text'))

    def _normalize_extracted_data(self, data_dict, source_url, extraction_method_used):
        if not isinstance(data_dict, dict): data_dict = {}
        title = data_dict.get('title') or data_dict.get('headline')
        text = data_dict.get('text') or data_dict.get('content') or data_dict.get('articleBody')
        raw_date = data_dict.get('published_date_utc') or data_dict.get('datePublished') or \
                   data_dict.get('dateModified') or data_dict.get('date') or data_dict.get('published_time')
        published_date_utc = self._parse_generic_date_to_utc(raw_date, source_url)
        authors_data = data_dict.get('authors') or data_dict.get('author')
        authors_list = []
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

    def _parse_with_custom_selectors(self, html_content, url, source_config):
        selectors = source_config.get("extraction_selectors")
        if not selectors or not isinstance(selectors, dict): return None

        strategy_map = { # Map our config keys to common output keys
            "title": selectors.get("article_title_selector"),
            "text": selectors.get("article_content_selector"),
            "authors": selectors.get("article_author_selector"), # Assuming it might be a list
            "date": selectors.get("article_date_selector")
        }
        # Filter out selectors that are None or empty strings
        active_selectors = {k: v for k, v in strategy_map.items() if v and str(v).strip()}
        if not active_selectors: self._log_event("DEBUG", "No active custom selectors found after filtering.", {"url": url}); return None

        self._log_event("INFO", f"Attempting extraction with custom CSS for {url}", {"selectors": active_selectors})
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            extracted_data = {}
            for field, selector in active_selectors.items():
                elements = soup.select(selector)
                if elements:
                    if field == "text": extracted_data[field] = "\n".join([el.get_text(separator="\n", strip=True) for el in elements])
                    elif field == "authors": extracted_data[field] = [el.get_text(strip=True) for el in elements]
                    elif field == "date": extracted_data[field] = elements[0].get('datetime', elements[0].get_text(strip=True))
                    else: extracted_data[field] = elements[0].get_text(strip=True)
            return self._normalize_extracted_data(extracted_data, url, "custom_css") if extracted_data else None
        except Exception as e: self._log_event("ERROR", f"Custom CSS parsing error for {url}: {e}", {"selectors": active_selectors}); return None

    def _parse_with_schema_org(self, html_content, url):
        self._log_event("INFO", f"Attempting Schema.org (extruct) for {url}")
        try:
            data = extruct.extract(html_content, base_url=url, syntaxes=['json-ld', 'microdata'], uniform=True)
            for entry_type in ['json-ld', 'microdata']:
                for item in data.get(entry_type, []):
                    item_type_val = item.get('@type')
                    item_type = item_type_val[0] if isinstance(item_type_val, list) else item_type_val
                    if item_type in ['Article', 'NewsArticle', 'BlogPosting', 'WebPage']:
                        mapped = {'title': item.get('headline') or item.get('name'), 'text': item.get('articleBody') or item.get('text'),
                                  'authors': item.get('author'), 'date': item.get('datePublished') or item.get('dateModified'), 'url': item.get('url')}
                        if mapped.get('title') or mapped.get('text'):
                            return self._normalize_extracted_data(mapped, url, f"schema_org_{str(item_type).lower()}")
        except Exception as e: self._log_event("ERROR", f"Schema.org parsing error for {url}: {e}");
        return None

    def _parse_with_general_ai(self, html_content, url):
        if not self.crawler: self._log_event("ERROR", "crawl4ai not init for general AI parsing.", {"url": url}); return None
        self._log_event("INFO", f"Attempting general AI (crawl4ai) for {url}")
        try:
            res = self.crawler.read(Url(url=url, html_content=html_content))
            if res and (res.text or res.metadata):
                ai_data = {'title': res.metadata.get('title'), 'text': res.text, 'date': res.metadata.get('date'),
                           'authors': [res.metadata.get('author')] if res.metadata.get('author') else []}
                return self._normalize_extracted_data(ai_data, url, "general_ai")
        except Exception as e: self._log_event("ERROR", f"General AI parsing error for {url}: {e}");
        return None

    def parse_content(self, html_content, url, source_config):
        source_config = source_config or {} # Ensure it's a dict
        source_name = source_config.get("name", "UnknownSource")
        self._log_event("INFO", f"Multi-strategy parsing for {url}", {"source": source_name})
        final_result = None

        result_custom = self._parse_with_custom_selectors(html_content, url, source_config)
        if self._is_data_sufficient(result_custom): final_result = result_custom
        else:
            result_schema = self._parse_with_schema_org(html_content, url)
            if self._is_data_sufficient(result_schema): final_result = result_schema
            elif result_schema and not final_result: final_result = result_schema # Keep weak schema if nothing else

        result_general_ai = self._parse_with_general_ai(html_content, url)
        if not self._is_data_sufficient(final_result) and self._is_data_sufficient(result_general_ai):
            final_result = result_general_ai
        elif result_general_ai and not final_result: # If we have nothing, take AI's attempt
            final_result = result_general_ai

        needs_llm = (not source_config.get("extraction_selectors") or \
                     source_config.get("extraction_selectors",{}).get("_isEmpty",False)) and \
                    source_config.get("llm_analysis_pending", True)

        if needs_llm and (not final_result or not self._is_data_sufficient(final_result)):
            self._log_event("INFO", f"Attempting LLM selector generation for {source_name} ({url}).")
            if self.structure_analyzer and self.planner_ref:
                new_selectors = self.structure_analyzer.generate_extraction_selectors(url, html_content)
                if new_selectors:
                    self.planner_ref.update_source_extraction_selectors(source_name, new_selectors)
                    if hasattr(self.planner_ref, 'save_config'): self.planner_ref.save_config()
                    source_config["extraction_selectors"] = new_selectors # Update local copy
                    source_config["llm_analysis_pending"] = False
                    self._log_event("INFO", "Re-parsing with LLM-generated selectors.", {"url": url})
                    result_after_llm = self._parse_with_custom_selectors(html_content, url, source_config)
                    if self._is_data_sufficient(result_after_llm): final_result = result_after_llm
                else:
                    self.planner_ref.set_llm_analysis_flag(source_name, False)
                    if hasattr(self.planner_ref, 'save_config'): self.planner_ref.save_config()
            else: self._log_event("WARNING", "StructureAnalyzer or Planner ref missing for LLM generation.", {"url": url})

        return final_result if final_result else self._normalize_extracted_data({}, url, "no_data_found")

    # --- Existing methods (ensure _log_event is used if they had prints) ---
    def find_rss_links_in_html(self, html_content, base_url): # ... (no change from previous correct version) ...
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
    def find_sitemap_links_in_robots(self, robots_txt_content): # ... (no change from previous correct version) ...
        sitemap_links = []
        if not robots_txt_content: return sitemap_links
        try:
            for line in robots_txt_content.splitlines():
                if line.strip().lower().startswith('sitemap:'):
                    if parts := line.split(':', 1):
                        if len(parts) > 1 and parts[1].strip(): sitemap_links.append(parts[1].strip())
        except Exception as e: self._log_event("ERROR", f"robots.txt sitemap link parsing error: {e}")
        return list(set(sitemap_links))
    def parse_rss_feed(self, feed_xml_content, feed_url): # ... (no change from previous correct version, uses _parse_generic_date_to_utc) ...
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
                          "source_feed_url": feed_url, "feed_entry_raw": entry}) # Removed raw_entry for brevity
        return items
    def parse_sitemap(self, sitemap_xml_content, sitemap_url): # ... (no change from previous correct version, uses _parse_generic_date_to_utc) ...
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
    def parse_crawl_delay(self, robots_txt_content, target_user_agent="*"): # ... (no change from previous correct version) ...
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
                    if in_target_agent_block: specific_delay = delay; break # Specific takes precedence
                    if in_wildcard_block: wildcard_delay = delay
                except ValueError: pass
        return specific_delay if specific_delay is not None else wildcard_delay

if __name__ == '__main__': # Updated __main__ for new parser logic
    class MockPlannerLite:
        def update_source_extraction_selectors(self, sn, sel): print(f"MockPlanner: Updated selectors for {sn}: {sel}")
        def set_llm_analysis_flag(self, sn, flag): print(f"MockPlanner: Set LLM flag for {sn} to {flag}")
        def save_config(self): print("MockPlanner: Config saved.")
    class MockMonitorLite:
        def log_event(self,l,m,d=None): print(f"[{l}] {m} {json.dumps(d) if d else ''}")

    mock_analyzer = StructureAnalyzer(monitor_instance=MockMonitorLite())
    parser = Parser(monitor_instance=MockMonitorLite(), planner_reference=MockPlannerLite(), structure_analyzer_instance=mock_analyzer)

    sample_html = "<html><head><title>Test Article</title></head><body><article><h1>Main Title</h1><p>Some content here.</p><span class='author'>Author Name</span> <time datetime='2024-01-15T12:00:00Z'>Jan 15</time></article></body></html>"
    sample_url = "http://example.com/article_page_1"

    print("\n--- Test Case 1: No selectors, LLM pending, LLM success ---")
    cfg1 = {"name": "TestSite1", "llm_analysis_pending": True, "extraction_selectors": None}
    mock_analyzer.generate_extraction_selectors = MagicMock(return_value={"article_title_selector": "h1", "article_content_selector": "article p"})
    result1 = parser.parse_content(sample_html, sample_url, cfg1)
    print(f"Result 1 (Title): {result1.get('title')}, Method: {result1.get('extraction_method')}")
    assert result1.get('extraction_method') == "custom_css" # Re-parsed with LLM selectors

    print("\n--- Test Case 2: No selectors, LLM pending, LLM fails ---")
    cfg2 = {"name": "TestSite2", "llm_analysis_pending": True, "extraction_selectors": None}
    mock_analyzer.generate_extraction_selectors = MagicMock(return_value=None) # LLM fails
    # Mock general AI to return something
    parser.crawler.read = MagicMock(return_value=MagicMock(text="AI content", metadata={"title": "AI Title"}))
    result2 = parser.parse_content(sample_html, sample_url, cfg2)
    print(f"Result 2 (Title): {result2.get('title')}, Method: {result2.get('extraction_method')}")
    assert result2.get('extraction_method') == "general_ai" # Should use AI fallback

    print("\n--- Test Case 3: Existing good selectors, LLM pending is False ---")
    cfg3 = {"name": "TestSite3", "llm_analysis_pending": False,
            "extraction_selectors": {"article_title_selector": "h1", "article_content_selector": "article p"}}
    mock_analyzer.generate_extraction_selectors = MagicMock() # Reset mock
    result3 = parser.parse_content(sample_html, sample_url, cfg3)
    print(f"Result 3 (Title): {result3.get('title')}, Method: {result3.get('extraction_method')}")
    mock_analyzer.generate_extraction_selectors.assert_not_called() # LLM should not be called
    assert result3.get('extraction_method') == "custom_css"

    print("\n--- Test Case 4: Schema.org data present, no custom selectors ---")
    html_with_schema_data = """
    <html><head><title>Schema Page</title></head><body>
    <script type="application/ld+json">
    {"@context": "http://schema.org", "@type": "NewsArticle", "headline": "Schema News Title", "articleBody": "Schema body."}
    </script></body></html>"""
    cfg4 = {"name": "TestSite4", "llm_analysis_pending": False, "extraction_selectors": None} # No LLM, no custom
    result4 = parser.parse_content(html_with_schema_data, "http://example.com/schema_article", cfg4)
    print(f"Result 4 (Title): {result4.get('title')}, Method: {result4.get('extraction_method')}")
    assert result4.get('extraction_method') == "schema_org_newsarticle"

    print("\n--- Parser multi-strategy __main__ tests finished ---")
