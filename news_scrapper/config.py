"""
Global configuration settings for the News Scrapper.
"""
import os

# Base directory of the news_scrapper package.
# This assumes config.py is in the 'news_scrapper' directory.
# os.path.abspath(__file__) gives the absolute path to config.py
# os.path.dirname() then gives the directory containing config.py
PROJECT_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to the sources configuration file, located in 'news_scrapper/config/sources.json'
SOURCES_CONFIG_PATH = os.path.join(PROJECT_ROOT_DIR, "config", "sources.json")

# Example other global configurations (can be added as needed):

# Default User-Agent for the Fetcher component
DEFAULT_USER_AGENT = "NewsScrapperBot/1.0 (+https://github.com/your_username/news_scrapper)" # Replace with your project URL

# Default timeout for HTTP requests in seconds
DEFAULT_REQUEST_TIMEOUT = 15

# Default delay between requests to the same domain in seconds (for Fetcher politeness)
DEFAULT_REQUEST_DELAY = 1

# Path for storing logs from the Monitor component
LOG_FILE_PATH = os.path.join(PROJECT_ROOT_DIR, "logs", "scraper.log") # Ensure 'logs' directory exists or is created

# Path for storing results from the Pipeline (e.g., if saving to JSON files)
RESULTS_DIR = os.path.join(PROJECT_ROOT_DIR, "scraped_results") # Ensure 'scraped_results' directory exists

# Max number of full result items to keep in the pipeline's in-memory list
MAX_RESULTS_TO_STORE_IN_MEMORY = 1000

# Database connection string (example, if using a database)
# DATABASE_URI = "sqlite:///" + os.path.join(PROJECT_ROOT_DIR, "data", "news_data.db")


if __name__ == '__main__':
    # Print out the determined paths for verification if this script is run directly
    print(f"Project Root Directory: {PROJECT_ROOT_DIR}")
    print(f"Sources Configuration File Path: {SOURCES_CONFIG_PATH}")
    print(f"Log File Path: {LOG_FILE_PATH}")
    print(f"Results Directory: {RESULTS_DIR}")
    # print(f"Database URI: {DATABASE_URI}")

    # You might want to ensure necessary directories exist when the config is loaded/used.
    # For example, by creating them here or in the components that use them.
    # os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
    # os.makedirs(RESULTS_DIR, exist_ok=True)
