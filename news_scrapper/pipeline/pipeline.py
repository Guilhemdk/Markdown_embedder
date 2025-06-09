"""
This module contains the Pipeline component.
The Pipeline is responsible for managing the queue of URLs to be processed,
storing the parsed results, and potentially triggering downstream tasks.
"""
import collections

class Pipeline:
    """
    Manages the workflow of URL processing, from queuing to storing results.
    """
    def __init__(self):
        """
        Initializes the Pipeline.
        Sets up a queue for URLs and a list to store results.
        """
        # Using collections.deque for efficient appends and pops, especially from the left (FIFO)
        self.url_queue = collections.deque()
        # A simple list to store processed results in memory for this basic implementation
        self.results = []
        # Keep track of URLs that have been added to avoid processing duplicates if desired.
        # For a simple list-based queue, checking existence in deque can be O(n).
        # For very large scale, a set alongside the deque would be better for seen URLs.
        self.seen_urls = set()

    def add_url(self, url):
        """
        Adds a URL to the processing queue if it hasn't been added before.
        Args:
            url (str): The URL to add.
        """
        if not isinstance(url, str) or not url.strip():
            print(f"WARNING: Invalid URL provided: {url}. Skipping.")
            return

        if url not in self.seen_urls:
            self.url_queue.append(url)
            self.seen_urls.add(url)
            # print(f"DEBUG: Added to queue: {url}. Queue size: {len(self.url_queue)}")
        else:
            # print(f"DEBUG: URL already processed or in queue: {url}")
            pass

    def add_urls(self, urls):
        """
        Adds a list of URLs to the processing queue.
        Args:
            urls (list): A list of URL strings to add.
        """
        if not isinstance(urls, list):
            print("WARNING: `add_urls` expects a list of URLs.")
            return
        for url in urls:
            self.add_url(url)

    def get_next_url(self):
        """
        Retrieves and removes the next URL from the queue (FIFO).
        Returns:
            str: The next URL to process, or None if the queue is empty.
        """
        if self.url_queue:
            url = self.url_queue.popleft()
            # print(f"DEBUG: Retrieving URL from queue: {url}. Queue size: {len(self.url_queue)}")
            return url
        # print("DEBUG: URL queue is empty.")
        return None

    def store_result(self, data):
        """
        Stores the processed data.
        For this basic implementation, it appends to an internal list and prints a summary.
        In a real application, this would save to a database, file system, message queue, etc.
        Args:
            data (dict): The structured data extracted by the Parser.
        """
        if data and isinstance(data, dict) and 'url' in data:
            self.results.append(data)
            print(f"INFO: Stored result for URL: {data.get('url', 'N/A')}. Title: '{data.get('title', 'N/A')}'")
        else:
            print("WARNING: No valid data provided to store, or data is missing 'url' key.")

    def has_pending_urls(self):
        """
        Checks if there are any URLs left in the queue.
        Returns:
            bool: True if there are URLs to process, False otherwise.
        """
        return len(self.url_queue) > 0

    def get_all_results(self):
        """
        Returns all stored results.
        Returns:
            list: A list of all processed and stored data dictionaries.
        """
        return self.results

    def clear_results(self):
        """
        Clears all stored results from memory.
        """
        self.results = []
        print("INFO: All stored results have been cleared.")

    def clear_queue(self):
        """
        Clears all URLs from the queue and the set of seen URLs.
        """
        self.url_queue.clear()
        self.seen_urls.clear()
        print("INFO: URL queue and seen URLs have been cleared.")

if __name__ == '__main__':
    pipeline = Pipeline()

    print("Pipeline Initialized.")
    print(f"Has pending URLs: {pipeline.has_pending_urls()} (Expected: False)")

    print("\nAdding URLs...")
    pipeline.add_url("http://example.com/page1")
    pipeline.add_url("http://example.com/page2")
    pipeline.add_url("http://example.com/page1") # Attempting to add a duplicate
    pipeline.add_url("  ") # Attempting to add an invalid URL
    pipeline.add_urls(["http://example.com/page3", "http://example.com/page4"])

    print(f"\nHas pending URLs: {pipeline.has_pending_urls()} (Expected: True)")
    print(f"Queue size: {len(pipeline.url_queue)} (Expected: 4, as one was duplicate and one invalid)")

    print("\nProcessing URLs from queue:")
    next_url = pipeline.get_next_url()
    if next_url:
        print(f"Processing URL: {next_url}") # Expected: http://example.com/page1
        sample_data_1 = {"url": next_url, "title": "Page 1 Title", "text": "Some text..."}
        pipeline.store_result(sample_data_1)

    print(f"\nHas pending URLs: {pipeline.has_pending_urls()}")
    next_url = pipeline.get_next_url()
    if next_url:
        print(f"Processing URL: {next_url}") # Expected: http://example.com/page2
        sample_data_2 = {"url": next_url, "title": "Page 2 Title", "text": "More text..."}
        pipeline.store_result(sample_data_2)

    # Process remaining URLs
    while pipeline.has_pending_urls():
        next_url = pipeline.get_next_url()
        if next_url:
            print(f"Processing URL: {next_url}")
            sample_data_n = {"url": next_url, "title": f"Title for {next_url.split('/')[-1]}", "text": "Some content."}
            pipeline.store_result(sample_data_n)


    print(f"\nHas pending URLs: {pipeline.has_pending_urls()} (Expected: False)")
    print(f"Total results stored: {len(pipeline.get_all_results())}")

    print("\nDisplaying all stored results:")
    for i, res in enumerate(pipeline.get_all_results()):
        print(f"  Result {i+1}: URL='{res['url']}', Title='{res['title']}'")

    pipeline.clear_results()
    print(f"Total results after clearing: {len(pipeline.get_all_results())}")

    pipeline.clear_queue()
    print(f"Queue size after clearing: {len(pipeline.url_queue)}")
    print(f"Seen URLs count after clearing: {len(pipeline.seen_urls)}")
