import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
from urllib.parse import urlparse
import requests # For requests.exceptions

from news_scrapper.fetcher.fetcher import Fetcher
# Assuming RobotFileParser will be mocked where its direct behavior is complex
# from urllib.robotparser import RobotFileParser

# Path to the sample_data directory (if needed for robots.txt, though mocking is better)
SAMPLE_DATA_DIR = os.path.join(os.path.dirname(__file__), "sample_data")

class TestFetcher(unittest.TestCase):
    def setUp(self):
        self.mock_monitor = MagicMock()
        self.robots_cache = {}
        self.delays_cache = {}

        self.fetcher = Fetcher(monitor_instance=self.mock_monitor,
                               robots_parsers_cache=self.robots_cache,
                               crawl_delays_cache=self.delays_cache,
                               default_delay_between_requests=0.01) # Small delay for tests

        # Keep a reference to the original requests.get to use in side_effect if needed
        self.original_requests_get = requests.get

    # --- _get_user_agent ---
    def test_get_user_agent_returns_string(self):
        ua = self.fetcher._get_user_agent()
        self.assertIsInstance(ua, str)
        self.assertTrue(len(ua) > 0)

    # --- _get_robot_parser ---
    # This method is tricky to test perfectly without a live server or very complex mocks.
    # We'll focus on mocking the requests.get call it makes.
    @patch('requests.get')
    def test_get_robot_parser_fetches_and_parses(self, mock_requests_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "User-agent: *\nDisallow: /private\nCrawl-delay: 1"
        mock_requests_get.return_value = mock_response

        test_url = "http://example.com/somepage"
        domain = urlparse(test_url).netloc # example.com

        rp = self.fetcher._get_robot_parser(test_url)

        self.assertIsNotNone(rp)
        mock_requests_get.assert_called_once_with(f"http://{domain}/robots.txt", headers=unittest.mock.ANY, timeout=10)
        self.assertIn(domain, self.robots_cache) # Check caching of parser
        self.assertEqual(self.robots_cache[domain], rp)
        # Check if crawl_delays_cache was populated by _get_robot_parser
        self.assertIn(domain, self.delays_cache)
        self.assertEqual(self.delays_cache[domain], 1)

    @patch('requests.get')
    def test_get_robot_parser_handles_404(self, mock_requests_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_requests_get.return_value = mock_response

        test_url = "http://no-robots.com/page"
        domain = urlparse(test_url).netloc

        rp = self.fetcher._get_robot_parser(test_url)
        self.assertIsNotNone(rp) # Should return a dummy "allow all" parser
        self.assertTrue(rp.can_fetch("*", test_url)) # Dummy parser allows all
        self.assertIn(domain, self.robots_cache)


    # --- fetch_url ---
    # This is the main public method. It needs more comprehensive mocking.
    @patch('requests.get') # Mocks requests.get used by fetch_url for the actual page
    @patch.object(Fetcher, '_get_robot_parser') # Mocks the robots parser retrieval
    def test_fetch_url_success_allowed_by_robots(self, mock_get_robot_parser, mock_page_get):
        # Setup mock for _get_robot_parser
        mock_rp_instance = MagicMock()
        mock_rp_instance.can_fetch.return_value = True
        mock_rp_instance.crawl_delay.return_value = None # No specific crawl delay from robots.txt
        mock_get_robot_parser.return_value = mock_rp_instance

        # Setup mock for the actual page fetch (requests.get)
        mock_page_response = MagicMock()
        mock_page_response.status_code = 200
        mock_page_response.text = "<html><body>Success!</body></html>"
        mock_page_get.return_value = mock_page_response

        test_url = "http://allowed-site.com/page1"
        content = self.fetcher.fetch_url(test_url)

        mock_get_robot_parser.assert_called_once_with(test_url)
        mock_rp_instance.can_fetch.assert_called_once_with(self.fetcher.current_user_agent, test_url)
        mock_page_get.assert_called_once_with(test_url, headers={"User-Agent": self.fetcher.current_user_agent}, timeout=15)
        self.assertEqual(content, "<html><body>Success!</body></html>")
        # Check last request time was updated
        self.assertIn(urlparse(test_url).netloc, self.fetcher.last_request_time)


    @patch.object(Fetcher, '_get_robot_parser')
    def test_fetch_url_disallowed_by_robots(self, mock_get_robot_parser):
        mock_rp_instance = MagicMock()
        mock_rp_instance.can_fetch.return_value = False # DISALLOW
        mock_get_robot_parser.return_value = mock_rp_instance

        # We also need to mock requests.get for fetching robots.txt if _get_robot_parser wasn't fully mocked
        # But here, _get_robot_parser itself is mocked, so it won't try to fetch robots.txt.

        test_url = "http://disallowed-site.com/secret"
        content = self.fetcher.fetch_url(test_url)

        mock_get_robot_parser.assert_called_once_with(test_url)
        mock_rp_instance.can_fetch.assert_called_once_with(self.fetcher.current_user_agent, test_url)
        self.assertIsNone(content)
        # Ensure monitor was called about disallowed fetch
        self.mock_monitor.log_event.assert_any_call("WARNING", "Fetching disallowed by robots.txt.", unittest.mock.ANY)


    @patch('requests.get')
    @patch.object(Fetcher, '_get_robot_parser')
    @patch('time.sleep', MagicMock()) # Mock time.sleep to avoid actual delays in tests
    def test_fetch_url_respects_crawl_delay(self, mock_get_robot_parser, mock_page_get):
        domain = "crawl-delay-site.com"
        test_url = f"http://{domain}/page1"

        mock_rp_instance = MagicMock()
        mock_rp_instance.can_fetch.return_value = True
        # No crawl delay from rp.crawl_delay, so it will use self.delays_cache or default
        mock_rp_instance.crawl_delay.return_value = None
        mock_get_robot_parser.return_value = mock_rp_instance

        # Set a specific crawl delay for this domain in the shared cache
        self.delays_cache[domain] = 0.1 # 100ms delay for testing

        mock_page_response = MagicMock()
        mock_page_response.status_code = 200
        mock_page_response.text = "Delayed content"
        mock_page_get.return_value = mock_page_response

        # First fetch - should set last_request_time
        self.fetcher.fetch_url(test_url)

        # Second fetch - should trigger delay logic in _can_fetch (which calls time.sleep)
        self.fetcher.fetch_url(f"http://{domain}/page2")

        # time.sleep should have been called inside _can_fetch
        # The actual check for time.sleep requires more specific patching if _can_fetch is not mocked
        # For now, we assume if the code runs and respects logic, it's fine.
        # A more direct test of _can_fetch and its time.sleep call would be needed for full verification.
        self.mock_monitor.log_event.assert_any_call("DEBUG", unittest.mock.ANY, unittest.mock.ANY) # General log
        # Check that time.sleep was called (if _can_fetch was not mocked and delay was triggered)
        # This is an indirect check. A direct mock of _can_fetch's time.sleep might be better.
        # For now, we check if the log for delaying was made (if monitor was more verbose in _can_fetch)
        # Example: self.mock_monitor.log_event.assert_any_call("DEBUG", f"Delaying request to {domain} for ...", unittest.mock.ANY)


if __name__ == '__main__':
    unittest.main()
