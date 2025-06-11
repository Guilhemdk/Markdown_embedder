import unittest
from unittest.mock import MagicMock, patch, call # Added call
from datetime import datetime, timezone, timedelta
import os
import json # For loading sample data if needed, or comparing dicts

from news_scrapper.parser.parser import Parser
from news_scrapper.analyzer.structure_analyzer import StructureAnalyzer # For mocking
# from news_scrapper.planner.planner import Planner # For type hinting/mocking planner_ref

SAMPLE_DATA_DIR = os.path.join(os.path.dirname(__file__), "sample_data")

# Mock Planner and StructureAnalyzer for Parser tests
class MockPlannerForParser:
    def __init__(self):
        self.updated_selectors = None
        self.saved_config = False
        self.llm_flag_set = None

    def update_source_extraction_selectors(self, source_name, selectors_dict):
        print(f"MockPlannerForParser: update_source_extraction_selectors called for {source_name} with {selectors_dict}")
        self.updated_selectors = selectors_dict
        # Simulate source_config update if parser relies on it being immediate (it does via local copy)
        return True

    def save_config(self):
        print("MockPlannerForParser: save_config called")
        self.saved_config = True

    def set_llm_analysis_flag(self, source_name, flag_status):
        print(f"MockPlannerForParser: set_llm_analysis_flag for {source_name} to {flag_status}")
        self.llm_flag_set = (source_name, flag_status)
        return True

class TestParserAdvanced(unittest.TestCase):
    def setUp(self):
        self.mock_monitor = MagicMock()
        self.mock_planner_ref = MockPlannerForParser() # Use our detailed mock
        self.mock_structure_analyzer = MagicMock(spec=StructureAnalyzer)

        self.parser = Parser(monitor_instance=self.mock_monitor,
                             planner_reference=self.mock_planner_ref,
                             structure_analyzer_instance=self.mock_structure_analyzer)

        # Make sure parser.crawler is mocked if it's used by _parse_with_general_ai and might not init in test env
        if self.parser.crawler is None: # If WebCrawler init failed (e.g. no internet for model download)
            self.parser.crawler = MagicMock()
            # Define return value for crawler.read if needed by tests directly calling _parse_with_general_ai
            mock_ai_result = MagicMock()
            mock_ai_result.text = "AI extracted text"
            mock_ai_result.metadata = {"title": "AI Title", "date": "2024-01-01T00:00:00Z"}
            self.parser.crawler.read.return_value = mock_ai_result


        # Sample HTML and URL
        self.sample_url = "http://example.com/article1"
        self.sample_html = "<html><head><title>Original Title</title></head><body><p>Original content.</p></body></html>"
        self.source_config_empty = {"name": "TestHTMLSource"} # No selectors, LLM pending by default

        # Sample HTML for schema.org
        self.html_with_schema = """
        <html><head><title>Schema Title</title></head><body>
        <script type="application/ld+json">
        {
            "@context": "http://schema.org",
            "@type": "NewsArticle",
            "headline": "Schema Headline",
            "articleBody": "Schema article body content.",
            "datePublished": "2024-03-15T12:00:00Z",
            "author": {"@type": "Person", "name": "Schema Author"}
        }
        </script>
        <p>Some other text.</p></body></html>
        """
        self.url_with_schema = "http://example.com/schemapage"
        self.source_config_schema = {"name": "SchemaSource", "base_url": self.url_with_schema}

        # Sample HTML for custom selectors
        self.html_for_custom = """
        <html><head><title>Custom Title Here</title></head><body>
        <h1 class="custom-title-class">Actual Title</h1>
        <div class="custom-content-class"><p>First paragraph.</p><p>Second paragraph.</p></div>
        <span class="custom-author-class">Custom Author</span>
        <time class="custom-date-class" datetime="2024-02-10T10:00:00Z">Feb 10, 2024</time>
        </body></html>
        """
        self.url_for_custom = "http://example.com/custompage"
        self.source_config_custom = {
            "name": "CustomSource", "base_url": self.url_for_custom,
            "extraction_selectors": {
                "article_title_selector": "h1.custom-title-class",
                "article_content_selector": "div.custom-content-class p", # Will get multiple <p>
                "article_author_selector": ".custom-author-class",
                "article_date_selector": "time.custom-date-class[datetime]"
            },
            "llm_analysis_pending": False
        }


    def test_is_data_sufficient(self):
        self.assertTrue(self.parser._is_data_sufficient({"title": "t", "text": "c"}))
        self.assertFalse(self.parser._is_data_sufficient({"title": "t", "text": ""}))
        self.assertFalse(self.parser._is_data_sufficient({"title": "", "text": "c"}))
        self.assertFalse(self.parser._is_data_sufficient(None))
        self.assertFalse(self.parser._is_data_sufficient({"foo": "bar"}))

    def test_normalize_extracted_data(self):
        raw = {"headline": "A Title", "articleBody": "Content here.", "author": {"name": "John Doe"}, "datePublished": "2024-01-01"}
        norm = self.parser._normalize_extracted_data(raw, "http://example.com", "test_method")
        self.assertEqual(norm["title"], "A Title")
        self.assertEqual(norm["text"], "Content here.")
        self.assertEqual(norm["authors"], ["John Doe"])
        self.assertEqual(norm["published_date_utc"], datetime(2024,1,1, tzinfo=timezone.utc))
        self.assertEqual(norm["url"], "http://example.com")
        self.assertEqual(norm["extraction_method"], "test_method")

    # --- Test individual parsing strategies (mocking underlying tools if complex) ---
    def test_parse_with_custom_selectors_success(self):
        result = self.parser._parse_with_custom_selectors(self.html_for_custom, self.url_for_custom, self.source_config_custom)
        self.assertIsNotNone(result)
        self.assertEqual(result.get("title"), "Actual Title")
        self.assertIn("First paragraph.\nSecond paragraph.", result.get("text", ""))
        self.assertIn("Custom Author", result.get("authors", []))
        self.assertEqual(result.get("published_date_utc"), datetime(2024,2,10,10,0,0, tzinfo=timezone.utc))
        self.assertEqual(result.get("extraction_method"), "custom_css")

    def test_parse_with_schema_org_success(self):
        result = self.parser._parse_with_schema_org(self.html_with_schema, self.url_with_schema)
        self.assertIsNotNone(result)
        self.assertEqual(result.get("title"), "Schema Headline")
        self.assertEqual(result.get("text"), "Schema article body content.")
        self.assertIn("Schema Author", result.get("authors", []))
        self.assertEqual(result.get("published_date_utc"), datetime(2024,3,15,12,0,0, tzinfo=timezone.utc))
        self.assertEqual(result.get("extraction_method"), "schema_org_newsarticle") # or article

    @patch.object(Parser, '_parse_generic_date_to_utc', return_value=datetime(2024,1,1, tzinfo=timezone.utc)) # Mock date parsing for simplicity
    def test_parse_with_general_ai_success(self, mock_date_parser):
        # Ensure self.parser.crawler and its 'read' method are properly mocked if WebCrawler init might fail
        mock_ai_read_result = MagicMock()
        mock_ai_read_result.text = "AI extracted general text"
        mock_ai_read_result.metadata = {"title": "AI General Title", "date": "2024-01-01T00:00:00Z", "author": "AI Author"}
        self.parser.crawler.read.return_value = mock_ai_read_result # Patching the read method of the mocked crawler

        result = self.parser._parse_with_general_ai(self.sample_html, self.sample_url)
        self.assertIsNotNone(result)
        self.assertEqual(result.get("title"), "AI General Title")
        self.assertEqual(result.get("text"), "AI extracted general text")
        self.assertIn("AI Author", result.get("authors", []))
        self.assertEqual(result.get("extraction_method"), "general_ai")

    # --- Test parse_content orchestrator ---
    @patch.object(Parser, '_parse_with_custom_selectors')
    @patch.object(Parser, '_parse_with_schema_org')
    @patch.object(Parser, '_parse_with_general_ai')
    def test_parse_content_uses_custom_if_sufficient(self, mock_ai, mock_schema, mock_custom):
        mock_custom.return_value = {"title": "Custom Title", "text": "Custom Text", "extraction_method": "custom_css"}
        self.parser.parse_content("html", "url", self.source_config_custom) # source_config_custom has selectors
        mock_custom.assert_called_once()
        mock_schema.assert_not_called()
        # mock_ai might be called depending on logic (e.g. always call for comparison)
        # For now, assuming it's not called if custom is sufficient. Adjust if logic changes.

    @patch.object(Parser, '_parse_with_custom_selectors', return_value=None) # Custom fails
    @patch.object(Parser, '_parse_with_schema_org')
    @patch.object(Parser, '_parse_with_general_ai')
    def test_parse_content_falls_back_to_schema(self, mock_ai, mock_schema, mock_custom):
        mock_schema.return_value = {"title": "Schema Title", "text": "Schema Text", "extraction_method": "schema_org"}
        self.parser.parse_content("html", "url", self.source_config_empty)
        mock_custom.assert_called_once()
        mock_schema.assert_called_once()
        # mock_ai call depends on whether schema was sufficient or if AI is always called.

    @patch.object(Parser, '_parse_with_custom_selectors', return_value=None)
    @patch.object(Parser, '_parse_with_schema_org', return_value=None) # Schema also fails
    @patch.object(Parser, '_parse_with_general_ai')
    def test_parse_content_falls_back_to_general_ai(self, mock_ai, mock_schema, mock_custom):
        mock_ai.return_value = {"title": "AI Title", "text": "AI Text", "extraction_method": "general_ai"}
        self.parser.parse_content("html", "url", self.source_config_empty)
        mock_custom.assert_called_once()
        mock_schema.assert_called_once()
        mock_ai.assert_called_once() # Should be called as others failed

    # --- Test LLM Trigger Logic ---
    @patch.object(Parser, '_parse_with_custom_selectors', side_effect=[None, {"title": "LLM Title", "text": "LLM Text", "extraction_method":"custom_css_after_llm"}]) # First call no selectors, second call has new ones
    @patch.object(Parser, '_parse_with_schema_org', return_value=None)
    @patch.object(Parser, '_parse_with_general_ai', return_value=None) # All initial methods return insufficient data
    def test_parse_content_triggers_llm_and_reparses(self, mock_ai, mock_schema, mock_custom_parse_calls):
        source_name_llm = "LLMSourceTest"
        llm_test_config = {"name": source_name_llm, "llm_analysis_pending": True, "extraction_selectors": None}

        # Mock StructureAnalyzer to return some selectors
        dummy_llm_selectors = {"article_title_selector": "h1.llm", "article_content_selector": "div.llm"}
        self.mock_structure_analyzer.generate_extraction_selectors.return_value = dummy_llm_selectors

        result = self.parser.parse_content(self.sample_html, self.sample_url, llm_test_config)

        self.mock_structure_analyzer.generate_extraction_selectors.assert_called_once_with(self.sample_url, self.sample_html)
        self.assertEqual(self.mock_planner_ref.updated_selectors, dummy_llm_selectors)
        self.assertTrue(self.mock_planner_ref.saved_config)
        self.assertEqual(mock_custom_parse_calls.call_count, 2) # Initial try (fail), second try (with LLM selectors)
        self.assertIsNotNone(result)
        self.assertEqual(result.get("title"), "LLM Title") # From the second call to _parse_with_custom_selectors
        self.assertEqual(result.get("extraction_method"), "custom_css_after_llm") # Ensure it's from the re-parse


    @patch.object(Parser, '_parse_with_general_ai', return_value={"title":"AI Fallback", "text":"Text"}) # Ensure general AI has something
    def test_parse_content_llm_fails_uses_general_ai(self, mock_ai):
        source_name_llm_fail = "LLMSourceFailTest"
        llm_fail_config = {"name": source_name_llm_fail, "llm_analysis_pending": True, "extraction_selectors": None}

        self.mock_structure_analyzer.generate_extraction_selectors.return_value = None # LLM returns no selectors

        # Mock other parsing methods to return None or insufficient
        with patch.object(self.parser, '_parse_with_custom_selectors', return_value=None), \
             patch.object(self.parser, '_parse_with_schema_org', return_value=None):
            result = self.parser.parse_content(self.sample_html, self.sample_url, llm_fail_config)

        self.mock_structure_analyzer.generate_extraction_selectors.assert_called_once()
        self.assertEqual(self.mock_planner_ref.llm_flag_set, (source_name_llm_fail, False)) # Flag set to False
        self.assertTrue(self.mock_planner_ref.saved_config)
        self.assertIsNotNone(result)
        self.assertEqual(result.get("title"), "AI Fallback") # Should use general AI's result

if __name__ == '__main__':
    unittest.main()
