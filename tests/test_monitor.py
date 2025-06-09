import unittest
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta
import time # For time.sleep if testing delays that involve it.

from news_scrapper.monitor.monitor import Monitor

class TestMonitor(unittest.TestCase):
    def setUp(self):
        # Mock planner_reference for testing rate limit feedback if Monitor expects it
        self.mock_planner = MagicMock()
        self.mock_planner.crawl_delays_cache = {} # Simulate the cache

        self.monitor = Monitor(log_to_console=False, planner_reference=self.mock_planner)
        # log_to_console=False to keep test output clean

    def test_log_event_adds_to_log(self):
        initial_log_count = len(self.monitor.get_event_log())
        self.monitor.log_event("INFO", "Test event for log.", {"detail1": "value1"})
        self.assertEqual(len(self.monitor.get_event_log()), initial_log_count + 1)

        last_event = self.monitor.get_event_log()[-1]
        self.assertEqual(last_event["type"], "INFO")
        self.assertEqual(last_event["message"], "Test event for log.")
        self.assertEqual(last_event["details"]["detail1"], "value1")
        self.assertTrue("timestamp" in last_event)

    def test_report_failure_logs_error_event(self):
        self.monitor.report_failure("TestComponent", "Something broke", url="http://example.com/broken")
        last_event = self.monitor.get_event_log()[-1]
        self.assertEqual(last_event["type"], "ERROR")
        self.assertIn("TestComponent", last_event["message"])
        self.assertIn("Something broke", last_event["message"])
        self.assertEqual(last_event["details"]["url"], "http://example.com/broken")
        self.assertEqual(last_event["details"]["component"], "TestComponent")

    def test_is_article_new_by_date_recent(self):
        recent_date = datetime.now(timezone.utc) - timedelta(days=1)
        self.assertTrue(self.monitor.is_article_new_by_date("article1", recent_date, recency_delta_days=2))

    def test_is_article_new_by_date_old(self):
        old_date = datetime.now(timezone.utc) - timedelta(days=3)
        self.assertFalse(self.monitor.is_article_new_by_date("article2", old_date, recency_delta_days=2))

    def test_is_article_new_by_date_none(self):
        # Depending on policy, None date might be new or old. Current Monitor treats as new.
        self.assertTrue(self.monitor.is_article_new_by_date("article3", None, recency_delta_days=2))

    def test_is_rate_limited_status_code_429_increases_delay(self):
        domain = "ratelimited.com"
        url = f"http://{domain}/api"
        initial_delay = self.mock_planner.crawl_delays_cache.get(domain, 1) # Default to 1 if not present

        self.assertTrue(self.monitor.is_rate_limited("Fetcher", url, http_status_code=429))

        self.assertIn(domain, self.mock_planner.crawl_delays_cache)
        self.assertGreater(self.mock_planner.crawl_delays_cache[domain], initial_delay)

    def test_is_rate_limited_no_planner_reference(self):
        monitor_no_planner = Monitor(log_to_console=False, planner_reference=None)
        # This should still return True for rate limit detection, but not attempt to update delays
        self.assertTrue(monitor_no_planner.is_rate_limited("Fetcher", "http://example.com/api", http_status_code=429))
        # And no error should occur due to planner_reference being None

    def test_is_rate_limited_keyword_increases_delay(self):
        domain = "captcha-site.com"
        url = f"http://{domain}/login"
        initial_delay = self.mock_planner.crawl_delays_cache.get(domain, 1)

        self.assertTrue(self.monitor.is_rate_limited("Fetcher", url, content_snippet="please enter captcha now"))
        self.assertIn(domain, self.mock_planner.crawl_delays_cache)
        self.assertGreater(self.mock_planner.crawl_delays_cache[domain], initial_delay)


if __name__ == '__main__':
    unittest.main()
