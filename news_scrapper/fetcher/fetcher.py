"""
This module contains the Fetcher component.
The Fetcher is responsible for retrieving raw content (HTML, JSON, etc.)
from URLs, handling proxies, and respecting politeness policies.
"""
import requests
import time
import random

# Placeholder for a list of user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Mobile/15E148 Safari/604.1"
]

class Fetcher:
    """
    Handles fetching content from URLs.
    """
    def __init__(self, user_agent_list=None, delay_between_requests=1):
        """
        Initializes the Fetcher.
        Args:
            user_agent_list (list, optional): A list of user agents to rotate through.
                                              Defaults to a predefined list.
            delay_between_requests (int, optional): Seconds to wait between requests
                                                    to the same domain. Defaults to 1.
        """
        self.user_agents = user_agent_list if user_agent_list else USER_AGENTS
        self.delay = delay_between_requests
        self.last_request_time = {} # To store last request time per domain

    def _get_user_agent(self):
        """
        Selects a random user agent from the list.
        Returns:
            str: A user agent string.
        """
        if not self.user_agents:
            # Fallback if the list is somehow empty
            return "Mozilla/5.0 (compatible; DefaultFetcher/1.0)"
        return random.choice(self.user_agents)

    def _can_fetch(self, domain):
        """
        Checks if a request can be made to the domain based on the configured delay.
        This is a basic politeness measure. Respecting robots.txt is more complex
        and should be handled by a dedicated part of the system or library.

        Args:
            domain (str): The domain of the URL to fetch.
        Returns:
            bool: True if fetching is allowed based on delay, False otherwise.
        """
        # Placeholder for respecting robots.txt:
        # In a real application, you would use a library like 'reppy' or 'robotexclusionrulesparser'
        # to parse robots.txt and check if the path is allowed for your user-agent.
        # For now, this is just a print statement.
        # print(f"INFO: Checking robots.txt for {domain} (not implemented, assuming allowed)")

        current_time = time.time()
        if domain in self.last_request_time:
            elapsed_time = current_time - self.last_request_time[domain]
            if elapsed_time < self.delay:
                wait_time = self.delay - elapsed_time
                # print(f"DEBUG: Delaying request to {domain} for {wait_time:.2f} seconds.")
                time.sleep(wait_time) # Applying delay
        return True

    def fetch_url(self, url):
        """
        Fetches the content of a given URL.
        It incorporates a delay mechanism to be polite to servers and rotates user agents.
        Args:
            url (str): The URL to fetch.
        Returns:
            str: The content of the URL as text, or None if fetching fails.
        """
        try:
            domain = url.split('//')[-1].split('/')[0]
        except IndexError:
            print(f"ERROR: Invalid URL format: {url}")
            return None

        if not self._can_fetch(domain):
            # This part of the logic is now handled within _can_fetch by sleeping.
            # If _can_fetch were to return False, it means a more complex rule (like robots.txt)
            # disallowed fetching, and we should not proceed.
            print(f"INFO: Fetching disallowed for {url} by politeness rules (e.g. robots.txt).")
            return None

        headers = {"User-Agent": self._get_user_agent()}

        # print(f"DEBUG: Fetching {url} with User-Agent: {headers['User-Agent']}")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)

            self.last_request_time[domain] = time.time() # Update last request time *after* successful fetch
            return response.text
        except requests.exceptions.HTTPError as e:
            print(f"ERROR: HTTP error fetching {url}: {e}")
        except requests.exceptions.ConnectionError as e:
            print(f"ERROR: Connection error fetching {url}: {e}")
        except requests.exceptions.Timeout as e:
            print(f"ERROR: Timeout error fetching {url}: {e}")
        except requests.exceptions.RequestException as e: # Catching broader exceptions
            print(f"ERROR: General error fetching {url}: {e}")
        return None

if __name__ == '__main__':
    fetcher = Fetcher(delay_between_requests=2) # Set a 2-second delay for politeness

    print("Fetching example.com (first request):")
    content1 = fetcher.fetch_url("http://example.com")
    if content1:
        print(f"  Successfully fetched content from example.com (first 100 chars):\n  '{content1[:100].strip()}...'")

    # This request should be delayed by ~2 seconds due to the delay_between_requests setting.
    print("\nFetching example.com again (should be delayed):")
    start_time = time.time()
    content2 = fetcher.fetch_url("http://example.com")
    end_time = time.time()
    print(f"  Second request to example.com took {end_time - start_time:.2f} seconds.")
    if content2:
        print(f"  Successfully fetched content again.")

    print("\nAttempting to fetch a non-existent page:")
    fetcher.fetch_url("http://example.com/nonexistentpage12345.html")

    print("\nAttempting to fetch a URL from a different domain (should not be delayed by previous example.com requests):")
    # Using a known service that returns your IP, good for testing if requests go out.
    content_httpbin = fetcher.fetch_url("https://httpbin.org/get")
    if content_httpbin:
        print(f"  Successfully fetched content from httpbin.org/get.")

    print("\nAttempting to fetch an invalid URL:")
    fetcher.fetch_url("htp:/invalid-url")

    print("\nFetcher with no user agents (should use fallback):")
    fetcher_no_ua = Fetcher(user_agent_list=[])
    content_no_ua = fetcher_no_ua.fetch_url("http://example.com")
    if content_no_ua:
        print(f"  Successfully fetched with fallback UA.")
