"""
This module contains the Parser component.
The Parser is responsible for transforming raw HTML/JSON into clean, structured data.
It uses crawl4ai for intelligent content extraction.
"""
from crawl4ai import WebCrawler
from crawl4ai.web_crawler import Url # Correct import for Url

class Parser:
    """
    Parses HTML content to extract structured data using crawl4ai.
    """
    def __init__(self):
        """
        Initializes the Parser.
        Initializes the crawl4ai WebCrawler.
        """
        try:
            self.crawler = WebCrawler()
        except Exception as e:
            # Handle potential errors during WebCrawler initialization,
            # e.g., if it tries to download models and fails without internet.
            print(f"ERROR: Failed to initialize WebCrawler: {e}")
            print("Ensure that crawl4ai is installed correctly and any necessary models are available.")
            self.crawler = None


    def parse_content(self, html_content, url):
        """
        Parses the given HTML content to extract news article data.
        Args:
            html_content (str): The HTML content of the page.
            url (str): The URL of the page, used by crawl4ai for context.
        Returns:
            dict: A dictionary containing extracted data (e.g., title, text, date),
                  or None if parsing fails or no significant content is found.
        """
        if not self.crawler:
            print(f"ERROR: Parser not initialized. Cannot parse content for {url}.")
            return None

        if not html_content:
            print(f"INFO: No HTML content provided for URL: {url}")
            return None

        try:
            # Create a crawl4ai Url object with the pre-fetched HTML content.
            # crawl4ai's `read` method will then process this content.
            url_object = Url(url=url, html_content=html_content)

            # The read() method processes the content.
            # It's designed to extract the main content and metadata.
            result = self.crawler.read(url_object)

            if result and (result.text or result.metadata):
                # crawl4ai's `result` object typically has:
                # - result.text: The main textual content of the page.
                # - result.metadata: A dictionary containing various metadata elements
                #   like title, author, date, etc. The exact keys can vary.

                title = result.metadata.get("title", "N/A")
                main_text = result.text if result.text else "N/A"

                # Date extraction can be complex; crawl4ai might provide it in various forms.
                # Common keys could be 'date', 'publish_date', 'published_time', etc.
                # We'll check a few common ones or rely on a general one if available.
                published_date = result.metadata.get("date",
                                 result.metadata.get("publish_date",
                                 result.metadata.get("published_time", "N/A")))

                extracted_data = {
                    "url": url,
                    "title": title,
                    "text": main_text,
                    "published_date": published_date,
                    "raw_metadata": result.metadata # Include for debugging/further processing
                }
                # print(f"DEBUG: Successfully parsed content for {url}. Title: {title}")
                return extracted_data
            else:
                print(f"INFO: Could not extract sufficient data from {url} using crawl4ai.")
                if result:
                    print(f"DEBUG: crawl4ai result was present but text or metadata might be empty. Metadata: {result.metadata}, Text empty: {not result.text}")
                return None

        except Exception as e:
            print(f"ERROR: Error parsing content for {url} with crawl4ai: {e}")
            # You might want to log the html_content or parts of it for debugging,
            # but be careful about log size and sensitive data.
            return None

if __name__ == '__main__':
    # This example requires crawl4ai to be set up and potentially download models.
    # It might fail in environments without internet access if models aren't cached.
    print("Initializing Parser...")
    parser = Parser()

    if parser.crawler: # Proceed only if crawler was initialized
        # Example HTML content (very basic, but crawl4ai should handle it)
        sample_url = "http://example.com/news_article_today"
        sample_html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Big News Today! A Major Event Shakes the World</title>
            <meta name="description" content="A detailed report on the major event that occurred today.">
            <meta name="publish-date" content="2023-01-15T10:00:00Z">
            <meta name="author" content="John Doe">
        </head>
        <body>
            <header>
                <h1>Important Headline: A Major Event Shakes the World</h1>
            </header>
            <article>
                <p>This is the first paragraph of the article. It describes the initial shock and reactions.</p>
                <p>Further details emerge about the event, indicating its global impact. Experts are weighing in on the consequences.</p>
                <section>
                    <h2>Expert Opinions</h2>
                    <p>Dr. Jane Smith comments on the economic fallout.</p>
                </section>
            </article>
            <footer>
                <p>Copyright 2023 News Corp. Published on 2023-01-15.</p>
            </footer>
        </body>
        </html>
        """

        print(f"\nParsing sample content for {sample_url}...")
        parsed_data = parser.parse_content(sample_html, sample_url)

        if parsed_data:
            print(f"Successfully parsed data from {sample_url}:")
            for key, value in parsed_data.items():
                if key == "text" and isinstance(value, str):
                    print(f"  {key}: {value[:150].replace('\n', ' ')}...") # Print only first 150 chars of text
                elif key == "raw_metadata":
                    print(f"  {key} (type): {type(value)}")
                    # print(f"  {key} (content): {value}") # Uncomment to see full metadata
                else:
                    print(f"  {key}: {value}")
        else:
            print(f"Failed to parse data for {sample_url} or no data extracted.")

        print("\nTesting with None (empty) HTML content:")
        parsed_data_none = parser.parse_content(None, "http://example.com/empty_content_page")
        if not parsed_data_none:
            print("Correctly handled None HTML content (returned None).")

        # Example of a URL that might be harder for generic parsers if HTML is minimal
        minimal_html_url = "http://example.com/minimal"
        minimal_html = "<html><head><title>Minimal Test</title></head><body>Just a sentence.</body></html>"
        print(f"\nParsing minimal HTML for {minimal_html_url}...")
        parsed_minimal = parser.parse_content(minimal_html, minimal_html_url)
        if parsed_minimal:
            print(f"Parsed data from {minimal_html_url}:")
            print(f"  Title: {parsed_minimal.get('title')}")
            print(f"  Text: {parsed_minimal.get('text')}")
        else:
            print(f"Failed to parse or extract data from {minimal_html_url}.")
    else:
        print("Parser could not be initialized. Skipping __main__ examples.")
