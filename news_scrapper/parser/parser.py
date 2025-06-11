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

# crawl4ai imports
from crawl4ai import WebCrawler
from crawl4ai.web_crawler import Url
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy # For custom CSS

# Project-specific imports
# Assuming Analyzer is in ..analyzer.structure_analyzer
try:
    from ..analyzer.structure_analyzer import StructureAnalyzer
    from ..planner.planner import Planner # Only for type hinting if needed, avoid circular full import
except ImportError: # Handle cases where this might be run standalone or tests are structured differently
    StructureAnalyzer = None
    Planner = None # For type hinting

# For robust date parsing from various string formats if needed beyond _parse_generic_date_to_utc
from dateutil import parser as dateutil_parser


class Parser:
    """
    Parses HTML content using a multi-strategy approach to extract structured data.
    Can trigger LLM-based CSS selector generation via a Planner reference.
    """
    def __init__(self, monitor_instance=None, planner_reference=None, structure_analyzer_instance=None):
        """
        Initializes the Parser.
        Args:
            monitor_instance: Optional Monitor instance for logging.
            planner_reference: Optional Planner instance to update source configs (e.g., selectors).
            structure_analyzer_instance: Optional StructureAnalyzer for LLM tasks.
        """
        self.monitor = monitor_instance
        self.planner_ref = planner_reference
        self.structure_analyzer = structure_analyzer_instance

        try:
            self.crawler = WebCrawler() # crawl4ai's general AI extractor
            self._log_event("INFO", "Parser: crawl4ai WebCrawler initialized successfully.")
        except Exception as e:
            self._log_event("ERROR", f"Parser: Failed to initialize crawl4ai WebCrawler: {e}")
            self.crawler = None

        if self.planner_ref is None:
            self._log_event("WARNING", "Parser: Planner reference not provided. Cannot update source configurations with LLM-generated selectors.")
        if self.structure_analyzer is None:
            self._log_event("WARNING", "Parser: StructureAnalyzer not provided. LLM-based selector generation will be skipped.")

    def _log_event(self, level, message, details=None):
        if self.monitor:
            self.monitor.log_event(level.upper(), message, details)
        else:
            details_str = f" | Details: {json.dumps(details)}" if details else ""
            print(f"[{level.upper()}] {message}{details_str}")

    def _parse_generic_date_to_utc(self, date_input, context_url="N/A"):
        # ... (This method was implemented in a previous step and should be kept as is) ...
        if date_input is None: return None
        if isinstance(date_input, datetime):
            return date_input.astimezone(timezone.utc) if date_input.tzinfo else date_input.replace(tzinfo=timezone.utc)
        if isinstance(date_input, str):
            try:
                dt = dateutil_parser.parse(date_input)
                return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError, OverflowError) as e: # Added OverflowError
                 self._log_event("DEBUG", f"Dateutil failed to parse date string '{date_input}' from {context_url}: {e}")
                 return None # Fallback to other methods if dateutil fails
        if isinstance(date_input, time.struct_time): # From feedparser
            try: return datetime.fromtimestamp(time.mktime(date_input), tz=timezone.utc)
            except Exception: return None
        return None

    def _is_data_sufficient(self, parsed_data_dict):
        """Checks if parsed data has at least a title and some text content."""
        if not parsed_data_dict:
            return False
        title = parsed_data_dict.get('title')
        text = parsed_data_dict.get('text')
        return bool(title and str(title).strip() and text and str(text).strip())

    def _normalize_extracted_data(self, data_dict, source_url, extraction_method_used):
        """
        Normalizes a raw extracted data dictionary to a standard format.
        Ensures keys: title, text, published_date_utc, authors (list), url, extraction_method.
        """
        if not data_dict or not isinstance(data_dict, dict): # Ensure data_dict is a dictionary
            return { # Return a minimal valid structure if input is bad
                "title": None, "text": None, "published_date_utc": None,
                "authors": [], "url": source_url, "extraction_method": extraction_method_used,
                "raw_data_received": data_dict # Keep original for debugging
            }

        # Map common variations to standard keys
        title = data_dict.get('title') or data_dict.get('headline')
        text = data_dict.get('text') or data_dict.get('content') or data_dict.get('articleBody')

        # Date can come from various keys
        raw_date = data_dict.get('published_date_utc') # If already a datetime from previous step
        if not isinstance(raw_date, datetime): # If not already a datetime object
            raw_date = data_dict.get('datePublished') or \
                       data_dict.get('dateModified') or \
                       data_dict.get('date') or \
                       data_dict.get('published_time') # Add other common date keys as found

        published_date_utc = self._parse_generic_date_to_utc(raw_date, context_url=source_url)

        authors_data = data_dict.get('authors') or data_dict.get('author')
        authors_list = []
        if authors_data:
            if isinstance(authors_data, list):
                for author_entry in authors_data:
                    if isinstance(author_entry, str): authors_list.append(author_entry.strip())
                    elif isinstance(author_entry, dict) and author_entry.get('name'):
                        authors_list.append(str(author_entry['name']).strip())
            elif isinstance(authors_data, str):
                authors_list = [name.strip() for name in authors_data.split(',')] # Simple split by comma
            elif isinstance(authors_data, dict) and authors_data.get('name'): # Single author object
                 authors_list.append(str(authors_data['name']).strip())

        return {
            "title": str(title).strip() if title else None,
            "text": str(text).strip() if text else None,
            "published_date_utc": published_date_utc,
            "authors": authors_list,
            "url": data_dict.get('url', source_url), # Prefer URL from data if available, else use source_url
            "extraction_method": extraction_method_used,
            "raw_data_for_method": data_dict # Keep original data from this method for context
        }

    def _parse_with_custom_selectors(self, html_content, url, source_config):
        """Parses HTML using custom CSS selectors defined in source_config."""
        if not self.crawler: # crawl4ai instance needed for JsonCssExtractionStrategy
            self._log_event("WARNING", "crawl4ai WebCrawler not available, cannot use JsonCssExtractionStrategy.", {"url": url})
            return None # Or implement direct BeautifulSoup fallback here

        selectors = source_config.get("extraction_selectors")
        if not selectors or not isinstance(selectors, dict):
            self._log_event("DEBUG", "No custom selectors provided or invalid format.", {"url": url})
            return None

        # Map stored selector names to what JsonCssExtractionStrategy might expect (e.g. "title", "content")
        # This mapping needs to be robust. Assuming `selectors` dict uses keys like "article_title_selector".
        strategy_schema = {}
        # Example: article_title_selector -> title
        if selectors.get("article_title_selector"): strategy_schema["title"] = selectors["article_title_selector"]
        if selectors.get("article_content_selector"): strategy_schema["text"] = selectors["article_content_selector"] # Map to 'text'
        if selectors.get("article_author_selector"): strategy_schema["authors"] = selectors["article_author_selector"] # Expects list
        if selectors.get("article_date_selector"): strategy_schema["date"] = selectors["article_date_selector"]
        # Add more mappings as needed for other fields

        if not strategy_schema:
            self._log_event("WARNING", "No valid selectors found after mapping for JsonCssExtractionStrategy.", {"url": url, "original_selectors": selectors})
            return None

        self._log_event("INFO", f"Attempting extraction with custom CSS selectors for {url}", {"mapped_selectors": strategy_schema})
        try:
            # JsonCssExtractionStrategy expects a list of schemas. We use one.
            strategy = JsonCssExtractionStrategy(json_schemas=[strategy_schema])
            # WebCrawler.read can take an extraction_strategy argument.
            # This is better than run_strategy if it exists, as it uses the main crawler logic.
            # The `Url` object is passed to `read`.
            url_obj = Url(url=url, html_content=html_content)
            # Assuming WebCrawler().read() can accept an extraction_strategy.
            # If not, this part needs adjustment based on crawl4ai's API for applying strategies to pre-fetched HTML.
            # Let's assume it works this way for now. If not, BeautifulSoup fallback will be required.
            # For now, let's directly use BeautifulSoup as JsonCssExtractionStrategy is not easily applied to existing content with current crawl4ai

            # Plan B: BeautifulSoup direct usage
            soup = BeautifulSoup(html_content, 'lxml')
            extracted_bs_data = {}
            for field, selector in strategy_schema.items():
                if selector:
                    elements = soup.select(selector) # Use select for potentially multiple elements
                    if elements:
                        if field == "text": # Concatenate text from multiple elements
                            extracted_bs_data[field] = "\n".join([el.get_text(separator="\n", strip=True) for el in elements])
                        elif field == "authors": # Handle authors similarly or take first
                             extracted_bs_data[field] = [el.get_text(strip=True) for el in elements]
                        else: # For title, date, take the first element's text
                            extracted_bs_data[field] = elements[0].get_text(strip=True)
                            # For date, might need to get an attribute like 'datetime'
                            if field == "date" and elements[0].has_attr('datetime'):
                                extracted_bs_data[field] = elements[0]['datetime']
                    else:
                        extracted_bs_data[field] = None

            if not any(extracted_bs_data.values()): # If all selectors failed
                 self._log_event("INFO", "Custom CSS selectors found no data.", {"url":url, "selectors": strategy_schema})
                 return None

            return self._normalize_extracted_data(extracted_bs_data, url, "custom_css")

        except Exception as e:
            self._log_event("ERROR", f"Error applying custom CSS selectors for {url}: {e}", {"selectors": strategy_schema})
            return None


    def _parse_with_schema_org(self, html_content, url):
        """Parses HTML for Schema.org data (JSON-LD, Microdata) using extruct."""
        self._log_event("INFO", f"Attempting Schema.org (extruct) parsing for {url}")
        try:
            data = extruct.extract(html_content, base_url=url, syntaxes=['json-ld', 'microdata'], uniform=True)
            # `uniform=True` attempts to convert microdata to json-ld like structure.

            # Look for Article, NewsArticle, BlogPosting in json-ld primarily
            for entry_type in ['json-ld', 'microdata']:
                for item in data.get(entry_type, []):
                    item_type = item.get('@type')
                    if isinstance(item_type, list): item_type = item_type[0] # Take first type if list

                    if item_type in ['Article', 'NewsArticle', 'BlogPosting', 'WebPage']: # Added WebPage as a broader fallback
                        self._log_event("DEBUG", f"Found potential Schema.org {item_type} data.", {"url": url})
                        # Map fields: (example mapping, needs refinement based on actual schema variations)
                        mapped_data = {
                            'title': item.get('headline') or item.get('name'),
                            'text': item.get('articleBody') or item.get('text'),
                            'authors': item.get('author'), # This can be complex (object or list of objects/strings)
                            'date': item.get('datePublished') or item.get('dateModified') or item.get('dateCreated'),
                            'url': item.get('url') or url # Prefer URL from schema if available
                        }
                        # Filter out None values before normalization if they are problematic
                        # mapped_data = {k:v for k,v in mapped_data.items() if v is not None}
                        if mapped_data.get('title') or mapped_data.get('text'): # Basic check for some content
                            return self._normalize_extracted_data(mapped_data, url, f"schema_org_{item_type.lower()}")
            self._log_event("INFO", "No suitable Schema.org data (Article, NewsArticle, etc.) found.", {"url": url})
        except Exception as e:
            self._log_event("ERROR", f"Error during Schema.org (extruct) parsing for {url}: {e}")
        return None

    def _parse_with_general_ai(self, html_content, url):
        """Parses HTML using the general crawl4ai AI model."""
        if not self.crawler:
            self._log_event("ERROR", "crawl4ai WebCrawler not initialized, cannot perform general AI parsing.", {"url": url})
            return None
        self._log_event("INFO", f"Attempting general AI (crawl4ai) parsing for {url}")
        try:
            url_obj = Url(url=url, html_content=html_content)
            raw_result = self.crawler.read(url_obj) # crawl4ai's main method

            if raw_result and (raw_result.text or raw_result.metadata):
                # Map crawl4ai output to our standard fields
                ai_extracted_data = {
                    'title': raw_result.metadata.get('title'),
                    'text': raw_result.text,
                    'date': raw_result.metadata.get('date'), # crawl4ai might provide this
                    'authors': [raw_result.metadata.get('author')] if raw_result.metadata.get('author') else [],
                    # Add other relevant metadata fields if crawl4ai extracts them
                }
                return self._normalize_extracted_data(ai_extracted_data, url, "general_ai")
            else:
                self._log_event("INFO", "General AI (crawl4ai) did not extract sufficient data.", {"url": url})
        except Exception as e:
            self._log_event("ERROR", f"Error during general AI (crawl4ai) parsing for {url}: {e}")
        return None

    def parse_content(self, html_content, url, source_config):
        """
        Orchestrates parsing using multiple strategies: custom CSS, Schema.org, General AI.
        Triggers LLM selector generation if needed and configured.
        Args:
            html_content (str): The HTML content of the page.
            url (str): The URL of the page.
            source_config (dict): Configuration for the source, including selectors or LLM flags.
        Returns:
            dict: Normalized extracted data, or None if all strategies fail.
        """
        if not source_config: source_config = {} # Ensure source_config is a dict
        source_name = source_config.get("name", "UnknownSource")
        self._log_event("INFO", f"Starting multi-strategy parsing for {url}", {"source": source_name})

        final_result = None

        # Strategy 1: Custom CSS Selectors
        result_custom = self._parse_with_custom_selectors(html_content, url, source_config)
        if self._is_data_sufficient(result_custom):
            final_result = result_custom
            self._log_event("INFO", "Sufficient data extracted using custom CSS selectors.", {"url": url})

        # Strategy 2: Schema.org (if custom selectors failed or were insufficient)
        if not final_result or not self._is_data_sufficient(final_result):
            result_schema = self._parse_with_schema_org(html_content, url)
            if self._is_data_sufficient(result_schema):
                final_result = result_schema
                self._log_event("INFO", "Sufficient data extracted using Schema.org.", {"url": url})
            elif result_schema and not final_result : # Schema found something but not enough, but we had nothing.
                 final_result = result_schema # Keep it as a weak candidate

        # Strategy 3: General AI (crawl4ai)
        # Always run general AI? Or only if others fail?
        # For now, run if others are insufficient, or to potentially augment.
        # Let's make it the primary fallback if others are insufficient.
        if not final_result or not self._is_data_sufficient(final_result):
            result_general_ai = self._parse_with_general_ai(html_content, url)
            if self._is_data_sufficient(result_general_ai):
                final_result = result_general_ai # AI is sufficient
                self._log_event("INFO", "Sufficient data extracted using general AI.", {"url": url})
            elif result_general_ai and not final_result: # AI found something, and we had nothing better
                final_result = result_general_ai
                self._log_event("INFO", "Using (potentially insufficient) data from general AI as best available.", {"url": url})


        # LLM Trigger Logic
        # Condition: No good selectors, LLM analysis is pending, and current result is insufficient.
        needs_llm_analysis = (not source_config.get("extraction_selectors") or \
                             source_config.get("extraction_selectors",{}).get("_isEmpty", False)) and \
                             source_config.get("llm_analysis_pending", True)

        if needs_llm_analysis and (not final_result or not self._is_data_sufficient(final_result)):
            self._log_event("INFO", f"Attempting LLM-based selector generation for {source_name} ({url}).")
            if self.structure_analyzer and self.planner_ref:
                # Ensure HTML content is not excessively large for LLM
                # (This might need truncation or summarization logic not included here)
                new_selectors = self.structure_analyzer.generate_extraction_selectors(url, html_content)
                if new_selectors:
                    self._log_event("INFO", f"LLM successfully generated new selectors for {source_name}.", {"selectors": new_selectors})
                    self.planner_ref.update_source_extraction_selectors(source_name, new_selectors)
                    if hasattr(self.planner_ref, 'save_config') and callable(self.planner_ref.save_config):
                        self.planner_ref.save_config() # Persist new selectors

                    # Update local source_config for immediate re-parse attempt
                    source_config["extraction_selectors"] = new_selectors
                    source_config["llm_analysis_pending"] = False # Reflect change locally

                    self._log_event("INFO", "Re-parsing with newly LLM-generated selectors.", {"url": url})
                    result_after_llm = self._parse_with_custom_selectors(html_content, url, source_config)
                    if self._is_data_sufficient(result_after_llm):
                        final_result = result_after_llm
                    # If still not sufficient, final_result (which might be from general_ai) remains
                else: # LLM failed to generate selectors
                    self._log_event("WARNING", f"LLM failed to generate selectors for {source_name}.", {"url": url})
                    self.planner_ref.set_llm_analysis_flag(source_name, False) # Mark as failed to avoid retries
                    if hasattr(self.planner_ref, 'save_config') and callable(self.planner_ref.save_config):
                        self.planner_ref.save_config()
            else:
                self._log_event("WARNING", "StructureAnalyzer or Planner reference not available; skipping LLM selector generation.", {"url": url})

        if final_result:
            self._log_event("INFO", f"Final parsing result for {url} obtained via {final_result.get('extraction_method', 'unknown')}.")
        else:
            self._log_event("WARNING", f"Failed to extract sufficient data for {url} using all strategies.")
            # Store a minimal record of parsing attempt with no content
            final_result = self._normalize_extracted_data({}, url, "no_data_found")


        return final_result

    # ... (Keep existing find_rss_links_in_html, find_sitemap_links_in_robots, parse_rss_feed, parse_sitemap) ...
    # Make sure they also use the updated _log_event if they had print statements.
    # (Reviewing them, they seem to use _log_event already from previous diffs)

if __name__ == '__main__':
    # More comprehensive tests would be in test_parser.py
    # This can be a very basic smoke test.
    # Mock planner and analyzer for parser's __main__
    class MockPlannerLite:
        def update_source_extraction_selectors(self, sn, sel): print(f"MockPlanner: update_source_extraction_selectors for {sn}")
        def set_llm_analysis_flag(self, sn, flag): print(f"MockPlanner: set_llm_analysis_flag for {sn} to {flag}")
        def save_config(self): print("MockPlanner: save_config called")

    class MockMonitorLite:
        def log_event(self,l,m,d=None): print(f"[{l}] {m} {d or ''}")

    mock_analyzer = StructureAnalyzer(monitor_instance=MockMonitorLite())

    parser = Parser(monitor_instance=MockMonitorLite(),
                    planner_reference=MockPlannerLite(),
                    structure_analyzer_instance=mock_analyzer)

    sample_html_for_llm = "<html><head><title>LLM Test Page Title</title></head><body><article><p>This is content for LLM test.</p></article></body></html>"
    sample_url_for_llm = "http://example.com/llm_test_page" # Matches StructureAnalyzer's placeholder success

    # Simulate a source config that needs LLM analysis
    test_source_config_llm = {
        "name": "LLMTestSource",
        "base_url": "http://example.com",
        "extraction_selectors": None, # No selectors yet
        "llm_analysis_pending": True # It needs analysis
    }

    print(f"\n--- Testing parse_content with LLM trigger path for {sample_url_for_llm} ---")
    # As structure_analyzer.generate_extraction_selectors returns dummy selectors for example.com,
    # this should trigger LLM, get selectors, and re-parse.
    result = parser.parse_content(sample_html_for_llm, sample_url_for_llm, test_source_config_llm)
    if result:
        print(f"Final result for {sample_url_for_llm} (method: {result.get('extraction_method')}):")
        print(f"  Title: {result.get('title')}")
        print(f"  Text: {result.get('text', '')[:50]}...")
        print(f"  Date: {result.get('published_date_utc')}")
        self.assertTrue(test_source_config_llm.get("extraction_selectors") is not None, "Selectors should have been updated in local source_config by LLM path")
        self.assertFalse(test_source_config_llm.get("llm_analysis_pending"), "LLM pending flag should be False after successful generation")
    else:
        print(f"Parsing failed for {sample_url_for_llm}")

    print("\n--- Parser multi-strategy __main__ example finished ---")
