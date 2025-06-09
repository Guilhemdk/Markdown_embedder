import unittest
from datetime import datetime, timezone, timedelta # Added timedelta for more date tests
import os # For loading sample data

# Assuming 'tests' and 'news_scrapper' are sibling directories at the project root
from news_scrapper.parser.parser import Parser
# from news_scrapper.monitor.monitor import Monitor # If testing with a real monitor

# Path to the sample_data directory
SAMPLE_DATA_DIR = os.path.join(os.path.dirname(__file__), "sample_data")

class TestParser(unittest.TestCase):
    def setUp(self):
        # self.mock_monitor = unittest.mock.MagicMock() # If Parser expects a monitor
        self.parser = Parser(monitor_instance=None) # Pass None or a mock monitor

        # Load sample data files
        with open(os.path.join(SAMPLE_DATA_DIR, "sample_page_with_rss.html"), 'r') as f:
            self.sample_html_with_rss = f.read()
        with open(os.path.join(SAMPLE_DATA_DIR, "sample_rss_feed.xml"), 'r') as f:
            self.sample_rss_xml = f.read()
        with open(os.path.join(SAMPLE_DATA_DIR, "sample_sitemap_index.xml"), 'r') as f:
            self.sample_sitemap_index_xml = f.read()
        with open(os.path.join(SAMPLE_DATA_DIR, "sample_sitemap_urlset.xml"), 'r') as f:
            self.sample_sitemap_urlset_xml = f.read()
        with open(os.path.join(SAMPLE_DATA_DIR, "robots_with_delay.txt"), 'r') as f:
            self.robots_txt_with_delay = f.read()

    # --- Tests for _parse_generic_date_to_utc ---
    def test_parse_generic_date_to_utc_valid_iso_z(self):
        dt_str = "2024-01-15T10:30:00Z"
        expected_dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        self.assertEqual(self.parser._parse_generic_date_to_utc(dt_str, "test_url_iso_z"), expected_dt)

    def test_parse_generic_date_to_utc_valid_iso_offset(self):
        dt_str = "2024-01-15T10:30:00+02:00" # Should convert to UTC
        expected_dt = datetime(2024, 1, 15, 8, 30, 0, tzinfo=timezone.utc)
        self.assertEqual(self.parser._parse_generic_date_to_utc(dt_str, "test_url_iso_offset"), expected_dt)

    def test_parse_generic_date_to_utc_naive_datetime(self):
        dt_naive = datetime(2024, 1, 15, 10, 30, 0)
        expected_dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc) # Assumes UTC
        self.assertEqual(self.parser._parse_generic_date_to_utc(dt_naive, "test_url_naive_dt"), expected_dt)

    def test_parse_generic_date_to_utc_aware_datetime_other_tz(self):
        dt_aware_est = datetime(2024, 1, 15, 5, 30, 0, tzinfo=timezone(timedelta(hours=-5)))
        expected_dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc) # Converted to UTC
        self.assertEqual(self.parser._parse_generic_date_to_utc(dt_aware_est, "test_url_aware_dt"), expected_dt)

    def test_parse_generic_date_to_utc_simple_date_str(self):
        dt_str = "2024-03-10" # Should parse as midnight UTC
        expected_dt = datetime(2024, 3, 10, 0, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(self.parser._parse_generic_date_to_utc(dt_str, "test_url_simple_date"), expected_dt)

    def test_parse_generic_date_to_utc_none_input(self):
        self.assertIsNone(self.parser._parse_generic_date_to_utc(None, "test_url_none"))

    def test_parse_generic_date_to_utc_invalid_string(self):
        self.assertIsNone(self.parser._parse_generic_date_to_utc("not a real date", "test_url_invalid_str"))

    # --- Tests for find_rss_links_in_html ---
    def test_find_rss_links_in_html_found(self):
        base_url = "http://example.com"
        # Uses self.sample_html_with_rss loaded in setUp
        expected_links = ["http://example.com/feed.rss"]
        self.assertEqual(self.parser.find_rss_links_in_html(self.sample_html_with_rss, base_url), expected_links)

    def test_find_rss_links_in_html_not_found(self):
        sample_html_no_rss = '<html><head></head><body>No RSS links</body></html>'
        base_url = "http://example.com"
        self.assertEqual(self.parser.find_rss_links_in_html(sample_html_no_rss, base_url), [])

    # --- Tests for parse_rss_feed ---
    def test_parse_rss_feed_valid(self):
        # Uses self.sample_rss_xml
        feed_url = "http://example.com/test_feed.xml"
        items = self.parser.parse_rss_feed(self.sample_rss_xml, feed_url)
        self.assertEqual(len(items), 2)

        self.assertEqual(items[0]['title'], "Item 1")
        self.assertEqual(items[0]['link'], "http://example.com/item1")
        self.assertEqual(items[0]['id'], "item1")
        self.assertEqual(items[0]['published_date_utc'], datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(items[0]['source_feed_url'], feed_url)

        self.assertEqual(items[1]['title'], "Item 2")
        self.assertEqual(items[1]['link'], "http://example.com/item2")
        self.assertEqual(items[1]['id'], "item2") # feedparser might make this the link if guid isPermaLink=false
        self.assertEqual(items[1]['published_date_utc'], datetime(2024, 1, 2, 13, 0, 0, tzinfo=timezone.utc))

    def test_parse_rss_feed_empty_content(self):
        self.assertEqual(self.parser.parse_rss_feed("", "http://example.com/empty.xml"), [])

    # --- Tests for parse_sitemap ---
    def test_parse_sitemap_index(self):
        # Uses self.sample_sitemap_index_xml
        sitemap_url = "http://example.com/sitemap_index.xml"
        parsed = self.parser.parse_sitemap(self.sample_sitemap_index_xml, sitemap_url)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['type'], 'sitemap_index')
        self.assertEqual(parsed['source_sitemap_url'], sitemap_url)
        self.assertIn("http://example.com/sitemap1.xml", parsed['sitemap_urls'])
        self.assertEqual(len(parsed['sitemap_urls']), 1)

    def test_parse_sitemap_urlset(self):
        # Uses self.sample_sitemap_urlset_xml
        sitemap_url = "http://example.com/sitemap_urlset.xml"
        parsed = self.parser.parse_sitemap(self.sample_sitemap_urlset_xml, sitemap_url)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['type'], 'urlset')
        self.assertEqual(parsed['source_sitemap_url'], sitemap_url)
        self.assertEqual(len(parsed['items']), 1)
        item = parsed['items'][0]
        self.assertEqual(item['loc'], "http://example.com/page1")
        self.assertEqual(item['lastmod_utc'], datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc))

    # --- Tests for parse_crawl_delay ---
    def test_parse_crawl_delay(self):
        # Uses self.robots_txt_with_delay
        self.assertEqual(self.parser.parse_crawl_delay(self.robots_txt_with_delay, "TestBot"), 5.0)
        self.assertEqual(self.parser.parse_crawl_delay(self.robots_txt_with_delay, "OtherBot"), 1.0) # Uses wildcard
        self.assertEqual(self.parser.parse_crawl_delay(self.robots_txt_with_delay, "*"), 1.0)
        self.assertIsNone(self.parser.parse_crawl_delay("User-agent: *\nDisallow: /", "*"))

    # TODO: Add tests for parse_content (might need to mock crawl4ai if it makes external calls during init/read)

if __name__ == '__main__':
    unittest.main()
