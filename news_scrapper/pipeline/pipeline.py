"""
This module contains the Pipeline component.
The Pipeline is responsible for managing the queue of items (articles) to be processed,
storing the parsed results to files, and potentially triggering downstream tasks.
"""
import collections
import json
import os
import re
import time # For fallback item ID if needed
from datetime import datetime # For processed_timestamp_utc, though main.py adds this

# Attempt to import config values
try:
    from ..config import RESULTS_DIR, MAX_RESULTS_TO_STORE_IN_MEMORY # Corrected to ..config
except ImportError: # Likely running pipeline.py directly or config is not in python path
    print("Pipeline: Could not import from ..config, using default result storage settings.")
    # Define defaults if config import fails (e.g. for standalone testing)
    # Determine a sensible default for RESULTS_DIR relative to this file if needed
    # For now, assume it might be set by main.py or test environment
    RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scraped_results_pipeline_default")
    MAX_RESULTS_TO_STORE_IN_MEMORY = 100


class Pipeline:
    """
    Manages the workflow of item processing, from queuing to storing results as JSON files.
    Items are typically dictionaries containing article metadata from RSS feeds or parsed pages.
    """
    def __init__(self, monitor_instance=None, results_output_dir=None, max_results_in_memory=None):
        """
        Initializes the Pipeline.
        Sets up a queue for items and a list to store recent results (or references).
        Args:
            monitor_instance (Monitor, optional): An instance of the Monitor component.
            results_output_dir (str, optional): Directory to save JSON results. Defaults to config.RESULTS_DIR.
            max_results_in_memory (int, optional): Max items to keep in self.processed_results. Defaults to config.MAX_RESULTS_TO_STORE_IN_MEMORY.
        """
        self.item_queue = collections.deque()
        self.seen_item_ids = set() # To avoid processing duplicate items based on their ID
        self.monitor = monitor_instance

        self.processed_results_in_memory = [] # Stores recent full items or references
        self.results_output_dir = results_output_dir if results_output_dir is not None else RESULTS_DIR
        self.max_results_in_memory = max_results_in_memory if max_results_in_memory is not None else MAX_RESULTS_TO_STORE_IN_MEMORY

        self._ensure_results_dir()
        self._log_event("INFO", f"Pipeline initialized. Results will be saved to: {self.results_output_dir}")

    def _log_event(self, level, message, details=None):
        if self.monitor:
            self.monitor.log_event(level, message, details)
        else:
            details_str = f" | Details: {details}" if details else ""
            print(f"[{level}] {message}{details_str}")

    def _ensure_results_dir(self):
        """Ensures the results output directory exists."""
        try:
            if not os.path.exists(self.results_output_dir):
                os.makedirs(self.results_output_dir)
                self._log_event("INFO", f"Created results directory: {self.results_output_dir}")
        except OSError as e:
            self._log_event("ERROR", f"Could not create results directory {self.results_output_dir}: {e}",
                            details={"exception_type": type(e).__name__, "errno": e.errno, "strerror": e.strerror})
            # Fallback to a local temp dir or disable file saving if critical, for now just log

    def _sanitize_filename(self, name):
        """
        Sanitizes a string to be suitable for use as a filename.
        Replaces most non-alphanumeric characters with underscores.
        Args:
            name (str): The input string (e.g., URL, title, ID).
        Returns:
            str: A sanitized string for use as a filename.
        """
        if not name: return "untitled"
        # Remove http(s):// prefix
        name = re.sub(r'^https?://', '', name)
        # Replace slashes, colons, and other problematic chars with underscore
        name = re.sub(r'[/\:?*"<>|]', '_', name)
        # Keep only alphanumeric, underscore, hyphen, dot. Replace others with underscore.
        name = re.sub(r'[^\w._-]', '_', name)
        # Truncate if too long (OS path limits)
        return name[:150] # Max length for filename part

    def add_item(self, item_data):
        if not isinstance(item_data, dict):
            self._log_event("WARNING", "Invalid item_data (not a dict), skipping.", {"item_data_type": type(item_data)})
            return

        # Use 'link' as primary ID if 'id' is missing or generic, as 'link' should be the article URL.
        # Ensure ID is reasonably unique for `seen_item_ids`.
        item_id = item_data.get('id')
        item_link = item_data.get('link')

        if not item_link and not item_id: # Must have at least one, preferably link
             self._log_event("WARNING", "Item data is missing both 'id' and 'link'. Skipping.", {"item_data_preview": str(item_data)[:100]})
             return

        # Prioritize link for seen check if it's a valid URL, otherwise use id.
        # This helps avoid reprocessing the same content if IDs are unstable but links are canonical.
        seen_key = item_link if item_link else item_id

        if seen_key not in self.seen_item_ids:
            self.item_queue.append(item_data)
            self.seen_item_ids.add(seen_key)
            self._log_event("DEBUG", "Added item to queue.",
                            {"id": item_id, "link": item_link, "seen_key": seen_key, "queue_size": len(self.item_queue)})
        else:
            self._log_event("DEBUG", "Item already seen or in queue (based on link/id), skipping.",
                            {"id": item_id, "link": item_link, "seen_key": seen_key})

    def add_items(self, items_data_list):
        # ... (existing add_items) ...
        if not isinstance(items_data_list, list):
            self._log_event("WARNING", "`add_items` expects a list of item dictionaries.")
            return
        for item_data in items_data_list:
            self.add_item(item_data)


    def get_next_item(self):
        # ... (existing get_next_item) ...
        if self.item_queue:
            item = self.item_queue.popleft()
            self._log_event("DEBUG", f"Retrieving item from queue.",
                            {"id": item.get("id"), "link": item.get("link"), "queue_size": len(self.item_queue)})
            return item
        self._log_event("DEBUG", "Item queue is empty.")
        return None

    def store_result(self, article_data):
        """
        Stores the processed article data as a JSON file and optionally in memory.
        Args:
            article_data (dict): The structured and processed article data.
        """
        # Determine a robust ID for the article, preferring 'link' or 'url' if 'id' is generic or missing
        article_identifier = article_data.get('link') or article_data.get('url') or article_data.get('id')
        if not article_identifier: # Fallback if all preferred keys are missing
            article_identifier = str(time.time()) # Should be rare
            self._log_event("WARNING", "Article data missing 'link', 'url', and 'id'. Using timestamp as identifier.",
                            {"title": article_data.get('title', 'N/A')})

        filename_base = self._sanitize_filename(article_identifier)
        filename = filename_base + ".json"
        filepath = os.path.join(self.results_output_dir, filename)

        log_details = {"filepath": filepath, "article_id": article_identifier, "title": article_data.get("title", "N/A")}

        try:
            # Ensure all datetime objects are ISO formatted strings before saving to JSON
            def datetime_converter(o):
                if isinstance(o, datetime):
                    return o.isoformat()

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(article_data, f, indent=2, ensure_ascii=False, default=datetime_converter)

            self._log_event("INFO", "Result saved to file.", log_details)

            if len(self.processed_results_in_memory) < self.max_results_in_memory:
                # Store a reference or a summary, not necessarily the full data if memory is a concern
                # For now, storing the full dict as per previous behavior of self.results
                self.processed_results_in_memory.append(article_data)
                # self.processed_results_in_memory.append({"id": article_identifier, "filepath": filepath, "title": article_data.get("title")})
            else:
                self._log_event("DEBUG", "Max in-memory results reached. Not adding to list.", {"limit": self.max_results_in_memory})

        except Exception as e:
            self._log_event("ERROR", f"Failed to save result to JSON file {filepath}: {e}",
                            {**log_details, "exception_type": type(e).__name__, "error": str(e)})


    def has_pending_items(self):
        # ... (existing has_pending_items) ...
        return len(self.item_queue) > 0

    def get_all_results(self):
        """Returns the list of results currently held in memory."""
        return self.processed_results_in_memory

    def get_processed_item_count_in_memory(self):
        """Returns the count of items currently held in the in-memory results list."""
        return len(self.processed_results_in_memory)

    def get_processed_item_count_on_disk(self):
        """Counts the number of .json files in the results directory."""
        try:
            if os.path.exists(self.results_output_dir):
                return len([name for name in os.listdir(self.results_output_dir) if name.endswith(".json")])
        except OSError as e:
            self._log_event("ERROR", f"Could not count files in results directory {self.results_output_dir}: {e}")
        return 0


    def clear_results(self): # Clears in-memory results
        self.processed_results_in_memory = []
        self._log_event("INFO", "In-memory results have been cleared.")

    def clear_queue(self):
        # ... (existing clear_queue) ...
        self.item_queue.clear()
        self.seen_item_ids.clear() # Also clear seen IDs when queue is cleared
        self._log_event("INFO", "Item queue and seen item IDs have been cleared.")


if __name__ == '__main__':
    # Test with a mock monitor
    class MockMonitor:
        def log_event(self, lvl, msg, details=None): print(f"[{lvl}] {msg} {details if details else ''}")

    test_monitor = MockMonitor()
    # Create a temporary results directory for testing
    test_results_dir = os.path.join(os.path.dirname(__file__), "test_pipeline_results")
    if not os.path.exists(test_results_dir): os.makedirs(test_results_dir)

    pipeline = Pipeline(monitor_instance=test_monitor,
                        results_output_dir=test_results_dir,
                        max_results_in_memory=3)

    print("Pipeline Initialized for item processing and storage.")

    item1 = {"id": "item1_id", "link": "http://example.com/item1", "title": "Item 1 Title", "content": "abc", "published_date_utc": datetime.now(timezone.utc)}
    item2 = {"id": "item2_id", "link": "http://example.com/item2", "title": "Item 2 Title", "content": "def", "processed_timestamp_utc": datetime.now(timezone.utc).isoformat()}
    item3_no_id = {"link": "http://example.com/item3_no_id", "title": "Item 3 No Explicit ID", "content": "ghi"}
    item4_dup_link = {"id": "item4_id", "link": "http://example.com/item1", "title": "Item 4 Duplicate Link", "content": "xyz"}


    pipeline.add_item(item1) # Added
    pipeline.add_item(item2) # Added
    pipeline.add_item(item3_no_id) # Added, ID will be link
    pipeline.add_item(item1) # Skipped (duplicate ID/Link)
    pipeline.add_item(item4_dup_link) # Skipped (duplicate link 'http://example.com/item1' used as seen_key)


    print(f"\nQueue size: {len(pipeline.item_queue)}") # Expected 3

    # Simulate processing and storing
    while pipeline.has_pending_items():
        current_item = pipeline.get_next_item()
        if current_item:
            # Simulate that 'current_item' is now fully processed data
            pipeline.store_result(current_item)

    print(f"\nIn-memory results count: {pipeline.get_processed_item_count_in_memory()} (Max: {pipeline.max_results_in_memory})")
    print(f"Results on disk in '{test_results_dir}': {pipeline.get_processed_item_count_on_disk()}")

    # Verify file creation (manual check or os.listdir)
    print("\nFiles in test_pipeline_results:")
    for f_name in os.listdir(test_results_dir):
        print(f"  - {f_name}")
        # Clean up by removing the file after test
        try: os.remove(os.path.join(test_results_dir, f_name))
        except Exception: pass

    try: os.rmdir(test_results_dir)
    except Exception: pass

    print("\n--- Pipeline storage example finished ---")
