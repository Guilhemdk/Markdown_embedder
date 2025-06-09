"""
This module contains the Fetcher component.
The Fetcher is responsible for retrieving raw content (HTML, JSON, XML, etc.)
from URLs, handling proxies, respecting politeness policies (robots.txt, crawl delays),
and managing user agents.
"""
import requests
import time
import random
import urllib.robotparser
from urllib.parse import urlparse

# Default list of user agents if none provided
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
    # Add more diverse user agents if needed
]

class Fetcher:
    """
    Handles fetching content from URLs, respecting robots.txt and crawl delays.
    """
    def __init__(self, user_agent_list=None,
                 default_delay_between_requests=1,
                 robots_parsers_cache=None,
                 crawl_delays_cache=None,
                 monitor_instance=None):
        """
        Initializes the Fetcher.
        Args:
            user_agent_list (list, optional): List of user agents. Defaults to USER_AGENTS.
            default_delay_between_requests (int, optional): Default seconds to wait between requests
                                                           to the same domain if no crawl-delay is specified.
            robots_parsers_cache (dict, optional): Shared cache for RobotFileParser instances.
            crawl_delays_cache (dict, optional): Shared cache for domain-specific crawl delays.
            monitor_instance (Monitor, optional): Instance of the Monitor component for logging.
        """
        self.user_agents = user_agent_list if user_agent_list else USER_AGENTS
        self.current_user_agent = self._get_user_agent() # Set an initial user agent

        self.default_delay_between_requests = default_delay_between_requests
        self.last_request_time = {} # Stores last request time per domain: {domain: timestamp}

        # Shared caches (can be managed externally, e.g., by Planner)
        self.robots_parsers_cache = robots_parsers_cache if robots_parsers_cache is not None else {}
        self.crawl_delays_cache = crawl_delays_cache if crawl_delays_cache is not None else {}

        self.monitor = monitor_instance

    def _log_event(self, level, message, details=None):
        if self.monitor:
            self.monitor.log_event(level, message, details)
        else:
            details_str = f" | Details: {details}" if details else ""
            print(f"[{level}] {message}{details_str}")

    def _get_user_agent(self):
        """Selects a random user agent from the list. Can be called to rotate UA."""
        if not self.user_agents:
            return "NewsScrapper/1.0 (DefaultFetcher; +https://github.com/your_project)" # Fallback
        self.current_user_agent = random.choice(self.user_agents)
        return self.current_user_agent

    def _get_robot_parser(self, url_to_fetch):
        """
        Retrieves, caches, or fetches and parses a robots.txt file for the domain of the given URL.
        Args:
            url_to_fetch (str): The URL whose domain's robots.txt is needed.
        Returns:
            urllib.robotparser.RobotFileParser instance or None if robots.txt is inaccessible/invalid.
        """
        parsed_url = urlparse(url_to_fetch)
        domain = parsed_url.netloc
        robots_url = f"{parsed_url.scheme}://{domain}/robots.txt"

        if domain in self.robots_parsers_cache:
            return self.robots_parsers_cache[domain]

        self._log_event("INFO", f"Fetching robots.txt for {domain}", {"robots_url": robots_url})
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)

        try:
            # urllib.robotparser.RobotFileParser fetches the URL itself when read() is called.
            # It uses urllib.request internally. We need to ensure it uses our headers for politeness.
            # However, RobotFileParser doesn't directly support passing custom headers for its internal fetching.
            # For now, we'll let it fetch as is. If issues arise, a custom fetch of robots.txt might be needed here.
            # A more robust solution would be to fetch robots.txt using requests with headers, then parse.

            # Temporary workaround: Fetch with requests, then parse.
            headers = {"User-Agent": self.current_user_agent} # Use current UA for fetching robots.txt
            response = requests.get(robots_url, headers=headers, timeout=10)
            response.raise_for_status() # Check for HTTP errors

            rp.parse(response.text.splitlines())
            self.robots_parsers_cache[domain] = rp
            self._log_event("INFO", f"Successfully fetched and parsed robots.txt for {domain}")

            # After parsing, try to get crawl-delay using robotparser's own method
            # This is often more reliable than custom parsing if robots.txt is standard.
            agent_delay = rp.crawl_delay(self.current_user_agent)
            if agent_delay is not None:
                self.crawl_delays_cache[domain] = agent_delay
                self._log_event("INFO", f"Crawl-delay for {domain} (agent: {self.current_user_agent}) set to {agent_delay}s via robotparser.")
            else: # Fallback for '*' if specific agent has no delay
                star_delay = rp.crawl_delay("*")
                if star_delay is not None:
                    self.crawl_delays_cache[domain] = star_delay
                    self._log_event("INFO", f"Crawl-delay for {domain} (agent: *) set to {star_delay}s via robotparser.")

            return rp
        except requests.exceptions.HTTPError as e:
            # Common for 404 (no robots.txt) or 403. Treat as "allow all" if 404.
            # Other errors might be more problematic.
            if e.response.status_code == 404:
                self._log_event("INFO", f"No robots.txt found for {domain} (404). Assuming allow all.", {"robots_url": robots_url})
                # Cache a "dummy" parser that allows everything for this domain to avoid re-fetching.
                rp.parse("User-agent: *\nAllow: /".splitlines())
                self.robots_parsers_cache[domain] = rp
                return rp
            else:
                self._log_event("WARNING", f"HTTP error fetching robots.txt for {domain}: {e}", {"robots_url": robots_url})
                self.robots_parsers_cache[domain] = None # Cache None to indicate failure to fetch/parse
                return None
        except Exception as e:
            self._log_event("ERROR", f"Error fetching/parsing robots.txt for {domain}: {e}", {"robots_url": robots_url})
            self.robots_parsers_cache[domain] = None # Cache None
            return None


    def _can_fetch(self, domain, url_to_check):
        """
        Checks if a URL can be fetched based on robots.txt and crawl delay.
        Args:
            domain (str): The domain of the URL.
            url_to_check (str): The full URL to check.
        Returns:
            bool: True if fetching is allowed, False otherwise.
        """
        # 1. Robots.txt check
        rp = self._get_robot_parser(url_to_check) # This handles fetching and caching
        if rp:
            # Rotate user agent *before* can_fetch check for consistency with actual fetch
            # current_ua_for_check = self._get_user_agent() # Rotate for this check
            current_ua_for_check = self.current_user_agent # Or use the already set one for the upcoming fetch
            if not rp.can_fetch(current_ua_for_check, url_to_check):
                self._log_event("WARNING", "Fetching disallowed by robots.txt.",
                                {"url": url_to_check, "user_agent": current_ua_for_check})
                return False
        # If rp is None (robots.txt failed to load/parse), conservatively assume disallow or implement specific policy.
        # For now, if rp is None, we might skip robots check and only rely on delay.
        # A stricter policy might be to return False if robots.txt is unreadable but not a 404.
        # Current _get_robot_parser returns a dummy "allow all" on 404, and None on other errors.
        # So, if rp is None here, it means a significant error occurred fetching robots.txt.
        elif rp is None and domain in self.robots_parsers_cache: # Check if failure was cached
             self._log_event("WARNING", f"Cannot determine robots.txt permission for {url_to_check} due to previous fetch/parse error. Proceeding with caution (delay only).")


        # 2. Crawl-delay check
        # Use delay from cache (set by _get_robot_parser or Planner) or default
        delay = self.crawl_delays_cache.get(domain, self.default_delay_between_requests)

        current_time = time.time()
        last_fetch_time = self.last_request_time.get(domain, 0)

        if current_time - last_fetch_time < delay:
            wait_time = delay - (current_time - last_fetch_time)
            self._log_event("DEBUG", f"Delaying request to {domain} for {wait_time:.2f}s (Crawl-Delay: {delay}s).")
            time.sleep(wait_time) # Apply delay directly here
        return True

    def fetch_url(self, url):
        """
        Fetches the content of a given URL, respecting robots.txt and crawl delays.
        Args:
            url (str): The URL to fetch.
        Returns:
            str: The content of the URL as text, or None if fetching fails or is disallowed.
        """
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            if not domain: # Should not happen with valid URLs
                self._log_event("ERROR", "Invalid URL: Missing domain.", {"url": url})
                return None
        except Exception as e:
            self._log_event("ERROR", f"URL parsing failed for: {url}. Error: {e}")
            return None

        # Rotate user agent for this fetch attempt
        self.current_user_agent = self._get_user_agent()
        headers = {"User-Agent": self.current_user_agent}

        # _can_fetch now handles both robots.txt check and delay.
        # If it returns False, it means robots.txt disallowed it *before* any delay logic.
        if not self._can_fetch(domain, url):
            # If _can_fetch returned False, it means robots.txt disallows.
            # The log for this is already in _can_fetch or _get_robot_parser.
            return None

        # If _can_fetch returned True, it means robots.txt allows, and any necessary delay has already occurred.
        self._log_event("DEBUG", f"Fetching {url}", {"user_agent": self.current_user_agent})
        try:
            response = requests.get(url, headers=headers, timeout=15) # Increased timeout slightly
            response.raise_for_status()

            self.last_request_time[domain] = time.time() # Update last request time
            return response.text
        except requests.exceptions.HTTPError as e:
            self._log_event("ERROR", f"HTTP error fetching {url}: {e.response.status_code} {e.response.reason}", {"url": url})
            if self.monitor: # Signal potential rate limiting to monitor
                self.monitor.is_rate_limited("Fetcher", domain, http_status_code=e.response.status_code, content_snippet=e.response.text[:200])
        except requests.exceptions.ConnectionError as e:
            self._log_event("ERROR", f"Connection error fetching {url}: {e}", {"url": url})
        except requests.exceptions.Timeout as e:
            self._log_event("ERROR", f"Timeout error fetching {url}: {e}", {"url": url})
        except requests.exceptions.RequestException as e:
            self._log_event("ERROR", f"General error fetching {url}: {e}", {"url": url})
        return None


if __name__ == '__main__':
    # For __main__ testing, we need a Monitor instance if we want logs to show up via the monitor
    # from news_scrapper.monitor.monitor import Monitor # Adjust import path if necessary
    # test_monitor = Monitor()
    test_monitor = None # Simpler console output for now

    # Initialize caches for testing
    test_robots_cache = {}
    test_delays_cache = {}

    fetcher = Fetcher(default_delay_between_requests=1,
                      robots_parsers_cache=test_robots_cache,
                      crawl_delays_cache=test_delays_cache,
                      monitor_instance=test_monitor)

    print("Fetcher initialized for __main__ example.")

    # Test URLs - replace with actual URLs that have robots.txt for meaningful tests
    # For example, python.org has a robots.txt
    test_urls = [
        "https://www.python.org/",                  # Should be allowed
        "https://www.python.org/psf/",             # Should be allowed
        "https://www.python.org/search/",          # Often disallowed by robots.txt for '*'
        "http://example.com/nonexistentrobots.txt" # To test 404 handling for robots.txt
    ]
    # Note: To truly test disallows, you might need a specific user-agent that python.org disallows from /search/
    # For now, we use default user agents which are typically not disallowed from major paths.

    print("\n--- Testing Fetcher with robots.txt and delays ---")
    for t_url in test_urls:
        print(f"\nAttempting to fetch: {t_url}")
        content = fetcher.fetch_url(t_url)
        if content:
            print(f"  Successfully fetched {t_url}. Content length: {len(content)}. Snippet: '{content[:80].replace('\n',' ')}...'")
        else:
            print(f"  Failed to fetch or disallowed: {t_url}")

        # Show cache status (optional)
        domain_of_url = urlparse(t_url).netloc
        if domain_of_url in test_robots_cache:
            print(f"  Robots.txt for {domain_of_url} is now in cache.")
        if domain_of_url in test_delays_cache:
             print(f"  Crawl delay for {domain_of_url} is {test_delays_cache[domain_of_url]}s.")

    print("\n--- Fetcher example finished ---")
