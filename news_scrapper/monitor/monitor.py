"""
This module contains the Monitor component.
The Monitor is responsible for watching for failures, changes in site structure,
or indications of being rate-limited or blocked. It also handles general logging.
"""
import datetime
import json # For potentially more structured details

class Monitor:
    """
    Handles logging, failure reporting, and detection of potential issues
    like site changes or rate limiting.
    """
    def __init__(self, log_to_console=True):
        """
        Initializes the Monitor.
        Args:
            log_to_console (bool): If True, prints log events to the console.
        """
        self.event_log = []
        self.log_to_console = log_to_console

    def log_event(self, event_type, message, details=None):
        """
        Logs an event with a timestamp.
        Args:
            event_type (str): Type of event (e.g., "INFO", "WARNING", "ERROR", "CRITICAL", "DEBUG").
            message (str): The main message for the event.
            details (dict, optional): Additional structured details about the event. Defaults to None.
        """
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        log_entry = {
            "timestamp": timestamp,
            "type": event_type.upper(),
            "message": message,
            "details": details if details is not None else {}
        }
        self.event_log.append(log_entry)

        if self.log_to_console:
            details_str = ""
            if log_entry['details']:
                try:
                    details_str = json.dumps(log_entry['details'])
                except TypeError: # Handle non-serializable details gracefully
                    details_str = str(log_entry['details'])

            print(f"[{log_entry['timestamp']}] [{log_entry['type']}] {log_entry['message']}" + (f" | Details: {details_str}" if details_str else ""))


    def report_failure(self, component_name, error_message, url=None, error_details=None):
        """
        Reports a failure in one of the scraper components. This is a specialized log_event.
        Args:
            component_name (str): Name of the component that failed (e.g., "Fetcher", "Parser").
            error_message (str): Description of the error.
            url (str, optional): The URL being processed when the failure occurred. Defaults to None.
            error_details (dict, optional): Additional details specific to the error.
        """
        details = error_details if error_details is not None else {}
        details['component'] = component_name
        if url:
            details['url'] = url

        message = f"Component '{component_name}' encountered an error: {error_message}"
        self.log_event("ERROR", message, details)

    def check_site_change(self, url, old_indicator, new_indicator, indicator_type="hash"):
        """
        Compares an old and new indicator (e.g., content hash, structural hash)
        to detect significant changes in a website's structure or content.
        Args:
            url (str): The URL of the site being checked.
            old_indicator (str): The old indicator value.
            new_indicator (str): The new indicator value.
            indicator_type (str): Description of what the indicator represents (e.g., "content_hash", "structure_hash").
        Returns:
            bool: True if a change is detected, False otherwise.
        """
        if old_indicator != new_indicator:
            self.log_event("WARNING", f"Potential site change detected for {url} based on {indicator_type}.",
                           {"url": url, f"old_{indicator_type}": old_indicator, f"new_{indicator_type}": new_indicator})
            return True
        # self.log_event("INFO", f"No site change detected for {url} based on {indicator_type}.")
        return False

    def is_rate_limited(self, component_name, source_identifier, http_status_code=None, content_snippet=None):
        """
        Assesses if the scraper might be rate-limited or blocked.
        This could be based on HTTP status codes (e.g., 429, 503), CAPTCHAs in content, or specific error messages.
        Args:
            component_name (str): The component that encountered the potential rate limiting (e.g., "Fetcher").
            source_identifier (str): URL, domain, or IP that might be rate-limited.
            http_status_code (int, optional): The HTTP status code received.
            content_snippet (str, optional): A snippet of the received content to check for CAPTCHAs or block messages.
        Returns:
            bool: True if rate limiting is suspected, False otherwise.
        """
        details = {"component": component_name, "source": source_identifier}
        if http_status_code:
            details["status_code"] = http_status_code
        if content_snippet:
            # In a real scenario, you might truncate or hash the snippet if it's too long for logs
            details["content_snippet_preview"] = content_snippet[:200]

        # Rule 1: HTTP 429 (Too Many Requests) or 503 (Service Unavailable) are strong indicators
        if http_status_code in [429, 503]:
            self.log_event("CRITICAL",
                           f"Rate limiting strongly suspected for '{source_identifier}' (Component: {component_name}). HTTP Status: {http_status_code}.",
                           details)
            return True

        # Rule 2: Check for common CAPTCHA or block-related keywords in content
        if content_snippet:
            block_keywords = ["captcha", "are you a robot", "access denied", "verify you are human", "to continue please"]
            for keyword in block_keywords:
                if keyword in content_snippet.lower():
                    self.log_event("CRITICAL",
                                   f"Rate limiting or block suspected for '{source_identifier}' (Component: {component_name}). Found keyword: '{keyword}'.",
                                   details)
                    return True

        # self.log_event("DEBUG", f"No clear sign of rate limiting for '{source_identifier}' by '{component_name}'.", details)
        return False

    def get_event_log(self, last_n=None):
        """
        Retrieves logged events.
        Args:
            last_n (int, optional): If provided, returns only the last N events.
        Returns:
            list: A list of log entry dictionaries.
        """
        if last_n is not None and isinstance(last_n, int) and last_n > 0:
            return self.event_log[-last_n:]
        return self.event_log

    def clear_log(self):
        """Clears all events from the log."""
        self.event_log = []
        self.log_event("INFO", "Event log cleared.")


if __name__ == '__main__':
    monitor = Monitor()

    monitor.log_event("INFO", "Scraper process starting up.", {"pid": 12345})
    monitor.log_event("DEBUG", "Configuration loaded successfully.", {"config_path": "/etc/scraper.conf"})
    monitor.log_event("WARNING", "Network latency detected.", {"avg_latency_ms": 1200})

    monitor.report_failure("Fetcher", "Connection timeout after 3 retries",
                           url="http://nonexistent.example.com",
                           error_details={"retries": 3, "timeout_seconds": 30})

    monitor.report_failure("Parser", "Required HTML element not found",
                           url="http://example.com/article/123",
                           error_details={"element_selector": "div.article-content", "parser_version": "v1.2"})

    monitor.check_site_change("http://example.com/home", "hash_v1_0_0", "hash_v1_0_1", indicator_type="layout_hash")
    monitor.check_site_change("http://example.com/product/1", "content_hash_abc", "content_hash_xyz", indicator_type="product_data_hash")

    monitor.is_rate_limited("Fetcher", "http://api.example.com/data", http_status_code=200)
    monitor.is_rate_limited("Fetcher", "http://api.example.com/data", http_status_code=429)
    monitor.is_rate_limited("Fetcher", "http://example.com/login", content_snippet="Please verify you are human by completing the CAPTCHA.")
    monitor.is_rate_limited("Fetcher", "http://example.com/anotherpage", content_snippet="Normal content here, nothing suspicious.")


    print(f"\n--- Last 5 Events from Log ({len(monitor.get_event_log())} total) ---")
    for log_entry in monitor.get_event_log(last_n=5):
        print(f"  {log_entry['timestamp']} [{log_entry['type']}] {log_entry['message']}")

    monitor.clear_log()
    print(f"\nLog size after clearing: {len(monitor.get_event_log())}")

```
