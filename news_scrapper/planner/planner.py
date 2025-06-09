"""
This module contains the Planner component.
The Planner is responsible for defining target websites, categories,
managing their configurations, including how often to crawl them,
discovering RSS feeds, polling those feeds, processing sitemaps,
initiating fallback crawls, and managing domain-specific settings like crawl delays.
"""
import json
import os
import urllib.parse # For urljoin and urlparse
from urllib.parse import urlparse as lib_urlparse # Specific alias to avoid conflict

try:
    from ..fetcher.fetcher import Fetcher
    from ..parser.parser import Parser
    from ..monitor.monitor import Monitor
    from ..pipeline.pipeline import Pipeline
except ImportError:
    print("WARNING: Could not import one or more components (Fetcher, Parser, Monitor, Pipeline). "
          "Planner functionality will be limited if run standalone.")
    Fetcher, Parser, Monitor, Pipeline = None, None, None, None

DEFAULT_CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "sources.json"))

class Planner:
    """
    Manages news sources, configurations, discovery, polling, sitemaps, fallback crawls,
    and shared domain settings (robots.txt cache, crawl delays).
    """
    def __init__(self, config_path=DEFAULT_CONFIG_PATH,
                 monitor_instance=None, fetcher_instance=None,
                 parser_instance=None, pipeline_instance=None): # Added pipeline_instance
        self.config_path = config_path
        self.sources = []

        # Shared caches for domain-specific settings
        self.robots_parsers_cache = {}  # domain -> RobotFileParser instance
        self.crawl_delays_cache = {}    # domain -> delay_seconds

        self.monitor = monitor_instance if monitor_instance else (Monitor() if Monitor else None)
        # Pass shared caches to Fetcher if creating a new one
        self.fetcher = fetcher_instance if fetcher_instance else \
                       (Fetcher(monitor_instance=self.monitor,
                                robots_parsers_cache=self.robots_parsers_cache,
                                crawl_delays_cache=self.crawl_delays_cache) if Fetcher else None)
        self.parser = parser_instance if parser_instance else (Parser(monitor_instance=self.monitor) if Parser else None)
        # Use provided pipeline_instance or create a new one
        self.pipeline = pipeline_instance if pipeline_instance else \
                        (Pipeline(monitor_instance=self.monitor) if Pipeline else None)


        self._log_event("INFO", f"Planner initialized with config path: {self.config_path}")
        if not all([self.fetcher, self.parser, self.monitor, self.pipeline]):
            self._log_event("WARNING", "One or more components are not available. Planner functionality will be reduced.")
        self.load_config()

    def _log_event(self, level, message, details=None):
        if self.monitor: self.monitor.log_event(level, message, details)
        else: print(f"[{level}] {message}" + (f" | Details: {details}" if details else ""))

    # --- Config and Source Management ---
    def load_config(self):
        # ... (existing, no changes) ...
        self._log_event("INFO", f"Attempting to load configuration from: {self.config_path}")
        try:
            if not os.path.exists(self.config_path):
                self._log_event("ERROR", "Planner configuration file not found.", {"path": self.config_path, "cwd": os.getcwd()})
                self.sources = []
                return
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.sources = data.get("sources", [])
                self._log_event("INFO", f"Successfully loaded {len(self.sources)} sources.", {"path": self.config_path})
        except Exception as e:
            self._log_event("ERROR", f"Failed to load/parse configuration: {e}", {"path": self.config_path, "error": str(e)})
            self.sources = []
    def get_targets(self): return self.sources
    def get_source_by_name(self, name):
        for s_ in self.sources:
            if s_.get("name") == name: return s_
        return None
    def save_config(self):
        # ... (existing, no changes) ...
        self._log_event("INFO", f"Attempting to save configuration to: {self.config_path}")
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump({"sources": self.sources}, f, indent=2, ensure_ascii=False)
        except Exception as e: self._log_event("ERROR", f"Failed to save configuration: {e}", {"path": self.config_path})

    # --- Domain Settings Management ---
    def prime_domain_settings(self, source_name_or_base_url):
        """
        Ensures robots.txt for the domain of the given source/URL is fetched and processed,
        populating crawl_delays_cache. This is called before major operations on a domain.
        Args:
            source_name_or_base_url (str): The name of a configured source or a base URL string.
        """
        if not self.fetcher or not self.parser:
            self._log_event("ERROR", "Fetcher/Parser not available for priming domain settings.")
            return

        base_url_to_use = None
        domain_key = None

        source = self.get_source_by_name(source_name_or_base_url)
        if source: # It's a source name
            base_url_to_use = source.get("base_url")
            if base_url_to_use:
                domain_key = lib_urlparse(base_url_to_use).netloc
        else: # Assume it's a direct base_url
            base_url_to_use = source_name_or_base_url
            domain_key = lib_urlparse(base_url_to_use).netloc

        if not base_url_to_use or not domain_key:
            self._log_event("ERROR", "Invalid source name or base URL for priming domain settings.", {"input": source_name_or_base_url})
            return

        self._log_event("INFO", f"Priming domain settings for '{domain_key}' using base URL '{base_url_to_use}'.")

        # Fetcher's _get_robot_parser handles fetching, parsing, and caching RobotFileParser.
        # It also attempts to set crawl_delay in self.crawl_delays_cache via rp.crawl_delay().
        robot_parser_instance = self.fetcher._get_robot_parser(base_url_to_use)

        if robot_parser_instance and not self.crawl_delays_cache.get(domain_key):
            # If robot_parser_instance.crawl_delay() didn't set it (e.g. no delay for specific UA or '*'),
            # try our custom parser for Crawl-delay. This needs raw robots.txt content.
            # This part is a bit more involved as Fetcher's _get_robot_parser doesn't directly return content.
            # For now, we rely on what _get_robot_parser itself populates in crawl_delays_cache.
            # A future refactor could make _get_robot_parser return content or have a separate method.
            self._log_event("DEBUG", f"Relying on Fetcher's _get_robot_parser to set crawl_delay for {domain_key} if available from rp.crawl_delay().")
            # Example of how one might get content if fetcher exposed it:
            # robots_content = self.fetcher.get_cached_robots_content(domain_key)
            # if robots_content:
            #     custom_delay = self.parser.parse_crawl_delay(robots_content, self.fetcher.current_user_agent)
            #     if custom_delay is not None and domain_key not in self.crawl_delays_cache: # Only if not already set by rp.crawl_delay
            #         self.crawl_delays_cache[domain_key] = custom_delay
            #         self._log_event("INFO", f"Crawl-delay for {domain_key} set to {custom_delay}s via custom parsing.")
        elif not robot_parser_instance:
             self._log_event("WARNING", f"Could not get/process robots.txt for priming {domain_key}.")


    # --- Discovery, Polling, and Crawling methods ---
    # (These methods should call prime_domain_settings before first fetch to a domain)
    def discover_rss_feed_for_source(self, source_name, persist_changes=True):
        source = self.get_source_by_name(source_name)
        if not source or not source.get("base_url"): self._log_event("ERROR",f"Source {source_name} invalid for RSS discovery."); return None
        self.prime_domain_settings(source.get("base_url")) # Prime before fetching homepage
        # ... (rest of existing RSS discovery logic) ...
        if source.get("rss_feed"): self._log_event("INFO", f"RSS already configured for {source_name}"); return source['rss_feed']
        if not self.fetcher or not self.parser: self._log_event("ERROR", "Fetcher/Parser missing for RSS discovery"); return None
        html_content = self.fetcher.fetch_url(source["base_url"])
        if html_content:
            rss_links = self.parser.find_rss_links_in_html(html_content, source["base_url"])
            if rss_links:
                self.update_source_rss_feed(source_name, rss_links[0])
                if persist_changes: self.save_config()
                self._log_event("INFO", f"Discovered RSS for {source_name}: {rss_links[0]}")
                return rss_links[0]
        self._log_event("INFO", f"No RSS discovered via homepage for {source_name}")
        return None


    def poll_rss_feed(self, source_name, recency_delta_days=2):
        source = self.get_source_by_name(source_name)
        if not source or not source.get("rss_feed"): self._log_event("DEBUG",f"Skipping RSS poll for {source_name} (no feed URL)."); return 0
        # Domain of the RSS feed URL itself needs priming for robots.txt if it's different from source's base_url domain
        rss_feed_domain = lib_urlparse(source["rss_feed"]).netloc
        if rss_feed_domain: self.prime_domain_settings(source["rss_feed"]) # Prime using the full feed URL
        # ... (rest of existing RSS polling logic) ...
        if not all([self.fetcher,self.parser,self.monitor,self.pipeline]): return 0
        feed_xml = self.fetcher.fetch_url(source["rss_feed"]); items_added=0
        if not feed_xml: self._log_event("WARNING", f"Failed to fetch RSS feed {source['rss_feed']}"); return 0
        if (items := self.parser.parse_rss_feed(feed_xml, source["rss_feed"])):
            for item in items:
                item_id = item.get("id",item.get("link"))
                if self.monitor.is_article_new_by_date(item_id, item.get("published_date_utc"),recency_delta_days):
                    self.pipeline.add_item(item); items_added+=1
                    self._log_event("DEBUG", f"Added new RSS item from {source_name}: {item.get('title')}")
        self._log_event("INFO", f"RSS poll for {source_name} added {items_added} items.")
        return items_added

    def process_sitemap(self, source_name, sitemap_url, recency_delta_days=2, processed_sitemaps=None):
        source_domain = lib_urlparse(sitemap_url).netloc # Sitemap URL's domain
        if source_domain: self.prime_domain_settings(sitemap_url) # Prime sitemap's domain
        # ... (rest of existing sitemap processing logic) ...
        if not all([self.fetcher,self.parser,self.monitor,self.pipeline]): return 0
        processed_sitemaps = processed_sitemaps or set()
        if sitemap_url in processed_sitemaps: return 0
        processed_sitemaps.add(sitemap_url)
        xml = self.fetcher.fetch_url(sitemap_url); items_added=0
        if not xml: self._log_event("WARNING", f"Failed to fetch sitemap {sitemap_url}"); return 0
        if (parsed := self.parser.parse_sitemap(xml, sitemap_url)):
            if parsed['type'] == 'sitemap_index':
                for sub_url in parsed['sitemap_urls']: items_added += self.process_sitemap(source_name, sub_url, recency_delta_days, processed_sitemaps)
            elif parsed['type'] == 'urlset':
                for item in parsed['items']:
                    loc_url = item['loc']
                    # Prime domain of each loc_url before potential fetch (if Monitor needs to check it)
                    # However, for sitemap items, we usually don't fetch the 'loc' URL here, just add to pipeline.
                    # The pipeline consumer would fetch it. So, priming loc_url's domain is for later.
                    if self.monitor.is_article_new_by_date(loc_url,item.get('lastmod_utc'),recency_delta_days):
                        adapted={'id':loc_url,'link':loc_url,'title':f"Sitemap: {os.path.basename(lib_urlparse(loc_url).path)}",
                                 'published_date_utc':item.get('lastmod_utc'),'source_sitemap_url':sitemap_url,'type':'sitemap_derived', 'source_name': source_name}
                        self.pipeline.add_item(adapted); items_added+=1
                        self._log_event("DEBUG", f"Added new sitemap item from {source_name}: {loc_url}")
        self._log_event("INFO", f"Sitemap {sitemap_url} processing for {source_name} added {items_added} items.")
        return items_added

    def discover_and_process_sitemaps_for_source(self, source_name, recency_delta_days=2):
        source = self.get_source_by_name(source_name)
        if not source or not source.get("base_url"): self._log_event("ERROR",f"Source {source_name} invalid for sitemap discovery."); return 0
        self.prime_domain_settings(source.get("base_url")) # Prime source's base_url domain for robots.txt
        # ... (rest of existing sitemap discovery logic) ...
        if not all([self.fetcher,self.parser]): return 0
        urls = []; robots_url = urllib.parse.urljoin(source["base_url"],"/robots.txt")
        content = self.fetcher.fetch_url(robots_url) # Fetcher handles robots for robots_url itself
        if content and (robot_sitemaps := self.parser.find_sitemap_links_in_robots(content)): urls.extend(robot_sitemaps)
        if not urls: default_sitemap = urllib.parse.urljoin(source["base_url"],"/sitemap.xml"); urls.append(default_sitemap)
        total_added=0; processed_session=set()
        for url in list(set(urls)): total_added += self.process_sitemap(source_name, url, recency_delta_days, processed_session)
        self._log_event("INFO", f"Sitemap discovery/processing for {source_name} added {total_added} items.")
        return total_added

    def initiate_fallback_crawl_for_source(self, source_name, recency_delta_days=2):
        source_config = self.get_source_by_name(source_name)
        if not source_config: self._log_event("ERROR",f"Source {source_name} not found for fallback."); return 0
        if not self.needs_fallback_crawl(source_config): return 0
        if source_config.get("base_url"): self.prime_domain_settings(source_config.get("base_url"))
        # ... (rest of existing fallback logic) ...
        if not all([self.fetcher,self.parser,self.monitor,self.pipeline]): return 0
        entry_urls = []; base_url = source_config.get("base_url")
        if base_url: entry_urls.append(base_url)
        for section in source_config.get("sections",[]):
            if isinstance(section,dict) and section.get("url"): entry_urls.append(section["url"])
        if not entry_urls: return 0
        items_added=0
        for entry_url in list(set(entry_urls)):
            # Prime domain for each entry_url if different from base_url (already primed)
            if lib_urlparse(entry_url).netloc != lib_urlparse(base_url if base_url else entry_url).netloc : self.prime_domain_settings(entry_url)
            html = self.fetcher.fetch_url(entry_url)
            if html and (data := self.parser.parse_content(html, entry_url)):
                item_id = data.get('url',entry_url)
                if self.monitor.is_article_new_by_date(item_id, data.get('published_date_utc'), recency_delta_days):
                    adapted = {'id':item_id, 'link':item_id, 'title':data.get('title',f"Crawled: {item_id}"),
                               'published_date_utc':data.get('published_date_utc'), 'text_content':data.get('text'),
                               'source_crawl_url':entry_url, 'source_name':source_name, 'type':'fallback_crawl_derived'}
                    self.pipeline.add_item(adapted); items_added+=1
                    self._log_event("DEBUG", f"Added new fallback item from {source_name}: {data.get('title')}")
        self._log_event("INFO", f"Fallback crawl for {source_name} added {items_added} items.")
        return items_added

    # --- Aggregate methods (unchanged but benefit from priming calls in sub-methods) ---
    def discover_all_rss_feeds(self, persist_changes=True):
        # ... (Existing implementation) ...
        any_change = False
        for src_cfg in self.sources:
            name = src_cfg.get("name")
            if name and not src_cfg.get("rss_feed"):
                if self.discover_rss_feed_for_source(name, persist_changes=False): any_change = True
        if any_change and persist_changes: self.save_config()
    def poll_all_rss_feeds(self, recency_delta_days=2):
        # ... (Existing implementation) ...
        for src_cfg in self.sources:
            if src_cfg.get("name"): self.poll_rss_feed(src_cfg["name"], recency_delta_days)
    def discover_and_process_all_sitemaps(self, recency_delta_days=2):
        # ... (Existing implementation) ...
        for src_cfg in self.sources:
            if src_cfg.get("name"): self.discover_and_process_sitemaps_for_source(src_cfg["name"], recency_delta_days)
    def initiate_all_fallback_crawls(self, recency_delta_days=2):
        # ... (Existing implementation) ...
        for src_cfg in self.sources:
            name = src_cfg.get("name")
            if name and self.needs_fallback_crawl(src_cfg):
                 self.initiate_fallback_crawl_for_source(name, recency_delta_days)
    def needs_fallback_crawl(self, source_config): # Definition was missing in provided snippet, ensure it exists
        if not source_config: return False
        return not (source_config.get("rss_feed") and str(source_config.get("rss_feed","")).strip())


if __name__ == '__main__':
    if not all([Fetcher, Parser, Monitor, Pipeline]):
        print("ERROR: Core components missing. Planner __main__ test for robots/delays cannot run.")
    else:
        test_monitor = Monitor()
        # Planner will init Fetcher with shared caches
        planner = Planner(monitor_instance=test_monitor)

        if not planner.fetcher: print("ERROR: Planner failed to init Fetcher."); exit()

        print("\n--- Testing Planner with Robots.txt and Crawl Delays ---")

        # Add a source that's known to have robots.txt with crawl-delay or specific rules
        # (e.g., python.org, or a local test server if possible)
        # For this example, let's use python.org and assume its robots.txt might have some rules.
        test_source_name = "PythonOrgForRobotsTest"
        if not planner.get_source_by_name(test_source_name):
            planner.sources.append({
                "name": test_source_name,
                "base_url": "https://www.python.org/",
                "rss_feed": "https://feeds.feedburner.com/PythonSoftwareFoundationNews", # Has an RSS
                # No sections needed for this specific test of priming
            })
            print(f"INFO: Added temporary source '{test_source_name}' for testing.")

        # 1. Prime domain settings for python.org
        print(f"\nPriming domain settings for '{test_source_name}'...")
        planner.prime_domain_settings(test_source_name) # Pass source name

        # Check if crawl_delays_cache got populated for 'www.python.org'
        python_domain = "www.python.org"
        if python_domain in planner.crawl_delays_cache:
            print(f"  Crawl delay for {python_domain} is now: {planner.crawl_delays_cache[python_domain]}s")
        else:
            print(f"  No specific Crawl-delay found or set for {python_domain} in planner's cache from priming (may use default).")

        # 2. Attempt to poll its RSS feed (Fetcher should now use the primed settings)
        print(f"\nPolling RSS feed for '{test_source_name}' (should respect robots.txt and delays)...")
        # Use large recency so it finds items if the feed is old, focusing on fetch mechanics
        items_polled = planner.poll_rss_feed(test_source_name, recency_delta_days=365*5)
        print(f"  Items polled from '{test_source_name}': {items_polled}")
        if planner.pipeline:
            print(f"  Pipeline size after polling: {len(planner.pipeline.item_queue)}")
            # planner.pipeline.clear_queue() # Clean up for next potential test

        # 3. (Optional) Test a disallowed URL from python.org if known (e.g., /search/)
        # This would be a direct fetch_url call, which is more of a Fetcher test,
        # but Planner sets up the Fetcher.
        # print("\nAttempting to fetch a typically disallowed URL (e.g., /search/) via Fetcher...")
        # disallowed_url = "https://www.python.org/search/"
        # # Need to ensure python.org is primed if not done by source name above
        # planner.prime_domain_settings(disallowed_url)
        # content = planner.fetcher.fetch_url(disallowed_url)
        # if content is None:
        #     print(f"  Fetching {disallowed_url} correctly returned None (likely disallowed or failed as expected).")
        # else:
        #     print(f"  Fetching {disallowed_url} returned content (unexpected for a disallowed URL, or robots.txt changed).")


    print("\n--- Planner robots/delays __main__ example finished ---")
