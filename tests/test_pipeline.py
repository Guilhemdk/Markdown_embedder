import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import json # For checking json.dump calls
import shutil # For reliably removing test directory

# Adjust import path based on project structure
# Assuming 'tests' and 'news_scrapper' are sibling directories at the project root
from news_scrapper.pipeline.pipeline import Pipeline
# We need to control these for tests, so we might patch them or ensure test-specific values.
# from news_scrapper.config import RESULTS_DIR, MAX_RESULTS_TO_STORE_IN_MEMORY

# Define a specific test results directory
TEST_RESULTS_DIR = os.path.join(os.path.dirname(__file__), "test_pipeline_output_dir_temp")
TEST_MAX_MEMORY_RESULTS = 3

class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.mock_monitor = MagicMock()

        # Ensure the test results directory is clean before each test
        if os.path.exists(TEST_RESULTS_DIR):
            shutil.rmtree(TEST_RESULTS_DIR) # Remove dir and all its contents
        os.makedirs(TEST_RESULTS_DIR) # Create fresh for the test

        # Initialize pipeline with test-specific paths and limits
        # We are patching the constants that Pipeline's constructor uses by default.
        # This is cleaner if Pipeline's constructor itself doesn't take these as args.
        # However, my Pipeline constructor *does* take them as args, which is better for testing.
        self.pipeline = Pipeline(monitor_instance=self.mock_monitor,
                                 results_output_dir=TEST_RESULTS_DIR,
                                 max_results_in_memory=TEST_MAX_MEMORY_RESULTS)

    def tearDown(self):
        # Clean up the test results directory after all tests in the class
        if os.path.exists(TEST_RESULTS_DIR):
            shutil.rmtree(TEST_RESULTS_DIR)

    def test_add_item_new(self):
        item = {"id": "item1_unique", "link": "http://example.com/item1_unique", "title": "Test New"}
        self.pipeline.add_item(item)
        self.assertEqual(len(self.pipeline.item_queue), 1)
        # Check based on 'link' because add_item prioritizes link for seen_key
        self.assertIn("http://example.com/item1_unique", self.pipeline.seen_item_ids)
        self.assertEqual(self.pipeline.item_queue[0], item)

    def test_add_item_duplicate_id_different_link(self):
        item1 = {"id": "dup_id1", "link": "http://example.com/link_for_dup_id1", "title": "Test1"}
        item2 = {"id": "dup_id1", "link": "http://example.com/link_for_dup_id2", "title": "Test2"} # Same ID, different link
        self.pipeline.add_item(item1)
        self.pipeline.add_item(item2)
        # Both should be added because their `seen_key` (link) is different.
        self.assertEqual(len(self.pipeline.item_queue), 2)

    def test_add_item_duplicate_link_different_id(self):
        item1 = {"id": "id_for_dup_link1", "link": "http://example.com/shared_link", "title": "Test1"}
        item2 = {"id": "id_for_dup_link2", "link": "http://example.com/shared_link", "title": "Test2"} # Different ID, Same link
        self.pipeline.add_item(item1)
        self.pipeline.add_item(item2)
        # item2 should be ignored because its `seen_key` (link) is already seen.
        self.assertEqual(len(self.pipeline.item_queue), 1)
        self.assertIn("http://example.com/shared_link", self.pipeline.seen_item_ids)

    def test_add_item_missing_link_and_id(self):
        item_bad = {"title": "Bad Item"}
        self.pipeline.add_item(item_bad)
        self.assertEqual(len(self.pipeline.item_queue), 0)
        self.mock_monitor.log_event.assert_called_with(
            "WARNING", "Item data is missing both 'id' and 'link'. Skipping.",
            unittest.mock.ANY # or specific dict if you want to match details
        )

    @patch('news_scrapper.pipeline.pipeline.open', new_callable=mock_open)
    @patch('news_scrapper.pipeline.pipeline.json.dump')
    def test_store_result_saves_file_and_adds_to_memory(self, mock_json_dump, mock_file_open):
        article_data = {"id": "article_x", "link": "http://example.com/article_x", "title": "Article X Title"}

        self.pipeline.store_result(article_data)

        expected_filename = self.pipeline._sanitize_filename(article_data['link']) + ".json"
        expected_filepath = os.path.join(TEST_RESULTS_DIR, expected_filename) # Use TEST_RESULTS_DIR

        mock_file_open.assert_called_once_with(expected_filepath, 'w', encoding='utf-8')
        mock_json_dump.assert_called_once()
        # Check if the first argument to json.dump was our article_data
        self.assertEqual(mock_json_dump.call_args[0][0], article_data)

        self.assertIn(article_data, self.pipeline.processed_results_in_memory)
        self.assertEqual(self.pipeline.get_processed_item_count_in_memory(), 1)

    @patch('news_scrapper.pipeline.pipeline.open', new_callable=mock_open)
    @patch('news_scrapper.pipeline.pipeline.json.dump')
    def test_store_result_memory_limit(self, mock_json_dump, mock_file_open):
        # Fill up in-memory results to max
        for i in range(TEST_MAX_MEMORY_RESULTS):
            item = {"id": f"mem_item{i}", "link": f"http://example.com/mem_item{i}", "title": f"Mem Item {i}"}
            # We need to make sure these calls to store_result don't fail on file ops for this specific test focus
            # The mocks already prevent actual file writes, which is good.
            self.pipeline.store_result(item)

        self.assertEqual(self.pipeline.get_processed_item_count_in_memory(), TEST_MAX_MEMORY_RESULTS)

        # Try to add one more
        extra_item = {"id": "extra_item", "link": "http://example.com/extra_item", "title": "Extra Item"}
        self.pipeline.store_result(extra_item)

        # In-memory count should still be at max
        self.assertEqual(self.pipeline.get_processed_item_count_in_memory(), TEST_MAX_MEMORY_RESULTS)
        # And the extra_item should not be the first one (FIFO for memory if it were a capped queue, but it's a list)
        # Check that extra_item is NOT in the memory list if the list was already full.
        # Current implementation just stops appending.
        self.assertNotIn(extra_item, self.pipeline.processed_results_in_memory)
        # The mock_monitor should have been called about max results reached.
        self.mock_monitor.log_event.assert_any_call("DEBUG", "Max in-memory results reached. Not adding to list.", unittest.mock.ANY)


    def test_get_next_item_empty_queue(self):
        self.assertIsNone(self.pipeline.get_next_item())

    def test_get_next_item_fifo(self):
        item1 = {"id": "q_item1", "link": "http://example.com/q_item1"}
        item2 = {"id": "q_item2", "link": "http://example.com/q_item2"}
        self.pipeline.add_item(item1)
        self.pipeline.add_item(item2)

        self.assertEqual(self.pipeline.get_next_item(), item1)
        self.assertEqual(self.pipeline.get_next_item(), item2)
        self.assertIsNone(self.pipeline.get_next_item())

    def test_ensure_results_dir_creates_directory(self):
        # This is implicitly tested by setUp, but an explicit test is fine.
        # Remove it first to test creation
        if os.path.exists(TEST_RESULTS_DIR):
            shutil.rmtree(TEST_RESULTS_DIR)
        self.assertFalse(os.path.exists(TEST_RESULTS_DIR))
        self.pipeline._ensure_results_dir() # Call directly
        self.assertTrue(os.path.exists(TEST_RESULTS_DIR))


if __name__ == '__main__':
    unittest.main()
