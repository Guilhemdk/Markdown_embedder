"""
This module contains the Monitor component.
The Monitor is responsible for watching for failures, changes in site structure,
or indications of being rate-limited or blocked. It also handles general logging
and basic checks like article newness. It can also interact with Planner's
crawl delay settings upon detecting rate limits.
"""
import datetime
import json
from datetime import timezone, timedelta
from urllib.parse import urlparse

class Monitor:
    """
    Handles logging, failure reporting, detection of potential issues,
    and can adjust crawl delays via a Planner reference upon rate limiting.
    """
    def __init__(self, log_to_console=True, planner_reference=None):
        """
        Initializes the Monitor.
        Args:
            log_to_console (bool): If True, prints log events to the console.
            planner_reference (Planner, optional): A reference to the Planner instance
                                                   to allow feedback (e.g., adjusting crawl delays).
        """
        self.event_log = []
        self.log_to_console = log_to_console
        self.planner_reference = planner_reference # Could also be just the crawl_delays_cache dict

    def _log_event(self, level, message, details=None): # Renamed to avoid conflict with log_event method
        # ... (existing _log_event method - no changes specified for it here) ...
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        log_entry = {
            "timestamp": timestamp,
            "type": event_type.upper() if isinstance(event_type:=level, str) else "UNKNOWN", # Python 3.8+
            "message": message,
            "details": details if details is not None else {}
        }
        self.event_log.append(log_entry)

        if self.log_to_console:
            details_str = ""
            if log_entry['details']:
                try:
                    details_str = json.dumps(log_entry['details'])
                except TypeError:
                    details_str = str(log_entry['details'])

            print(f"[{log_entry['timestamp']}] [{log_entry['type']}] {log_entry['message']}" + (f" | Details: {details_str}" if details_str else ""))


    def log_event(self, event_type, message, details=None): # Public method
        # This is the method that should be called externally.
        # The one above can be renamed to _internal_log_event or similar if needed,
        # but for now, let's assume _log_event was a typo for the internal call.
        # For consistency, I'll assume the one taking `level` was meant to be `_log_event_internal`
        # and this is the public one.
        # Let's fix the internal one to avoid confusion.
        self._internal_log_event_formatter(event_type, message, details)

    def _internal_log_event_formatter(self, event_type_str, message, details=None):
        """Formats and appends a log entry, prints to console if enabled."""
        timestamp = datetime.datetime.now(timezone.utc).isoformat()
        log_entry = {
            "timestamp": timestamp,
            "type": event_type_str.upper(),
            "message": message,
            "details": details if details is not None else {}
        }
        self.event_log.append(log_entry)

        if self.log_to_console:
            details_json_str = ""
            if log_entry['details']:
                try:
                    details_json_str = json.dumps(log_entry['details']) # Ensure details are serializable for consistency
                except TypeError: # Fallback if details contain non-serializable items
                    details_json_str = str(log_entry['details'])

            print(f"[{log_entry['timestamp']}] [{log_entry['type']}] {log_entry['message']}" +
                  (f" | Details: {details_json_str}" if details_json_str else ""))


    def report_failure(self, component_name, error_message, url=None, error_details=None):
        # ... (existing report_failure method) ...
        details = error_details if error_details is not None else {}
        details['component'] = component_name
        if url: details['url'] = url
        self.log_event("ERROR", f"Component '{component_name}' failed: {error_message}", details)


    def check_site_change(self, url, old_indicator, new_indicator, indicator_type="hash"):
        # ... (existing check_site_change method) ...
        if old_indicator != new_indicator:
            self.log_event("WARNING", f"Potential site change for {url} by {indicator_type}.",
                           {"url": url, f"old_{indicator_type}": old_indicator, f"new_{indicator_type}": new_indicator})
            return True
        return False

    def is_rate_limited(self, component_name, source_identifier, http_status_code=None, content_snippet=None):
        """
        Assesses if the scraper might be rate-limited or blocked and attempts to increase crawl delay.
        Args:
            source_identifier (str): URL or domain that might be rate-limited.
            Other args as before.
        Returns:
            bool: True if rate limiting is suspected, False otherwise.
        """
        is_limited = False
        details = {"component": component_name, "source": source_identifier}
        if http_status_code: details["status_code"] = http_status_code
        # Truncate content_snippet for logging if it's too long
        if content_snippet: details["content_snippet_preview"] = content_snippet[:200]

        if http_status_code in [429, 503]: # Common rate-limiting/busy codes
            self.log_event("CRITICAL", f"Rate limiting strongly suspected for '{source_identifier}'. HTTP Status: {http_status_code}.", details)
            is_limited = True
        elif content_snippet:
            block_keywords = ["captcha", "are you a robot", "access denied", "verify you are human", "to continue please", "too many requests"]
            for keyword in block_keywords:
                if keyword in content_snippet.lower():
                    self.log_event("CRITICAL", f"Rate limiting/block suspected for '{source_identifier}'. Found keyword: '{keyword}'.", details)
                    is_limited = True
                    break

        if is_limited and self.planner_reference and hasattr(self.planner_reference, 'crawl_delays_cache'):
            domain_to_penalize = None
            try:
                # source_identifier could be a full URL or just a domain.
                parsed_url = urlparse(source_identifier)
                if parsed_url.netloc:
                    domain_to_penalize = parsed_url.netloc
                elif '.' in source_identifier: # Simple check if it might be a domain string
                    domain_to_penalize = source_identifier
            except Exception as e:
                self.log_event("ERROR", f"Could not parse domain from source_identifier '{source_identifier}' for rate limit penalty: {e}")

            if domain_to_penalize:
                current_delay = self.planner_reference.crawl_delays_cache.get(domain_to_penalize, 1) # Default to 1s if not set
                new_delay = min(current_delay * 2, 300) # Double delay, max 5 minutes
                if new_delay == current_delay and current_delay > 1: # If already high, increment by a fixed amount
                    new_delay = min(current_delay + 60, 300)


                self.planner_reference.crawl_delays_cache[domain_to_penalize] = new_delay
                self.log_event("WARNING", f"Applied rate limit penalty: Increased crawl delay for domain '{domain_to_penalize}' to {new_delay}s.",
                               {"domain": domain_to_penalize, "old_delay": current_delay, "new_delay": new_delay})
            else:
                 self.log_event("WARNING", "Rate limit detected, but could not determine domain to apply penalty.", {"source_identifier": source_identifier})

        return is_limited


    def is_article_new_by_date(self, article_id, published_date_utc, recency_delta_days=2):
        # ... (existing is_article_new_by_date method) ...
        details = {"article_id": article_id, "recency_delta_days": recency_delta_days}
        if published_date_utc is None:
            self.log_event("WARNING", "Article has no published date, considering it new by default.", details)
            return True
        if not isinstance(published_date_utc, datetime.datetime):
            self.log_event("ERROR", "Invalid published_date_utc (not a datetime object).", details); return True
        if published_date_utc.tzinfo is None or published_date_utc.tzinfo.utcoffset(None) != timezone.utc.utcoffset(None) :
            self.log_event("WARNING", "Published date not UTC aware. Assuming UTC.", details)
        now_utc = datetime.datetime.now(timezone.utc)
        is_new = published_date_utc >= (now_utc - timedelta(days=recency_delta_days))
        details.update({"published_date_utc": published_date_utc.isoformat(), "is_new": is_new})
        self.log_event("DEBUG", f"Article newness check by date: {is_new}.", details)
        return is_new

    def get_event_log(self, last_n=None):
        # ... (existing get_event_log method) ...
        return self.event_log[-last_n:] if last_n and isinstance(last_n, int) and last_n > 0 else self.event_log

    def clear_log(self):
        # ... (existing clear_log method) ...
        self.event_log = []
        self.log_event("INFO", "Event log cleared.")


if __name__ == '__main__':
    # Mock Planner and its crawl_delays_cache for testing Monitor's feedback loop
    class MockPlanner:
        def __init__(self):
            self.crawl_delays_cache = {"example.com": 1, "test-domain.org": 5}
            print(f"MockPlanner initialized with delays: {self.crawl_delays_cache}")

        def _log_event(self, level, message, details=None): # Mock a log for planner if needed
            print(f"[MockPlanner-{level}] {message} {details if details else ''}")

    mock_planner_instance = MockPlanner()

    # Pass the mock_planner_instance to the Monitor
    monitor = Monitor(planner_reference=mock_planner_instance)

    monitor.log_event("INFO", "Monitor test with MockPlanner reference.")

    print("\n--- Testing Monitor: Rate Limiting Feedback ---")
    # Test 1: Rate limit detected for a known domain
    monitor.is_rate_limited("Fetcher", "http://example.com/some/path", http_status_code=429)
    print(f"  Crawl delays after example.com rate limit: {mock_planner_instance.crawl_delays_cache}")
    # Expected: example.com delay should increase (e.g., to 2)

    # Test 2: Rate limit for a new domain
    monitor.is_rate_limited("Fetcher", "https://newsite.net/api", http_status_code=503)
    print(f"  Crawl delays after newsite.net rate limit: {mock_planner_instance.crawl_delays_cache}")
    # Expected: newsite.net delay should be added (e.g., to 2, as default was 1 * 2)

    # Test 3: Rate limit by content keyword
    monitor.is_rate_limited("Fetcher", "www.another-domain.com", content_snippet="Please complete the CAPTCHA to continue.")
    print(f"  Crawl delays after another-domain.com CAPTCHA: {mock_planner_instance.crawl_delays_cache}")

    # Test 4: Rate limit again on example.com to see further increase
    monitor.is_rate_limited("Fetcher", "example.com", http_status_code=429) # Pass domain directly
    print(f"  Crawl delays after second example.com rate limit: {mock_planner_instance.crawl_delays_cache}")


    print("\n--- Monitor __main__ tests (including rate limiting feedback) finished ---")
