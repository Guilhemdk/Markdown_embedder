import unittest
from unittest.mock import MagicMock, patch, mock_open
import os
import json

# Adjust import path
from news_scrapper.planner.planner import Planner
from news_scrapper.fetcher.fetcher import Fetcher
from news_scrapper.parser.parser import Parser
from news_scrapper.pipeline.pipeline import Pipeline
from news_scrapper.monitor.monitor import Monitor

# Define a path for a temporary test config file
TEST_CONFIG_DIR = os.path.join(os.path.dirname(__file__), "test_planner_config_temp")
TEST_SOURCES_JSON_PATH = os.path.join(TEST_CONFIG_DIR, "test_sources.json")

class TestPlanner(unittest.TestCase):
    def setUp(self):
        # Create a mock for each dependency
        self.mock_monitor = MagicMock(spec=Monitor)
        self.mock_fetcher = MagicMock(spec=Fetcher)
        self.mock_parser = MagicMock(spec=Parser)
        self.mock_pipeline = MagicMock(spec=Pipeline)

        # Ensure test config directory exists
        os.makedirs(TEST_CONFIG_DIR, exist_ok=True)

        # Default test sources data
        self.test_sources_data = {
            "sources": [
                {"name": "SourceA", "base_url": "http://sourceA.com", "rss_feed": "http://sourceA.com/feed.xml"},
                {"name": "SourceB", "base_url": "http://sourceB.com", "rss_feed": None}, # For RSS discovery
                {"name": "SourceC", "base_url": "http://sourceC.com/news", "rss_feed": "http://sourceC.com/rss",
                 "sections": [{"name": "politics", "url": "http://sourceC.com/news/politics"}]}
            ]
        }
        # Write it to the temporary test_sources.json
        with open(TEST_SOURCES_JSON_PATH, 'w') as f:
            json.dump(self.test_sources_data, f)

        # Initialize Planner with mocks and the path to the test config
        self.planner = Planner(config_path=TEST_SOURCES_JSON_PATH,
                               monitor_instance=self.mock_monitor,
                               fetcher_instance=self.mock_fetcher,
                               parser_instance=self.mock_parser,
                               pipeline_instance=self.mock_pipeline)

        # Planner's __init__ also initializes its own shared caches, which is fine.
        # We can also directly manipulate them for some tests if needed:
        # self.planner.crawl_delays_cache = {}
        # self.planner.robots_parsers_cache = {}


    def tearDown(self):
        # Clean up: remove the temporary config file and directory
        if os.path.exists(TEST_SOURCES_JSON_PATH):
            os.remove(TEST_SOURCES_JSON_PATH)
        if os.path.exists(TEST_CONFIG_DIR):
            os.rmdir(TEST_CONFIG_DIR)

    def test_load_config_success(self):
        self.assertEqual(len(self.planner.get_targets()), 3)
        self.assertEqual(self.planner.get_targets()[0]['name'], "SourceA")
        self.mock_monitor.log_event.assert_any_call("INFO", unittest.mock.ANY, {"path": TEST_SOURCES_JSON_PATH})


    @patch('builtins.open', side_effect=FileNotFoundError("File not found for test"))
    def test_load_config_file_not_found(self, mock_open_filenotfound):
        # Re-initialize planner with a non-existent path or rely on mock to prevent load in setUp
        # For this test, let's create a new planner instance to test its load_config directly
        # with a bad path, without affecting self.planner from setUp for other tests.
        temp_planner = Planner(config_path="non_existent_path.json", monitor_instance=self.mock_monitor)
        self.assertEqual(len(temp_planner.get_targets()), 0)
        self.mock_monitor.log_event.assert_any_call("ERROR", "Planner configuration file not found.", unittest.mock.ANY)


    def test_get_source_by_name(self):
        source = self.planner.get_source_by_name("SourceA")
        self.assertIsNotNone(source)
        self.assertEqual(source['base_url'], "http://sourceA.com")
        self.assertIsNone(self.planner.get_source_by_name("UnknownSource"))

    # --- RSS Discovery ---
    def test_discover_rss_feed_for_source_already_exists(self):
        # SourceA already has an RSS feed
        found_rss = self.planner.discover_rss_feed_for_source("SourceA")
        self.assertEqual(found_rss, "http://sourceA.com/feed.xml")
        self.mock_fetcher.fetch_url.assert_not_called() # Should not fetch if RSS exists

    def test_discover_rss_feed_for_source_success(self):
        # SourceB has no RSS feed, base_url "http://sourceB.com"
        source_b_url = self.test_sources_data["sources"][1]["base_url"]
        self.mock_fetcher.fetch_url.return_value = "<html><head><link rel='alternate' type='application/rss+xml' href='/discovered.xml'></head></html>"
        self.mock_parser.find_rss_links_in_html.return_value = [f"{source_b_url}/discovered.xml"]

        # Test without auto-saving config
        found_rss = self.planner.discover_rss_feed_for_source("SourceB", persist_changes=False)

        self.assertEqual(found_rss, f"{source_b_url}/discovered.xml")
        self.mock_fetcher.fetch_url.assert_called_once_with(source_b_url)
        self.mock_parser.find_rss_links_in_html.assert_called_once()
        source_b_config = self.planner.get_source_by_name("SourceB")
        self.assertEqual(source_b_config['rss_feed'], f"{source_b_url}/discovered.xml") # Updated in memory

    # --- Polling ---
    def test_poll_rss_feed_success(self):
        source_name = "SourceA"
        feed_url = self.test_sources_data["sources"][0]["rss_feed"]
        self.mock_fetcher.fetch_url.return_value = "<rss><channel><item><title>New Article</title><link>http://sourceA.com/article1</link><guid>1</guid></item></channel></rss>" # Sample XML

        # Mock parser to return one item
        parsed_items = [{"id": "1", "link": "http://sourceA.com/article1", "title": "New Article", "published_date_utc": datetime.now(timezone.utc)}]
        self.mock_parser.parse_rss_feed.return_value = parsed_items

        # Mock monitor to say article is new
        self.mock_monitor.is_article_new_by_date.return_value = True

        items_added = self.planner.poll_rss_feed(source_name, recency_delta_days=1)

        self.assertEqual(items_added, 1)
        self.mock_fetcher.fetch_url.assert_called_once_with(feed_url)
        self.mock_parser.parse_rss_feed.assert_called_once()
        self.mock_monitor.is_article_new_by_date.assert_called_once()
        self.mock_pipeline.add_item.assert_called_once_with(parsed_items[0])

    # --- Sitemap Processing ---
    # (Simplified: Test one call, assume recursion works if single call works)
    @patch.object(Planner, 'prime_domain_settings') # Mock priming for this specific test
    def test_process_sitemap_urlset(self, mock_prime_domain):
        sitemap_url = "http://sourceA.com/sitemap.xml" # Assumed, not from config for this test
        source_name = "SourceA"

        self.mock_fetcher.fetch_url.return_value = "<urlset><url><loc>http://sourceA.com/page1</loc><lastmod>2024-01-01T00:00:00Z</lastmod></url></urlset>"
        parsed_sitemap_items = [{'loc': 'http://sourceA.com/page1', 'lastmod_utc': datetime(2024,1,1, tzinfo=timezone.utc), 'source_sitemap_url': sitemap_url}]
        self.mock_parser.parse_sitemap.return_value = {'type': 'urlset', 'items': parsed_sitemap_items, 'source_sitemap_url': sitemap_url}
        self.mock_monitor.is_article_new_by_date.return_value = True

        items_added = self.planner.process_sitemap(source_name, sitemap_url, recency_delta_days=365)

        self.assertEqual(items_added, 1)
        mock_prime_domain.assert_called_with(sitemap_url) # Check priming was called for sitemap's URL
        self.mock_fetcher.fetch_url.assert_called_once_with(sitemap_url)
        self.mock_parser.parse_sitemap.assert_called_once()
        # Form the expected adapted item based on Planner's logic
        expected_adapted_item = {
            'id': 'http://sourceA.com/page1', 'link': 'http://sourceA.com/page1',
            'title': 'Sitemap: page1', # Based on Planner's title generation
            'published_date_utc': datetime(2024,1,1, tzinfo=timezone.utc),
            'source_sitemap_url': sitemap_url, 'type': 'sitemap_derived', 'source_name': source_name
        }
        self.mock_pipeline.add_item.assert_called_once_with(expected_adapted_item)

    # --- Fallback Crawl ---
    @patch.object(Planner, 'prime_domain_settings')
    def test_initiate_fallback_crawl_for_source(self, mock_prime_domain):
        source_name = "SourceB" # Configured with no RSS feed
        base_url = self.test_sources_data["sources"][1]["base_url"] # http://sourceB.com

        self.mock_fetcher.fetch_url.return_value = "<html><title>Crawled Page</title><body>Content</body></html>"
        # Mock parser.parse_content to return a dict like crawl4ai would
        parsed_content_data = {"url": base_url, "title": "Crawled Page", "text": "Content", "published_date_utc": datetime.now(timezone.utc)}
        self.mock_parser.parse_content.return_value = parsed_content_data
        self.mock_monitor.is_article_new_by_date.return_value = True

        items_added = self.planner.initiate_fallback_crawl_for_source(source_name, recency_delta_days=1)

        self.assertEqual(items_added, 1)
        # prime_domain_settings should be called for base_url
        mock_prime_domain.assert_any_call(base_url) # Or more specific if sections were tested
        self.mock_fetcher.fetch_url.assert_called_once_with(base_url)
        self.mock_parser.parse_content.assert_called_once()

        expected_adapted_item = {
            'id': base_url, 'link': base_url, 'title': 'Crawled Page',
            'published_date_utc': parsed_content_data['published_date_utc'],
            'text_content': 'Content', 'source_crawl_url': base_url,
            'source_name': source_name, 'type': 'fallback_crawl_derived'
        }
        self.mock_pipeline.add_item.assert_called_once_with(expected_adapted_item)

if __name__ == '__main__':
    unittest.main()
