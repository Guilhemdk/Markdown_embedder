import unittest
from unittest.mock import MagicMock, patch, mock_open
import os
import json
from datetime import datetime, timezone # For use in mock data if needed

# Adjust import path
from news_scrapper.planner.planner import Planner
from news_scrapper.fetcher.fetcher import Fetcher
from news_scrapper.parser.parser import Parser
from news_scrapper.pipeline.pipeline import Pipeline
from news_scrapper.monitor.monitor import Monitor
from news_scrapper.analyzer.structure_analyzer import StructureAnalyzer # Import for mocking

TEST_CONFIG_DIR = os.path.join(os.path.dirname(__file__), "test_planner_config_temp")
TEST_SOURCES_JSON_PATH = os.path.join(TEST_CONFIG_DIR, "test_sources.json")

class TestPlanner(unittest.TestCase):
    def setUp(self):
        self.mock_monitor = MagicMock(spec=Monitor)
        self.mock_fetcher = MagicMock(spec=Fetcher)
        self.mock_parser = MagicMock(spec=Parser)
        self.mock_pipeline = MagicMock(spec=Pipeline)
        self.mock_structure_analyzer = MagicMock(spec=StructureAnalyzer)

        os.makedirs(TEST_CONFIG_DIR, exist_ok=True)

        self.test_sources_data = {
            "sources": [
                {
                    "name": "SourceA_WithSelectors",
                    "base_url": "http://sourceA.com", "rss_feed": "http://sourceA.com/feed.xml",
                    "parser_config_name": "siteA_custom", # New name
                    "extraction_selectors": {"title_selector": "h1.title", "content_selector": "div.article"}, # Note: keys changed from example
                    "llm_analysis_pending": False
                },
                {
                    "name": "SourceB_NoSelectors",
                    "base_url": "http://sourceB.com", "rss_feed": None,
                    "parser_config_name": "default",
                    "extraction_selectors": None,
                    "llm_analysis_pending": True # Explicitly true
                },
                {
                    "name": "SourceC_OldConfig",
                    "base_url": "http://sourceC.com/news", "rss_feed": "http://sourceC.com/rss",
                    "parser_config": "old_style_config_name" # Old key
                    # extraction_selectors and llm_analysis_pending are missing
                }
            ]
        }
        with open(TEST_SOURCES_JSON_PATH, 'w') as f:
            json.dump(self.test_sources_data, f)

        self.planner = Planner(config_path=TEST_SOURCES_JSON_PATH,
                               monitor_instance=self.mock_monitor,
                               fetcher_instance=self.mock_fetcher,
                               parser_instance=self.mock_parser,
                               pipeline_instance=self.mock_pipeline,
                               structure_analyzer_instance=self.mock_structure_analyzer)

    def tearDown(self):
        if os.path.exists(TEST_SOURCES_JSON_PATH):
            os.remove(TEST_SOURCES_JSON_PATH)
        if os.path.exists(TEST_CONFIG_DIR):
            os.rmdir(TEST_CONFIG_DIR) # rmdir only if empty, use shutil.rmtree if it might have other files

    def test_load_config_handles_new_and_old_fields(self):
        self.assertEqual(len(self.planner.get_targets()), 3)

        source_a = self.planner.get_source_by_name("SourceA_WithSelectors")
        self.assertIsNotNone(source_a)
        self.assertEqual(source_a.get('parser_config_name'), "siteA_custom")
        self.assertIsNotNone(source_a.get('extraction_selectors'))
        self.assertEqual(source_a['extraction_selectors']['title_selector'], "h1.title")
        self.assertEqual(source_a.get('llm_analysis_pending'), False)

        source_b = self.planner.get_source_by_name("SourceB_NoSelectors")
        self.assertIsNotNone(source_b)
        self.assertIsNone(source_b.get('extraction_selectors'))
        self.assertEqual(source_b.get('llm_analysis_pending'), True)

        source_c = self.planner.get_source_by_name("SourceC_OldConfig")
        self.assertIsNotNone(source_c)
        self.assertEqual(source_c.get('parser_config_name'), "old_style_config_name") # Migrated from 'parser_config'
        self.assertNotIn('parser_config', source_c) # Old key should be removed
        self.assertIsNone(source_c.get('extraction_selectors')) # Defaulted
        self.assertEqual(source_c.get('llm_analysis_pending'), True) # Defaulted because no selectors

    def test_update_source_extraction_selectors(self):
        source_name = "SourceB_NoSelectors"
        new_selectors = {"title_selector": "h2.articleHeader", "content_selector": "section.body"}

        self.assertTrue(self.planner.update_source_extraction_selectors(source_name, new_selectors))
        updated_source = self.planner.get_source_by_name(source_name)
        self.assertEqual(updated_source['extraction_selectors'], new_selectors)
        self.assertEqual(updated_source['llm_analysis_pending'], False)
        self.mock_monitor.log_event.assert_any_call("INFO", f"Updated extraction selectors for source '{source_name}'.", unittest.mock.ANY)

    def test_set_llm_analysis_flag(self):
        source_name = "SourceA_WithSelectors" # llm_analysis_pending is False initially
        self.assertTrue(self.planner.set_llm_analysis_flag(source_name, True))
        updated_source = self.planner.get_source_by_name(source_name)
        self.assertEqual(updated_source['llm_analysis_pending'], True)

        self.assertTrue(self.planner.set_llm_analysis_flag(source_name, False))
        updated_source = self.planner.get_source_by_name(source_name)
        self.assertEqual(updated_source['llm_analysis_pending'], False)

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_config_writes_new_fields(self, mock_json_dump, mock_file_open):
        source_name = "SourceB_NoSelectors"
        test_selectors = {"test_selector_key": "test_selector_value"}
        self.planner.update_source_extraction_selectors(source_name, test_selectors)
        # This also sets llm_analysis_pending to False

        self.planner.save_config() # Attempt to save

        mock_file_open.assert_called_once_with(TEST_SOURCES_JSON_PATH, 'w', encoding='utf-8')

        # Check the data that was passed to json.dump
        # json.dump is called with (data_to_save, file_handle, ...)
        saved_data_arg = mock_json_dump.call_args[0][0]
        self.assertIn("sources", saved_data_arg)
        saved_sources_list = saved_data_arg["sources"]

        found_source_b_in_save = False
        for src_in_save in saved_sources_list:
            if src_in_save.get('name') == source_name:
                found_source_b_in_save = True
                self.assertEqual(src_in_save.get('extraction_selectors'), test_selectors)
                self.assertEqual(src_in_save.get('llm_analysis_pending'), False)
                self.assertEqual(src_in_save.get('parser_config_name'), "default") # Ensure other fields are preserved
                break
        self.assertTrue(found_source_b_in_save, "SourceB_NoSelectors not found or not correctly updated in saved data.")

    # Example of an existing test that should still pass
    def test_get_source_by_name_existing(self):
        source = self.planner.get_source_by_name("SourceA_WithSelectors")
        self.assertIsNotNone(source)
        self.assertEqual(source['base_url'], "http://sourceA.com")


if __name__ == '__main__':
    unittest.main()
