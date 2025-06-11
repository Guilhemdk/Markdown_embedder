import unittest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timezone, timedelta
import os
import json

from news_scrapper.parser.parser import Parser
from news_scrapper.analyzer.structure_analyzer import StructureAnalyzer
# from news_scrapper.planner.planner import Planner # For type hinting/mocking planner_ref (actual import not needed for mock)

SAMPLE_DATA_DIR = os.path.join(os.path.dirname(__file__), "sample_data")

class MockPlannerForParserTests: # Renamed to avoid conflict with other mocks if any
    def __init__(self):
        self.updated_selectors_log = []
        self.saved_config_log = []
        self.llm_flag_log = []

    def update_source_extraction_selectors(self, source_name, selectors_dict):
        # print(f"MockPlannerForParserTests: update_source_extraction_selectors for {source_name} with {selectors_dict}")
        self.updated_selectors_log.append({"source_name": source_name, "selectors": selectors_dict})
        return True

    def save_config(self):
        # print("MockPlannerForParserTests: save_config called")
        self.saved_config_log.append(True)

    def set_llm_analysis_flag(self, source_name, flag_status):
        # print(f"MockPlannerForParserTests: set_llm_analysis_flag for {source_name} to {flag_status}")
        self.llm_flag_log.append({"source_name": source_name, "status": flag_status})
        return True

class TestParserMultiStrategy(unittest.TestCase): # Renamed class
    def setUp(self):
        self.mock_monitor = MagicMock()
        self.mock_planner_ref = MockPlannerForParserTests()
        self.mock_structure_analyzer = MagicMock(spec=StructureAnalyzer)

        self.parser = Parser(monitor_instance=self.mock_monitor,
                             planner_reference=self.mock_planner_ref,
                             structure_analyzer_instance=self.mock_structure_analyzer)

        # Mock parser.crawler if it's used and might not init in test env
        if self.parser.crawler is None:
            self.parser.crawler = MagicMock()

        # Default mock for general AI if not overridden in a specific test
        self.mock_ai_result_default = MagicMock()
        self.mock_ai_result_default.text = "Default AI text"
        self.mock_ai_result_default.metadata = {"title": "Default AI Title", "date": "2024-01-01T00:00:00Z"}
        self.parser.crawler.read.return_value = self.mock_ai_result_default

        self.sample_url = "http://example.com/article_sample"
        self.sample_html = "<html><head><title>Sample Article</title></head><body><article><h1>Main Title</h1><p>Content here.</p></article></body></html>"
        self.empty_source_config = {"name": "TestEmptyConfig"}


    def test_is_data_sufficient_true(self):
        self.assertTrue(self.parser._is_data_sufficient({"title": "A Title", "text": "Some content."}))

    def test_is_data_sufficient_false_no_title(self):
        self.assertFalse(self.parser._is_data_sufficient({"text": "Some content."}))

    def test_is_data_sufficient_false_no_text(self):
        self.assertFalse(self.parser._is_data_sufficient({"title": "A Title"}))

    def test_is_data_sufficient_false_empty(self):
        self.assertFalse(self.parser._is_data_sufficient({"title": " ", "text": "  "}))
        self.assertFalse(self.parser._is_data_sufficient(None))


    def test_normalize_extracted_data(self):
        raw = {"headline": " Test Title ", "articleBody": " Body text. ", "author": {"name": " Author Name "}, "datePublished": "2023-10-05T10:00:00+02:00"}
        norm = self.parser._normalize_extracted_data(raw, self.sample_url, "test_method")
        self.assertEqual(norm["title"], "Test Title")
        self.assertEqual(norm["text"], "Body text.")
        self.assertEqual(norm["authors"], ["Author Name"])
        self.assertEqual(norm["published_date_utc"], datetime(2023, 10, 5, 8, 0, 0, tzinfo=timezone.utc)) # Converted to UTC
        self.assertEqual(norm["url"], self.sample_url)
        self.assertEqual(norm["extraction_method"], "test_method")


    def test_parse_with_custom_selectors_success(self):
        html = "<html><body><h1 class='article-headline'>Title</h1><div class='content'><p>P1</p><p>P2</p></div></body></html>"
        config = {"extraction_selectors": {"article_title_selector": "h1.article-headline", "article_content_selector": "div.content p"}}
        result = self.parser._parse_with_custom_selectors(html, self.sample_url, config)
        self.assertEqual(result.get("title"), "Title")
        self.assertEqual(result.get("text"), "P1\nP2")
        self.assertEqual(result.get("extraction_method"), "custom_css")

    @patch('extruct.extract')
    def test_parse_with_schema_org_success(self, mock_extruct_extract):
        mock_extruct_extract.return_value = {
            "json-ld": [{"@type": "NewsArticle", "headline": "SchemaTitle", "articleBody": "SchemaText", "datePublished": "2023-01-01T12:00:00Z"}]
        }
        result = self.parser._parse_with_schema_org("<html></html>", self.sample_url)
        self.assertEqual(result.get("title"), "SchemaTitle")
        self.assertEqual(result.get("text"), "SchemaText")
        self.assertEqual(result.get("extraction_method"), "schema_org_newsarticle")

    def test_parse_with_general_ai_success(self):
        # Uses the default mock_ai_result_default from setUp
        result = self.parser._parse_with_general_ai(self.sample_html, self.sample_url)
        self.assertEqual(result.get("title"), "Default AI Title")
        self.assertEqual(result.get("text"), "Default AI text")
        self.assertEqual(result.get("extraction_method"), "general_ai")

    # --- Test parse_content orchestrator logic ---
    def test_parse_content_prioritizes_custom_then_schema_then_ai(self):
        # Custom is sufficient
        with patch.object(self.parser, '_parse_with_custom_selectors', return_value={"title":"Custom", "text":"Content", "extraction_method":"custom"}) as m_custom, \
             patch.object(self.parser, '_parse_with_schema_org') as m_schema, \
             patch.object(self.parser, '_parse_with_general_ai') as m_ai:
            result = self.parser.parse_content(self.sample_html, self.sample_url, {"extraction_selectors": {"title": "h1"}})
            m_custom.assert_called_once()
            m_schema.assert_not_called() # Should not be called if custom is sufficient
            m_ai.assert_called_once() # AI is called for comparison/ultimate fallback
            self.assertEqual(result.get("extraction_method"), "custom")

        # Custom fails, Schema is sufficient
        with patch.object(self.parser, '_parse_with_custom_selectors', return_value={"title":None, "text":None, "extraction_method":"custom"}) as m_custom, \
             patch.object(self.parser, '_parse_with_schema_org', return_value={"title":"Schema", "text":"Content", "extraction_method":"schema"}) as m_schema, \
             patch.object(self.parser, '_parse_with_general_ai') as m_ai:
            result = self.parser.parse_content(self.sample_html, self.sample_url, {"extraction_selectors": {"title": "h1"}})
            m_custom.assert_called_once()
            m_schema.assert_called_once()
            m_ai.assert_called_once()
            self.assertEqual(result.get("extraction_method"), "schema")

        # Custom and Schema fail, AI is sufficient
        with patch.object(self.parser, '_parse_with_custom_selectors', return_value=None) as m_custom, \
             patch.object(self.parser, '_parse_with_schema_org', return_value=None) as m_schema, \
             patch.object(self.parser, '_parse_with_general_ai', return_value={"title":"AI", "text":"Content", "extraction_method":"ai"}) as m_ai:
            result = self.parser.parse_content(self.sample_html, self.sample_url, self.empty_source_config)
            m_custom.assert_called_once()
            m_schema.assert_called_once()
            m_ai.assert_called_once()
            self.assertEqual(result.get("extraction_method"), "ai")


    def test_parse_content_llm_trigger_success_updates_and_reparses(self):
        source_config_for_llm = {"name": "LLMTriggerSource", "llm_analysis_pending": True, "extraction_selectors": None}
        # Initial parsing attempts fail or are insufficient
        self.parser._parse_with_custom_selectors = MagicMock(return_value=None)
        self.parser._parse_with_schema_org = MagicMock(return_value=None)
        self.parser._parse_with_general_ai = MagicMock(return_value={"title": "Weak AI", "text": None}) # Insufficient

        # LLM returns new selectors
        llm_generated_selectors = {"article_title_selector": "h1.llm_title", "article_content_selector": "div.llm_content"}
        self.mock_structure_analyzer.generate_extraction_selectors.return_value = llm_generated_selectors

        # Mock custom selector parsing to return good data on the *second* call (after LLM)
        mock_custom_parse_results = [
            None, # First call (no selectors or existing ones failed)
            self.parser._normalize_extracted_data( # Second call (with LLM selectors)
                {"title": "Title From LLM Selectors", "text": "Content from LLM selectors"},
                self.sample_url,
                "custom_css_llm"
            )
        ]
        self.parser._parse_with_custom_selectors = MagicMock(side_effect=mock_custom_parse_results)

        result = self.parser.parse_content(self.sample_html, self.sample_url, source_config_for_llm)

        self.mock_structure_analyzer.generate_extraction_selectors.assert_called_once_with(self.sample_url, self.sample_html)
        self.assertIn({"source_name": "LLMTriggerSource", "selectors": llm_generated_selectors}, self.mock_planner_ref.updated_selectors_log)
        self.assertTrue(self.mock_planner_ref.saved_config) # Config should be saved
        self.assertEqual(self.parser._parse_with_custom_selectors.call_count, 2) # Called once before LLM, once after
        self.assertEqual(result.get("title"), "Title From LLM Selectors")
        self.assertEqual(result.get("extraction_method"), "custom_css_llm")
        # Check that llm_analysis_pending was updated in the local source_config copy
        self.assertFalse(source_config_for_llm.get("llm_analysis_pending"))


    def test_parse_content_llm_trigger_llm_fails(self):
        source_config_for_llm_fail = {"name": "LLMFailSource", "llm_analysis_pending": True, "extraction_selectors": None}
        self.parser._parse_with_custom_selectors = MagicMock(return_value=None)
        self.parser._parse_with_schema_org = MagicMock(return_value=None)
        # General AI provides some data, but it's deemed insufficient to prevent LLM trigger
        self.parser._parse_with_general_ai = MagicMock(return_value={"title": "AI Title only", "text": None, "extraction_method": "general_ai"})

        self.mock_structure_analyzer.generate_extraction_selectors.return_value = None # LLM fails

        result = self.parser.parse_content(self.sample_html, self.sample_url, source_config_for_llm_fail)

        self.mock_structure_analyzer.generate_extraction_selectors.assert_called_once()
        self.assertIn({"source_name": "LLMFailSource", "status": False}, self.mock_planner_ref.llm_flag_log)
        self.assertTrue(self.mock_planner_ref.saved_config)
        self.assertEqual(result.get("title"), "AI Title only") # Falls back to the (insufficient) AI data
        self.assertEqual(result.get("extraction_method"), "general_ai")


if __name__ == '__main__':
    unittest.main()
