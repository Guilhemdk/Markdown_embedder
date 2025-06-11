"""
This module contains the Planner component.
The Planner is responsible for defining target websites, categories,
managing their configurations, including how often to crawl them,
discovering RSS feeds, polling those feeds, processing sitemaps,
initiating fallback crawls, managing domain-specific settings like crawl delays,
and interacting with the StructureAnalyzer.
"""
import json
import os
import urllib.parse # For urljoin and urlparse
from urllib.parse import urlparse as lib_urlparse # Specific alias to avoid conflict
from datetime import datetime, timedelta, timezone

try:
    from ..fetcher.fetcher import Fetcher
    from ..parser.parser import Parser
    from ..monitor.monitor import Monitor
    from ..pipeline.pipeline import Pipeline
    from ..analyzer.structure_analyzer import StructureAnalyzer # Import StructureAnalyzer
except ImportError:
    print("WARNING: Could not import one or more components (Fetcher, Parser, Monitor, Pipeline, StructureAnalyzer). "
          "Planner functionality will be limited if run standalone.")
    Fetcher, Parser, Monitor, Pipeline, StructureAnalyzer = None, None, None, None, None

DEFAULT_CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "sources.json"))

class Planner:
    """
    Manages news sources, configurations, discovery, polling, sitemaps, fallback crawls,
    shared domain settings, and LLM-based structure analysis.
    """
    def __init__(self, config_path=DEFAULT_CONFIG_PATH,
                 monitor_instance=None, fetcher_instance=None,
                 parser_instance=None, pipeline_instance=None,
                 structure_analyzer_instance=None):
        self.config_path = config_path
        self.sources = []

        self.robots_parsers_cache = {}
        self.crawl_delays_cache = {}

        self.monitor = monitor_instance if monitor_instance else (Monitor() if Monitor else None)
        self.fetcher = fetcher_instance if fetcher_instance else \
                       (Fetcher(monitor_instance=self.monitor,
                                robots_parsers_cache=self.robots_parsers_cache,
                                crawl_delays_cache=self.crawl_delays_cache) if Fetcher else None)
        self.structure_analyzer = structure_analyzer_instance if structure_analyzer_instance else \
                                  (StructureAnalyzer(monitor_instance=self.monitor) if StructureAnalyzer else None)
        self.parser = parser_instance if parser_instance else \
                      (Parser(monitor_instance=self.monitor,
                              planner_reference=self,
                              structure_analyzer_instance=self.structure_analyzer) if Parser else None)
        self.pipeline = pipeline_instance if pipeline_instance else \
                        (Pipeline(monitor_instance=self.monitor) if Pipeline else None)

        self._log_event("INFO", f"Planner initialized with config path: {self.config_path}")
        if not all([self.fetcher, self.parser, self.monitor, self.pipeline, self.structure_analyzer]):
            self._log_event("WARNING", "One or more components (Fetcher, Parser, Monitor, Pipeline, StructureAnalyzer) are not available.")
        self.load_config()

    def _log_event(self, level, message, details=None):
        if self.monitor: self.monitor.log_event(level, message, details)
        else: print(f"[{level}] {message}" + (f" | Details: {details}" if details else ""))

    def load_config(self): # ... (no changes from previous correct version) ...
        self._log_event("INFO", f"Attempting to load configuration from: {self.config_path}")
        try:
            if not os.path.exists(self.config_path):
                self._log_event("ERROR", "Planner configuration file not found.", {"path": self.config_path, "cwd": os.getcwd()})
                self.sources = []
                return
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                loaded_sources = data.get("sources", [])
                for src in loaded_sources:
                    src.setdefault('parser_config_name', src.get('parser_config', 'default'))
                    src.setdefault('extraction_selectors', None)
                    src.setdefault('llm_analysis_pending', not bool(src.get('extraction_selectors')))
                    if 'parser_config' in src: del src['parser_config']
                self.sources = loaded_sources
                self._log_event("INFO", f"Successfully loaded {len(self.sources)} sources.", {"path": self.config_path})
        except Exception as e:
            self._log_event("ERROR", f"Failed to load/parse configuration: {e}", {"path": self.config_path, "error": str(e)})
            self.sources = []
    def get_targets(self): return self.sources
    def get_source_by_name(self, name): # ... (no changes) ...
        for src_config in self.sources:
            if src_config.get("name") == name: return src_config
        return None
    def update_source_extraction_selectors(self, source_name, selectors_dict): # ... (no changes) ...
        source = self.get_source_by_name(source_name)
        if source:
            source['extraction_selectors'] = selectors_dict; source['llm_analysis_pending'] = False
            self._log_event("INFO", f"Updated extraction selectors for source '{source_name}'.")
            return True
        return False
    def set_llm_analysis_flag(self, source_name, flag_status): # ... (no changes) ...
        source = self.get_source_by_name(source_name)
        if source: source['llm_analysis_pending'] = flag_status; self._log_event("INFO", f"Set llm_analysis_pending to {flag_status} for '{source_name}'."); return True
        return False
    def save_config(self): # ... (no changes) ...
        self._log_event("INFO", f"Saving configuration to: {self.config_path}")
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f: json.dump({"sources": self.sources}, f, indent=2, ensure_ascii=False)
        except Exception as e: self._log_event("ERROR", f"Failed to save config: {e}")
    def update_source_rss_feed(self, source_name, rss_feed_url): # ... (no changes) ...
        source = self.get_source_by_name(source_name)
        if source: source["rss_feed"] = rss_feed_url; return True
        return False
    def prime_domain_settings(self, source_name_or_base_url): # ... (no changes) ...
        if not self.fetcher: return
        base_url, domain_key = None, None; source = self.get_source_by_name(source_name_or_base_url)
        if source: base_url = source.get("base_url")
        else: base_url = source_name_or_base_url
        if base_url: domain_key = lib_urlparse(base_url).netloc
        if not (base_url and domain_key): return
        self.fetcher._get_robot_parser(base_url)
    def discover_rss_feed_for_source(self, source_name, persist_changes=True): # ... (no changes) ...
        source = self.get_source_by_name(source_name);
        if not source or not source.get("base_url"): return None
        self.prime_domain_settings(source.get("base_url"))
        if source.get("rss_feed"): return source['rss_feed']
        if not self.fetcher or not self.parser: return None
        html = self.fetcher.fetch_url(source["base_url"])
        if html and (rss_links := self.parser.find_rss_links_in_html(html, source["base_url"])):
            self.update_source_rss_feed(source_name, rss_links[0])
            if persist_changes: self.save_config()
            return rss_links[0]
        return None

    def poll_rss_feed(self, source_name, recency_delta_days=2):
        source = self.get_source_by_name(source_name)
        if not source or not source.get("rss_feed"): return 0
        if (domain := lib_urlparse(source["rss_feed"]).netloc): self.prime_domain_settings(source["rss_feed"])
        if not all([self.fetcher,self.parser,self.monitor,self.pipeline]): return 0
        feed_xml = self.fetcher.fetch_url(source["rss_feed"]); items_added=0
        if not feed_xml: return 0
        if (items := self.parser.parse_rss_feed(feed_xml, source["rss_feed"])): # parse_rss_feed returns list of dicts
            for item_data in items:
                item_id = item_data.get("id", item_data.get("link"))
                if self.monitor.is_article_new_by_date(item_id, item_data.get("published_date_utc"), recency_delta_days):
                    item_to_add = {**item_data, "source_name": source_name} # Add source_name
                    self.pipeline.add_item(item_to_add); items_added+=1
        return items_added

    def process_sitemap(self, source_name, sitemap_url, recency_delta_days=2, processed_sitemaps=None):
        if (domain := lib_urlparse(sitemap_url).netloc): self.prime_domain_settings(sitemap_url)
        if not all([self.fetcher,self.parser,self.monitor,self.pipeline]): return 0
        processed_sitemaps = processed_sitemaps or set()
        if sitemap_url in processed_sitemaps: return 0
        processed_sitemaps.add(sitemap_url)
        xml = self.fetcher.fetch_url(sitemap_url); items_added=0
        if not xml: return 0
        if (parsed := self.parser.parse_sitemap(xml, sitemap_url)):
            if parsed['type'] == 'sitemap_index':
                for sub_url in parsed['sitemap_urls']: items_added += self.process_sitemap(source_name, sub_url, recency_delta_days, processed_sitemaps)
            elif parsed['type'] == 'urlset':
                for item in parsed['items']: # item is {'loc': str, 'lastmod_utc': datetime, 'source_sitemap_url': str}
                    loc = item['loc']
                    if self.monitor.is_article_new_by_date(loc,item.get('lastmod_utc'),recency_delta_days):
                        adapted = {'id':loc,'link':loc,'title':f"Sitemap: {os.path.basename(lib_urlparse(loc).path)}",
                                   'published_date_utc':item.get('lastmod_utc'), 'source_sitemap_url':sitemap_url,
                                   'type':'sitemap_derived', 'source_name': source_name} # Add source_name
                        self.pipeline.add_item(adapted); items_added+=1
        return items_added

    def discover_and_process_sitemaps_for_source(self, source_name, recency_delta_days=2): # ... (no changes other than what process_sitemap does) ...
        source = self.get_source_by_name(source_name);
        if not source or not source.get("base_url"): return 0
        self.prime_domain_settings(source.get("base_url"))
        if not all([self.fetcher,self.parser]): return 0
        urls = []; content = self.fetcher.fetch_url(urllib.parse.urljoin(source["base_url"],"/robots.txt"))
        if content and (robot_sitemaps := self.parser.find_sitemap_links_in_robots(content)): urls.extend(robot_sitemaps)
        if not urls: urls.append(urllib.parse.urljoin(source["base_url"],"/sitemap.xml"))
        total_added=0; processed_session=set()
        for url in list(set(urls)): total_added += self.process_sitemap(source_name, url, recency_delta_days, processed_session)
        return total_added

    def initiate_fallback_crawl_for_source(self, source_name, recency_delta_days=2):
        source_config = self.get_source_by_name(source_name)
        if not source_config or not self.needs_fallback_crawl(source_config): return 0
        base_url = source_config.get("base_url")
        if base_url: self.prime_domain_settings(base_url)
        if not all([self.fetcher,self.parser,self.monitor,self.pipeline]): return 0
        entry_urls = [base_url] if base_url else []
        for section in source_config.get("sections",[]):
            if isinstance(section,dict) and section.get("url"): entry_urls.append(section["url"])
        if not entry_urls: return 0
        items_added=0
        for entry_url in list(set(entry_urls)):
            if base_url and lib_urlparse(entry_url).netloc != lib_urlparse(base_url).netloc : self.prime_domain_settings(entry_url)
            elif not base_url: self.prime_domain_settings(entry_url)
            html = self.fetcher.fetch_url(entry_url)
            # parser.parse_content now takes source_config
            if html and (data := self.parser.parse_content(html, entry_url, source_config)):
                item_id = data.get('url',entry_url)
                if self.monitor.is_article_new_by_date(item_id, data.get('published_date_utc'), recency_delta_days):
                    adapted = {'id':item_id, 'link':item_id, 'title':data.get('title',f"Crawled: {item_id}"),
                               'published_date_utc':data.get('published_date_utc'), 'text_content':data.get('text'),
                               'source_crawl_url':entry_url,
                               'source_name':source_name, # Add source_name
                               'type':'fallback_crawl_derived'}
                    self.pipeline.add_item(adapted); items_added+=1
        return items_added

    def discover_all_rss_feeds(self, persist_changes=True): # ... (no changes) ...
        any_change=False; [(self.discover_rss_feed_for_source(s.get("name"), False), globals().update(any_change=True)) for s in self.sources if s.get("name") and not s.get("rss_feed")]; (any_change and persist_changes and self.save_config())
    def poll_all_rss_feeds(self, recency_delta_days=2): # ... (no changes) ...
        [self.poll_rss_feed(s.get("name"), recency_delta_days) for s in self.sources if s.get("name")]
    def discover_and_process_all_sitemaps(self, recency_delta_days=2): # ... (no changes) ...
        [self.discover_and_process_sitemaps_for_source(s.get("name"), recency_delta_days) for s in self.sources if s.get("name")]
    def initiate_all_fallback_crawls(self, recency_delta_days=2): # ... (no changes) ...
        [self.initiate_fallback_crawl_for_source(s.get("name"), recency_delta_days) for s in self.sources if s.get("name") and self.needs_fallback_crawl(s)]
    def needs_fallback_crawl(self, source_config): # ... (no changes) ...
        return not (source_config and source_config.get("rss_feed") and str(source_config.get("rss_feed","")).strip())
    def discover_new_sources_from_rss(self, rss_feed_urls_to_scan, recency_hours=24): # ... (no changes) ...
        if not all([self.fetcher, self.parser, self.monitor]): return []
        discovered_domains_origins = {}
        cutoff_datetime_utc = datetime.now(timezone.utc) - timedelta(hours=recency_hours)
        for feed_url in rss_feed_urls_to_scan:
            self.prime_domain_settings(feed_url)
            feed_content = self.fetcher.fetch_url(feed_url)
            if not feed_content: continue
            parsed_items = self.parser.parse_rss_feed(feed_content, feed_url) # This already returns list of dicts
            if not parsed_items: continue
            for item in parsed_items: # item is already a dict
                item_date_utc = item.get("published_date_utc")
                if item_date_utc and isinstance(item_date_utc, datetime) :
                    if item_date_utc.tzinfo is None: item_date_utc = item_date_utc.replace(tzinfo=timezone.utc)
                    if item_date_utc < cutoff_datetime_utc: continue
                    if (article_link := item.get("link")) and (domain := lib_urlparse(article_link).netloc):
                        discovered_domains_origins.setdefault(domain, set()).add(feed_url)
        if not discovered_domains_origins: return []
        known_domains = {lib_urlparse(s["base_url"]).netloc.lower() for s in self.sources if s.get("base_url") and lib_urlparse(s["base_url"]).netloc}
        return [{"new_domain": dom, "discovered_from_rss_feeds": list(origins),"suggestion_source": "rss_link_discovery"}
                for dom, origins in discovered_domains_origins.items() if dom.lower() not in known_domains]

if __name__ == '__main__': # ... (no changes to __main__) ...
    if not all([Fetcher, Parser, Monitor, Pipeline, StructureAnalyzer]):
        print("ERROR: Core components missing. Planner __main__ tests cannot run comprehensively.")
    else:
        test_monitor = Monitor()
        test_pipeline = Pipeline(monitor_instance=test_monitor)
        planner = Planner(config_path=DEFAULT_CONFIG_PATH,
                          monitor_instance=test_monitor,
                          pipeline_instance=test_pipeline)
        if not all([planner.fetcher, planner.parser, planner.structure_analyzer]):
            print("ERROR: Planner could not init Fetcher/Parser/StructureAnalyzer.")
        else:
            print(f"\n--- Testing Planner with config: {planner.config_path} ---")
            all_sources = planner.get_targets()
            print(f"Loaded {len(all_sources)} sources.")
            for i, src in enumerate(all_sources):
                print(f"  Source {i+1}: {src.get('name')} (LLM Pending: {src.get('llm_analysis_pending')}, Selectors: {src.get('extraction_selectors') is not None})")
            test_select_src = "Placeholder LLM Test Site"
            if planner.get_source_by_name(test_select_src):
                print(f"\n--- Testing selector update for '{test_select_src}' ---")
                new_sels = {"title": "h1.title", "content": "div.article"}
                planner.update_source_extraction_selectors(test_select_src, new_sels)
                updated_src = planner.get_source_by_name(test_select_src)
                print(f"  Updated selectors: {updated_src.get('extraction_selectors')}")
                print(f"  LLM Pending: {updated_src.get('llm_analysis_pending')}")
                planner.set_llm_analysis_flag(test_select_src, True)
                print(f"  LLM Pending after reset: {planner.get_source_by_name(test_select_src).get('llm_analysis_pending')}")
    print("\n--- Planner __main__ tests (incl. selector config) finished ---")
