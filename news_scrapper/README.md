# News Scrapper

This project is a web scraper designed to extract news articles from various sources.
It is organized into several components to manage different aspects of the scraping process.

## Project Structure

The project is divided into the following main components:

-   **`planner/`**: Defines the target websites, news categories, and scraping strategies.
    -   `planner.py`: Contains the `Planner` class responsible for providing the list of URLs to scrape.
-   **`fetcher/`**: Handles the actual downloading of web pages.
    -   `fetcher.py`: Contains the `Fetcher` class used to retrieve HTML content from URLs, managing aspects like user-agents and politeness.
-   **`parser/`**: Extracts structured data from the raw HTML content.
    -   `parser.py`: Contains the `Parser` class which uses `crawl4ai` to parse HTML and extract relevant information like headlines, article text, and publication dates.
-   **`pipeline/`**: Manages the flow of data, from URL queuing to storing results.
    -   `pipeline.py`: Contains the `Pipeline` class for managing the queue of URLs to be scraped and for storing the extracted data.
-   **`monitor/`**: Logs events, monitors for errors, and detects potential issues like site changes or blocks.
    -   `monitor.py`: Contains the `Monitor` class for logging events and reporting issues during the scraping process.
-   **`main.py`**: The main script to orchestrate the different components and run the scraper.
-   **`config.py`**: (Placeholder) For storing configuration settings for the scraper.
-   **`utils.py`**: (Placeholder) For utility functions shared across components.
-   **`requirements.txt`**: Lists the Python dependencies for this project.

## Installation

1.  Clone the repository (if applicable).
2.  Navigate to the `news_scrapper` directory.
3.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    If you encounter issues with `crawl4ai` model downloads during installation or first run, ensure you have an active internet connection. `crawl4ai` may download necessary NLP models on its first use if they are not already cached.

## Basic Usage

(Note: The `main.py` script is still under development. The following is a conceptual overview.)

To run the scraper, you would typically execute the `main.py` script from within the `news_scrapper` directory:

```bash
python main.py
```

This script will (eventually) perform the following steps:
1.  Initialize all components: `Planner`, `Fetcher`, `Parser`, `Pipeline`, and `Monitor`.
2.  The `Planner` will generate or load a list of target URLs/configurations.
3.  These targets will be added to the `Pipeline`'s processing queue.
4.  The main loop will iterate while the `Pipeline` has pending URLs:
    a.  Get the next URL from the `Pipeline`.
    b.  The `Fetcher` will attempt to download the content of the URL.
    c.  If fetching is successful, the `Parser` will process the HTML content to extract structured news data.
    d.  The extracted data (or any errors encountered) will be passed to the `Pipeline` for storage or handling.
5.  Throughout this process, the `Monitor` will log activities, errors, warnings, and any detected anomalies (like site changes or rate limiting).
6.  Results collected by the `Pipeline` can then be outputted to a file, database, or another system as configured.

Configuration for targets, API keys (if any), database connections, and other operational parameters will ideally be managed via `config.py` or external configuration files loaded by the `Planner` and other components.
```
