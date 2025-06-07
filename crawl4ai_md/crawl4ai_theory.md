

# Core Functionality - Memory
Source: crawl4ai_core_memory_content.llm.md

Okay, I have read the objective and instructions. I will now generate the detailed Markdown outline for a "Foundational Memory" document for the `core` component of `crawl4ai`, using the provided `code_analysis_output.md` (the concatenated code snippets from the previous prompt) as the primary source of truth for API details.

```markdown
# Detailed Outline for crawl4ai - core Component

**Target Document Type:** memory
**Target Output Filename Suggestion:** `llm_memory_core.md`
**Library Version Context:** 0.6.3
**Outline Generation Date:** 2025-05-24
---

## 1. Introduction to Core Components
    * 1.1. Purpose: Provides the foundational classes, configurations, and data models for web crawling and scraping operations within the `crawl4ai` library.
    * 1.2. Key Functionalities:
        *   Orchestration of asynchronous web crawling (`AsyncWebCrawler`).
        *   Configuration of browser behavior and specific crawl runs (`BrowserConfig`, `CrawlerRunConfig`).
        *   Standardized data structures for crawl results and associated data (`CrawlResult`, `Media`, `Links`, etc.).
        *   Strategies for fetching web content (`AsyncPlaywrightCrawlerStrategy`, `AsyncHTTPCrawlerStrategy`).
        *   Management of browser instances and sessions (`BrowserManager`, `ManagedBrowser`).
        *   Asynchronous logging (`AsyncLogger`).
    * 1.3. Relationship with other `crawl4ai` components:
        *   The `core` component serves as the foundation upon which specialized strategies (e.g., PDF processing, Markdown generation, content extraction, chunking, content filtering) are built and integrated.

## 2. Main Class: `AsyncWebCrawler`
    * 2.1. Purpose: The primary class for orchestrating asynchronous web crawling operations. It manages browser instances (via a `BrowserManager`), applies crawling strategies, and processes HTML content to produce structured results.
    * 2.2. Initialization (`__init__`)
        * 2.2.1. Signature:
            ```python
            def __init__(
                self,
                crawler_strategy: Optional[AsyncCrawlerStrategy] = None,
                config: Optional[BrowserConfig] = None,
                base_directory: str = str(os.getenv("CRAWL4_AI_BASE_DIRECTORY", Path.home())),
                thread_safe: bool = False,
                logger: Optional[AsyncLoggerBase] = None,
                **kwargs,
            ):
            ```
        * 2.2.2. Parameters:
            * `crawler_strategy (Optional[AsyncCrawlerStrategy])`: The strategy to use for fetching web content. If `None`, defaults to `AsyncPlaywrightCrawlerStrategy` initialized with `config` and `logger`.
            * `config (Optional[BrowserConfig])`: Configuration object for browser settings. If `None`, a default `BrowserConfig()` is created.
            * `base_directory (str)`: The base directory for storing crawl4ai related files, such as cache and logs. Defaults to `os.getenv("CRAWL4_AI_BASE_DIRECTORY", Path.home())`.
            * `thread_safe (bool)`: If `True`, uses an `asyncio.Lock` for thread-safe operations, particularly relevant for `arun_many`. Default: `False`.
            * `logger (Optional[AsyncLoggerBase])`: An instance of a logger. If `None`, a default `AsyncLogger` is initialized using `base_directory` and `config.verbose`.
            * `**kwargs`: Additional keyword arguments, primarily for backward compatibility, passed to the `AsyncPlaywrightCrawlerStrategy` if `crawler_strategy` is not provided.
    * 2.3. Key Public Attributes/Properties:
        * `browser_config (BrowserConfig)`: Read-only. The browser configuration object used by the crawler.
        * `crawler_strategy (AsyncCrawlerStrategy)`: Read-only. The active crawling strategy instance.
        * `logger (AsyncLoggerBase)`: Read-only. The logger instance used by the crawler.
        * `ready (bool)`: Read-only. `True` if the crawler has been started and is ready to perform crawl operations, `False` otherwise.
    * 2.4. Lifecycle Methods:
        * 2.4.1. `async start() -> AsyncWebCrawler`:
            * Purpose: Asynchronously initializes the crawler strategy (e.g., launches the browser). This must be called before `arun` or `arun_many` if the crawler is not used as an asynchronous context manager.
            * Returns: The `AsyncWebCrawler` instance (`self`).
        * 2.4.2. `async close() -> None`:
            * Purpose: Asynchronously closes the crawler strategy and cleans up resources (e.g., closes the browser). This should be called if `start()` was used explicitly.
        * 2.4.3. `async __aenter__() -> AsyncWebCrawler`:
            * Purpose: Entry point for asynchronous context management. Calls `self.start()`.
            * Returns: The `AsyncWebCrawler` instance (`self`).
        * 2.4.4. `async __aexit__(exc_type, exc_val, exc_tb) -> None`:
            * Purpose: Exit point for asynchronous context management. Calls `self.close()`.
    * 2.5. Primary Crawl Methods:
        * 2.5.1. `async arun(url: str, config: Optional[CrawlerRunConfig] = None, **kwargs) -> RunManyReturn`:
            * Purpose: Performs a single crawl operation for the given URL or raw HTML content.
            * Parameters:
                * `url (str)`: The URL to crawl (e.g., "http://example.com", "file:///path/to/file.html") or raw HTML content prefixed with "raw:" (e.g., "raw:<html>...</html>").
                * `config (Optional[CrawlerRunConfig])`: Configuration for this specific crawl run. If `None`, a default `CrawlerRunConfig()` is used.
                * `**kwargs`: Additional parameters passed to the underlying `aprocess_html` method, can be used to override settings in `config`.
            * Returns: `RunManyReturn` (which resolves to `CrawlResultContainer` containing a single `CrawlResult`).
        * 2.5.2. `async arun_many(urls: List[str], config: Optional[CrawlerRunConfig] = None, dispatcher: Optional[BaseDispatcher] = None, **kwargs) -> RunManyReturn`:
            * Purpose: Crawls multiple URLs concurrently using a specified or default dispatcher strategy.
            * Parameters:
                * `urls (List[str])`: A list of URLs to crawl.
                * `config (Optional[CrawlerRunConfig])`: Configuration applied to all crawl runs in this batch.
                * `dispatcher (Optional[BaseDispatcher])`: The dispatcher strategy to manage concurrent crawls. Defaults to `MemoryAdaptiveDispatcher`.
                * `**kwargs`: Additional parameters passed to the underlying `arun` method for each URL.
            * Returns: `RunManyReturn`. If `config.stream` is `True`, returns an `AsyncGenerator[CrawlResult, None]`. Otherwise, returns a `CrawlResultContainer` (list-like) of `CrawlResult` objects.
    * 2.6. Internal Processing Method (User-Facing Effects):
        * 2.6.1. `async aprocess_html(url: str, html: str, extracted_content: Optional[str], config: CrawlerRunConfig, screenshot_data: Optional[str], pdf_data: Optional[bytes], verbose: bool, **kwargs) -> CrawlResult`:
            * Purpose: Processes the fetched HTML content. This method is called internally by `arun` after content is fetched (either from a live crawl or cache). It applies scraping strategies, content filtering, and Markdown generation based on the `config`.
            * Parameters:
                * `url (str)`: The URL of the content being processed.
                * `html (str)`: The raw HTML content.
                * `extracted_content (Optional[str])`: Pre-extracted content from a previous step or cache.
                * `config (CrawlerRunConfig)`: Configuration for this processing run.
                * `screenshot_data (Optional[str])`: Base64 encoded screenshot data, if available.
                * `pdf_data (Optional[bytes])`: PDF data, if available.
                * `verbose (bool)`: Verbosity setting for logging during processing.
                * `**kwargs`: Additional parameters, including `is_raw_html` and `redirected_url`.
            * Returns: A `CrawlResult` object containing the processed data.

## 3. Core Configuration Objects

    * 3.1. Class `BrowserConfig` (from `crawl4ai.async_configs`)
        * 3.1.1. Purpose: Configures the browser instance launched by Playwright, including its type, mode, display settings, proxy, user agent, and persistent storage options.
        * 3.1.2. Initialization (`__init__`)
            * Signature:
            ```python
            def __init__(
                self,
                browser_type: str = "chromium",
                headless: bool = True,
                browser_mode: str = "dedicated",
                use_managed_browser: bool = False,
                cdp_url: Optional[str] = None,
                use_persistent_context: bool = False,
                user_data_dir: Optional[str] = None,
                channel: Optional[str] = "chromium", # Note: 'channel' from code, outline had 'chrome_channel'
                proxy: Optional[str] = None, # Note: 'proxy' from code, outline had 'proxy_config' for this level
                proxy_config: Optional[Union[ProxyConfig, dict, None]] = None,
                viewport_width: int = 1080,
                viewport_height: int = 600,
                viewport: Optional[dict] = None,
                accept_downloads: bool = False,
                downloads_path: Optional[str] = None,
                storage_state: Optional[Union[str, dict, None]] = None,
                ignore_https_errors: bool = True,
                java_script_enabled: bool = True,
                sleep_on_close: bool = False,
                verbose: bool = True,
                cookies: Optional[list] = None,
                headers: Optional[dict] = None,
                user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/116.0.0.0 Safari/537.36",
                user_agent_mode: str = "",
                user_agent_generator_config: Optional[dict] = None, # Note: 'user_agent_generator_config' from code
                text_mode: bool = False,
                light_mode: bool = False,
                extra_args: Optional[list] = None,
                debugging_port: int = 9222,
                host: str = "localhost",
            ):
            ```
            * Key Parameters:
                * `browser_type (str)`: Type of browser to launch ("chromium", "firefox", "webkit"). Default: "chromium".
                * `headless (bool)`: Whether to run the browser in headless mode. Default: `True`.
                * `browser_mode (str)`: How the browser should be initialized ("builtin", "dedicated", "cdp", "docker"). Default: "dedicated".
                * `use_managed_browser (bool)`: Whether to launch the browser using a managed approach (e.g., via CDP). Default: `False`.
                * `cdp_url (Optional[str])`: URL for Chrome DevTools Protocol endpoint. Default: `None`.
                * `use_persistent_context (bool)`: Use a persistent browser context (profile). Default: `False`.
                * `user_data_dir (Optional[str])`: Path to user data directory for persistent sessions. Default: `None`.
                * `channel (Optional[str])`: Browser channel (e.g., "chromium", "chrome", "msedge"). Default: "chromium".
                * `proxy (Optional[str])`: Simple proxy server URL string.
                * `proxy_config (Optional[Union[ProxyConfig, dict, None]])`: Detailed proxy configuration object or dictionary. Takes precedence over `proxy`.
                * `viewport_width (int)`: Default viewport width. Default: `1080`.
                * `viewport_height (int)`: Default viewport height. Default: `600`.
                * `viewport (Optional[dict])`: Dictionary to set viewport dimensions, overrides `viewport_width` and `viewport_height` if set (e.g., `{"width": 1920, "height": 1080}`). Default: `None`.
                * `accept_downloads (bool)`: Whether to allow file downloads. Default: `False`.
                * `downloads_path (Optional[str])`: Directory to store downloaded files. Default: `None`.
                * `storage_state (Optional[Union[str, dict, None]])`: Path to a file or a dictionary containing browser storage state (cookies, localStorage). Default: `None`.
                * `ignore_https_errors (bool)`: Ignore HTTPS certificate errors. Default: `True`.
                * `java_script_enabled (bool)`: Enable JavaScript execution. Default: `True`.
                * `user_agent (str)`: Custom User-Agent string. Default: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/116.0.0.0 Safari/537.36".
                * `user_agent_mode (str)`: Mode for generating User-Agent (e.g., "random"). Default: `""` (uses provided `user_agent`).
                * `user_agent_generator_config (Optional[dict])`: Configuration for User-Agent generation if `user_agent_mode` is active. Default: `{}`.
                * `text_mode (bool)`: If `True`, disables images and rich content for faster loading. Default: `False`.
                * `light_mode (bool)`: Disables certain background features for performance. Default: `False`.
                * `extra_args (Optional[list])`: Additional command-line arguments for the browser. Default: `None` (resolves to `[]`).
                * `debugging_port (int)`: Port for browser debugging protocol. Default: `9222`.
                * `host (str)`: Host for browser debugging protocol. Default: "localhost".
        * 3.1.3. Key Public Methods:
            * `clone(**kwargs) -> BrowserConfig`: Creates a new `BrowserConfig` instance as a copy of the current one, with specified keyword arguments overriding existing values.
            * `to_dict() -> dict`: Returns a dictionary representation of the configuration object's attributes.
            * `dump() -> dict`: Serializes the configuration object to a JSON-serializable dictionary, including nested objects.
            * `static load(data: dict) -> BrowserConfig`: Deserializes a `BrowserConfig` instance from a dictionary (previously created by `dump`).
            * `static from_kwargs(kwargs: dict) -> BrowserConfig`: Creates a `BrowserConfig` instance directly from a dictionary of keyword arguments.

    * 3.2. Class `CrawlerRunConfig` (from `crawl4ai.async_configs`)
        * 3.2.1. Purpose: Specifies settings for an individual crawl operation initiated by `arun()` or `arun_many()`. These settings can override or augment the global `BrowserConfig`.
        * 3.2.2. Initialization (`__init__`)
            * Signature:
            ```python
            def __init__(
                self,
                # Content Processing Parameters
                word_count_threshold: int = MIN_WORD_THRESHOLD,
                extraction_strategy: Optional[ExtractionStrategy] = None,
                chunking_strategy: ChunkingStrategy = RegexChunking(),
                markdown_generator: MarkdownGenerationStrategy = DefaultMarkdownGenerator(),
                only_text: bool = False,
                css_selector: Optional[str] = None,
                target_elements: Optional[List[str]] = None,
                excluded_tags: Optional[list] = None,
                excluded_selector: Optional[str] = None,
                keep_data_attributes: bool = False,
                keep_attrs: Optional[list] = None,
                remove_forms: bool = False,
                prettify: bool = False,
                parser_type: str = "lxml",
                scraping_strategy: ContentScrapingStrategy = None, # Will default to WebScrapingStrategy
                proxy_config: Optional[Union[ProxyConfig, dict, None]] = None,
                proxy_rotation_strategy: Optional[ProxyRotationStrategy] = None,
                # Browser Location and Identity Parameters
                locale: Optional[str] = None,
                timezone_id: Optional[str] = None,
                geolocation: Optional[GeolocationConfig] = None,
                # SSL Parameters
                fetch_ssl_certificate: bool = False,
                # Caching Parameters
                cache_mode: CacheMode = CacheMode.BYPASS,
                session_id: Optional[str] = None,
                bypass_cache: bool = False, # Legacy
                disable_cache: bool = False, # Legacy
                no_cache_read: bool = False, # Legacy
                no_cache_write: bool = False, # Legacy
                shared_data: Optional[dict] = None,
                # Page Navigation and Timing Parameters
                wait_until: str = "domcontentloaded",
                page_timeout: int = PAGE_TIMEOUT,
                wait_for: Optional[str] = None,
                wait_for_timeout: Optional[int] = None,
                wait_for_images: bool = False,
                delay_before_return_html: float = 0.1,
                mean_delay: float = 0.1,
                max_range: float = 0.3,
                semaphore_count: int = 5,
                # Page Interaction Parameters
                js_code: Optional[Union[str, List[str]]] = None,
                js_only: bool = False,
                ignore_body_visibility: bool = True,
                scan_full_page: bool = False,
                scroll_delay: float = 0.2,
                process_iframes: bool = False,
                remove_overlay_elements: bool = False,
                simulate_user: bool = False,
                override_navigator: bool = False,
                magic: bool = False,
                adjust_viewport_to_content: bool = False,
                # Media Handling Parameters
                screenshot: bool = False,
                screenshot_wait_for: Optional[float] = None,
                screenshot_height_threshold: int = SCREENSHOT_HEIGHT_THRESHOLD,
                pdf: bool = False,
                capture_mhtml: bool = False,
                image_description_min_word_threshold: int = IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD,
                image_score_threshold: int = IMAGE_SCORE_THRESHOLD,
                table_score_threshold: int = 7,
                exclude_external_images: bool = False,
                exclude_all_images: bool = False,
                # Link and Domain Handling Parameters
                exclude_social_media_domains: Optional[list] = None, # Note: 'exclude_social_media_domains' from code
                exclude_external_links: bool = False,
                exclude_social_media_links: bool = False,
                exclude_domains: Optional[list] = None,
                exclude_internal_links: bool = False,
                # Debugging and Logging Parameters
                verbose: bool = True,
                log_console: bool = False,
                # Network and Console Capturing Parameters
                capture_network_requests: bool = False,
                capture_console_messages: bool = False,
                # Connection Parameters (for HTTPCrawlerStrategy)
                method: str = "GET",
                stream: bool = False,
                url: Optional[str] = None,
                # Robots.txt Handling
                check_robots_txt: bool = False,
                # User Agent Parameters
                user_agent: Optional[str] = None,
                user_agent_mode: Optional[str] = None,
                user_agent_generator_config: Optional[dict] = None, # Note: 'user_agent_generator_config' from code
                # Deep Crawl Parameters
                deep_crawl_strategy: Optional[DeepCrawlStrategy] = None,
                # Experimental Parameters
                experimental: Optional[Dict[str, Any]] = None,
            ):
            ```
            * Key Parameters:
                * `word_count_threshold (int)`: Minimum word count for a content block to be considered. Default: `MIN_WORD_THRESHOLD` (200).
                * `extraction_strategy (Optional[ExtractionStrategy])`: Strategy for structured data extraction (e.g., `LLMExtractionStrategy`, `JsonCssExtractionStrategy`). Default: `None` (falls back to `NoExtractionStrategy`).
                * `chunking_strategy (ChunkingStrategy)`: Strategy for splitting content into chunks before extraction. Default: `RegexChunking()`.
                * `markdown_generator (MarkdownGenerationStrategy)`: Strategy for converting HTML to Markdown. Default: `DefaultMarkdownGenerator()`.
                * `cache_mode (CacheMode)`: Caching behavior for this run. Default: `CacheMode.BYPASS`.
                * `session_id (Optional[str])`: ID for session persistence (reusing browser tabs/contexts). Default: `None`.
                * `js_code (Optional[Union[str, List[str]]])`: JavaScript code snippets to execute on the page. Default: `None`.
                * `wait_for (Optional[str])`: CSS selector or JS condition (prefixed with "js:") to wait for before proceeding. Default: `None`.
                * `page_timeout (int)`: Timeout for page operations (e.g., navigation) in milliseconds. Default: `PAGE_TIMEOUT` (60000ms).
                * `screenshot (bool)`: If `True`, capture a screenshot of the page. Default: `False`.
                * `pdf (bool)`: If `True`, generate a PDF of the page. Default: `False`.
                * `capture_mhtml (bool)`: If `True`, capture an MHTML snapshot of the page. Default: `False`.
                * `exclude_external_links (bool)`: If `True`, exclude external links from results. Default: `False`.
                * `stream (bool)`: If `True` (used with `arun_many`), results are yielded as an `AsyncGenerator`. Default: `False`.
                * `check_robots_txt (bool)`: If `True`, crawler will check and respect `robots.txt` rules. Default: `False`.
                * `user_agent (Optional[str])`: Override the browser's User-Agent for this specific run.
        * 3.2.3. Key Public Methods:
            * `clone(**kwargs) -> CrawlerRunConfig`: Creates a new `CrawlerRunConfig` instance as a copy of the current one, with specified keyword arguments overriding existing values.
            * `to_dict() -> dict`: Returns a dictionary representation of the configuration object's attributes.
            * `dump() -> dict`: Serializes the configuration object to a JSON-serializable dictionary, including nested objects.
            * `static load(data: dict) -> CrawlerRunConfig`: Deserializes a `CrawlerRunConfig` instance from a dictionary (previously created by `dump`).
            * `static from_kwargs(kwargs: dict) -> CrawlerRunConfig`: Creates a `CrawlerRunConfig` instance directly from a dictionary of keyword arguments.

    * 3.3. Supporting Configuration Objects (from `crawl4ai.async_configs`)
        * 3.3.1. Class `GeolocationConfig`
            * Purpose: Defines geolocation (latitude, longitude, accuracy) to be emulated by the browser.
            * Initialization (`__init__`):
                ```python
                def __init__(
                    self,
                    latitude: float,
                    longitude: float,
                    accuracy: Optional[float] = 0.0
                ):
                ```
            * Parameters:
                * `latitude (float)`: Latitude coordinate (e.g., 37.7749).
                * `longitude (float)`: Longitude coordinate (e.g., -122.4194).
                * `accuracy (Optional[float])`: Accuracy in meters. Default: `0.0`.
            * Methods:
                * `static from_dict(geo_dict: Dict) -> GeolocationConfig`: Creates an instance from a dictionary.
                * `to_dict() -> Dict`: Converts the instance to a dictionary.
                * `clone(**kwargs) -> GeolocationConfig`: Creates a copy with updated values.
        * 3.3.2. Class `ProxyConfig`
            * Purpose: Defines the settings for a single proxy server, including server address, authentication credentials, and optional IP.
            * Initialization (`__init__`):
                ```python
                def __init__(
                    self,
                    server: str,
                    username: Optional[str] = None,
                    password: Optional[str] = None,
                    ip: Optional[str] = None,
                ):
                ```
            * Parameters:
                * `server (str)`: Proxy server URL (e.g., "http://127.0.0.1:8080", "socks5://user:pass@host:port").
                * `username (Optional[str])`: Username for proxy authentication.
                * `password (Optional[str])`: Password for proxy authentication.
                * `ip (Optional[str])`: Optional IP address associated with the proxy for verification.
            * Methods:
                * `static from_string(proxy_str: str) -> ProxyConfig`: Creates an instance from a string (e.g., "ip:port:username:password" or "ip:port").
                * `static from_dict(proxy_dict: Dict) -> ProxyConfig`: Creates an instance from a dictionary.
                * `static from_env(env_var: str = "PROXIES") -> List[ProxyConfig]`: Loads a list of proxies from a comma-separated environment variable.
                * `to_dict() -> Dict`: Converts the instance to a dictionary.
                * `clone(**kwargs) -> ProxyConfig`: Creates a copy with updated values.
        * 3.3.3. Class `HTTPCrawlerConfig`
            * Purpose: Configuration for the `AsyncHTTPCrawlerStrategy`, specifying HTTP method, headers, data/JSON payload, and redirect/SSL verification behavior.
            * Initialization (`__init__`):
                ```python
                def __init__(
                    self,
                    method: str = "GET",
                    headers: Optional[Dict[str, str]] = None,
                    data: Optional[Dict[str, Any]] = None,
                    json: Optional[Dict[str, Any]] = None,
                    follow_redirects: bool = True,
                    verify_ssl: bool = True,
                ):
                ```
            * Parameters:
                * `method (str)`: HTTP method (e.g., "GET", "POST"). Default: "GET".
                * `headers (Optional[Dict[str, str]])`: Dictionary of HTTP request headers. Default: `None`.
                * `data (Optional[Dict[str, Any]])`: Dictionary of form data to send in the request body. Default: `None`.
                * `json (Optional[Dict[str, Any]])`: JSON data to send in the request body. Default: `None`.
                * `follow_redirects (bool)`: Whether to automatically follow HTTP redirects. Default: `True`.
                * `verify_ssl (bool)`: Whether to verify SSL certificates. Default: `True`.
            * Methods:
                * `static from_kwargs(kwargs: dict) -> HTTPCrawlerConfig`: Creates an instance from keyword arguments.
                * `to_dict() -> dict`: Converts config to a dictionary.
                * `clone(**kwargs) -> HTTPCrawlerConfig`: Creates a copy with updated values.
                * `dump() -> dict`: Serializes the config to a dictionary.
                * `static load(data: dict) -> HTTPCrawlerConfig`: Deserializes from a dictionary.
        * 3.3.4. Class `LLMConfig`
            * Purpose: Configures settings for interacting with Large Language Models, including provider choice, API credentials, and generation parameters.
            * Initialization (`__init__`):
                ```python
                def __init__(
                    self,
                    provider: str = DEFAULT_PROVIDER,
                    api_token: Optional[str] = None,
                    base_url: Optional[str] = None,
                    temperature: Optional[float] = None,
                    max_tokens: Optional[int] = None,
                    top_p: Optional[float] = None,
                    frequency_penalty: Optional[float] = None,
                    presence_penalty: Optional[float] = None,
                    stop: Optional[List[str]] = None,
                    n: Optional[int] = None,
                ):
                ```
            * Key Parameters:
                * `provider (str)`: Name of the LLM provider (e.g., "openai/gpt-4o", "ollama/llama3.3", "groq/llama3-8b-8192"). Default: `DEFAULT_PROVIDER` (from `crawl4ai.config`).
                * `api_token (Optional[str])`: API token for the LLM provider. If prefixed with "env:", it reads from the specified environment variable (e.g., "env:OPENAI_API_KEY"). If not provided, it attempts to load from default environment variables based on the provider.
                * `base_url (Optional[str])`: Custom base URL for the LLM API endpoint.
                * `temperature (Optional[float])`: Sampling temperature for generation.
                * `max_tokens (Optional[int])`: Maximum number of tokens to generate.
                * `top_p (Optional[float])`: Nucleus sampling parameter.
                * `frequency_penalty (Optional[float])`: Penalty for token frequency.
                * `presence_penalty (Optional[float])`: Penalty for token presence.
                * `stop (Optional[List[str]])`: List of stop sequences for generation.
                * `n (Optional[int])`: Number of completions to generate.
            * Methods:
                * `static from_kwargs(kwargs: dict) -> LLMConfig`: Creates an instance from keyword arguments.
                * `to_dict() -> dict`: Converts config to a dictionary.
                * `clone(**kwargs) -> LLMConfig`: Creates a copy with updated values.

## 4. Core Data Models (Results & Payloads from `crawl4ai.models`)

    * 4.1. Class `CrawlResult(BaseModel)`
        * Purpose: A Pydantic model representing the comprehensive result of a single crawl and processing operation.
        * Key Fields:
            * `url (str)`: The final URL that was crawled (after any redirects).
            * `html (str)`: The raw HTML content fetched from the URL.
            * `success (bool)`: `True` if the crawl operation (fetching and initial processing) was successful, `False` otherwise.
            * `cleaned_html (Optional[str])`: HTML content after sanitization and removal of unwanted tags/attributes as per configuration. Default: `None`.
            * `_markdown (Optional[MarkdownGenerationResult])`: (Private Attribute) Holds the `MarkdownGenerationResult` object if Markdown generation was performed. Use the `markdown` property to access. Default: `None`.
            * `markdown (Optional[Union[str, MarkdownGenerationResult]])`: (Property) Provides access to Markdown content. Behaves as a string (raw markdown) by default but allows access to `MarkdownGenerationResult` attributes (e.g., `result.markdown.fit_markdown`).
            * `extracted_content (Optional[str])`: JSON string representation of structured data extracted by an `ExtractionStrategy`. Default: `None`.
            * `media (Media)`: An object containing lists of `MediaItem` for images, videos, audio, and extracted tables. Default: `Media()`.
            * `links (Links)`: An object containing lists of `Link` for internal and external hyperlinks found on the page. Default: `Links()`.
            * `downloaded_files (Optional[List[str]])`: A list of file paths if any files were downloaded during the crawl. Default: `None`.
            * `js_execution_result (Optional[Dict[str, Any]])`: The result of any JavaScript code executed on the page. Default: `None`.
            * `screenshot (Optional[str])`: Base64 encoded string of the page screenshot, if `screenshot=True` was set. Default: `None`.
            * `pdf (Optional[bytes])`: Raw bytes of the PDF generated from the page, if `pdf=True` was set. Default: `None`.
            * `mhtml (Optional[str])`: MHTML snapshot of the page, if `capture_mhtml=True` was set. Default: `None`.
            * `metadata (Optional[dict])`: Dictionary of metadata extracted from the page (e.g., title, description, OpenGraph tags, Twitter card data). Default: `None`.
            * `error_message (Optional[str])`: A message describing the error if `success` is `False`. Default: `None`.
            * `session_id (Optional[str])`: The session ID used for this crawl, if applicable. Default: `None`.
            * `response_headers (Optional[dict])`: HTTP response headers from the server. Default: `None`.
            * `status_code (Optional[int])`: HTTP status code of the response. Default: `None`.
            * `ssl_certificate (Optional[SSLCertificate])`: Information about the SSL certificate if `fetch_ssl_certificate=True`. Default: `None`.
            * `dispatch_result (Optional[DispatchResult])`: Metadata about the task execution from the dispatcher (e.g., timings, memory usage). Default: `None`.
            * `redirected_url (Optional[str])`: The original URL if the request was redirected. Default: `None`.
            * `network_requests (Optional[List[Dict[str, Any]]])`: List of captured network requests if `capture_network_requests=True`. Default: `None`.
            * `console_messages (Optional[List[Dict[str, Any]]])`: List of captured browser console messages if `capture_console_messages=True`. Default: `None`.
        * Methods:
            * `model_dump(*args, **kwargs)`: Serializes the `CrawlResult` model to a dictionary, ensuring the `_markdown` private attribute is correctly handled and included as "markdown" in the output if present.

    * 4.2. Class `MarkdownGenerationResult(BaseModel)`
        * Purpose: A Pydantic model that holds various forms of Markdown generated from HTML content.
        * Fields:
            * `raw_markdown (str)`: The basic, direct conversion of HTML to Markdown.
            * `markdown_with_citations (str)`: Markdown content with inline citations (e.g., [^1^]) and a references section.
            * `references_markdown (str)`: The Markdown content for the "References" section, listing all cited links.
            * `fit_markdown (Optional[str])`: Markdown generated specifically from content deemed "relevant" by a content filter (like `PruningContentFilter` or `LLMContentFilter`), if such a filter was applied. Default: `None`.
            * `fit_html (Optional[str])`: The filtered HTML content that was used to generate `fit_markdown`. Default: `None`.
        * Methods:
            * `__str__(self) -> str`: Returns `self.raw_markdown` when the object is cast to a string.

    * 4.3. Class `ScrapingResult(BaseModel)`
        * Purpose: A Pydantic model representing a standardized output from content scraping strategies.
        * Fields:
            * `cleaned_html (str)`: The primary sanitized and processed HTML content.
            * `success (bool)`: Indicates if the scraping operation was successful.
            * `media (Media)`: A `Media` object containing extracted images, videos, audio, and tables.
            * `links (Links)`: A `Links` object containing extracted internal and external links.
            * `metadata (Dict[str, Any])`: A dictionary of metadata extracted from the page (e.g., title, description).

    * 4.4. Class `MediaItem(BaseModel)`
        * Purpose: A Pydantic model representing a generic media item like an image, video, or audio file.
        * Fields:
            * `src (Optional[str])`: The source URL of the media item. Default: `""`.
            * `data (Optional[str])`: Base64 encoded data for inline media. Default: `""`.
            * `alt (Optional[str])`: Alternative text for the media item (e.g., image alt text). Default: `""`.
            * `desc (Optional[str])`: A description or surrounding text related to the media item. Default: `""`.
            * `score (Optional[int])`: A relevance or importance score, if calculated by a strategy. Default: `0`.
            * `type (str)`: The type of media (e.g., "image", "video", "audio"). Default: "image".
            * `group_id (Optional[int])`: An identifier to group related media variants (e.g., different resolutions of the same image from a srcset). Default: `0`.
            * `format (Optional[str])`: The detected file format (e.g., "jpeg", "png", "mp4"). Default: `None`.
            * `width (Optional[int])`: The width of the media item in pixels, if available. Default: `None`.

    * 4.5. Class `Link(BaseModel)`
        * Purpose: A Pydantic model representing an extracted hyperlink.
        * Fields:
            * `href (Optional[str])`: The URL (href attribute) of the link. Default: `""`.
            * `text (Optional[str])`: The anchor text of the link. Default: `""`.
            * `title (Optional[str])`: The title attribute of the link, if present. Default: `""`.
            * `base_domain (Optional[str])`: The base domain extracted from the `href`. Default: `""`.

    * 4.6. Class `Media(BaseModel)`
        * Purpose: A Pydantic model that acts as a container for lists of different types of media items found on a page.
        * Fields:
            * `images (List[MediaItem])`: A list of `MediaItem` objects representing images. Default: `[]`.
            * `videos (List[MediaItem])`: A list of `MediaItem` objects representing videos. Default: `[]`.
            * `audios (List[MediaItem])`: A list of `MediaItem` objects representing audio files. Default: `[]`.
            * `tables (List[Dict])`: A list of dictionaries, where each dictionary represents an extracted HTML table with keys like "headers", "rows", "caption", "summary". Default: `[]`.

    * 4.7. Class `Links(BaseModel)`
        * Purpose: A Pydantic model that acts as a container for lists of internal and external links.
        * Fields:
            * `internal (List[Link])`: A list of `Link` objects considered internal to the crawled site. Default: `[]`.
            * `external (List[Link])`: A list of `Link` objects pointing to external sites. Default: `[]`.

    * 4.8. Class `AsyncCrawlResponse(BaseModel)`
        * Purpose: A Pydantic model representing the raw response from a crawler strategy's `crawl` method. This data is then processed further to create a `CrawlResult`.
        * Fields:
            * `html (str)`: The raw HTML content of the page.
            * `response_headers (Dict[str, str])`: A dictionary of HTTP response headers.
            * `js_execution_result (Optional[Dict[str, Any]])`: The result from any JavaScript code executed on the page. Default: `None`.
            * `status_code (int)`: The HTTP status code of the response.
            * `screenshot (Optional[str])`: Base64 encoded screenshot data, if captured. Default: `None`.
            * `pdf_data (Optional[bytes])`: Raw PDF data, if captured. Default: `None`.
            * `mhtml_data (Optional[str])`: MHTML snapshot data, if captured. Default: `None`.
            * `downloaded_files (Optional[List[str]])`: A list of local file paths for any files downloaded during the crawl. Default: `None`.
            * `ssl_certificate (Optional[SSLCertificate])`: SSL certificate information for the site. Default: `None`.
            * `redirected_url (Optional[str])`: The original URL requested if the final URL is a result of redirection. Default: `None`.
            * `network_requests (Optional[List[Dict[str, Any]]])`: Captured network requests if enabled. Default: `None`.
            * `console_messages (Optional[List[Dict[str, Any]]])`: Captured console messages if enabled. Default: `None`.

    * 4.9. Class `TokenUsage(BaseModel)`
        * Purpose: A Pydantic model to track token usage statistics for interactions with Large Language Models.
        * Fields:
            * `completion_tokens (int)`: Number of tokens used for the LLM's completion/response. Default: `0`.
            * `prompt_tokens (int)`: Number of tokens used for the input prompt to the LLM. Default: `0`.
            * `total_tokens (int)`: Total number of tokens used (prompt + completion). Default: `0`.
            * `completion_tokens_details (Optional[dict])`: Provider-specific detailed breakdown of completion tokens. Default: `None`.
            * `prompt_tokens_details (Optional[dict])`: Provider-specific detailed breakdown of prompt tokens. Default: `None`.

    * 4.10. Class `SSLCertificate(dict)` (from `crawl4ai.ssl_certificate`)
        * Purpose: Represents an SSL certificate's information, behaving like a dictionary for direct JSON serialization and easy access to its fields.
        * Key Fields (accessed as dictionary keys):
            * `subject (dict)`: Dictionary of subject fields (e.g., `{"CN": "example.com", "O": "Example Inc."}`).
            * `issuer (dict)`: Dictionary of issuer fields.
            * `version (int)`: Certificate version number.
            * `serial_number (str)`: Certificate serial number (hexadecimal string).
            * `not_before (str)`: Validity start date and time (ASN.1/UTC format string, e.g., "YYYYMMDDHHMMSSZ").
            * `not_after (str)`: Validity end date and time (ASN.1/UTC format string).
            * `fingerprint (str)`: SHA-256 fingerprint of the certificate (lowercase hex string).
            * `signature_algorithm (str)`: The algorithm used to sign the certificate (e.g., "sha256WithRSAEncryption").
            * `raw_cert (str)`: Base64 encoded string of the raw DER-encoded certificate.
            * `extensions (List[dict])`: A list of dictionaries, each representing a certificate extension with "name" and "value" keys.
        * Static Methods:
            * `from_url(url: str, timeout: int = 10) -> Optional[SSLCertificate]`: Fetches the SSL certificate from the given URL and returns an `SSLCertificate` instance, or `None` on failure.
        * Instance Methods:
            * `to_json(filepath: Optional[str] = None) -> Optional[str]`: Exports the certificate information as a JSON string. If `filepath` is provided, writes to the file and returns `None`.
            * `to_pem(filepath: Optional[str] = None) -> Optional[str]`: Exports the certificate in PEM format as a string. If `filepath` is provided, writes to the file and returns `None`.
            * `to_der(filepath: Optional[str] = None) -> Optional[bytes]`: Exports the raw certificate in DER format as bytes. If `filepath` is provided, writes to the file and returns `None`.
        * Example:
            ```python
            # Assuming 'cert' is an SSLCertificate instance
            # print(cert["subject"]["CN"])
            # cert.to_pem("my_cert.pem")
            ```

    * 4.11. Class `DispatchResult(BaseModel)`
        * Purpose: Contains metadata about a task's execution when processed by a dispatcher (e.g., in `arun_many`).
        * Fields:
            * `task_id (str)`: A unique identifier for the dispatched task.
            * `memory_usage (float)`: Memory usage (in MB) recorded during the task's execution.
            * `peak_memory (float)`: Peak memory usage (in MB) recorded during the task's execution.
            * `start_time (Union[datetime, float])`: The start time of the task (can be a `datetime` object or a Unix timestamp float).
            * `end_time (Union[datetime, float])`: The end time of the task.
            * `error_message (str)`: Any error message if the task failed during dispatch or execution. Default: `""`.

    * 4.12. `CrawlResultContainer(Generic[CrawlResultT])`
        * Purpose: A generic container for `CrawlResult` objects, primarily used as the return type for `arun_many` when `stream=False`. It behaves like a list, allowing iteration, indexing, and length checking.
        * Methods:
            * `__iter__(self)`: Allows iteration over the contained `CrawlResult` objects.
            * `__getitem__(self, index)`: Allows accessing `CrawlResult` objects by index.
            * `__len__(self)`: Returns the number of `CrawlResult` objects contained.
            * `__repr__(self)`: Provides a string representation of the container.
        * Attribute:
            * `_results (List[CrawlResultT])`: The internal list holding the `CrawlResult` objects.

    * 4.13. `RunManyReturn` (Type Alias from `crawl4ai.models`)
        * Purpose: A type alias defining the possible return types for the `arun_many` method of `AsyncWebCrawler`.
        * Definition: `Union[CrawlResultContainer[CrawlResult], AsyncGenerator[CrawlResult, None]]`
            * This means `arun_many` will return a `CrawlResultContainer` (a list-like object of all `CrawlResult` instances) if `CrawlerRunConfig.stream` is `False` (the default).
            * It will return an `AsyncGenerator` yielding individual `CrawlResult` instances if `CrawlerRunConfig.stream` is `True`.

## 5. Core Crawler Strategies (from `crawl4ai.async_crawler_strategy`)

    * 5.1. Abstract Base Class `AsyncCrawlerStrategy(ABC)`
        * Purpose: Defines the common interface that all asynchronous crawler strategies must implement. This allows `AsyncWebCrawler` to use different fetching mechanisms (e.g., Playwright, HTTP requests) interchangeably.
        * Initialization (`__init__`):
            ```python
            def __init__(self, browser_config: BrowserConfig, logger: AsyncLoggerBase):
            ```
            * Parameters:
                * `browser_config (BrowserConfig)`: The browser configuration to be used by the strategy.
                * `logger (AsyncLoggerBase)`: The logger instance for logging strategy-specific events.
        * Key Abstract Methods (must be implemented by concrete subclasses):
            * `async crawl(self, url: str, config: CrawlerRunConfig) -> AsyncCrawlResponse`:
                * Purpose: Fetches the content from the given URL according to the `config`.
                * Returns: An `AsyncCrawlResponse` object containing the raw fetched data.
            * `async __aenter__(self)`:
                * Purpose: Asynchronous context manager entry, typically for initializing resources (e.g., launching a browser).
            * `async __aexit__(self, exc_type, exc_val, exc_tb)`:
                * Purpose: Asynchronous context manager exit, for cleaning up resources.
        * Key Concrete Methods (available to all strategies):
            * `set_custom_headers(self, headers: dict) -> None`:
                * Purpose: Sets custom HTTP headers to be used by the strategy for subsequent requests.
            * `update_user_agent(self, user_agent: str) -> None`:
                * Purpose: Updates the User-Agent string used by the strategy.
            * `set_hook(self, hook_name: str, callback: Callable) -> None`:
                * Purpose: Registers a callback function for a specific hook point in the crawling lifecycle.
            * `async_run_hook(self, hook_name: str, *args, **kwargs) -> Any`:
                * Purpose: Executes a registered hook with the given arguments.
            * `async_get_default_context(self) -> BrowserContext`:
                * Purpose: Retrieves the default browser context (Playwright specific, might raise `NotImplementedError` in non-Playwright strategies).
            * `async_create_new_page(self, context: BrowserContext) -> Page`:
                * Purpose: Creates a new page within a given browser context (Playwright specific).
            * `async_get_page(self, url: str, config: CrawlerRunConfig, session_id: Optional[str]) -> Tuple[Page, BrowserContext]`:
                * Purpose: Gets an existing page/context for a session or creates a new one (Playwright specific, managed by `BrowserManager`).
            * `async_close_page(self, page: Page, session_id: Optional[str]) -> None`:
                * Purpose: Closes a page, potentially keeping the associated context/session alive (Playwright specific).
            * `async_kill_session(self, session_id: str) -> None`:
                * Purpose: Kills (closes) a specific browser session, including its page and context (Playwright specific).

    * 5.2. Class `AsyncPlaywrightCrawlerStrategy(AsyncCrawlerStrategy)`
        * Purpose: The default crawler strategy, using Playwright to control a web browser for fetching and interacting with web pages. It supports complex JavaScript execution and provides hooks for various stages of the crawl.
        * Initialization (`__init__`):
            ```python
            def __init__(
                self,
                browser_config: Optional[BrowserConfig] = None,
                logger: Optional[AsyncLoggerBase] = None,
                browser_manager: Optional[BrowserManager] = None
            ):
            ```
            * Parameters:
                * `browser_config (Optional[BrowserConfig])`: Browser configuration. Defaults to a new `BrowserConfig()` if not provided.
                * `logger (Optional[AsyncLoggerBase])`: Logger instance. Defaults to a new `AsyncLogger()`.
                * `browser_manager (Optional[BrowserManager])`: An instance of `BrowserManager` to manage browser lifecycles and contexts. If `None`, a new `BrowserManager` is created internally.
        * Key Overridden/Implemented Methods:
            * `async crawl(self, url: str, config: CrawlerRunConfig) -> AsyncCrawlResponse`:
                * Purpose: Implements the crawling logic using Playwright. It navigates to the URL, executes JavaScript if specified, waits for conditions, captures screenshots/PDFs if requested, and returns the page content and other metadata.
            * `async aprocess_html(self, url: str, html: str, config: CrawlerRunConfig, **kwargs) -> CrawlResult`:
                * Purpose: (Note: While `AsyncWebCrawler` calls this, the default implementation is in `AsyncPlaywrightCrawlerStrategy` for convenience, acting as a bridge to the scraping strategy.) Processes the fetched HTML to produce a `CrawlResult`. This involves using the `scraping_strategy` from the `config` (defaults to `WebScrapingStrategy`) to clean HTML, extract media/links, and then uses the `markdown_generator` to produce Markdown.
        * Specific Public Methods:
            * `async_create_new_context(self, config: Optional[CrawlerRunConfig] = None) -> BrowserContext`:
                * Purpose: Creates a new Playwright `BrowserContext` based on the global `BrowserConfig` and optional overrides from `CrawlerRunConfig`.
            * `async_setup_context_default(self, context: BrowserContext, config: Optional[CrawlerRunConfig] = None) -> None`:
                * Purpose: Applies default settings to a `BrowserContext`, such as viewport size, user agent, custom headers, locale, timezone, and geolocation, based on `BrowserConfig` and `CrawlerRunConfig`.
            * `async_setup_context_hooks(self, context: BrowserContext, config: CrawlerRunConfig) -> None`:
                * Purpose: Sets up event listeners on the context for capturing network requests and console messages if `config.capture_network_requests` or `config.capture_console_messages` is `True`.
            * `async_handle_storage_state(self, context: BrowserContext, config: CrawlerRunConfig) -> None`:
                * Purpose: Loads cookies and localStorage from a `storage_state` file or dictionary (specified in `BrowserConfig` or `CrawlerRunConfig`) into the given `BrowserContext`.
        * Hooks (Callable via `set_hook(hook_name, callback)` and executed by `async_run_hook`):
            * `on_browser_created`: Called after the Playwright browser instance is launched or connected. Callback receives `(browser, **kwargs)`.
            * `on_page_context_created`: Called after a new Playwright `BrowserContext` and `Page` are created. Callback receives `(page, context, **kwargs)`.
            * `before_goto`: Called just before `page.goto(url)` is executed. Callback receives `(page, context, url, **kwargs)`.
            * `after_goto`: Called after `page.goto(url)` completes successfully. Callback receives `(page, context, url, response, **kwargs)`.
            * `on_user_agent_updated`: Called when the User-Agent string is updated for a context. Callback receives `(page, context, user_agent, **kwargs)`.
            * `on_execution_started`: Called when `js_code` execution begins on a page. Callback receives `(page, context, **kwargs)`.
            * `before_retrieve_html`: Called just before the final HTML content is retrieved from the page. Callback receives `(page, context, **kwargs)`.
            * `before_return_html`: Called just before the `AsyncCrawlResponse` is returned by the `crawl()` method of the strategy. Callback receives `(page, context, html_content, **kwargs)`.

    * 5.3. Class `AsyncHTTPCrawlerStrategy(AsyncCrawlerStrategy)`
        * Purpose: A lightweight crawler strategy that uses direct HTTP requests (via `httpx`) instead of a full browser. Suitable for static sites or when JavaScript execution is not needed.
        * Initialization (`__init__`):
            ```python
            def __init__(self, http_config: Optional[HTTPCrawlerConfig] = None, logger: Optional[AsyncLoggerBase] = None):
            ```
            * Parameters:
                * `http_config (Optional[HTTPCrawlerConfig])`: Configuration for HTTP requests (method, headers, data, etc.). Defaults to a new `HTTPCrawlerConfig()`.
                * `logger (Optional[AsyncLoggerBase])`: Logger instance. Defaults to a new `AsyncLogger()`.
        * Key Overridden/Implemented Methods:
            * `async crawl(self, url: str, http_config: Optional[HTTPCrawlerConfig] = None, **kwargs) -> AsyncCrawlResponse`:
                * Purpose: Fetches content from the URL using an HTTP GET or POST request via `httpx`. Does not execute JavaScript. Returns an `AsyncCrawlResponse` with HTML, status code, and headers. Screenshot, PDF, and MHTML capabilities are not available with this strategy.

## 6. Browser Management (from `crawl4ai.browser_manager`)

    * 6.1. Class `BrowserManager`
        * Purpose: Manages the lifecycle of Playwright browser instances and their contexts. It handles launching/connecting to browsers, creating new contexts with specific configurations, managing sessions for page reuse, and cleaning up resources.
        * Initialization (`__init__`):
            ```python
            def __init__(self, browser_config: BrowserConfig, logger: Optional[AsyncLoggerBase] = None):
            ```
            * Parameters:
                * `browser_config (BrowserConfig)`: The global browser configuration settings.
                * `logger (Optional[AsyncLoggerBase])`: Logger instance for browser management events.
        * Key Methods:
            * `async start() -> None`: Initializes the Playwright instance and launches or connects to the browser based on `browser_config` (e.g., launches a new browser instance or connects to an existing CDP endpoint via `ManagedBrowser`).
            * `async create_browser_context(self, crawlerRunConfig: Optional[CrawlerRunConfig] = None) -> playwright.async_api.BrowserContext`: Creates a new browser context. If `crawlerRunConfig` is provided, its settings (e.g., locale, viewport, proxy) can override the global `BrowserConfig`.
            * `async setup_context(self, context: playwright.async_api.BrowserContext, crawlerRunConfig: Optional[CrawlerRunConfig] = None, is_default: bool = False) -> None`: Applies various settings to a given browser context, including headers, cookies, viewport, geolocation, permissions, and storage state, based on `BrowserConfig` and `CrawlerRunConfig`.
            * `async get_page(self, crawlerRunConfig: CrawlerRunConfig) -> Tuple[playwright.async_api.Page, playwright.async_api.BrowserContext]`: Retrieves an existing page and context for a given `session_id` (if present in `crawlerRunConfig` and the session is active) or creates a new page and context. Manages context reuse based on a signature derived from `CrawlerRunConfig` to ensure contexts with different core settings (like proxy, locale) are isolated.
            * `async kill_session(self, session_id: str) -> None`: Closes the page and browser context associated with the given `session_id`, effectively ending that session.
            * `async close() -> None`: Closes all managed browser contexts and the main browser instance.

    * 6.2. Class `ManagedBrowser`
        * Purpose: Manages the lifecycle of a single, potentially persistent, browser process. It's used when `BrowserConfig.use_managed_browser` is `True` or `BrowserConfig.use_persistent_context` is `True`. It handles launching the browser with a specific user data directory and connecting via CDP.
        * Initialization (`__init__`):
            ```python
            def __init__(
                self,
                browser_type: str = "chromium",
                user_data_dir: Optional[str] = None,
                headless: bool = False,
                logger=None,
                host: str = "localhost",
                debugging_port: int = 9222,
                cdp_url: Optional[str] = None, # Added as per code_analysis
                browser_config: Optional[BrowserConfig] = None # Added as per code_analysis
            ):
            ```
            * Parameters:
                * `browser_type (str)`: "chromium", "firefox", or "webkit". Default: "chromium".
                * `user_data_dir (Optional[str])`: Path to the user data directory for the browser profile. If `None`, a temporary directory might be created.
                * `headless (bool)`: Whether to launch the browser in headless mode. Default: `False` (typically for managed/persistent scenarios).
                * `logger`: Logger instance.
                * `host (str)`: Host for the debugging port. Default: "localhost".
                * `debugging_port (int)`: Port for the Chrome DevTools Protocol. Default: `9222`.
                * `cdp_url (Optional[str])`: If provided, attempts to connect to an existing browser at this CDP URL instead of launching a new one.
                * `browser_config (Optional[BrowserConfig])`: The `BrowserConfig` object providing overall browser settings.
        * Key Methods:
            * `async start() -> str`: Starts the browser process (if not connecting to an existing `cdp_url`). If a new browser is launched, it uses the specified `user_data_dir` and `debugging_port`.
            * Returns: The CDP endpoint URL (e.g., "http://localhost:9222").
            * `async cleanup() -> None`: Terminates the browser process (if launched by this instance) and removes any temporary user data directory created by it.
        * Static Methods:
            * `async create_profile(cls, browser_config: Optional[BrowserConfig] = None, profile_name: Optional[str] = None, logger=None) -> str`:
                * Purpose: Launches a browser instance with a new or existing user profile, allowing interactive setup (e.g., manual login, cookie acceptance). The browser remains open until the user closes it.
                * Parameters:
                    * `browser_config (Optional[BrowserConfig])`: Optional browser configuration to use.
                    * `profile_name (Optional[str])`: Name for the profile. If `None`, a default name is used.
                    * `logger`: Logger instance.
                * Returns: The path to the created/used user data directory, which can then be passed to `BrowserConfig.user_data_dir`.
            * `list_profiles(cls) -> List[str]`:
                * Purpose: Lists the names of all browser profiles stored in the default Crawl4AI profiles directory (`~/.crawl4ai/profiles`).
                * Returns: A list of profile name strings.
            * `delete_profile(cls, profile_name_or_path: str) -> bool`:
                * Purpose: Deletes a browser profile either by its name (if in the default directory) or by its full path.
                * Returns: `True` if deletion was successful, `False` otherwise.

    * 6.3. Function `clone_runtime_state(src: BrowserContext, dst: BrowserContext, crawlerRunConfig: Optional[CrawlerRunConfig] = None, browserConfig: Optional[BrowserConfig] = None) -> None`
        * Purpose: Asynchronously copies runtime state (cookies, localStorage, session storage) from a source `BrowserContext` to a destination `BrowserContext`. Can also apply headers and geolocation from `CrawlerRunConfig` or `BrowserConfig` to the destination context.
        * Parameters:
            * `src (BrowserContext)`: The source browser context.
            * `dst (BrowserContext)`: The destination browser context.
            * `crawlerRunConfig (Optional[CrawlerRunConfig])`: Optional run configuration to apply to `dst`.
            * `browserConfig (Optional[BrowserConfig])`: Optional browser configuration to apply to `dst`.

## 7. Proxy Rotation Strategies (from `crawl4ai.proxy_strategy`)

    * 7.1. Abstract Base Class `ProxyRotationStrategy(ABC)`
        * Purpose: Defines the interface for strategies that provide a sequence of proxy configurations, enabling proxy rotation.
        * Abstract Methods:
            * `async get_next_proxy(self) -> Optional[ProxyConfig]`:
                * Purpose: Asynchronously retrieves the next `ProxyConfig` from the strategy.
                * Returns: A `ProxyConfig` object or `None` if no more proxies are available or an error occurs.
            * `add_proxies(self, proxies: List[ProxyConfig]) -> None`:
                * Purpose: Adds a list of `ProxyConfig` objects to the strategy's pool of proxies.

    * 7.2. Class `RoundRobinProxyStrategy(ProxyRotationStrategy)`
        * Purpose: A simple proxy rotation strategy that cycles through a list of provided proxies in a round-robin fashion.
        * Initialization (`__init__`):
            ```python
            def __init__(self, proxies: Optional[List[ProxyConfig]] = None):
            ```
            * Parameters:
                * `proxies (Optional[List[ProxyConfig]])`: An initial list of `ProxyConfig` objects. If `None`, the list is empty and proxies must be added via `add_proxies`.
        * Methods:
            * `add_proxies(self, proxies: List[ProxyConfig]) -> None`: Adds new `ProxyConfig` objects to the internal list of proxies and reinitializes the cycle.
            * `async get_next_proxy(self) -> Optional[ProxyConfig]`: Returns the next `ProxyConfig` from the list, cycling back to the beginning when the end is reached. Returns `None` if the list is empty.

## 8. Logging (from `crawl4ai.async_logger`)

    * 8.1. Abstract Base Class `AsyncLoggerBase(ABC)`
        * Purpose: Defines the basic interface for an asynchronous logger. Concrete implementations should provide methods for logging messages at different levels.
    * 8.2. Class `AsyncLogger(AsyncLoggerBase)`
        * Purpose: The default asynchronous logger for `crawl4ai`. It provides structured logging to both the console and optionally to a file, with customizable icons, colors, and verbosity levels.
        * Initialization (`__init__`):
            ```python
            def __init__(
                self,
                log_file: Optional[str] = None,
                verbose: bool = True,
                tag_width: int = 15, # outline had 10, code has 15
                icons: Optional[Dict[str, str]] = None,
                colors: Optional[Dict[LogLevel, LogColor]] = None, # Corrected type annotation
                log_level: LogLevel = LogLevel.INFO # Assuming LogLevel.INFO is a typical default
            ):
            ```
            * Parameters:
                * `log_file (Optional[str])`: Path to a file where logs should be written. If `None`, logs only to console.
                * `verbose (bool)`: If `True`, enables more detailed logging (DEBUG level). Default: `True`.
                * `tag_width (int)`: Width for the tag part of the log message. Default: `15`.
                * `icons (Optional[Dict[str, str]])`: Custom icons for different log tags.
                * `colors (Optional[Dict[LogLevel, LogColor]])`: Custom colors for different log levels.
                * `log_level (LogLevel)`: Minimum log level to output.
        * Key Methods (for logging):
            * `info(self, message: str, tag: Optional[str] = None, **params) -> None`: Logs an informational message.
            * `warning(self, message: str, tag: Optional[str] = None, **params) -> None`: Logs a warning message.
            * `error(self, message: str, tag: Optional[str] = None, **params) -> None`: Logs an error message.
            * `debug(self, message: str, tag: Optional[str] = None, **params) -> None`: Logs a debug message (only if `verbose=True` or `log_level` is DEBUG).
            * `url_status(self, url: str, success: bool, timing: float, tag: str = "FETCH", **params) -> None`: Logs the status of a URL fetch operation, including success/failure and timing.
            * `error_status(self, url: str, error: str, tag: str = "ERROR", **params) -> None`: Logs an error encountered for a specific URL.

## 9. Core Utility Functions (from `crawl4ai.async_configs`)
    * 9.1. `to_serializable_dict(obj: Any, ignore_default_value: bool = False) -> Dict`
        * Purpose: Recursively converts a Python object (often a Pydantic model or a dataclass instance used for configuration) into a dictionary that is safe for JSON serialization. It handles nested objects, enums, and basic types.
        * Parameters:
            * `obj (Any)`: The object to be serialized.
            * `ignore_default_value (bool)`: If `True`, fields whose current value is the same as their default value (if applicable, e.g., for Pydantic models) might be omitted from the resulting dictionary. Default: `False`.
        * Returns: `Dict` - A JSON-serializable dictionary representation of the object.
    * 9.2. `from_serializable_dict(data: Any) -> Any`
        * Purpose: Recursively reconstructs Python objects from a dictionary representation (typically one created by `to_serializable_dict`). It attempts to instantiate classes based on a "type" key in the dictionary if present.
        * Parameters:
            * `data (Any)`: The dictionary (or basic type) to be deserialized.
        * Returns: `Any` - The reconstructed Python object or the original data if no special deserialization rule applies.
    * 9.3. `is_empty_value(value: Any) -> bool`
        * Purpose: Checks if a given value is considered "empty" (e.g., `None`, an empty string, an empty list, an empty dictionary).
        * Returns: `bool` - `True` if the value is empty, `False` otherwise.

## 10. Enumerations (Key Enums used in Core)
    * 10.1. `CacheMode` (from `crawl4ai.cache_context`, defined in `crawl4ai.async_configs` as per provided code)
        * Purpose: Defines the caching behavior for crawl operations.
        * Members:
            * `ENABLE`: (Value: "enable") Normal caching behavior; read from cache if available, write to cache after fetching.
            * `DISABLE`: (Value: "disable") No caching at all; always fetch fresh content and do not write to cache.
            * `READ_ONLY`: (Value: "read_only") Only read from the cache; do not write new or updated content to the cache.
            * `WRITE_ONLY`: (Value: "write_only") Only write to the cache after fetching; do not read from the cache.
            * `BYPASS`: (Value: "bypass") Skip the cache entirely for this specific operation; fetch fresh content and do not write to cache. This is often the default for individual `CrawlerRunConfig` instances.
    * 10.2. `DisplayMode` (from `crawl4ai.models`, used by `CrawlerMonitor`)
        * Purpose: Defines the display mode for the `CrawlerMonitor`.
        * Members:
            * `DETAILED`: Shows detailed information for each task.
            * `AGGREGATED`: Shows summary statistics and overall progress.
    * 10.3. `CrawlStatus` (from `crawl4ai.models`, used by `CrawlStats`)
        * Purpose: Represents the status of a crawl task.
        * Members:
            * `QUEUED`: Task is waiting to be processed.
            * `IN_PROGRESS`: Task is currently being processed.
            * `COMPLETED`: Task finished successfully.
            * `FAILED`: Task failed.

## 11. Versioning
    * 11.1. Accessing Library Version:
        * The current version of the `crawl4ai` library can be accessed programmatically via the `__version__` attribute of the top-level `crawl4ai` package.
        * Example:
            ```python
            from crawl4ai import __version__ as crawl4ai_version
            print(f"Crawl4AI Version: {crawl4ai_version}")
            # Expected output based on provided code: Crawl4AI Version: 0.6.3
            ```

## 12. Basic Usage Examples

    * 12.1. Minimal Crawl:
        ```python
        import asyncio
        from crawl4ai import AsyncWebCrawler

        async def main():
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url="http://example.com")
                if result.success:
                    print("Markdown (first 300 chars):")
                    print(result.markdown.raw_markdown[:300]) # Accessing raw_markdown
                else:
                    print(f"Error: {result.error_message}")

        if __name__ == "__main__":
            asyncio.run(main())
        ```

    * 12.2. Crawl with Basic Configuration:
        ```python
        import asyncio
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

        async def main():
            browser_cfg = BrowserConfig(headless=True, browser_type="firefox")
            run_cfg = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                word_count_threshold=50
            )
            async with AsyncWebCrawler(config=browser_cfg) as crawler:
                result = await crawler.arun(url="http://example.com", config=run_cfg)
                if result.success:
                    print(f"Status Code: {result.status_code}")
                    print(f"Cleaned HTML length: {len(result.cleaned_html)}")
                else:
                    print(f"Error: {result.error_message}")
        
        if __name__ == "__main__":
            asyncio.run(main())
        ```

    * 12.3. Accessing Links and Images from Result:
        ```python
        import asyncio
        from crawl4ai import AsyncWebCrawler

        async def main():
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url="http://example.com")
                if result.success:
                    print(f"Found {len(result.links.internal)} internal links.")
                    if result.links.internal:
                        print(f"First internal link: {result.links.internal[0].href}")
                    
                    print(f"Found {len(result.media.images)} images.")
                    if result.media.images:
                        print(f"First image src: {result.media.images[0].src}")
                else:
                    print(f"Error: {result.error_message}")

        if __name__ == "__main__":
            asyncio.run(main())
        ```
```

---


# Configuration Objects - Memory
Source: crawl4ai_config_objects_memory_content.llm.md

# Detailed Outline for crawl4ai - config_objects Component

**Target Document Type:** memory
**Target Output Filename Suggestion:** `llm_memory_config_objects.md`
**Library Version Context:** 0.6.3
**Outline Generation Date:** 2024-05-24
---

## 1. Introduction to Configuration Objects in Crawl4ai

*   **1.1. Purpose of Configuration Objects**
    *   Explanation: Configuration objects in `crawl4ai` serve to centralize and manage settings for various components and behaviors of the library. This includes browser setup, individual crawl run parameters, LLM provider interactions, proxy settings, and more.
    *   Benefit: This approach enhances code readability by grouping related settings, improves maintainability by providing a clear structure for configurations, and offers ease of customization for users to tailor the library's behavior to their specific needs.
*   **1.2. General Principles and Usage**
    *   **1.2.1. Immutability/Cloning:**
        *   Concept: Most configuration objects are designed with a `clone()` method, allowing users to create modified copies without altering the original configuration instance. This promotes safer state management, especially when reusing base configurations for multiple tasks.
        *   Method: `clone(**kwargs)` on most configuration objects.
    *   **1.2.2. Serialization and Deserialization:**
        *   Concept: `crawl4ai` configuration objects can be serialized to dictionary format (e.g., for saving to JSON) and deserialized back into their respective class instances.
        *   Methods:
            *   `dump() -> dict`: Serializes the object to a dictionary suitable for JSON, often using the internal `to_serializable_dict` helper.
            *   `load(data: dict) -> ConfigClass` (Static Method): Deserializes an object from a dictionary, often using the internal `from_serializable_dict` helper.
            *   `to_dict() -> dict`: Converts the object to a standard Python dictionary.
            *   `from_dict(data: dict) -> ConfigClass` (Static Method): Creates an instance from a standard Python dictionary.
        *   Helper Functions:
            *   `crawl4ai.async_configs.to_serializable_dict(obj: Any, ignore_default_value: bool = False) -> Dict`: Recursively converts objects into a serializable dictionary format, handling complex types like enums and nested objects.
            *   `crawl4ai.async_configs.from_serializable_dict(data: Any) -> Any`: Reconstructs Python objects from the serializable dictionary format.
*   **1.3. Scope of this Document**
    *   Statement: This document provides a factual API reference for the primary configuration objects within the `crawl4ai` library, detailing their purpose, initialization parameters, attributes, and key methods.

## 2. Core Configuration Objects

### 2.1. `BrowserConfig`
Located in `crawl4ai.async_configs`.

*   **2.1.1. Purpose:**
    *   Description: The `BrowserConfig` class is used to configure the settings for a browser instance and its associated contexts when using browser-based crawler strategies like `AsyncPlaywrightCrawlerStrategy`. It centralizes all parameters that affect the creation and behavior of the browser.
*   **2.1.2. Initialization (`__init__`)**
    *   Signature:
        ```python
        class BrowserConfig:
            def __init__(
                self,
                browser_type: str = "chromium",
                headless: bool = True,
                browser_mode: str = "dedicated",
                use_managed_browser: bool = False,
                cdp_url: Optional[str] = None,
                use_persistent_context: bool = False,
                user_data_dir: Optional[str] = None,
                chrome_channel: Optional[str] = "chromium", # Note: 'channel' is preferred
                channel: Optional[str] = "chromium",
                proxy: Optional[str] = None,
                proxy_config: Optional[Union[ProxyConfig, dict]] = None,
                viewport_width: int = 1080,
                viewport_height: int = 600,
                viewport: Optional[dict] = None,
                accept_downloads: bool = False,
                downloads_path: Optional[str] = None,
                storage_state: Optional[Union[str, dict]] = None,
                ignore_https_errors: bool = True,
                java_script_enabled: bool = True,
                sleep_on_close: bool = False,
                verbose: bool = True,
                cookies: Optional[List[dict]] = None,
                headers: Optional[dict] = None,
                user_agent: Optional[str] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/116.0.0.0 Safari/537.36",
                user_agent_mode: Optional[str] = "",
                user_agent_generator_config: Optional[dict] = None, # Default is {} in __init__
                text_mode: bool = False,
                light_mode: bool = False,
                extra_args: Optional[List[str]] = None,
                debugging_port: int = 9222,
                host: str = "localhost"
            ): ...
        ```
    *   Parameters:
        *   `browser_type (str, default: "chromium")`: Specifies the browser engine to use. Supported values: `"chromium"`, `"firefox"`, `"webkit"`.
        *   `headless (bool, default: True)`: If `True`, runs the browser without a visible GUI. Set to `False` for debugging or visual interaction.
        *   `browser_mode (str, default: "dedicated")`: Defines how the browser is initialized. Options: `"builtin"` (uses built-in CDP), `"dedicated"` (new instance each time), `"cdp"` (connects to an existing CDP endpoint specified by `cdp_url`), `"docker"` (runs browser in a Docker container).
        *   `use_managed_browser (bool, default: False)`: If `True`, launches the browser using a managed approach (e.g., via CDP or Docker), allowing for more advanced control. Automatically set to `True` if `browser_mode` is `"builtin"`, `"docker"`, or if `cdp_url` is provided, or if `use_persistent_context` is `True`.
        *   `cdp_url (Optional[str], default: None)`: The URL for the Chrome DevTools Protocol (CDP) endpoint. If not provided and `use_managed_browser` is active, it might be set by an internal browser manager.
        *   `use_persistent_context (bool, default: False)`: If `True`, uses a persistent browser context (profile), saving cookies, localStorage, etc., across sessions. Requires `user_data_dir`. Sets `use_managed_browser=True`.
        *   `user_data_dir (Optional[str], default: None)`: Path to a directory for storing user data for persistent sessions. If `None` and `use_persistent_context` is `True`, a temporary directory might be used.
        *   `chrome_channel (Optional[str], default: "chromium")`: Specifies the Chrome channel (e.g., "chrome", "msedge", "chromium-beta"). Only applicable if `browser_type` is "chromium".
        *   `channel (Optional[str], default: "chromium")`: Preferred alias for `chrome_channel`. Set to `""` for Firefox or WebKit.
        *   `proxy (Optional[str], default: None)`: A string representing the proxy server URL (e.g., "http://username:password@proxy.example.com:8080").
        *   `proxy_config (Optional[Union[ProxyConfig, dict]], default: None)`: A `ProxyConfig` object or a dictionary specifying detailed proxy settings. Overrides the `proxy` string if both are provided.
        *   `viewport_width (int, default: 1080)`: Default width of the browser viewport in pixels.
        *   `viewport_height (int, default: 600)`: Default height of the browser viewport in pixels.
        *   `viewport (Optional[dict], default: None)`: A dictionary specifying viewport dimensions, e.g., `{"width": 1920, "height": 1080}`. If set, overrides `viewport_width` and `viewport_height`.
        *   `accept_downloads (bool, default: False)`: If `True`, allows files to be downloaded by the browser.
        *   `downloads_path (Optional[str], default: None)`: Directory path where downloaded files will be stored. Required if `accept_downloads` is `True`.
        *   `storage_state (Optional[Union[str, dict]], default: None)`: Path to a JSON file or a dictionary containing the browser's storage state (cookies, localStorage, etc.) to load.
        *   `ignore_https_errors (bool, default: True)`: If `True`, HTTPS certificate errors will be ignored.
        *   `java_script_enabled (bool, default: True)`: If `True`, JavaScript execution is enabled on web pages.
        *   `sleep_on_close (bool, default: False)`: If `True`, introduces a small delay before the browser is closed.
        *   `verbose (bool, default: True)`: If `True`, enables verbose logging for browser operations.
        *   `cookies (Optional[List[dict]], default: None)`: A list of cookie dictionaries to be set in the browser context. Each dictionary should conform to Playwright's cookie format.
        *   `headers (Optional[dict], default: None)`: A dictionary of additional HTTP headers to be sent with every request made by the browser.
        *   `user_agent (Optional[str], default: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/116.0.0.0 Safari/537.36")`: The User-Agent string the browser will use.
        *   `user_agent_mode (Optional[str], default: "")`: Mode for generating the User-Agent string. If set (e.g., to "random"), `user_agent_generator_config` can be used.
        *   `user_agent_generator_config (Optional[dict], default: {})`: Configuration dictionary for the User-Agent generator if `user_agent_mode` is active.
        *   `text_mode (bool, default: False)`: If `True`, attempts to disable images and other rich content to potentially speed up loading for text-focused crawls.
        *   `light_mode (bool, default: False)`: If `True`, disables certain background browser features for potential performance gains.
        *   `extra_args (Optional[List[str]], default: None)`: A list of additional command-line arguments to pass to the browser executable upon launch.
        *   `debugging_port (int, default: 9222)`: The port to use for the browser's remote debugging protocol (CDP).
        *   `host (str, default: "localhost")`: The host on which the browser's remote debugging protocol will listen.
*   **2.1.3. Key Public Attributes/Properties:**
    *   All parameters listed in `__init__` are available as public attributes with the same names and types.
    *   `browser_hint (str)`: [Read-only] - A string representing client hints (Sec-CH-UA) generated based on the `user_agent` string. This is automatically set during initialization.
*   **2.1.4. Key Public Methods:**
    *   `from_kwargs(cls, kwargs: dict) -> BrowserConfig` (Static Method):
        *   Purpose: Creates a `BrowserConfig` instance from a dictionary of keyword arguments.
    *   `to_dict(self) -> dict`:
        *   Purpose: Converts the `BrowserConfig` instance into a dictionary representation.
    *   `clone(self, **kwargs) -> BrowserConfig`:
        *   Purpose: Creates a deep copy of the current `BrowserConfig` instance. Keyword arguments can be provided to override specific attributes in the new instance.
    *   `dump(self) -> dict`:
        *   Purpose: Serializes the `BrowserConfig` object into a dictionary format that is suitable for JSON storage or transmission, utilizing the `to_serializable_dict` helper.
    *   `load(cls, data: dict) -> BrowserConfig` (Static Method):
        *   Purpose: Deserializes a `BrowserConfig` object from a dictionary (typically one created by `dump()`), utilizing the `from_serializable_dict` helper.

### 2.2. `CrawlerRunConfig`
Located in `crawl4ai.async_configs`.

*   **2.2.1. Purpose:**
    *   Description: The `CrawlerRunConfig` class encapsulates all settings that control the behavior of a single crawl operation performed by `AsyncWebCrawler.arun()` or multiple operations within `AsyncWebCrawler.arun_many()`. This includes parameters for content processing, page interaction, caching, and media handling.
*   **2.2.2. Initialization (`__init__`)**
    *   Signature:
        ```python
        class CrawlerRunConfig:
            def __init__(
                self,
                url: Optional[str] = None,
                word_count_threshold: int = MIN_WORD_THRESHOLD,
                extraction_strategy: Optional[ExtractionStrategy] = None,
                chunking_strategy: Optional[ChunkingStrategy] = RegexChunking(),
                markdown_generator: Optional[MarkdownGenerationStrategy] = DefaultMarkdownGenerator(),
                only_text: bool = False,
                css_selector: Optional[str] = None,
                target_elements: Optional[List[str]] = None, # Default is [] in __init__
                excluded_tags: Optional[List[str]] = None, # Default is [] in __init__
                excluded_selector: Optional[str] = "", # Default is "" in __init__
                keep_data_attributes: bool = False,
                keep_attrs: Optional[List[str]] = None, # Default is [] in __init__
                remove_forms: bool = False,
                prettify: bool = False,
                parser_type: str = "lxml",
                scraping_strategy: Optional[ContentScrapingStrategy] = None, # Instantiated with WebScrapingStrategy() if None
                proxy_config: Optional[Union[ProxyConfig, dict]] = None,
                proxy_rotation_strategy: Optional[ProxyRotationStrategy] = None,
                locale: Optional[str] = None,
                timezone_id: Optional[str] = None,
                geolocation: Optional[GeolocationConfig] = None,
                fetch_ssl_certificate: bool = False,
                cache_mode: CacheMode = CacheMode.BYPASS,
                session_id: Optional[str] = None,
                shared_data: Optional[dict] = None,
                wait_until: str = "domcontentloaded",
                page_timeout: int = PAGE_TIMEOUT,
                wait_for: Optional[str] = None,
                wait_for_timeout: Optional[int] = None,
                wait_for_images: bool = False,
                delay_before_return_html: float = 0.1,
                mean_delay: float = 0.1,
                max_range: float = 0.3,
                semaphore_count: int = 5,
                js_code: Optional[Union[str, List[str]]] = None,
                js_only: bool = False,
                ignore_body_visibility: bool = True,
                scan_full_page: bool = False,
                scroll_delay: float = 0.2,
                process_iframes: bool = False,
                remove_overlay_elements: bool = False,
                simulate_user: bool = False,
                override_navigator: bool = False,
                magic: bool = False,
                adjust_viewport_to_content: bool = False,
                screenshot: bool = False,
                screenshot_wait_for: Optional[float] = None,
                screenshot_height_threshold: int = SCREENSHOT_HEIGHT_THRESHOLD,
                pdf: bool = False,
                capture_mhtml: bool = False,
                image_description_min_word_threshold: int = IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD,
                image_score_threshold: int = IMAGE_SCORE_THRESHOLD,
                table_score_threshold: int = 7,
                exclude_external_images: bool = False,
                exclude_all_images: bool = False,
                exclude_social_media_domains: Optional[List[str]] = None, # Uses SOCIAL_MEDIA_DOMAINS if None
                exclude_external_links: bool = False,
                exclude_social_media_links: bool = False,
                exclude_domains: Optional[List[str]] = None, # Default is [] in __init__
                exclude_internal_links: bool = False,
                verbose: bool = True,
                log_console: bool = False,
                capture_network_requests: bool = False,
                capture_console_messages: bool = False,
                method: str = "GET",
                stream: bool = False,
                check_robots_txt: bool = False,
                user_agent: Optional[str] = None,
                user_agent_mode: Optional[str] = None,
                user_agent_generator_config: Optional[dict] = None, # Default is {} in __init__
                deep_crawl_strategy: Optional[DeepCrawlStrategy] = None,
                experimental: Optional[Dict[str, Any]] = None # Default is {} in __init__
            ): ...
        ```
    *   Parameters:
        *   `url (Optional[str], default: None)`: The target URL for this specific crawl run.
        *   `word_count_threshold (int, default: MIN_WORD_THRESHOLD)`: Minimum word count for a text block to be considered significant during content processing.
        *   `extraction_strategy (Optional[ExtractionStrategy], default: None)`: Strategy for extracting structured data from the page. If `None`, `NoExtractionStrategy` is used.
        *   `chunking_strategy (Optional[ChunkingStrategy], default: RegexChunking())`: Strategy to split content into chunks before extraction.
        *   `markdown_generator (Optional[MarkdownGenerationStrategy], default: DefaultMarkdownGenerator())`: Strategy for converting HTML to Markdown.
        *   `only_text (bool, default: False)`: If `True`, attempts to extract only textual content, potentially ignoring structural elements beneficial for rich Markdown.
        *   `css_selector (Optional[str], default: None)`: A CSS selector defining the primary region of the page to focus on for content extraction. The raw HTML is reduced to this region.
        *   `target_elements (Optional[List[str]], default: [])`: A list of CSS selectors. If provided, only the content within these elements will be considered for Markdown generation and structured data extraction. Unlike `css_selector`, this does not reduce the raw HTML but scopes the processing.
        *   `excluded_tags (Optional[List[str]], default: [])`: A list of HTML tag names (e.g., "nav", "footer") to be removed from the HTML before processing.
        *   `excluded_selector (Optional[str], default: "")`: A CSS selector specifying elements to be removed from the HTML before processing.
        *   `keep_data_attributes (bool, default: False)`: If `True`, `data-*` attributes on HTML elements are preserved during cleaning.
        *   `keep_attrs (Optional[List[str]], default: [])`: A list of specific HTML attribute names to preserve during HTML cleaning.
        *   `remove_forms (bool, default: False)`: If `True`, all `<form>` elements are removed from the HTML.
        *   `prettify (bool, default: False)`: If `True`, the cleaned HTML output is "prettified" for better readability.
        *   `parser_type (str, default: "lxml")`: The HTML parser to be used by the scraping strategy (e.g., "lxml", "html.parser").
        *   `scraping_strategy (Optional[ContentScrapingStrategy], default: WebScrapingStrategy())`: The strategy for scraping content from the HTML.
        *   `proxy_config (Optional[Union[ProxyConfig, dict]], default: None)`: Proxy configuration for this specific run. Overrides any proxy settings in `BrowserConfig`.
        *   `proxy_rotation_strategy (Optional[ProxyRotationStrategy], default: None)`: Strategy to use for rotating proxies if multiple are available.
        *   `locale (Optional[str], default: None)`: Locale to set for the browser context (e.g., "en-US", "fr-FR"). Affects `Accept-Language` header and JavaScript `navigator.language`.
        *   `timezone_id (Optional[str], default: None)`: Timezone ID to set for the browser context (e.g., "America/New_York", "Europe/Paris"). Affects JavaScript `Date` objects.
        *   `geolocation (Optional[GeolocationConfig], default: None)`: A `GeolocationConfig` object or dictionary to set the browser's mock geolocation.
        *   `fetch_ssl_certificate (bool, default: False)`: If `True`, the SSL certificate information for the main URL will be fetched and included in the `CrawlResult`.
        *   `cache_mode (CacheMode, default: CacheMode.BYPASS)`: Defines caching behavior for this run. See `CacheMode` enum for options.
        *   `session_id (Optional[str], default: None)`: An identifier for a browser session. If provided, `crawl4ai` will attempt to reuse an existing page/context associated with this ID, or create a new one and associate it.
        *   `shared_data (Optional[dict], default: None)`: A dictionary for passing custom data between hooks during the crawl lifecycle.
        *   `wait_until (str, default: "domcontentloaded")`: Playwright's page navigation wait condition (e.g., "load", "domcontentloaded", "networkidle", "commit").
        *   `page_timeout (int, default: PAGE_TIMEOUT)`: Maximum time in milliseconds for page navigation and other page operations.
        *   `wait_for (Optional[str], default: None)`: A CSS selector or a JavaScript expression (prefixed with "js:"). The crawler will wait until this condition is met before proceeding.
        *   `wait_for_timeout (Optional[int], default: None)`: Specific timeout in milliseconds for the `wait_for` condition. If `None`, `page_timeout` is used.
        *   `wait_for_images (bool, default: False)`: If `True`, attempts to wait for all images on the page to finish loading.
        *   `delay_before_return_html (float, default: 0.1)`: Delay in seconds to wait just before the final HTML content is retrieved from the page.
        *   `mean_delay (float, default: 0.1)`: Used with `arun_many`. The mean base delay in seconds between processing URLs.
        *   `max_range (float, default: 0.3)`: Used with `arun_many`. The maximum additional random delay (added to `mean_delay`) between processing URLs.
        *   `semaphore_count (int, default: 5)`: Used with `arun_many` and semaphore-based dispatchers. The maximum number of concurrent crawl operations.
        *   `js_code (Optional[Union[str, List[str]]], default: None)`: A string or list of strings containing JavaScript code to be executed on the page after it loads.
        *   `js_only (bool, default: False)`: If `True`, indicates that this `arun` call is primarily for JavaScript execution on an already loaded page (within a session) and a full page navigation might not be needed.
        *   `ignore_body_visibility (bool, default: True)`: If `True`, proceeds with content extraction even if the `<body>` element is not deemed visible by Playwright.
        *   `scan_full_page (bool, default: False)`: If `True`, the crawler will attempt to scroll through the entire page to trigger lazy-loaded content.
        *   `scroll_delay (float, default: 0.2)`: Delay in seconds between each scroll step when `scan_full_page` is `True`.
        *   `process_iframes (bool, default: False)`: If `True`, attempts to extract and inline content from `<iframe>` elements.
        *   `remove_overlay_elements (bool, default: False)`: If `True`, attempts to identify and remove common overlay elements (popups, cookie banners) before content extraction.
        *   `simulate_user (bool, default: False)`: If `True`, enables heuristics to simulate user interactions (like mouse movements) to potentially bypass some anti-bot measures.
        *   `override_navigator (bool, default: False)`: If `True`, overrides certain JavaScript `navigator` properties to appear more like a standard browser.
        *   `magic (bool, default: False)`: If `True`, enables a combination of techniques (like `remove_overlay_elements`, `simulate_user`) to try and handle dynamic/obfuscated sites.
        *   `adjust_viewport_to_content (bool, default: False)`: If `True`, attempts to adjust the browser viewport size to match the dimensions of the page content.
        *   `screenshot (bool, default: False)`: If `True`, a screenshot of the page will be taken and included in `CrawlResult.screenshot`.
        *   `screenshot_wait_for (Optional[float], default: None)`: Additional delay in seconds to wait before taking the screenshot.
        *   `screenshot_height_threshold (int, default: SCREENSHOT_HEIGHT_THRESHOLD)`: If page height exceeds this, a full-page screenshot strategy might be different.
        *   `pdf (bool, default: False)`: If `True`, a PDF version of the page will be generated and included in `CrawlResult.pdf`.
        *   `capture_mhtml (bool, default: False)`: If `True`, an MHTML archive of the page will be captured and included in `CrawlResult.mhtml`.
        *   `image_description_min_word_threshold (int, default: IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD)`: Minimum word count for surrounding text to be considered as an image description.
        *   `image_score_threshold (int, default: IMAGE_SCORE_THRESHOLD)`: Heuristic score threshold for an image to be included in `CrawlResult.media`.
        *   `table_score_threshold (int, default: 7)`: Heuristic score threshold for an HTML table to be considered a data table and included in `CrawlResult.media`.
        *   `exclude_external_images (bool, default: False)`: If `True`, images hosted on different domains than the main page URL are excluded.
        *   `exclude_all_images (bool, default: False)`: If `True`, all images are excluded from `CrawlResult.media`.
        *   `exclude_social_media_domains (Optional[List[str]], default: SOCIAL_MEDIA_DOMAINS from config)`: List of social media domains whose links should be excluded.
        *   `exclude_external_links (bool, default: False)`: If `True`, all links pointing to external domains are excluded from `CrawlResult.links`.
        *   `exclude_social_media_links (bool, default: False)`: If `True`, links to domains in `exclude_social_media_domains` are excluded.
        *   `exclude_domains (Optional[List[str]], default: [])`: A list of specific domains whose links should be excluded.
        *   `exclude_internal_links (bool, default: False)`: If `True`, all links pointing to the same domain are excluded.
        *   `verbose (bool, default: True)`: Enables verbose logging for this specific crawl run. Overrides `BrowserConfig.verbose`.
        *   `log_console (bool, default: False)`: If `True`, browser console messages are captured (requires `capture_console_messages=True` to be effective).
        *   `capture_network_requests (bool, default: False)`: If `True`, captures details of network requests and responses made by the page.
        *   `capture_console_messages (bool, default: False)`: If `True`, captures messages logged to the browser's console.
        *   `method (str, default: "GET")`: HTTP method to use, primarily for `AsyncHTTPCrawlerStrategy`.
        *   `stream (bool, default: False)`: If `True` when using `arun_many`, results are yielded as an async generator instead of returned as a list at the end.
        *   `check_robots_txt (bool, default: False)`: If `True`, `robots.txt` rules for the domain will be checked and respected.
        *   `user_agent (Optional[str], default: None)`: User-Agent string for this specific run. Overrides `BrowserConfig.user_agent`.
        *   `user_agent_mode (Optional[str], default: None)`: User-Agent generation mode for this specific run.
        *   `user_agent_generator_config (Optional[dict], default: {})`: Configuration for User-Agent generator for this run.
        *   `deep_crawl_strategy (Optional[DeepCrawlStrategy], default: None)`: Strategy to use for deep crawling beyond the initial URL.
        *   `experimental (Optional[Dict[str, Any]], default: {})`: A dictionary for passing experimental or beta parameters.
*   **2.2.3. Key Public Attributes/Properties:**
    *   All parameters listed in `__init__` are available as public attributes with the same names and types.
*   **2.2.4. Deprecated Property Handling (`__getattr__`, `_UNWANTED_PROPS`)**
    *   Behavior: Attempting to access a deprecated property (e.g., `bypass_cache`, `disable_cache`, `no_cache_read`, `no_cache_write`) raises an `AttributeError`. The error message directs the user to use the `cache_mode` parameter with the appropriate `CacheMode` enum member instead.
    *   List of Deprecated Properties and their `CacheMode` Equivalents:
        *   `bypass_cache`: Use `cache_mode=CacheMode.BYPASS`.
        *   `disable_cache`: Use `cache_mode=CacheMode.DISABLE`.
        *   `no_cache_read`: Use `cache_mode=CacheMode.WRITE_ONLY`.
        *   `no_cache_write`: Use `cache_mode=CacheMode.READ_ONLY`.
*   **2.2.5. Key Public Methods:**
    *   `from_kwargs(cls, kwargs: dict) -> CrawlerRunConfig` (Static Method):
        *   Purpose: Creates a `CrawlerRunConfig` instance from a dictionary of keyword arguments.
    *   `dump(self) -> dict`:
        *   Purpose: Serializes the `CrawlerRunConfig` object to a dictionary suitable for JSON storage, handling complex nested objects using `to_serializable_dict`.
    *   `load(cls, data: dict) -> CrawlerRunConfig` (Static Method):
        *   Purpose: Deserializes a `CrawlerRunConfig` object from a dictionary (typically one created by `dump()`), using `from_serializable_dict`.
    *   `to_dict(self) -> dict`:
        *   Purpose: Converts the `CrawlerRunConfig` instance into a dictionary representation. Complex objects like strategies are typically represented by their class name or a simplified form.
    *   `clone(self, **kwargs) -> CrawlerRunConfig`:
        *   Purpose: Creates a deep copy of the current `CrawlerRunConfig` instance. Keyword arguments can be provided to override specific attributes in the new instance.

### 2.3. `LLMConfig`
Located in `crawl4ai.async_configs`.

*   **2.3.1. Purpose:**
    *   Description: The `LLMConfig` class provides configuration for interacting with Large Language Model (LLM) providers. It includes settings for the provider name, API token, base URL, and various model-specific parameters like temperature and max tokens.
*   **2.3.2. Initialization (`__init__`)**
    *   Signature:
        ```python
        class LLMConfig:
            def __init__(
                self,
                provider: str = DEFAULT_PROVIDER, # e.g., "openai/gpt-4o-mini"
                api_token: Optional[str] = None,
                base_url: Optional[str] = None,
                temperature: Optional[float] = None,
                max_tokens: Optional[int] = None,
                top_p: Optional[float] = None,
                frequency_penalty: Optional[float] = None,
                presence_penalty: Optional[float] = None,
                stop: Optional[List[str]] = None,
                n: Optional[int] = None,
            ): ...
        ```
    *   Parameters:
        *   `provider (str, default: DEFAULT_PROVIDER)`: The identifier for the LLM provider and model (e.g., "openai/gpt-4o-mini", "ollama/llama3.3", "gemini/gemini-1.5-pro").
        *   `api_token (Optional[str], default: None)`: The API token for authenticating with the LLM provider. If `None`, it attempts to load from environment variables based on the provider (e.g., `OPENAI_API_KEY` for OpenAI, `GEMINI_API_KEY` for Gemini). Can also be set as "env:YOUR_ENV_VAR_NAME".
        *   `base_url (Optional[str], default: None)`: A custom base URL for the LLM API endpoint, useful for self-hosted models or proxies.
        *   `temperature (Optional[float], default: None)`: Controls the randomness of the LLM's output. Higher values (e.g., 0.8) make output more random, lower values (e.g., 0.2) make it more deterministic.
        *   `max_tokens (Optional[int], default: None)`: The maximum number of tokens the LLM should generate in its response.
        *   `top_p (Optional[float], default: None)`: Nucleus sampling parameter. The model considers only tokens with cumulative probability mass up to `top_p`.
        *   `frequency_penalty (Optional[float], default: None)`: Penalizes new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
        *   `presence_penalty (Optional[float], default: None)`: Penalizes new tokens based on whether they have appeared in the text so far, increasing the model's likelihood to talk about new topics.
        *   `stop (Optional[List[str]], default: None)`: A list of sequences where the API will stop generating further tokens.
        *   `n (Optional[int], default: None)`: The number of completions to generate for each prompt.
*   **2.3.3. Key Public Attributes/Properties:**
    *   All parameters listed in `__init__` are available as public attributes with the same names and types.
*   **2.3.4. Key Public Methods:**
    *   `from_kwargs(cls, kwargs: dict) -> LLMConfig` (Static Method):
        *   Purpose: Creates an `LLMConfig` instance from a dictionary of keyword arguments.
    *   `to_dict(self) -> dict`:
        *   Purpose: Converts the `LLMConfig` instance into a dictionary representation.
    *   `clone(self, **kwargs) -> LLMConfig`:
        *   Purpose: Creates a deep copy of the current `LLMConfig` instance. Keyword arguments can be provided to override specific attributes in the new instance.

### 2.4. `GeolocationConfig`
Located in `crawl4ai.async_configs`.

*   **2.4.1. Purpose:**
    *   Description: The `GeolocationConfig` class stores settings for mocking the browser's geolocation, including latitude, longitude, and accuracy.
*   **2.4.2. Initialization (`__init__`)**
    *   Signature:
        ```python
        class GeolocationConfig:
            def __init__(
                self,
                latitude: float,
                longitude: float,
                accuracy: Optional[float] = 0.0
            ): ...
        ```
    *   Parameters:
        *   `latitude (float)`: The latitude coordinate (e.g., 37.7749 for San Francisco).
        *   `longitude (float)`: The longitude coordinate (e.g., -122.4194 for San Francisco).
        *   `accuracy (Optional[float], default: 0.0)`: The accuracy of the geolocation in meters.
*   **2.4.3. Key Public Attributes/Properties:**
    *   `latitude (float)`: Stores the latitude.
    *   `longitude (float)`: Stores the longitude.
    *   `accuracy (Optional[float])`: Stores the accuracy.
*   **2.4.4. Key Public Methods:**
    *   `from_dict(cls, geo_dict: dict) -> GeolocationConfig` (Static Method):
        *   Purpose: Creates a `GeolocationConfig` instance from a dictionary.
    *   `to_dict(self) -> dict`:
        *   Purpose: Converts the `GeolocationConfig` instance to a dictionary: `{"latitude": ..., "longitude": ..., "accuracy": ...}`.
    *   `clone(self, **kwargs) -> GeolocationConfig`:
        *   Purpose: Creates a copy of the `GeolocationConfig` instance, allowing for overriding specific attributes with `kwargs`.

### 2.5. `ProxyConfig`
Located in `crawl4ai.async_configs` (and `crawl4ai.proxy_strategy`).

*   **2.5.1. Purpose:**
    *   Description: The `ProxyConfig` class encapsulates the configuration for a single proxy server, including its address, authentication credentials (if any), and optionally its public IP address.
*   **2.5.2. Initialization (`__init__`)**
    *   Signature:
        ```python
        class ProxyConfig:
            def __init__(
                self,
                server: str,
                username: Optional[str] = None,
                password: Optional[str] = None,
                ip: Optional[str] = None,
            ): ...
        ```
    *   Parameters:
        *   `server (str)`: The proxy server URL, including protocol and port (e.g., "http://127.0.0.1:8080", "socks5://proxy.example.com:1080").
        *   `username (Optional[str], default: None)`: The username for proxy authentication, if required.
        *   `password (Optional[str], default: None)`: The password for proxy authentication, if required.
        *   `ip (Optional[str], default: None)`: The public IP address of the proxy server. If not provided, it will be automatically extracted from the `server` string if possible.
*   **2.5.3. Key Public Attributes/Properties:**
    *   `server (str)`: The proxy server URL.
    *   `username (Optional[str])`: The username for proxy authentication.
    *   `password (Optional[str])`: The password for proxy authentication.
    *   `ip (Optional[str])`: The public IP address of the proxy. This is either user-provided or automatically extracted from the `server` string during initialization via the internal `_extract_ip_from_server` method.
*   **2.5.4. Key Public Methods:**
    *   `_extract_ip_from_server(self) -> Optional[str]` (Internal method):
        *   Purpose: Extracts the IP address component from the `self.server` URL string.
    *   `from_string(cls, proxy_str: str) -> ProxyConfig` (Static Method):
        *   Purpose: Creates a `ProxyConfig` instance from a string.
        *   Formats:
            *   `'ip:port:username:password'`
            *   `'ip:port'` (no authentication)
    *   `from_dict(cls, proxy_dict: dict) -> ProxyConfig` (Static Method):
        *   Purpose: Creates a `ProxyConfig` instance from a dictionary with keys "server", "username", "password", and "ip".
    *   `from_env(cls, env_var: str = "PROXIES") -> List[ProxyConfig]` (Static Method):
        *   Purpose: Loads a list of `ProxyConfig` objects from a comma-separated environment variable. Each proxy string in the variable should conform to the format accepted by `from_string`.
    *   `to_dict(self) -> dict`:
        *   Purpose: Converts the `ProxyConfig` instance to a dictionary: `{"server": ..., "username": ..., "password": ..., "ip": ...}`.
    *   `clone(self, **kwargs) -> ProxyConfig`:
        *   Purpose: Creates a copy of the `ProxyConfig` instance, allowing for overriding specific attributes with `kwargs`.

### 2.6. `HTTPCrawlerConfig`
Located in `crawl4ai.async_configs`.

*   **2.6.1. Purpose:**
    *   Description: The `HTTPCrawlerConfig` class holds configuration settings specific to direct HTTP-based crawling strategies (e.g., `AsyncHTTPCrawlerStrategy`), which do not use a full browser environment.
*   **2.6.2. Initialization (`__init__`)**
    *   Signature:
        ```python
        class HTTPCrawlerConfig:
            def __init__(
                self,
                method: str = "GET",
                headers: Optional[Dict[str, str]] = None,
                data: Optional[Dict[str, Any]] = None,
                json: Optional[Dict[str, Any]] = None,
                follow_redirects: bool = True,
                verify_ssl: bool = True,
            ): ...
        ```
    *   Parameters:
        *   `method (str, default: "GET")`: The HTTP method to use for the request (e.g., "GET", "POST", "PUT").
        *   `headers (Optional[Dict[str, str]], default: None)`: A dictionary of custom HTTP headers to send with the request.
        *   `data (Optional[Dict[str, Any]], default: None)`: Data to be sent in the body of the request, typically for "POST" or "PUT" requests (e.g., form data).
        *   `json (Optional[Dict[str, Any]], default: None)`: JSON data to be sent in the body of the request. If provided, the `Content-Type` header is typically set to `application/json`.
        *   `follow_redirects (bool, default: True)`: If `True`, the crawler will automatically follow HTTP redirects.
        *   `verify_ssl (bool, default: True)`: If `True`, SSL certificates will be verified. Set to `False` to ignore SSL errors (use with caution).
*   **2.6.3. Key Public Attributes/Properties:**
    *   All parameters listed in `__init__` are available as public attributes with the same names and types.
*   **2.6.4. Key Public Methods:**
    *   `from_kwargs(cls, kwargs: dict) -> HTTPCrawlerConfig` (Static Method):
        *   Purpose: Creates an `HTTPCrawlerConfig` instance from a dictionary of keyword arguments.
    *   `to_dict(self) -> dict`:
        *   Purpose: Converts the `HTTPCrawlerConfig` instance into a dictionary representation.
    *   `clone(self, **kwargs) -> HTTPCrawlerConfig`:
        *   Purpose: Creates a deep copy of the current `HTTPCrawlerConfig` instance. Keyword arguments can be provided to override specific attributes in the new instance.
    *   `dump(self) -> dict`:
        *   Purpose: Serializes the `HTTPCrawlerConfig` object to a dictionary.
    *   `load(cls, data: dict) -> HTTPCrawlerConfig` (Static Method):
        *   Purpose: Deserializes an `HTTPCrawlerConfig` object from a dictionary.

## 3. Enumerations and Helper Constants

### 3.1. `CacheMode` (Enum)
Located in `crawl4ai.cache_context`.

*   **3.1.1. Purpose:**
    *   Description: The `CacheMode` enumeration defines the different caching behaviors that can be applied to a crawl operation. It is used in `CrawlerRunConfig` to control how results are read from and written to the cache.
*   **3.1.2. Enum Members:**
    *   `ENABLE (str)`: Value: "ENABLE". Description: Enables normal caching behavior. The crawler will attempt to read from the cache first, and if a result is not found or is stale, it will perform the crawl and write the new result to the cache.
    *   `DISABLE (str)`: Value: "DISABLE". Description: Disables all caching. The crawler will not read from or write to the cache. Every request will be a fresh crawl.
    *   `READ_ONLY (str)`: Value: "READ_ONLY". Description: The crawler will only attempt to read from the cache. If a result is found, it will be used. If not, the crawl will not proceed further for that URL, and no new data will be written to the cache.
    *   `WRITE_ONLY (str)`: Value: "WRITE_ONLY". Description: The crawler will not attempt to read from the cache. It will always perform a fresh crawl and then write the result to the cache.
    *   `BYPASS (str)`: Value: "BYPASS". Description: The crawler will skip reading from the cache for this specific operation and will perform a fresh crawl. The result of this crawl *will* be written to the cache. This is the default `cache_mode` for `CrawlerRunConfig`.
*   **3.1.3. Usage:**
    *   Example:
        ```python
        from crawl4ai import CrawlerRunConfig, CacheMode
        config = CrawlerRunConfig(cache_mode=CacheMode.ENABLE) # Use cache fully
        config_bypass = CrawlerRunConfig(cache_mode=CacheMode.BYPASS) # Force fresh crawl, then cache
        ```

## 4. Serialization Helper Functions
Located in `crawl4ai.async_configs`.

### 4.1. `to_serializable_dict(obj: Any, ignore_default_value: bool = False) -> Dict`

*   **4.1.1. Purpose:**
    *   Description: This utility function recursively converts various Python objects, including `crawl4ai` configuration objects, into a dictionary format that is suitable for JSON serialization. It uses a `{ "type": "ClassName", "params": { ... } }` structure for custom class instances to enable proper deserialization later.
*   **4.1.2. Parameters:**
    *   `obj (Any)`: The Python object to be serialized.
    *   `ignore_default_value (bool, default: False)`: If `True`, when serializing class instances, parameters whose current values match their `__init__` default values might be excluded from the "params" dictionary. (Note: The exact behavior depends on the availability of default values in the class signature and handling of empty/None values).
*   **4.1.3. Returns:**
    *   `Dict`: A dictionary representation of the input object, structured for easy serialization (e.g., to JSON) and later deserialization by `from_serializable_dict`.
*   **4.1.4. Key Behaviors:**
    *   **Basic Types:** `str`, `int`, `float`, `bool`, `None` are returned as is.
    *   **Enums:** Serialized as `{"type": "EnumClassName", "params": enum_member.value}`.
    *   **Datetime Objects:** Serialized to their ISO 8601 string representation.
    *   **Lists, Tuples, Sets, Frozensets:** Serialized by recursively calling `to_serializable_dict` on each of their elements, returning a list.
    *   **Plain Dictionaries:** Serialized as `{"type": "dict", "value": {key: serialized_value, ...}}`.
    *   **Class Instances (e.g., Config Objects):**
        *   The object's class name is stored in the "type" field.
        *   Parameters from the `__init__` signature and attributes from `__slots__` (if defined) are collected.
        *   Their current values are recursively serialized and stored in the "params" dictionary.
        *   The structure is `{"type": "ClassName", "params": {"param_name": serialized_param_value, ...}}`.

### 4.2. `from_serializable_dict(data: Any) -> Any`

*   **4.2.1. Purpose:**
    *   Description: This utility function reconstructs Python objects, including `crawl4ai` configuration objects, from the serializable dictionary format previously created by `to_serializable_dict`.
*   **4.2.2. Parameters:**
    *   `data (Any)`: The dictionary (or basic data type) to be deserialized. This is typically the output of `to_serializable_dict` after being, for example, loaded from a JSON string.
*   **4.2.3. Returns:**
    *   `Any`: The reconstructed Python object (e.g., an instance of `BrowserConfig`, `LLMConfig`, a list, a plain dictionary, etc.).
*   **4.2.4. Key Behaviors:**
    *   **Basic Types:** `str`, `int`, `float`, `bool`, `None` are returned as is.
    *   **Typed Dictionaries (from `to_serializable_dict`):**
        *   If `data` is a dictionary and contains a "type" key:
            *   If `data["type"] == "dict"`, it reconstructs a plain Python dictionary from `data["value"]` by recursively deserializing its items.
            *   Otherwise, it attempts to locate the class specified by `data["type"]` within the `crawl4ai` module.
                *   If the class is an `Enum`, it instantiates the enum member using `data["params"]` (the enum value).
                *   If it's a regular class, it recursively deserializes the items in `data["params"]` and uses them as keyword arguments (`**kwargs`) to instantiate the class.
    *   **Lists:** If `data` is a list, it reconstructs a list by recursively calling `from_serializable_dict` on each of its elements.
    *   **Legacy Dictionaries:** If `data` is a dictionary but does not conform to the "type" key structure (for backward compatibility), it attempts to deserialize its values.

## 5. Cross-References and Relationships

*   **5.1. `BrowserConfig` Usage:**
    *   Typically instantiated once and passed to the `AsyncWebCrawler` constructor via its `config` parameter.
    *   `browser_config = BrowserConfig(headless=False)`
    *   `crawler = AsyncWebCrawler(config=browser_config)`
    *   It defines the global browser settings that will be used for all subsequent crawl operations unless overridden by `CrawlerRunConfig` on a per-run basis.
*   **5.2. `CrawlerRunConfig` Usage:**
    *   Passed to the `arun()` or `arun_many()` methods of `AsyncWebCrawler`.
    *   `run_config = CrawlerRunConfig(screenshot=True, cache_mode=CacheMode.BYPASS)`
    *   `result = await crawler.arun(url="https://example.com", config=run_config)`
    *   Allows for fine-grained control over individual crawl requests, overriding global settings from `BrowserConfig` or `AsyncWebCrawler`'s defaults where applicable (e.g., `user_agent`, `proxy_config`, `cache_mode`).
*   **5.3. `LLMConfig` Usage:**
    *   Instantiated and passed to LLM-based extraction strategies (e.g., `LLMExtractionStrategy`) or content filters (`LLMContentFilter`) during their initialization.
    *   `llm_conf = LLMConfig(provider="openai/gpt-4o-mini", api_token="sk-...")`
    *   `extraction_strategy = LLMExtractionStrategy(llm_config=llm_conf, schema=my_schema)`
*   **5.4. `GeolocationConfig` and `ProxyConfig` Usage:**
    *   `GeolocationConfig` is typically instantiated and assigned to the `geolocation` parameter of `CrawlerRunConfig`.
        *   `geo_conf = GeolocationConfig(latitude=34.0522, longitude=-118.2437)`
        *   `run_config = CrawlerRunConfig(geolocation=geo_conf)`
    *   `ProxyConfig` can be assigned to the `proxy_config` parameter of `BrowserConfig` (for a global proxy applied to all contexts) or `CrawlerRunConfig` (for a proxy specific to a single crawl run).
        *   `proxy_conf = ProxyConfig(server="http://myproxy:8080")`
        *   `browser_config = BrowserConfig(proxy_config=proxy_conf)` (global)
        *   `run_config = CrawlerRunConfig(proxy_config=proxy_conf)` (per-run)
*   **5.5. `HTTPCrawlerConfig` Usage:**
    *   Used when the `crawler_strategy` for `AsyncWebCrawler` is set to `AsyncHTTPCrawlerStrategy` (for non-browser-based HTTP requests).
    *   `http_conf = HTTPCrawlerConfig(method="POST", json={"key": "value"})`
    *   `http_strategy = AsyncHTTPCrawlerStrategy(http_crawler_config=http_conf)`
    *   `crawler = AsyncWebCrawler(crawler_strategy=http_strategy)`
    *   Alternatively, parameters like `method`, `data`, `json` can be passed directly to `arun()` when using `AsyncHTTPCrawlerStrategy` if they are part of the `CrawlerRunConfig`.

---


# Deployment - Memory
Source: crawl4ai_deployment_memory_content.llm.md

```markdown
# Detailed Outline for crawl4ai - deployment Component

**Target Document Type:** memory
**Target Output Filename Suggestion:** `llm_memory_deployment.md`
**Library Version Context:** 0.6.0 (as per Dockerfile ARG `C4AI_VER` from provided `Dockerfile` content)
**Outline Generation Date:** 2025-05-24
---

## 1. Introduction to Deployment
    * 1.1. Purpose: This document provides a factual reference for installing the `crawl4ai` library and deploying its server component using Docker. It covers basic and advanced library installation, various Docker deployment methods, server configuration, and an overview of the API for interaction.
    * 1.2. Scope:
        * Installation of the `crawl4ai` Python library.
        * Setup and diagnostic commands for the library.
        * Deployment of the `crawl4ai` server using Docker, including pre-built images, Docker Compose, and manual builds.
        * Explanation of Dockerfile parameters and server configuration via `config.yml`.
        * Details of API interaction, including the Playground UI, Python SDK, and direct REST API calls.
        * Overview of additional server API endpoints and Model Context Protocol (MCP) support.
        * High-level understanding of the server's internal logic relevant to users.
        * The library's version numbering scheme.

## 2. Library Installation

    * 2.1. **Basic Library Installation**
        * 2.1.1. Standard Installation
            * Command: `pip install crawl4ai`
            * Purpose: Installs the core `crawl4ai` library and its essential dependencies for performing web crawling and scraping tasks. This provides the fundamental `AsyncWebCrawler` and related configuration objects.
        * 2.1.2. Post-Installation Setup
            * Command: `crawl4ai-setup`
            * Purpose:
                * Initializes the user's home directory structure for Crawl4ai (e.g., `~/.crawl4ai/cache`).
                * Installs or updates necessary Playwright browsers (Chromium is installed by default) required for browser-based crawling. The `crawl4ai-setup` script internally calls `playwright install --with-deps chromium`.
                * Performs OS-level checks for common missing libraries that Playwright might depend on, providing guidance if issues are found.
                * Creates a default `global.yml` configuration file if one doesn't exist.
        * 2.1.3. Diagnostic Check
            * Command: `crawl4ai-doctor`
            * Purpose:
                * Verifies Python version compatibility.
                * Confirms Playwright installation and browser integrity by attempting a simple crawl of `https://crawl4ai.com`.
                * Inspects essential environment variables and potential library conflicts that might affect Crawl4ai's operation.
                * Provides diagnostic messages indicating success or failure of these checks, with suggestions for resolving common issues.
        * 2.1.4. Verification Process
            * Purpose: To confirm that the basic installation and setup were successful and Crawl4ai can perform a simple crawl.
            * Script Example (as inferred from `crawl4ai-doctor` logic and typical usage):
                ```python
                import asyncio
                from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

                async def main():
                    browser_config = BrowserConfig(
                        headless=True,
                        browser_type="chromium",
                        ignore_https_errors=True,
                        light_mode=True,
                        viewport_width=1280,
                        viewport_height=720,
                    )
                    run_config = CrawlerRunConfig(
                        cache_mode=CacheMode.BYPASS,
                        screenshot=True,
                    )
                    async with AsyncWebCrawler(config=browser_config) as crawler:
                        print("Testing crawling capabilities...")
                        result = await crawler.arun(url="https://crawl4ai.com", config=run_config)
                        if result and result.markdown:
                            print("✅ Crawling test passed!")
                            return True
                        else:
                            print("❌ Test failed: Failed to get content")
                            return False

                if __name__ == "__main__":
                    asyncio.run(main())
                ```
            * Expected Outcome: The script should print "✅ Crawling test passed!" and successfully output Markdown content from the crawled page.

    * 2.2. **Advanced Library Installation (Optional Features)**
        * 2.2.1. Installation of Optional Extras
            * Purpose: To install additional dependencies required for specific advanced features of Crawl4ai, such as those involving machine learning models.
            * Options (as defined in `pyproject.toml`):
                * `pip install crawl4ai[pdf]`:
                    * Purpose: Installs `PyPDF2` for PDF processing capabilities.
                * `pip install crawl4ai[torch]`:
                    * Purpose: Installs `torch`, `nltk`, and `scikit-learn`. Enables features relying on PyTorch models, such as some advanced text clustering or semantic analysis within extraction strategies.
                * `pip install crawl4ai[transformer]`:
                    * Purpose: Installs `transformers` and `tokenizers`. Enables the use of Hugging Face Transformers models for tasks like summarization, question answering, or other advanced NLP features within Crawl4ai.
                * `pip install crawl4ai[cosine]`:
                    * Purpose: Installs `torch`, `transformers`, and `nltk`. Specifically for features utilizing cosine similarity with embeddings (implies model usage).
                * `pip install crawl4ai[sync]`:
                    * Purpose: Installs `selenium` for synchronous crawling capabilities (less common, as Crawl4ai primarily focuses on async).
                * `pip install crawl4ai[all]`:
                    * Purpose: Installs all optional dependencies listed above (`PyPDF2`, `torch`, `nltk`, `scikit-learn`, `transformers`, `tokenizers`, `selenium`), providing the complete suite of Crawl4ai capabilities.
        * 2.2.2. Model Pre-fetching
            * Command: `crawl4ai-download-models` (maps to `crawl4ai.model_loader:main`)
            * Purpose: Downloads and caches machine learning models (e.g., specific sentence transformers or classification models from Hugging Face) that are used by certain optional features, particularly those installed via `crawl4ai[transformer]` or `crawl4ai[cosine]`. This avoids runtime downloads and ensures models are available offline.

## 3. Docker Deployment (Server Mode)

    * 3.1. **Prerequisites**
        * 3.1.1. Docker: A working Docker installation. (Link: `https://docs.docker.com/get-docker/`)
        * 3.1.2. Git: Required for cloning the `crawl4ai` repository if building locally or using Docker Compose from the repository. (Link: `https://git-scm.com/book/en/v2/Getting-Started-Installing-Git`)
        * 3.1.3. RAM Requirements:
            * Minimum: 2GB for the basic server without intensive LLM tasks. The `Dockerfile` HEALTCHECK indicates a warning if less than 2GB RAM is available.
            * Recommended for LLM support: 4GB+ (as specified in `docker-compose.yml` limits).
            * Shared Memory (`/dev/shm`): Recommended size is 1GB (`--shm-size=1g`) for optimal Chromium browser performance, as specified in `docker-compose.yml` and run commands.
    * 3.2. **Installation Options**
        * 3.2.1. **Using Pre-built Images from Docker Hub**
            * 3.2.1.1. Image Source: `unclecode/crawl4ai:<tag>`
                * Explanation of `<tag>`:
                    * `latest`: Points to the most recent stable release of Crawl4ai.
                    * Specific version tags (e.g., `0.6.0`, `0.5.1`): Correspond to specific library releases.
                    * Pre-release tags (e.g., `0.6.0-rc1`, `0.7.0-devN`): Development or release candidate versions for testing.
            * 3.2.1.2. Pulling the Image
                * Command: `docker pull unclecode/crawl4ai:<tag>` (e.g., `docker pull unclecode/crawl4ai:latest`)
            * 3.2.1.3. Environment Setup (`.llm.env`)
                * File Name: `.llm.env` (to be created by the user in the directory where `docker run` or `docker-compose` commands are executed).
                * Purpose: To securely provide API keys for various LLM providers used by Crawl4ai for features like LLM-based extraction or Q&A.
                * Example Content (based on `docker-compose.yml`):
                    ```env
                    OPENAI_API_KEY=your_openai_api_key
                    DEEPSEEK_API_KEY=your_deepseek_api_key
                    ANTHROPIC_API_KEY=your_anthropic_api_key
                    GROQ_API_KEY=your_groq_api_key
                    TOGETHER_API_KEY=your_together_api_key
                    MISTRAL_API_KEY=your_mistral_api_key
                    GEMINI_API_TOKEN=your_gemini_api_token
                    ```
                * Creation: Users should create this file and populate it with their API keys. An example (`.llm.env.example`) might be provided in the repository.
            * 3.2.1.4. Running the Container
                * Basic Run (without LLM support):
                    * Command: `docker run -d -p 11235:11235 --shm-size=1g --name crawl4ai-server unclecode/crawl4ai:<tag>`
                    * Port Mapping: `-p 11235:11235` maps port 11235 on the host to port 11235 in the container (default server port).
                    * Shared Memory: `--shm-size=1g` allocates 1GB of shared memory for the browser.
                * Run with LLM Support (mounting `.llm.env`):
                    * Command: `docker run -d -p 11235:11235 --env-file .llm.env --shm-size=1g --name crawl4ai-server unclecode/crawl4ai:<tag>`
            * 3.2.1.5. Stopping the Container
                * Command: `docker stop crawl4ai-server`
                * Command (to remove): `docker rm crawl4ai-server`
            * 3.2.1.6. Docker Hub Versioning:
                * Docker image tags on Docker Hub (e.g., `unclecode/crawl4ai:0.6.0`) directly correspond to `crawl4ai` library releases. The `latest` tag usually points to the most recent stable release. Pre-release tags include suffixes like `-devN`, `-aN`, `-bN`, or `-rcN`.

        * 3.2.2. **Using Docker Compose (`docker-compose.yml`)**
            * 3.2.2.1. Cloning the Repository
                * Command: `git clone https://github.com/unclecode/crawl4ai.git`
                * Command: `cd crawl4ai`
            * 3.2.2.2. Environment Setup (`.llm.env`)
                * File Name: `.llm.env` (should be created in the root of the cloned `crawl4ai` repository).
                * Purpose: Same as above, to provide LLM API keys.
            * 3.2.2.3. Running Pre-built Images
                * Command: `docker-compose up -d`
                * Behavior: Uses the image specified in `docker-compose.yml` (e.g., `${IMAGE:-unclecode/crawl4ai}:${TAG:-latest}`).
                * Overriding image tag: `TAG=0.6.0 docker-compose up -d` or `IMAGE=mycustom/crawl4ai TAG=mytag docker-compose up -d`.
            * 3.2.2.4. Building Locally with Docker Compose
                * Command: `docker-compose up -d --build`
                * Build Arguments (passed from environment variables to `docker-compose.yml` which then passes to `Dockerfile`):
                    * `INSTALL_TYPE`: (e.g., `default`, `torch`, `all`)
                        * Purpose: To include optional Python dependencies during the Docker image build process.
                        * Example: `INSTALL_TYPE=all docker-compose up -d --build`
                    * `ENABLE_GPU`: (e.g., `true`, `false`)
                        * Purpose: To include GPU support (e.g., CUDA toolkits) in the Docker image if the build hardware and target runtime support it.
                        * Example: `ENABLE_GPU=true docker-compose up -d --build`
            * 3.2.2.5. Stopping Docker Compose Services
                * Command: `docker-compose down`

        * 3.2.3. **Manual Local Build & Run**
            * 3.2.3.1. Cloning the Repository: (As above)
            * 3.2.3.2. Environment Setup (`.llm.env`): (As above)
            * 3.2.3.3. Building with `docker buildx`
                * Command Example:
                    ```bash
                    docker buildx build --platform linux/amd64,linux/arm64 \
                      --build-arg C4AI_VER=0.6.0 \
                      --build-arg INSTALL_TYPE=all \
                      --build-arg ENABLE_GPU=false \
                      --build-arg USE_LOCAL=true \
                      -t my-crawl4ai-image:custom .
                    ```
                * Purpose of `docker buildx`: A Docker CLI plugin that extends the `docker build` command with full support for BuildKit builder capabilities, including multi-architecture builds.
                * Explanation of `--platform`: Specifies the target platform(s) for the build (e.g., `linux/amd64`, `linux/arm64`).
                * Explanation of `--build-arg`: Passes build-time variables defined in the `Dockerfile` (see section 3.3).
            * 3.2.3.4. Running the Custom-Built Container
                * Basic Run: `docker run -d -p 11235:11235 --shm-size=1g --name my-crawl4ai-server my-crawl4ai-image:custom`
                * Run with LLM Support: `docker run -d -p 11235:11235 --env-file .llm.env --shm-size=1g --name my-crawl4ai-server my-crawl4ai-image:custom`
            * 3.2.3.5. Stopping the Container: (As above)

    * 3.3. **Dockerfile Parameters (`ARG` values)**
        * 3.3.1. `C4AI_VER`: (Default: `0.6.0`)
            * Role: Specifies the version of the `crawl4ai` library. Used for labeling the image and potentially for version-specific logic.
        * 3.3.2. `APP_HOME`: (Default: `/app`)
            * Role: Defines the working directory inside the Docker container where the application code and related files are stored and executed.
        * 3.3.3. `GITHUB_REPO`: (Default: `https://github.com/unclecode/crawl4ai.git`)
            * Role: The URL of the GitHub repository to clone if `USE_LOCAL` is set to `false`.
        * 3.3.4. `GITHUB_BRANCH`: (Default: `main`)
            * Role: The specific branch of the GitHub repository to clone if `USE_LOCAL` is `false`.
        * 3.3.5. `USE_LOCAL`: (Default: `true`)
            * Role: A boolean flag. If `true`, the `Dockerfile` installs `crawl4ai` from the local source code copied into `/tmp/project/` during the build context. If `false`, it clones the repository specified by `GITHUB_REPO` and `GITHUB_BRANCH`.
        * 3.3.6. `PYTHON_VERSION`: (Default: `3.12`)
            * Role: Specifies the Python version for the base image (e.g., `python:3.12-slim-bookworm`).
        * 3.3.7. `INSTALL_TYPE`: (Default: `default`)
            * Role: Controls which optional dependencies of `crawl4ai` are installed. Possible values: `default` (core), `pdf`, `torch`, `transformer`, `cosine`, `sync`, `all`.
        * 3.3.8. `ENABLE_GPU`: (Default: `false`)
            * Role: A boolean flag. If `true` and `TARGETARCH` is `amd64`, the `Dockerfile` attempts to install the NVIDIA CUDA toolkit for GPU acceleration.
        * 3.3.9. `TARGETARCH`:
            * Role: An automatic build argument provided by Docker, indicating the target architecture of the build (e.g., `amd64`, `arm64`). Used for conditional logic in the `Dockerfile`, such as installing platform-specific optimized libraries or CUDA for `amd64`.

    * 3.4. **Server Configuration (`config.yml`)**
        * 3.4.1. Location: The server loads its configuration from `/app/config.yml` inside the container by default. This path is relative to `APP_HOME`.
        * 3.4.2. Structure Overview (based on `deploy/docker/config.yml`):
            * `app`: General application settings.
                * `title (str)`: API title (e.g., "Crawl4AI API").
                * `version (str)`: API version (e.g., "1.0.0").
                * `host (str)`: Host address for the server to bind to (e.g., "0.0.0.0").
                * `port (int)`: Port for the server to listen on (e.g., 11234, though Docker usually maps to 11235).
                * `reload (bool)`: Enable/disable auto-reload for development (default: `false`).
                * `workers (int)`: Number of worker processes (default: 1).
                * `timeout_keep_alive (int)`: Keep-alive timeout in seconds (default: 300).
            * `llm`: Default LLM configuration.
                * `provider (str)`: Default LLM provider string (e.g., "openai/gpt-4o-mini").
                * `api_key_env (str)`: Environment variable name to read the API key from (e.g., "OPENAI_API_KEY").
                * `api_key (Optional[str])`: Directly pass API key (overrides `api_key_env`).
            * `redis`: Redis connection details.
                * `host (str)`: Redis host (e.g., "localhost").
                * `port (int)`: Redis port (e.g., 6379).
                * `db (int)`: Redis database number (e.g., 0).
                * `password (str)`: Redis password (default: "").
                * `ssl (bool)`: Enable SSL for Redis connection (default: `false`).
                * `ssl_cert_reqs (Optional[str])`: SSL certificate requirements (e.g., "none", "optional", "required").
                * `ssl_ca_certs (Optional[str])`: Path to CA certificate file.
                * `ssl_certfile (Optional[str])`: Path to SSL certificate file.
                * `ssl_keyfile (Optional[str])`: Path to SSL key file.
            * `rate_limiting`: Configuration for API rate limits.
                * `enabled (bool)`: Enable/disable rate limiting (default: `true`).
                * `default_limit (str)`: Default rate limit (e.g., "1000/minute").
                * `trusted_proxies (List[str])`: List of trusted proxy IP addresses.
                * `storage_uri (str)`: Storage URI for rate limit counters (e.g., "memory://", "redis://localhost:6379").
            * `security`: Security-related settings.
                * `enabled (bool)`: Master switch for security features (default: `false`).
                * `jwt_enabled (bool)`: Enable/disable JWT authentication (default: `false`).
                * `https_redirect (bool)`: Enable/disable HTTPS redirection (default: `false`).
                * `trusted_hosts (List[str])`: List of allowed host headers (e.g., `["*"]` or specific domains).
                * `headers (Dict[str, str])`: Default security headers to add to responses (e.g., `X-Content-Type-Options`, `Content-Security-Policy`).
            * `crawler`: Default crawler behavior.
                * `base_config (Dict[str, Any])`: Base parameters for `CrawlerRunConfig`.
                    * `simulate_user (bool)`: (default: `true`).
                * `memory_threshold_percent (float)`: Memory usage threshold for adaptive dispatcher (default: `95.0`).
                * `rate_limiter (Dict[str, Any])`: Configuration for the internal rate limiter for crawling.
                    * `enabled (bool)`: (default: `true`).
                    * `base_delay (List[float, float])`: Min/max delay range (e.g., `[1.0, 2.0]`).
                * `timeouts (Dict[str, float])`: Timeouts for different crawler operations.
                    * `stream_init (float)`: Timeout for stream initialization (default: `30.0`).
                    * `batch_process (float)`: Timeout for batch processing (default: `300.0`).
                * `pool (Dict[str, Any])`: Browser pool settings.
                    * `max_pages (int)`: Max concurrent browser pages (default: `40`).
                    * `idle_ttl_sec (int)`: Time-to-live for idle crawlers in seconds (default: `1800`).
                * `browser (Dict[str, Any])`: Default `BrowserConfig` parameters.
                    * `kwargs (Dict[str, Any])`: Keyword arguments for `BrowserConfig`.
                        * `headless (bool)`: (default: `true`).
                        * `text_mode (bool)`: (default: `true`).
                    * `extra_args (List[str])`: List of additional browser launch arguments (e.g., `"--no-sandbox"`).
            * `logging`: Logging configuration.
                * `level (str)`: Logging level (e.g., "INFO", "DEBUG").
                * `format (str)`: Log message format string.
            * `observability`: Observability settings.
                * `prometheus (Dict[str, Any])`: Prometheus metrics configuration.
                    * `enabled (bool)`: (default: `true`).
                    * `endpoint (str)`: Metrics endpoint path (e.g., "/metrics").
                * `health_check (Dict[str, str])`: Health check endpoint configuration.
                    * `endpoint (str)`: Health check endpoint path (e.g., "/health").
        * 3.4.3. JWT Authentication
            * Enabling: Set `security.enabled: true` and `security.jwt_enabled: true` in `config.yml`.
            * Secret Key: Configured via `security.jwt_secret_key`. This value can be overridden by the environment variable `JWT_SECRET_KEY`.
            * Algorithm: Configured via `security.jwt_algorithm` (default: `HS256`).
            * Token Expiry: Configured via `security.jwt_expire_minutes` (default: `30`).
            * Usage:
                * 1. Client obtains a token by sending a POST request to the `/token` endpoint with an email in the request body (e.g., `{"email": "user@example.com"}`). The email domain might be validated if configured.
                * 2. Client includes the received token in the `Authorization` header of subsequent requests to protected API endpoints: `Authorization: Bearer <your_jwt_token>`.
        * 3.4.4. Customizing `config.yml`
            * 3.4.4.1. Modifying Before Build:
                * Method: Edit the `deploy/docker/config.yml` file within the cloned `crawl4ai` repository before building the Docker image. This new configuration will be baked into the image.
            * 3.4.4.2. Runtime Mount:
                * Method: Mount a custom `config.yml` file from the host machine to `/app/config.yml` (or the path specified by `APP_HOME`) inside the running Docker container.
                * Example Command: `docker run -d -p 11235:11235 -v /path/on/host/my-config.yml:/app/config.yml --name crawl4ai-server unclecode/crawl4ai:latest`
        * 3.4.5. Key Configuration Recommendations
            * Security:
                * Enable JWT (`security.jwt_enabled: true`) if the server is exposed to untrusted networks.
                * Use a strong, unique `jwt_secret_key`.
                * Configure `security.trusted_hosts` to a specific list of allowed hostnames instead of `["*"]` for production.
                * If using a reverse proxy for SSL termination, ensure `https_redirect` is appropriately configured or disabled if the proxy handles it.
            * Resource Management:
                * Adjust `crawler.pool.max_pages` based on server resources to prevent overwhelming the system.
                * Tune `crawler.pool.idle_ttl_sec` to balance resource usage and responsiveness for pooled browser instances.
            * Monitoring:
                * Keep `observability.prometheus.enabled: true` for production monitoring via the `/metrics` endpoint.
                * Ensure the `/health` endpoint is accessible to health checking systems.
            * Performance:
                * Review and customize `crawler.browser.extra_args` for headless browser optimization (e.g., disabling GPU, sandbox if appropriate for your environment).
                * Set reasonable `crawler.timeouts` to prevent long-stalled crawls.

    * 3.5. **API Usage (Interacting with the Dockerized Server)**
        * 3.5.1. **Playground Interface**
            * Access URL: `http://localhost:11235/playground` (assuming default port mapping).
            * Purpose: An interactive web UI (Swagger UI/OpenAPI) allowing users to explore API endpoints, view schemas, construct requests, and test API calls directly from their browser.
        * 3.5.2. **Python SDK (`Crawl4aiDockerClient`)**
            * Class Name: `Crawl4aiDockerClient`
            * Location: (Typically imported as `from crawl4ai.docker_client import Crawl4aiDockerClient`) - Actual import might vary based on final library structure; refer to `docs/examples/docker_example.py` or `docs/examples/docker_python_sdk.py`.
            * Initialization:
                * Signature: `Crawl4aiDockerClient(base_url: str = "http://localhost:11235", api_token: Optional[str] = None, timeout: int = 300)`
                * Parameters:
                    * `base_url (str)`: The base URL of the Crawl4ai server. Default: `"http://localhost:11235"`.
                    * `api_token (Optional[str])`: JWT token for authentication if enabled on the server. Default: `None`.
                    * `timeout (int)`: Default timeout in seconds for HTTP requests to the server. Default: `300`.
            * Authentication (JWT):
                * Method: Pass the `api_token` during client initialization. The token can be obtained from the server's `/token` endpoint or other authentication mechanisms.
            * `crawl()` Method:
                * Signature (Conceptual, based on typical SDK patterns and server capabilities): `async def crawl(self, urls: Union[str, List[str]], browser_config: Optional[Dict] = None, crawler_config: Optional[Dict] = None, stream: bool = False) -> Union[List[Dict], AsyncGenerator[Dict, None]]`
                    *Note: SDK might take `BrowserConfig` and `CrawlerRunConfig` objects directly, which it then serializes.*
                * Key Parameters:
                    * `urls (Union[str, List[str]])`: A single URL string or a list of URL strings to crawl.
                    * `browser_config (Optional[Dict])`: A dictionary representing the `BrowserConfig` object, or a `BrowserConfig` instance itself.
                    * `crawler_config (Optional[Dict])`: A dictionary representing the `CrawlerRunConfig` object, or a `CrawlerRunConfig` instance itself.
                    * `stream (bool)`: If `True`, the method returns an async generator yielding individual `CrawlResult` dictionaries as they are processed by the server. If `False` (default), it returns a list containing all `CrawlResult` dictionaries after all URLs are processed.
                * Return Type: `List[Dict]` (for `stream=False`) or `AsyncGenerator[Dict, None]` (for `stream=True`), where each `Dict` represents a `CrawlResult`.
                * Streaming Behavior:
                    * `stream=True`: Allows processing of results incrementally, suitable for long crawl jobs or real-time data feeds.
                    * `stream=False`: Collects all results before returning, simpler for smaller batches.
            * `get_schema()` Method:
                * Signature: `async def get_schema(self) -> dict`
                * Return Type: `dict`.
                * Purpose: Fetches the JSON schemas for `BrowserConfig` and `CrawlerRunConfig` from the server's `/schema` endpoint. This helps in constructing valid configuration payloads.
        * 3.5.3. **JSON Request Schema for Configurations**
            * Structure: `{"type": "ClassName", "params": {...}}`
            * Purpose: This structure is used by the server (and expected by the Python SDK internally) to deserialize JSON payloads back into Pydantic configuration objects like `BrowserConfig`, `CrawlerRunConfig`, and their nested strategy objects (e.g., `LLMExtractionStrategy`, `PruningContentFilter`). The `type` field specifies the Python class name, and `params` holds the keyword arguments for its constructor.
            * Example (`BrowserConfig`):
                ```json
                {
                    "type": "BrowserConfig",
                    "params": {
                        "headless": true,
                        "browser_type": "chromium",
                        "viewport_width": 1920,
                        "viewport_height": 1080
                    }
                }
                ```
            * Example (`CrawlerRunConfig` with a nested `LLMExtractionStrategy`):
                ```json
                {
                    "type": "CrawlerRunConfig",
                    "params": {
                        "cache_mode": {"type": "CacheMode", "params": "BYPASS"},
                        "screenshot": false,
                        "extraction_strategy": {
                            "type": "LLMExtractionStrategy",
                            "params": {
                                "llm_config": {
                                    "type": "LLMConfig",
                                    "params": {"provider": "openai/gpt-4o-mini"}
                                },
                                "instruction": "Extract the main title and summary."
                            }
                        }
                    }
                }
                ```
        * 3.5.4. **REST API Examples**
            * `/crawl` Endpoint:
                * URL: `http://localhost:11235/crawl`
                * HTTP Method: `POST`
                * Payload Structure (`CrawlRequest` model from `deploy/docker/schemas.py`):
                    ```json
                    {
                        "urls": ["https://example.com"],
                        "browser_config": { // JSON representation of BrowserConfig
                            "type": "BrowserConfig",
                            "params": {"headless": true}
                        },
                        "crawler_config": { // JSON representation of CrawlerRunConfig
                            "type": "CrawlerRunConfig",
                            "params": {"screenshot": true}
                        }
                    }
                    ```
                * Response Structure: A JSON object, typically `{"success": true, "results": [CrawlResult, ...], "server_processing_time_s": float, ...}`.
            * `/crawl/stream` Endpoint:
                * URL: `http://localhost:11235/crawl/stream`
                * HTTP Method: `POST`
                * Payload Structure: Same as `/crawl` (`CrawlRequest` model).
                * Response Structure: Newline Delimited JSON (NDJSON, `application/x-ndjson`). Each line is a JSON string representing a `CrawlResult` object.
                    * Headers: Includes `Content-Type: application/x-ndjson` and `X-Stream-Status: active` while streaming, and a final JSON object `{"status": "completed"}`.

    * 3.6. **Additional API Endpoints (from `server.py`)**
        * 3.6.1. `/html`
            * Endpoint URL: `/html`
            * HTTP Method: `POST`
            * Purpose: Crawls the given URL, preprocesses its raw HTML content specifically for schema extraction purposes (e.g., by sanitizing and simplifying the structure), and returns the processed HTML.
            * Request Body (`HTMLRequest` from `deploy/docker/schemas.py`):
                * `url (str)`: The URL to fetch and process.
            * Response Structure (JSON):
                * `html (str)`: The preprocessed HTML string.
                * `url (str)`: The original URL requested.
                * `success (bool)`: Indicates if the operation was successful.
        * 3.6.2. `/screenshot`
            * Endpoint URL: `/screenshot`
            * HTTP Method: `POST`
            * Purpose: Captures a full-page PNG screenshot of the specified URL. Allows an optional delay before capture and an option to save the file server-side.
            * Request Body (`ScreenshotRequest` from `deploy/docker/schemas.py`):
                * `url (str)`: The URL to take a screenshot of.
                * `screenshot_wait_for (Optional[float])`: Seconds to wait before taking the screenshot. Default: `2.0`.
                * `output_path (Optional[str])`: If provided, the screenshot is saved to this path on the server, and the path is returned. Otherwise, the base64 encoded image is returned. Default: `None`.
            * Response Structure (JSON):
                * `success (bool)`: Indicates if the screenshot was successfully taken.
                * `screenshot (Optional[str])`: Base64 encoded PNG image data, if `output_path` was not provided.
                * `path (Optional[str])`: The absolute server-side path to the saved screenshot, if `output_path` was provided.
        * 3.6.3. `/pdf`
            * Endpoint URL: `/pdf`
            * HTTP Method: `POST`
            * Purpose: Generates a PDF document of the rendered content of the specified URL.
            * Request Body (`PDFRequest` from `deploy/docker/schemas.py`):
                * `url (str)`: The URL to convert to PDF.
                * `output_path (Optional[str])`: If provided, the PDF is saved to this path on the server, and the path is returned. Otherwise, the base64 encoded PDF data is returned. Default: `None`.
            * Response Structure (JSON):
                * `success (bool)`: Indicates if the PDF generation was successful.
                * `pdf (Optional[str])`: Base64 encoded PDF data, if `output_path` was not provided.
                * `path (Optional[str])`: The absolute server-side path to the saved PDF, if `output_path` was provided.
        * 3.6.4. `/execute_js`
            * Endpoint URL: `/execute_js`
            * HTTP Method: `POST`
            * Purpose: Executes a list of JavaScript snippets on the specified URL in the browser context and returns the full `CrawlResult` object, including any modifications or data retrieved by the scripts.
            * Request Body (`JSEndpointRequest` from `deploy/docker/schemas.py`):
                * `url (str)`: The URL on which to execute the JavaScript.
                * `scripts (List[str])`: A list of JavaScript code snippets to execute sequentially. Each script should be an expression that returns a value.
            * Response Structure (JSON): A `CrawlResult` object (serialized to a dictionary) containing the state of the page after JS execution, including `js_execution_result`.
        * 3.6.5. `/ask` (Endpoint defined as `/ask` in `server.py`)
            * Endpoint URL: `/ask`
            * HTTP Method: `GET`
            * Purpose: Retrieves context about the Crawl4ai library itself, either code snippets or documentation sections, filtered by a query. This is designed for AI assistants or RAG systems needing information about Crawl4ai.
            * Parameters (Query):
                * `context_type (str, default="all", enum=["code", "doc", "all"])`: Specifies whether to return "code", "doc", or "all" (both).
                * `query (Optional[str])`: A search query string used to filter relevant chunks using BM25 ranking. If `None`, returns all context of the specified type(s).
                * `score_ratio (float, default=0.5, ge=0.0, le=1.0)`: The minimum score (as a fraction of the maximum possible score for the query) for a chunk to be included in the results.
                * `max_results (int, default=20, ge=1)`: The maximum number of result chunks to return.
            * Response Structure (JSON):
                * If `query` is provided:
                    * `code_results (Optional[List[Dict[str, Union[str, float]]]])`: A list of dictionaries, where each dictionary contains `{"text": "code_chunk...", "score": bm25_score}`. Present if `context_type` is "code" or "all".
                    * `doc_results (Optional[List[Dict[str, Union[str, float]]]])`: A list of dictionaries, where each dictionary contains `{"text": "doc_chunk...", "score": bm25_score}`. Present if `context_type` is "doc" or "all".
                * If `query` is not provided:
                    * `code_context (Optional[str])`: The full concatenated code context as a single string. Present if `context_type` is "code" or "all".
                    * `doc_context (Optional[str])`: The full concatenated documentation context as a single string. Present if `context_type` is "doc" or "all".

    * 3.7. **MCP (Model Context Protocol) Support**
        * 3.7.1. Explanation of MCP:
            * Purpose: The Model Context Protocol (MCP) is a standardized way for AI models (like Anthropic's Claude with Code Interpreter capabilities) to discover and interact with external tools and data sources. Crawl4ai's MCP server exposes its functionalities as tools that an MCP-compatible AI can use.
        * 3.7.2. Connection Endpoints (defined in `mcp_bridge.py` and attached to FastAPI app):
            * `/mcp/sse`: Server-Sent Events (SSE) endpoint for MCP communication.
            * `/mcp/ws`: WebSocket endpoint for MCP communication.
            * `/mcp/messages`: Endpoint for clients to POST messages in the SSE transport.
        * 3.7.3. Usage with Claude Code Example:
            * Command: `claude mcp add -t sse c4ai-sse http://localhost:11235/mcp/sse`
            * Purpose: This command (specific to the Claude Code CLI) registers the Crawl4ai MCP server as a tool provider named `c4ai-sse` using the SSE transport. The AI can then discover and invoke tools from this source.
        * 3.7.4. List of Available MCP Tools (defined by `@mcp_tool` decorators in `server.py`):
            * `md`: Fetches Markdown for a URL.
                * Parameters (derived from `get_markdown` function signature): `url (str)`, `filter_type (FilterType)`, `query (Optional[str])`, `cache (Optional[str])`.
            * `html`: Generates preprocessed HTML for a URL.
                * Parameters (derived from `generate_html` function signature): `url (str)`.
            * `screenshot`: Generates a screenshot of a URL.
                * Parameters (derived from `generate_screenshot` function signature): `url (str)`, `screenshot_wait_for (Optional[float])`, `output_path (Optional[str])`.
            * `pdf`: Generates a PDF of a URL.
                * Parameters (derived from `generate_pdf` function signature): `url (str)`, `output_path (Optional[str])`.
            * `execute_js`: Executes JavaScript on a URL.
                * Parameters (derived from `execute_js` function signature): `url (str)`, `scripts (List[str])`.
            * `crawl`: Performs a full crawl operation.
                * Parameters (derived from `crawl` function signature): `urls (List[str])`, `browser_config (Optional[Dict])`, `crawler_config (Optional[Dict])`.
            * `ask`: Retrieves library context.
                * Parameters (derived from `get_context` function signature): `context_type (str)`, `query (Optional[str])`, `score_ratio (float)`, `max_results (int)`.
        * 3.7.5. Testing MCP Connections:
            * Method: Use an MCP client tool (e.g., `claude mcp call c4ai-sse.md url=https://example.com`) to invoke a tool and verify the response.
        * 3.7.6. Accessing MCP Schemas:
            * Endpoint URL: `/mcp/schema`
            * Purpose: Returns a JSON response detailing all registered MCP tools, including their names, descriptions, and input schemas, enabling clients to understand how to use them.

    * 3.8. **Metrics & Monitoring Endpoints**
        * 3.8.1. `/health`
            * Purpose: Provides a basic health check for the server, indicating if it's running and responsive.
            * Response Structure (JSON from `server.py`): `{"status": "ok", "timestamp": float, "version": str}` (where version is `__version__` from `server.py`).
            * Configuration: Path configurable via `observability.health_check.endpoint` in `config.yml`.
        * 3.8.2. `/metrics`
            * Purpose: Exposes application metrics in a format compatible with Prometheus for monitoring and alerting.
            * Response Format: Prometheus text format.
            * Configuration: Enabled via `observability.prometheus.enabled: true` and endpoint path via `observability.prometheus.endpoint` in `config.yml`.

    * 3.9. **Underlying Server Logic (`server.py` - High-Level Understanding)**
        * 3.9.1. FastAPI Application:
            * Framework: The server is built using the FastAPI Python web framework for creating APIs.
        * 3.9.2. `crawler_pool` (`CrawlerPool` from `deploy.docker.crawler_pool`):
            * Role: Manages a pool of `AsyncWebCrawler` instances to reuse browser resources efficiently.
            * `get_crawler(BrowserConfig)`: Fetches an existing idle crawler compatible with the `BrowserConfig` or creates a new one if none are available or compatible.
            * `close_all()`: Iterates through all pooled crawlers and closes them.
            * `janitor()`: An `asyncio.Task` that runs periodically to close and remove crawler instances that have been idle for longer than `crawler.pool.idle_ttl_sec` (configured in `config.yml`).
        * 3.9.3. Global Page Semaphore (`GLOBAL_SEM`):
            * Type: `asyncio.Semaphore`.
            * Purpose: A global semaphore that limits the total number of concurrently open browser pages across all `AsyncWebCrawler` instances managed by the server. This acts as a hard cap to prevent excessive resource consumption.
            * Configuration: The maximum number of concurrent pages is set by `crawler.pool.max_pages` in `config.yml` (default: `30` in `server.py`, but `40` in `config.yml`). The `AsyncWebCrawler.arun` method acquires this semaphore.
        * 3.9.4. Job Router (`init_job_router` from `deploy.docker.job`):
            * Role: Manages asynchronous, long-running tasks, particularly for the `/crawl` (non-streaming batch) endpoint.
            * Mechanism: Uses Redis (configured in `config.yml`) as a backend for task queuing (storing task metadata like status, creation time, URL, result, error) and status tracking.
            * User Interaction: When a job is submitted to an endpoint using this router (e.g., `/crawl/job`), a `task_id` is returned. The client then polls an endpoint like `/task/{task_id}` to get the status and eventual result or error.
        * 3.9.5. Rate Limiting Middleware:
            * Implementation: Uses the `slowapi` library, integrated with FastAPI.
            * Purpose: To protect the server from abuse by limiting the number of requests an IP address can make within a specified time window.
            * Configuration: Settings like `enabled`, `default_limit`, `storage_uri` (e.g., `memory://` or `redis://...`) are managed in the `rate_limiting` section of `config.yml`.
        * 3.9.6. Security Middleware:
            * Implementations: `HTTPSRedirectMiddleware` and `TrustedHostMiddleware` from FastAPI, plus custom logic for adding security headers.
            * Purpose:
                * `HTTPSRedirectMiddleware`: Redirects HTTP requests to HTTPS if `security.https_redirect` is true.
                * `TrustedHostMiddleware`: Ensures requests are only served if their `Host` header matches an entry in `security.trusted_hosts`.
                * Custom header logic: Adds HTTP security headers like `X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`, `Strict-Transport-Security` to all responses if `security.enabled` is true. These are defined in `security.headers` in `config.yml`.
        * 3.9.7. API Request Mapping:
            * Request Models: Pydantic models defined in `deploy/docker/schemas.py` (e.g., `CrawlRequest`, `MarkdownRequest`, `HTMLRequest`, `ScreenshotRequest`, `PDFRequest`, `JSEndpointRequest`, `TokenRequest`, `RawCode`) define the expected JSON structure for incoming API request bodies.
            * Endpoint Logic: Functions decorated with `@app.post(...)`, `@app.get(...)`, etc., in `server.py` handle incoming HTTP requests. These functions use FastAPI's dependency injection to parse and validate request bodies against the Pydantic models.
            * `AsyncWebCrawler` Interaction:
                * The parameters from the parsed request models (e.g., `CrawlRequest.urls`, `CrawlRequest.browser_config`, `CrawlRequest.crawler_config`) are used.
                * `BrowserConfig` and `CrawlerRunConfig` objects are created by calling their respective `.load()` class methods with the dictionary payloads received in the request (e.g., `BrowserConfig.load(crawl_request.browser_config)`).
                * These configuration objects are then passed to an `AsyncWebCrawler` instance obtained from the `crawler_pool`, typically to its `arun()` (for single URL or when JS execution context is critical) or `arun_many()` (for batch processing of multiple URLs) methods.
            * Result Serialization: The `CrawlResult` objects (or lists/generators of them) returned by the `AsyncWebCrawler` are usually serialized to JSON using their `.model_dump()` method before being included in the HTTP response. For streaming endpoints, each `CrawlResult` is serialized and sent as a separate NDJSON line.

## 4. Version Numbering Scheme

    * 4.1. **Standard Versioning (`MAJOR.MINOR.PATCH`)**
        * `MAJOR`: Incremented when incompatible API changes are made.
        * `MINOR`: Incremented when functionality is added in a backward-compatible manner.
        * `PATCH`: Incremented for backward-compatible bug fixes.
    * 4.2. **Pre-release Suffixes**
        * `devN`: (e.g., `0.6.0.dev1`) Development release. These are typically unstable and used for internal testing or early feedback on new, unrefined features.
        * `aN`: (e.g., `0.6.0a1`) Alpha release. Indicates an early preview of a new version, potentially unstable, and APIs might still change.
        * `bN`: (e.g., `0.6.0b1`) Beta release. Generally feature-complete for the targeted minor or major version but may still contain bugs. APIs are mostly stable at this point.
        * `rcN`: (e.g., `0.6.0rc1`) Release Candidate. A version that is potentially the final release, undergoing final testing to catch critical bugs before official release.
```

---


# Deep Crawling - Memory
Source: crawl4ai_deep_crawling_memory_content.llm.md

Okay, I have read and processed the information. I will now generate the detailed "Foundational Memory" document for the `deep_crawling` component of `crawl4ai`, based on the outline from the previous step and the provided code snippets.

```markdown
# Detailed Foundational Memory for crawl4ai - deep_crawling Component

**Target Document Type:** memory
**Target Output Filename Suggestion:** `llm_memory_deep_crawling.md`
**Library Version Context:** 0.6.3 (from `crawl4ai/__version__.py`)
**Outline Generation Date:** 2024-05-24
---

## 1. Introduction to Deep Crawling

*   1.1. Purpose: The `deep_crawling` component provides functionalities for recursively crawling web pages starting from an initial URL. It includes strategies for different traversal orders (BFS, DFS, Best-First), mechanisms for filtering which URLs to visit, and methods for scoring URLs to prioritize crawling.
*   1.2. Core Concepts:
    *   1.2.1. Definition of Deep Crawling in Crawl4ai context: The process of discovering and fetching multiple web pages by following links from an initial set of URLs, adhering to specified depth, page limits, and filtering/scoring rules.
    *   1.2.2. Key Abstractions:
        *   `DeepCrawlStrategy`: Defines the algorithm for traversing linked web pages (e.g., BFS, DFS).
        *   `URLFilter`: Determines whether a discovered URL should be considered for crawling.
        *   `URLScorer`: Assigns a score to URLs to influence crawling priority, especially in strategies like Best-First.

## 2. `DeepCrawlStrategy` Interface and Implementations

*   **2.1. `DeepCrawlStrategy` (Abstract Base Class)**
    *   Source: `crawl4ai/deep_crawling/base_strategy.py`
    *   2.1.1. Purpose: Defines the abstract base class for all deep crawling strategies, outlining the core methods required for traversal logic, resource management, URL validation, and link discovery.
    *   2.1.2. Key Abstract Methods:
        *   `async def _arun_batch(self, start_url: str, crawler: AsyncWebCrawler, config: CrawlerRunConfig) -> List[CrawlResult]`:
            *   Description: Core logic for batch (non-streaming) deep crawling. Processes URLs level by level (or according to strategy) and returns all results once the crawl is complete or limits are met.
        *   `async def _arun_stream(self, start_url: str, crawler: AsyncWebCrawler, config: CrawlerRunConfig) -> AsyncGenerator[CrawlResult, None]`:
            *   Description: Core logic for streaming deep crawling. Processes URLs and yields `CrawlResult` objects as they become available.
        *   `async def shutdown(self) -> None`:
            *   Description: Cleans up any resources used by the deep crawl strategy, such as signaling cancellation events.
        *   `async def can_process_url(self, url: str, depth: int) -> bool`:
            *   Description: Validates a given URL and current depth against configured filters and limits to decide if it should be processed.
        *   `async def link_discovery(self, result: CrawlResult, source_url: str, current_depth: int, visited: Set[str], next_level: List[tuple], depths: Dict[str, int]) -> None`:
            *   Description: Extracts links from a `CrawlResult`, validates them using `can_process_url`, optionally scores them, and appends valid URLs (and their parent references) to the `next_level` list. Updates the `depths` dictionary for newly discovered URLs.
    *   2.1.3. Key Concrete Methods:
        *   `async def arun(self, start_url: str, crawler: AsyncWebCrawler, config: Optional[CrawlerRunConfig] = None) -> RunManyReturn`:
            *   Description: Main entry point for initiating a deep crawl. It checks if a `CrawlerRunConfig` is provided and then delegates to either `_arun_stream` or `_arun_batch` based on the `config.stream` flag.
        *   `def __call__(self, start_url: str, crawler: AsyncWebCrawler, config: CrawlerRunConfig)`:
            *   Description: Makes the strategy instance callable, directly invoking the `arun` method.
    *   2.1.4. Attributes:
        *   `_cancel_event (asyncio.Event)`: Event to signal cancellation of the crawl.
        *   `_pages_crawled (int)`: Counter for the number of pages successfully crawled.

*   **2.2. `BFSDeepCrawlStrategy`**
    *   Source: `crawl4ai/deep_crawling/bfs_strategy.py`
    *   2.2.1. Purpose: Implements a Breadth-First Search (BFS) deep crawling strategy, exploring all URLs at the current depth level before moving to the next.
    *   2.2.2. Inheritance: `DeepCrawlStrategy`
    *   2.2.3. Initialization (`__init__`)
        *   2.2.3.1. Signature:
            ```python
            def __init__(
                self,
                max_depth: int,
                filter_chain: FilterChain = FilterChain(),
                url_scorer: Optional[URLScorer] = None,
                include_external: bool = False,
                score_threshold: float = -float('inf'),
                max_pages: int = float('inf'),
                logger: Optional[logging.Logger] = None,
            ):
            ```
        *   2.2.3.2. Parameters:
            *   `max_depth (int)`: Maximum depth to crawl relative to the `start_url`.
            *   `filter_chain (FilterChain`, default: `FilterChain()`)`: A `FilterChain` instance to apply to discovered URLs.
            *   `url_scorer (Optional[URLScorer]`, default: `None`)`: An optional `URLScorer` to score URLs. If provided, URLs below `score_threshold` are skipped, and for crawls exceeding `max_pages`, higher-scored URLs are prioritized.
            *   `include_external (bool`, default: `False`)`: If `True`, allows crawling of URLs from external domains.
            *   `score_threshold (float`, default: `-float('inf')`)`: Minimum score (if `url_scorer` is used) for a URL to be processed.
            *   `max_pages (int`, default: `float('inf')`)`: Maximum total number of pages to crawl.
            *   `logger (Optional[logging.Logger]`, default: `None`)`: An optional logger instance. If `None`, a default logger is created.
    *   2.2.4. Key Implemented Methods:
        *   `_arun_batch(...)`: Implements BFS traversal by processing URLs level by level. It collects all results from a level before discovering links for the next level. All results are returned as a list upon completion.
        *   `_arun_stream(...)`: Implements BFS traversal, yielding `CrawlResult` objects as soon as they are processed within a level. Link discovery for the next level happens after all URLs in the current level are processed and their results yielded.
        *   `can_process_url(...)`: Validates URL format, applies the `filter_chain`, and checks depth limits. For the start URL (depth 0), filtering is bypassed.
        *   `link_discovery(...)`: Extracts internal (and optionally external) links, normalizes them, checks against `visited` set and `can_process_url`. If a `url_scorer` is present and `max_pages` limit is a concern, it scores and sorts valid links, selecting the top ones within `remaining_capacity`.
        *   `shutdown(...)`: Sets an internal `_cancel_event` to signal graceful termination and records the end time in `stats`.
    *   2.2.5. Key Attributes/Properties:
        *   `stats (TraversalStats)`: [Read-only] - Instance of `TraversalStats` tracking the progress and statistics of the crawl.
        *   `max_depth (int)`: Maximum crawl depth.
        *   `filter_chain (FilterChain)`: The filter chain used.
        *   `url_scorer (Optional[URLScorer])`: The URL scorer used.
        *   `include_external (bool)`: Flag for including external URLs.
        *   `score_threshold (float)`: URL score threshold.
        *   `max_pages (int)`: Maximum pages to crawl.

*   **2.3. `DFSDeepCrawlStrategy`**
    *   Source: `crawl4ai/deep_crawling/dfs_strategy.py`
    *   2.3.1. Purpose: Implements a Depth-First Search (DFS) deep crawling strategy, exploring as far as possible along each branch before backtracking.
    *   2.3.2. Inheritance: `BFSDeepCrawlStrategy` (Note: Leverages much of the `BFSDeepCrawlStrategy`'s infrastructure but overrides traversal logic to use a stack.)
    *   2.3.3. Initialization (`__init__`)
        *   2.3.3.1. Signature: (Same as `BFSDeepCrawlStrategy`)
            ```python
            def __init__(
                self,
                max_depth: int,
                filter_chain: FilterChain = FilterChain(),
                url_scorer: Optional[URLScorer] = None,
                include_external: bool = False,
                score_threshold: float = -float('inf'),
                max_pages: int = infinity,
                logger: Optional[logging.Logger] = None,
            ):
            ```
        *   2.3.3.2. Parameters: Same as `BFSDeepCrawlStrategy`.
    *   2.3.4. Key Overridden/Implemented Methods:
        *   `_arun_batch(...)`: Implements DFS traversal using a LIFO stack. Processes one URL at a time, discovers its links, and adds them to the stack (typically in reverse order of discovery to maintain a natural DFS path). Collects all results in a list.
        *   `_arun_stream(...)`: Implements DFS traversal using a LIFO stack, yielding `CrawlResult` for each processed URL as it becomes available. Discovered links are added to the stack for subsequent processing.

*   **2.4. `BestFirstCrawlingStrategy`**
    *   Source: `crawl4ai/deep_crawling/bff_strategy.py`
    *   2.4.1. Purpose: Implements a Best-First Search deep crawling strategy, prioritizing URLs based on scores assigned by a `URLScorer`. It uses a priority queue to manage URLs to visit.
    *   2.4.2. Inheritance: `DeepCrawlStrategy`
    *   2.4.3. Initialization (`__init__`)
        *   2.4.3.1. Signature:
            ```python
            def __init__(
                self,
                max_depth: int,
                filter_chain: FilterChain = FilterChain(),
                url_scorer: Optional[URLScorer] = None,
                include_external: bool = False,
                max_pages: int = float('inf'),
                logger: Optional[logging.Logger] = None,
            ):
            ```
        *   2.4.3.2. Parameters:
            *   `max_depth (int)`: Maximum depth to crawl.
            *   `filter_chain (FilterChain`, default: `FilterChain()`)`: Chain of filters to apply.
            *   `url_scorer (Optional[URLScorer]`, default: `None`)`: Scorer to rank URLs. Crucial for this strategy; if not provided, URLs might effectively be processed in FIFO order (score 0).
            *   `include_external (bool`, default: `False`)`: Whether to include external links.
            *   `max_pages (int`, default: `float('inf')`)`: Maximum number of pages to crawl.
            *   `logger (Optional[logging.Logger]`, default: `None`)`: Logger instance.
    *   2.4.4. Key Implemented Methods:
        *   `_arun_batch(...)`: Aggregates results from `_arun_best_first` into a list.
        *   `_arun_stream(...)`: Yields results from `_arun_best_first` as they are generated.
        *   `_arun_best_first(...)`: Core logic for best-first traversal. Uses an `asyncio.PriorityQueue` where items are `(score, depth, url, parent_url)`. URLs are processed in batches (default size 10) from the priority queue. Discovered links are scored and added to the queue.
    *   2.4.5. Key Attributes/Properties:
        *   `stats (TraversalStats)`: [Read-only] - Traversal statistics object.
        *   `BATCH_SIZE (int)`: [Class constant, default: 10] - Number of URLs to process concurrently from the priority queue.

## 3. URL Filtering Mechanisms

*   **3.1. `URLFilter` (Abstract Base Class)**
    *   Source: `crawl4ai/deep_crawling/filters.py`
    *   3.1.1. Purpose: Defines the abstract base class for all URL filters, providing a common interface for deciding whether a URL should be processed.
    *   3.1.2. Key Abstract Methods:
        *   `apply(self, url: str) -> bool`:
            *   Description: Abstract method that must be implemented by subclasses. It takes a URL string and returns `True` if the URL passes the filter (should be processed), and `False` otherwise.
    *   3.1.3. Key Attributes/Properties:
        *   `name (str)`: [Read-only] - The name of the filter, typically the class name.
        *   `stats (FilterStats)`: [Read-only] - An instance of `FilterStats` to track how many URLs were processed, passed, and rejected by this filter.
        *   `logger (logging.Logger)`: [Read-only] - A logger instance specific to this filter, initialized lazily.
    *   3.1.4. Key Concrete Methods:
        *   `_update_stats(self, passed: bool) -> None`: Updates the `stats` object (total, passed, rejected counts).

*   **3.2. `FilterChain`**
    *   Source: `crawl4ai/deep_crawling/filters.py`
    *   3.2.1. Purpose: Manages a sequence of `URLFilter` instances. A URL must pass all filters in the chain to be considered valid.
    *   3.2.2. Initialization (`__init__`)
        *   3.2.2.1. Signature:
            ```python
            def __init__(self, filters: List[URLFilter] = None):
            ```
        *   3.2.2.2. Parameters:
            *   `filters (List[URLFilter]`, default: `None`)`: An optional list of `URLFilter` instances to initialize the chain with. If `None`, an empty chain is created.
    *   3.2.3. Key Public Methods:
        *   `add_filter(self, filter_: URLFilter) -> FilterChain`:
            *   Description: Adds a new `URLFilter` instance to the end of the chain.
            *   Returns: `(FilterChain)` - The `FilterChain` instance itself, allowing for method chaining.
        *   `async def apply(self, url: str) -> bool`:
            *   Description: Applies each filter in the chain to the given URL. If any filter returns `False` (rejects the URL), this method immediately returns `False`. If all filters pass, it returns `True`. Handles both synchronous and asynchronous `apply` methods of individual filters.
            *   Returns: `(bool)` - `True` if the URL passes all filters, `False` otherwise.
    *   3.2.4. Key Attributes/Properties:
        *   `filters (Tuple[URLFilter, ...])`: [Read-only] - An immutable tuple containing the `URLFilter` instances in the chain.
        *   `stats (FilterStats)`: [Read-only] - An instance of `FilterStats` tracking the aggregated statistics for the entire chain (total URLs processed, passed, and rejected by the chain as a whole).

*   **3.3. `URLPatternFilter`**
    *   Source: `crawl4ai/deep_crawling/filters.py`
    *   3.3.1. Purpose: Filters URLs based on whether they match a list of specified string patterns. Supports glob-style wildcards and regular expressions.
    *   3.3.2. Inheritance: `URLFilter`
    *   3.3.3. Initialization (`__init__`)
        *   3.3.3.1. Signature:
            ```python
            def __init__(
                self,
                patterns: Union[str, Pattern, List[Union[str, Pattern]]],
                use_glob: bool = True, # Deprecated, glob is always used for strings if not regex
                reverse: bool = False,
            ):
            ```
        *   3.3.3.2. Parameters:
            *   `patterns (Union[str, Pattern, List[Union[str, Pattern]]])`: A single pattern string/compiled regex, or a list of such patterns. String patterns are treated as glob patterns by default unless they are identifiable as regex (e.g., start with `^`, end with `$`, contain `\d`).
            *   `use_glob (bool`, default: `True`)`: [Deprecated] This parameter's functionality is now implicitly handled by pattern detection.
            *   `reverse (bool`, default: `False`)`: If `True`, the filter rejects URLs that match any of the patterns. If `False` (default), it accepts URLs that match any pattern and rejects those that don't match any.
    *   3.3.4. Key Implemented Methods:
        *   `apply(self, url: str) -> bool`:
            *   Description: Checks if the URL matches any of the configured patterns. Simple suffix/prefix/domain patterns are checked first for performance. For more complex patterns, it uses `fnmatch.translate` (for glob-like strings) or compiled regex objects. The outcome is affected by the `reverse` flag.
    *   3.3.5. Internal Categorization:
        *   `PATTERN_TYPES`: A dictionary mapping pattern types (SUFFIX, PREFIX, DOMAIN, PATH, REGEX) to integer constants.
        *   `_simple_suffixes (Set[str])`: Stores simple suffix patterns (e.g., `.html`).
        *   `_simple_prefixes (Set[str])`: Stores simple prefix patterns (e.g., `/blog/`).
        *   `_domain_patterns (List[Pattern])`: Stores compiled regex for domain-specific patterns (e.g., `*.example.com`).
        *   `_path_patterns (List[Pattern])`: Stores compiled regex for more general path patterns.

*   **3.4. `ContentTypeFilter`**
    *   Source: `crawl4ai/deep_crawling/filters.py`
    *   3.4.1. Purpose: Filters URLs based on their expected content type, primarily by inferring it from the file extension in the URL.
    *   3.4.2. Inheritance: `URLFilter`
    *   3.4.3. Initialization (`__init__`)
        *   3.4.3.1. Signature:
            ```python
            def __init__(
                self,
                allowed_types: Union[str, List[str]],
                check_extension: bool = True,
                ext_map: Dict[str, str] = _MIME_MAP, # _MIME_MAP is internal
            ):
            ```
        *   3.4.3.2. Parameters:
            *   `allowed_types (Union[str, List[str]])`: A single MIME type string (e.g., "text/html") or a list of allowed MIME types. Can also be partial types like "image/" to allow all image types.
            *   `check_extension (bool`, default: `True`)`: If `True` (default), the filter attempts to determine the content type by looking at the URL's file extension. If `False`, all URLs pass this filter (unless `allowed_types` is empty).
            *   `ext_map (Dict[str, str]`, default: `ContentTypeFilter._MIME_MAP`)`: A dictionary mapping file extensions to their corresponding MIME types. A comprehensive default map is provided.
    *   3.4.4. Key Implemented Methods:
        *   `apply(self, url: str) -> bool`:
            *   Description: Extracts the file extension from the URL. If `check_extension` is `True` and an extension is found, it checks if the inferred MIME type (or the extension itself if MIME type is unknown) is among the `allowed_types`. If no extension is found, it typically allows the URL (assuming it might be an HTML page or similar).
    *   3.4.5. Static Methods:
        *   `_extract_extension(url: str) -> str`: [Cached] Extracts the file extension from a URL path, handling query parameters and fragments.
    *   3.4.6. Class Variables:
        *   `_MIME_MAP (Dict[str, str])`: A class-level dictionary mapping common file extensions to MIME types.

*   **3.5. `DomainFilter`**
    *   Source: `crawl4ai/deep_crawling/filters.py`
    *   3.5.1. Purpose: Filters URLs based on a whitelist of allowed domains or a blacklist of blocked domains. Supports subdomain matching.
    *   3.5.2. Inheritance: `URLFilter`
    *   3.5.3. Initialization (`__init__`)
        *   3.5.3.1. Signature:
            ```python
            def __init__(
                self,
                allowed_domains: Union[str, List[str]] = None,
                blocked_domains: Union[str, List[str]] = None,
            ):
            ```
        *   3.5.3.2. Parameters:
            *   `allowed_domains (Union[str, List[str]]`, default: `None`)`: A single domain string or a list of domain strings. If provided, only URLs whose domain (or a subdomain thereof) is in this list will pass.
            *   `blocked_domains (Union[str, List[str]]`, default: `None`)`: A single domain string or a list of domain strings. URLs whose domain (or a subdomain thereof) is in this list will be rejected.
    *   3.5.4. Key Implemented Methods:
        *   `apply(self, url: str) -> bool`:
            *   Description: Extracts the domain from the URL. First, checks if the domain is in `_blocked_domains` (rejects if true). Then, if `_allowed_domains` is specified, checks if the domain is in that list (accepts if true). If `_allowed_domains` is not specified and the URL was not blocked, it passes.
    *   3.5.5. Static Methods:
        *   `_normalize_domains(domains: Union[str, List[str]]) -> Set[str]`: Converts input domains to a set of lowercase strings.
        *   `_is_subdomain(domain: str, parent_domain: str) -> bool`: Checks if `domain` is a subdomain of (or equal to) `parent_domain`.
        *   `_extract_domain(url: str) -> str`: [Cached] Extracts the domain name from a URL.

*   **3.6. `ContentRelevanceFilter`**
    *   Source: `crawl4ai/deep_crawling/filters.py`
    *   3.6.1. Purpose: Filters URLs by fetching their `<head>` section, extracting text content (title, meta tags), and scoring its relevance against a given query using the BM25 algorithm.
    *   3.6.2. Inheritance: `URLFilter`
    *   3.6.3. Initialization (`__init__`)
        *   3.6.3.1. Signature:
            ```python
            def __init__(
                self,
                query: str,
                threshold: float,
                k1: float = 1.2,
                b: float = 0.75,
                avgdl: int = 1000,
            ):
            ```
        *   3.6.3.2. Parameters:
            *   `query (str)`: The query string to assess relevance against.
            *   `threshold (float)`: The minimum BM25 score required for the URL to be considered relevant and pass the filter.
            *   `k1 (float`, default: `1.2`)`: BM25 k1 parameter (term frequency saturation).
            *   `b (float`, default: `0.75`)`: BM25 b parameter (length normalization).
            *   `avgdl (int`, default: `1000`)`: Assumed average document length for BM25 calculations (typically based on the head content).
    *   3.6.4. Key Implemented Methods:
        *   `async def apply(self, url: str) -> bool`:
            *   Description: Asynchronously fetches the HTML `<head>` content of the URL using `HeadPeeker.peek_html`. Extracts title and meta description/keywords. Calculates the BM25 score of this combined text against the `query`. Returns `True` if the score is >= `threshold`.
    *   3.6.5. Helper Methods:
        *   `_build_document(self, fields: Dict) -> str`: Constructs a weighted document string from title and meta tags.
        *   `_tokenize(self, text: str) -> List[str]`: Simple whitespace tokenizer.
        *   `_bm25(self, document: str) -> float`: Calculates the BM25 score.

*   **3.7. `SEOFilter`**
    *   Source: `crawl4ai/deep_crawling/filters.py`
    *   3.7.1. Purpose: Filters URLs by performing a quantitative SEO quality assessment based on the content of their `<head>` section (e.g., title length, meta description presence, canonical tags, robots meta tags, schema.org markup).
    *   3.7.2. Inheritance: `URLFilter`
    *   3.7.3. Initialization (`__init__`)
        *   3.7.3.1. Signature:
            ```python
            def __init__(
                self,
                threshold: float = 0.65,
                keywords: List[str] = None,
                weights: Dict[str, float] = None,
            ):
            ```
        *   3.7.3.2. Parameters:
            *   `threshold (float`, default: `0.65`)`: The minimum aggregated SEO score (typically 0.0 to 1.0 range, though individual factor weights can exceed 1) required for the URL to pass.
            *   `keywords (List[str]`, default: `None`)`: A list of keywords to check for presence in the title.
            *   `weights (Dict[str, float]`, default: `None`)`: A dictionary to override default weights for various SEO factors (e.g., `{"title_length": 0.2, "canonical": 0.15}`).
    *   3.7.4. Key Implemented Methods:
        *   `async def apply(self, url: str) -> bool`:
            *   Description: Asynchronously fetches the HTML `<head>` content. Calculates scores for individual SEO factors (title length, keyword presence, meta description, canonical tag, robots meta tag, schema.org presence, URL quality). Aggregates these scores using the defined `weights`. Returns `True` if the total score is >= `threshold`.
    *   3.7.5. Helper Methods (Scoring Factors):
        *   `_score_title_length(self, title: str) -> float`
        *   `_score_keyword_presence(self, text: str) -> float`
        *   `_score_meta_description(self, desc: str) -> float`
        *   `_score_canonical(self, canonical: str, original: str) -> float`
        *   `_score_schema_org(self, html: str) -> float`
        *   `_score_url_quality(self, parsed_url) -> float`
    *   3.7.6. Class Variables:
        *   `DEFAULT_WEIGHTS (Dict[str, float])`: Default weights for each SEO factor.

*   **3.8. `FilterStats` Data Class**
    *   Source: `crawl4ai/deep_crawling/filters.py`
    *   3.8.1. Purpose: A data class to track statistics for URL filtering operations, including total URLs processed, passed, and rejected.
    *   3.8.2. Fields:
        *   `_counters (array.array)`: An array of unsigned integers storing counts for `[total, passed, rejected]`.
    *   3.8.3. Properties:
        *   `total_urls (int)`: Returns the total number of URLs processed.
        *   `passed_urls (int)`: Returns the number of URLs that passed the filter.
        *   `rejected_urls (int)`: Returns the number of URLs that were rejected.

## 4. URL Scoring Mechanisms

*   **4.1. `URLScorer` (Abstract Base Class)**
    *   Source: `crawl4ai/deep_crawling/scorers.py`
    *   4.1.1. Purpose: Defines the abstract base class for all URL scorers. Scorers assign a numerical value to URLs, which can be used to prioritize crawling.
    *   4.1.2. Key Abstract Methods:
        *   `_calculate_score(self, url: str) -> float`:
            *   Description: Abstract method to be implemented by subclasses. It takes a URL string and returns a raw numerical score.
    *   4.1.3. Key Concrete Methods:
        *   `score(self, url: str) -> float`:
            *   Description: Calculates the final score for a URL by calling `_calculate_score` and multiplying the result by the scorer's `weight`. It also updates the internal `ScoringStats`.
            *   Returns: `(float)` - The weighted score.
    *   4.1.4. Key Attributes/Properties:
        *   `weight (ctypes.c_float)`: [Read-write] - The weight assigned to this scorer. The raw score calculated by `_calculate_score` will be multiplied by this weight. Default is 1.0. Stored as `ctypes.c_float` for memory efficiency.
        *   `stats (ScoringStats)`: [Read-only] - An instance of `ScoringStats` that tracks statistics for this scorer (number of URLs scored, total score, min/max scores).

*   **4.2. `KeywordRelevanceScorer`**
    *   Source: `crawl4ai/deep_crawling/scorers.py`
    *   4.2.1. Purpose: Scores URLs based on the presence and frequency of specified keywords within the URL string itself.
    *   4.2.2. Inheritance: `URLScorer`
    *   4.2.3. Initialization (`__init__`)
        *   4.2.3.1. Signature:
            ```python
            def __init__(self, keywords: List[str], weight: float = 1.0, case_sensitive: bool = False):
            ```
        *   4.2.3.2. Parameters:
            *   `keywords (List[str])`: A list of keyword strings to search for in the URL.
            *   `weight (float`, default: `1.0`)`: The weight to apply to the calculated score.
            *   `case_sensitive (bool`, default: `False`)`: If `True`, keyword matching is case-sensitive. Otherwise, both the URL and keywords are converted to lowercase for matching.
    *   4.2.4. Key Implemented Methods:
        *   `_calculate_score(self, url: str) -> float`:
            *   Description: Counts how many of the provided `keywords` are present in the `url`. The score is the ratio of matched keywords to the total number of keywords (0.0 to 1.0).
    *   4.2.5. Helper Methods:
        *   `_url_bytes(self, url: str) -> bytes`: [Cached] Converts URL to bytes, lowercasing if not case-sensitive.

*   **4.3. `PathDepthScorer`**
    *   Source: `crawl4ai/deep_crawling/scorers.py`
    *   4.3.1. Purpose: Scores URLs based on their path depth (number of segments in the URL path). It favors URLs closer to an `optimal_depth`.
    *   4.3.2. Inheritance: `URLScorer`
    *   4.3.3. Initialization (`__init__`)
        *   4.3.3.1. Signature:
            ```python
            def __init__(self, optimal_depth: int = 3, weight: float = 1.0):
            ```
        *   4.3.3.2. Parameters:
            *   `optimal_depth (int`, default: `3`)`: The path depth considered ideal. URLs at this depth get the highest score.
            *   `weight (float`, default: `1.0`)`: The weight to apply to the calculated score.
    *   4.3.4. Key Implemented Methods:
        *   `_calculate_score(self, url: str) -> float`:
            *   Description: Calculates the path depth of the URL. The score is `1.0 / (1.0 + abs(depth - optimal_depth))`, meaning URLs at `optimal_depth` score 1.0, and scores decrease as depth deviates. Uses a lookup table for common small differences for speed.
    *   4.3.5. Static Methods:
        *   `_quick_depth(path: str) -> int`: [Cached] Efficiently calculates path depth without full URL parsing.

*   **4.4. `ContentTypeScorer`**
    *   Source: `crawl4ai/deep_crawling/scorers.py`
    *   4.4.1. Purpose: Scores URLs based on their inferred content type, typically derived from the file extension.
    *   4.4.2. Inheritance: `URLScorer`
    *   4.4.3. Initialization (`__init__`)
        *   4.4.3.1. Signature:
            ```python
            def __init__(self, type_weights: Dict[str, float], weight: float = 1.0):
            ```
        *   4.4.3.2. Parameters:
            *   `type_weights (Dict[str, float])`: A dictionary mapping file extensions (e.g., "html", "pdf") or MIME type patterns (e.g., "text/html", "image/") to scores. Patterns ending with '$' are treated as exact extension matches.
            *   `weight (float`, default: `1.0`)`: The weight to apply to the calculated score.
    *   4.4.4. Key Implemented Methods:
        *   `_calculate_score(self, url: str) -> float`:
            *   Description: Extracts the file extension from the URL. Looks up the score in `type_weights` first by exact extension match (if pattern ends with '$'), then by general extension. If no direct match, it might try matching broader MIME type categories if defined in `type_weights`. Returns 0.0 if no match found.
    *   4.4.5. Static Methods:
        *   `_quick_extension(url: str) -> str`: [Cached] Efficiently extracts file extension.

*   **4.5. `FreshnessScorer`**
    *   Source: `crawl4ai/deep_crawling/scorers.py`
    *   4.5.1. Purpose: Scores URLs based on dates found within the URL string, giving higher scores to more recent dates.
    *   4.5.2. Inheritance: `URLScorer`
    *   4.5.3. Initialization (`__init__`)
        *   4.5.3.1. Signature:
            ```python
            def __init__(self, weight: float = 1.0, current_year: int = [datetime.date.today().year]): # Actual default is dynamic
            ```
        *   4.5.3.2. Parameters:
            *   `weight (float`, default: `1.0`)`: The weight to apply to the calculated score.
            *   `current_year (int`, default: `datetime.date.today().year`)`: The reference year to calculate freshness against.
    *   4.5.4. Key Implemented Methods:
        *   `_calculate_score(self, url: str) -> float`:
            *   Description: Uses a regex to find year patterns (YYYY) in the URL. If multiple years are found, it uses the latest valid year. The score is higher for years closer to `current_year`, using a predefined lookup for small differences or a decay function for larger differences. If no year is found, a default score (0.5) is returned.
    *   4.5.5. Helper Methods:
        *   `_extract_year(self, url: str) -> Optional[int]`: [Cached] Extracts the most recent valid year from the URL.

*   **4.6. `DomainAuthorityScorer`**
    *   Source: `crawl4ai/deep_crawling/scorers.py`
    *   4.6.1. Purpose: Scores URLs based on a predefined list of domain authority weights. This allows prioritizing or de-prioritizing URLs from specific domains.
    *   4.6.2. Inheritance: `URLScorer`
    *   4.6.3. Initialization (`__init__`)
        *   4.6.3.1. Signature:
            ```python
            def __init__(
                self,
                domain_weights: Dict[str, float],
                default_weight: float = 0.5,
                weight: float = 1.0,
            ):
            ```
        *   4.6.3.2. Parameters:
            *   `domain_weights (Dict[str, float])`: A dictionary mapping domain names (e.g., "example.com") to their authority scores (typically between 0.0 and 1.0).
            *   `default_weight (float`, default: `0.5`)`: The score to assign to URLs whose domain is not found in `domain_weights`.
            *   `weight (float`, default: `1.0`)`: The overall weight to apply to the calculated score.
    *   4.6.4. Key Implemented Methods:
        *   `_calculate_score(self, url: str) -> float`:
            *   Description: Extracts the domain from the URL. If the domain is in `_domain_weights`, its corresponding score is returned. Otherwise, `_default_weight` is returned. Prioritizes top domains for faster lookup.
    *   4.6.5. Static Methods:
        *   `_extract_domain(url: str) -> str`: [Cached] Efficiently extracts the domain from a URL.

*   **4.7. `CompositeScorer`**
    *   Source: `crawl4ai/deep_crawling/scorers.py`
    *   4.7.1. Purpose: Combines the scores from multiple `URLScorer` instances. Each constituent scorer contributes its weighted score to the final composite score.
    *   4.7.2. Inheritance: `URLScorer`
    *   4.7.3. Initialization (`__init__`)
        *   4.7.3.1. Signature:
            ```python
            def __init__(self, scorers: List[URLScorer], normalize: bool = True):
            ```
        *   4.7.3.2. Parameters:
            *   `scorers (List[URLScorer])`: A list of `URLScorer` instances to be combined.
            *   `normalize (bool`, default: `True`)`: If `True`, the final composite score is normalized by dividing the sum of weighted scores by the number of scorers. This can help keep scores in a more consistent range.
    *   4.7.4. Key Implemented Methods:
        *   `_calculate_score(self, url: str) -> float`:
            *   Description: Iterates through all scorers in its list, calls their `score(url)` method (which applies individual weights), and sums up these scores. If `normalize` is `True`, divides the total sum by the number of scorers.
    *   4.7.5. Key Concrete Methods (overrides `URLScorer.score`):
        *   `score(self, url: str) -> float`:
            *   Description: Calculates the composite score and updates its own `ScoringStats`. Note: The individual scorers' stats are updated when their `score` methods are called internally.

*   **4.8. `ScoringStats` Data Class**
    *   Source: `crawl4ai/deep_crawling/scorers.py`
    *   4.8.1. Purpose: A data class to track statistics for URL scoring operations, including the number of URLs scored, total score, and min/max scores.
    *   4.8.2. Fields:
        *   `_urls_scored (int)`: Count of URLs scored.
        *   `_total_score (float)`: Sum of all scores.
        *   `_min_score (Optional[float])`: Minimum score encountered.
        *   `_max_score (Optional[float])`: Maximum score encountered.
    *   4.8.3. Key Methods:
        *   `update(self, score: float) -> None`: Updates the statistics with a new score.
        *   `get_average(self) -> float`: Calculates and returns the average score.
        *   `get_min(self) -> float`: Lazily initializes and returns the minimum score.
        *   `get_max(self) -> float`: Lazily initializes and returns the maximum score.

## 5. `DeepCrawlDecorator`

*   Source: `crawl4ai/deep_crawling/base_strategy.py`
*   5.1. Purpose: A decorator class that transparently adds deep crawling functionality to the `AsyncWebCrawler.arun` method if a `deep_crawl_strategy` is specified in the `CrawlerRunConfig`.
*   5.2. Initialization (`__init__`)
    *   5.2.1. Signature:
        ```python
        def __init__(self, crawler: AsyncWebCrawler):
        ```
    *   5.2.2. Parameters:
        *   `crawler (AsyncWebCrawler)`: The `AsyncWebCrawler` instance whose `arun` method is to be decorated.
*   5.3. `__call__` Method
    *   5.3.1. Signature:
        ```python
        @wraps(original_arun)
        async def wrapped_arun(url: str, config: CrawlerRunConfig = None, **kwargs):
        ```
    *   5.3.2. Functionality: This method wraps the original `arun` method of the `AsyncWebCrawler`.
        *   It checks if `config` is provided, has a `deep_crawl_strategy` set, and if `DeepCrawlDecorator.deep_crawl_active` context variable is `False` (to prevent recursion).
        *   If these conditions are met:
            *   It sets `DeepCrawlDecorator.deep_crawl_active` to `True`.
            *   It calls the `arun` method of the specified `config.deep_crawl_strategy`.
            *   It handles potential streaming results from the strategy by wrapping them in an async generator.
            *   Finally, it resets `DeepCrawlDecorator.deep_crawl_active` to `False`.
        *   If the conditions are not met, it calls the original `arun` method of the crawler.
*   5.4. Class Variable:
    *   `deep_crawl_active (ContextVar)`:
        *   Purpose: A `contextvars.ContextVar` used as a flag to indicate if a deep crawl is currently in progress for the current asynchronous context. This prevents the decorator from re-triggering deep crawling if the strategy itself calls the crawler's `arun` or `arun_many` methods.
        *   Default Value: `False`.

## 6. `TraversalStats` Data Model

*   Source: `crawl4ai/models.py`
*   6.1. Purpose: A data class for storing and tracking statistics related to a deep crawl traversal.
*   6.2. Fields:
    *   `start_time (datetime)`: The timestamp (Python `datetime` object) when the traversal process began. Default: `datetime.now()`.
    *   `end_time (Optional[datetime])`: The timestamp when the traversal process completed. Default: `None`.
    *   `urls_processed (int)`: The total number of URLs that were successfully fetched and processed. Default: `0`.
    *   `urls_failed (int)`: The total number of URLs that resulted in an error during fetching or processing. Default: `0`.
    *   `urls_skipped (int)`: The total number of URLs that were skipped (e.g., due to filters, already visited, or depth limits). Default: `0`.
    *   `total_depth_reached (int)`: The maximum depth reached from the start URL during the crawl. Default: `0`.
    *   `current_depth (int)`: The current depth level being processed by the crawler (can fluctuate during the crawl, especially for BFS). Default: `0`.

## 7. Configuration for Deep Crawling (`CrawlerRunConfig`)

*   Source: `crawl4ai/async_configs.py`
*   7.1. Purpose: `CrawlerRunConfig` is the primary configuration object passed to `AsyncWebCrawler.arun()` and `AsyncWebCrawler.arun_many()`. It contains various settings that control the behavior of a single crawl run, including those specific to deep crawling.
*   7.2. Relevant Fields:
    *   `deep_crawl_strategy (Optional[DeepCrawlStrategy])`:
        *   Type: `Optional[DeepCrawlStrategy]` (where `DeepCrawlStrategy` is the ABC from `crawl4ai.deep_crawling.base_strategy`)
        *   Default: `None`
        *   Description: Specifies the deep crawling strategy instance (e.g., `BFSDeepCrawlStrategy`, `DFSDeepCrawlStrategy`, `BestFirstCrawlingStrategy`) to be used for the crawl. If `None`, deep crawling is disabled, and only the initial URL(s) will be processed.
    *   *Note: Parameters like `max_depth`, `max_pages`, `filter_chain`, `url_scorer`, `score_threshold`, and `include_external` are not direct attributes of `CrawlerRunConfig` for deep crawling. Instead, they are passed to the constructor of the chosen `DeepCrawlStrategy` instance, which is then assigned to `CrawlerRunConfig.deep_crawl_strategy`.*

## 8. Utility Functions

*   **8.1. `normalize_url_for_deep_crawl(url: str, source_url: str) -> str`**
    *   Source: `crawl4ai/deep_crawling/utils.py` (or `crawl4ai/utils.py` if it's a general utility)
    *   8.1.1. Purpose: Normalizes a URL found during deep crawling. This typically involves resolving relative URLs against the `source_url` to create absolute URLs and removing URL fragments (`#fragment`).
    *   8.1.2. Signature: `def normalize_url_for_deep_crawl(url: str, source_url: str) -> str:`
    *   8.1.3. Parameters:
        *   `url (str)`: The URL string to be normalized.
        *   `source_url (str)`: The URL of the page where the `url` was discovered. This is used as the base for resolving relative paths.
    *   8.1.4. Returns: `(str)` - The normalized, absolute URL without fragments.

*   **8.2. `efficient_normalize_url_for_deep_crawl(url: str, source_url: str) -> str`**
    *   Source: `crawl4ai/deep_crawling/utils.py` (or `crawl4ai/utils.py`)
    *   8.2.1. Purpose: Provides a potentially more performant version of URL normalization specifically for deep crawling scenarios, likely employing optimizations to avoid repeated or complex parsing operations. (Note: Based on the provided code, this appears to be the same as `normalize_url_for_deep_crawl` if only one is present, or it might contain specific internal optimizations not exposed differently at the API level but used by strategies).
    *   8.2.2. Signature: `def efficient_normalize_url_for_deep_crawl(url: str, source_url: str) -> str:`
    *   8.2.3. Parameters:
        *   `url (str)`: The URL string to be normalized.
        *   `source_url (str)`: The URL of the page where the `url` was discovered.
    *   8.2.4. Returns: `(str)` - The normalized, absolute URL, typically without fragments.

## 9. PDF Processing Integration (`crawl4ai.processors.pdf`)
    *   9.1. Overview of PDF processing in Crawl4ai: While not directly part of the `deep_crawling` package, PDF processing components can be used in conjunction if a deep crawl discovers PDF URLs and they need to be processed. The `PDFCrawlerStrategy` can fetch PDFs, and `PDFContentScrapingStrategy` can extract content from them.
    *   **9.2. `PDFCrawlerStrategy`**
        *   Source: `crawl4ai/processors/pdf/__init__.py`
        *   9.2.1. Purpose: An `AsyncCrawlerStrategy` designed to "crawl" PDF files. In practice, this usually means downloading the PDF content. It returns a minimal `AsyncCrawlResponse` that signals to a `ContentScrapingStrategy` (like `PDFContentScrapingStrategy`) that the content is a PDF.
        *   9.2.2. Inheritance: `AsyncCrawlerStrategy`
        *   9.2.3. Initialization (`__init__`)
            *   9.2.3.1. Signature: `def __init__(self, logger: AsyncLogger = None):`
            *   9.2.3.2. Parameters:
                *   `logger (AsyncLogger`, default: `None`)`: An optional logger instance.
        *   9.2.4. Key Methods:
            *   `async def crawl(self, url: str, **kwargs) -> AsyncCrawlResponse`:
                *   Description: For a PDF URL, this method typically signifies that the URL points to a PDF. It constructs an `AsyncCrawlResponse` with a `Content-Type` header of `application/pdf` and a placeholder HTML. The actual PDF processing (downloading and content extraction) is usually handled by a subsequent scraping strategy.
    *   **9.3. `PDFContentScrapingStrategy`**
        *   Source: `crawl4ai/processors/pdf/__init__.py`
        *   9.3.1. Purpose: A `ContentScrapingStrategy` specialized in extracting text, images (optional), and metadata from PDF files. It uses a `PDFProcessorStrategy` (like `NaivePDFProcessorStrategy`) internally.
        *   9.3.2. Inheritance: `ContentScrapingStrategy`
        *   9.3.3. Initialization (`__init__`)
            *   9.3.3.1. Signature:
                ```python
                def __init__(self,
                             save_images_locally: bool = False,
                             extract_images: bool = False,
                             image_save_dir: str = None,
                             batch_size: int = 4,
                             logger: AsyncLogger = None):
                ```
            *   9.3.3.2. Parameters:
                *   `save_images_locally (bool`, default: `False`)`: If `True`, extracted images will be saved to the local disk.
                *   `extract_images (bool`, default: `False`)`: If `True`, attempts to extract images from the PDF.
                *   `image_save_dir (str`, default: `None`)`: The directory where extracted images will be saved if `save_images_locally` is `True`.
                *   `batch_size (int`, default: `4`)`: The number of PDF pages to process in parallel batches (if the underlying processor supports it).
                *   `logger (AsyncLogger`, default: `None`)`: An optional logger instance.
        *   9.3.4. Key Methods:
            *   `scrape(self, url: str, html: str, **params) -> ScrapingResult`:
                *   Description: Takes the URL (which should point to a PDF or a local PDF path) and processes it. It downloads the PDF if it's a remote URL, then uses the internal `pdf_processor` to extract content. It formats the extracted text into basic HTML and collects image and link information.
            *   `async def ascrape(self, url: str, html: str, **kwargs) -> ScrapingResult`:
                *   Description: Asynchronous version of the `scrape` method, typically by running the synchronous `scrape` method in a separate thread.
        *   9.3.5. Helper Methods:
            *   `_get_pdf_path(self, url: str) -> str`: Downloads a PDF from a URL to a temporary file if it's not a local path.
    *   **9.4. `NaivePDFProcessorStrategy`**
        *   Source: `crawl4ai/processors/pdf/processor.py`
        *   9.4.1. Purpose: A concrete implementation of `PDFProcessorStrategy` that uses `PyPDF2` (or similar libraries if extended) to extract text, images, and metadata from PDF documents page by page or in batches.
        *   9.4.2. Initialization (`__init__`)
            *   Signature: `def __init__(self, image_dpi: int = 144, image_quality: int = 85, extract_images: bool = True, save_images_locally: bool = False, image_save_dir: Optional[Path] = None, batch_size: int = 4)`
            *   Parameters: [Details parameters for image extraction quality, saving, and batch processing size.]
        *   9.4.3. Key Methods:
            *   `process(self, pdf_path: Path) -> PDFProcessResult`:
                *   Description: Processes a single PDF file sequentially, page by page. Extracts metadata, text, and optionally images from each page.
            *   `process_batch(self, pdf_path: Path) -> PDFProcessResult`:
                *   Description: Processes a PDF file by dividing its pages into batches and processing these batches in parallel using a thread pool, potentially speeding up extraction for large PDFs.
        *   9.4.4. Helper Methods:
            *   `_process_page(self, page, image_dir: Optional[Path]) -> PDFPage`: Processes a single PDF page object.
            *   `_extract_images(self, page, image_dir: Optional[Path]) -> List[Dict]`: Extracts images from a page.
            *   `_extract_links(self, page) -> List[str]`: Extracts hyperlinks from a page.
            *   `_extract_metadata(self, pdf_path: Path, reader=None) -> PDFMetadata`: Extracts metadata from the PDF.
    *   **9.5. PDF Data Models**
        *   Source: `crawl4ai/processors/pdf/processor.py`
        *   9.5.1. `PDFMetadata`:
            *   Purpose: Stores metadata extracted from a PDF document.
            *   Fields:
                *   `title (Optional[str])`: The title of the PDF.
                *   `author (Optional[str])`: The author(s) of the PDF.
                *   `producer (Optional[str])`: The software used to produce the PDF.
                *   `created (Optional[datetime])`: The creation date of the PDF.
                *   `modified (Optional[datetime])`: The last modification date of the PDF.
                *   `pages (int)`: The total number of pages in the PDF. Default: `0`.
                *   `encrypted (bool)`: `True` if the PDF is encrypted, `False` otherwise. Default: `False`.
                *   `file_size (Optional[int])`: The size of the PDF file in bytes. Default: `None`.
        *   9.5.2. `PDFPage`:
            *   Purpose: Stores content extracted from a single page of a PDF document.
            *   Fields:
                *   `page_number (int)`: The page number (1-indexed).
                *   `raw_text (str)`: The raw text extracted from the page. Default: `""`.
                *   `markdown (str)`: Markdown representation of the page content. Default: `""`.
                *   `html (str)`: Basic HTML representation of the page content. Default: `""`.
                *   `images (List[Dict])`: A list of dictionaries, each representing an extracted image with details like format, path/data, dimensions. Default: `[]`.
                *   `links (List[str])`: A list of hyperlink URLs found on the page. Default: `[]`.
                *   `layout (List[Dict])`: Information about the layout of text elements on the page (e.g., coordinates). Default: `[]`.
        *   9.5.3. `PDFProcessResult`:
            *   Purpose: Encapsulates the results of processing a PDF document.
            *   Fields:
                *   `metadata (PDFMetadata)`: The metadata of the processed PDF.
                *   `pages (List[PDFPage])`: A list of `PDFPage` objects, one for each page processed.
                *   `processing_time (float)`: The time taken to process the PDF, in seconds. Default: `0.0`.
                *   `version (str)`: The version of the PDF processor. Default: `"1.1"`.

## 10. Version Information (`crawl4ai.__version__`)
*   Source: `crawl4ai/__version__.py`
*   10.1. `__version__ (str)`: A string representing the current installed version of the `crawl4ai` library (e.g., "0.6.3").

## 11. Asynchronous Configuration (`crawl4ai.async_configs`)
    *   11.1. Overview: The `crawl4ai.async_configs` module contains configuration classes used throughout the library, including those relevant for network requests like proxies (`ProxyConfig`) and general crawler/browser behavior.
    *   **11.2. `ProxyConfig`**
        *   Source: `crawl4ai/async_configs.py` (and `crawl4ai/proxy_strategy.py`)
        *   11.2.1. Purpose: Represents the configuration for a single proxy server, including its address, port, and optional authentication credentials.
        *   11.2.2. Initialization (`__init__`)
            *   11.2.2.1. Signature:
                ```python
                def __init__(
                    self,
                    server: str,
                    username: Optional[str] = None,
                    password: Optional[str] = None,
                    ip: Optional[str] = None,
                ):
                ```
            *   11.2.2.2. Parameters:
                *   `server (str)`: The proxy server URL (e.g., "http://proxy.example.com:8080", "socks5://proxy.example.com:1080").
                *   `username (Optional[str]`, default: `None`)`: The username for proxy authentication, if required.
                *   `password (Optional[str]`, default: `None`)`: The password for proxy authentication, if required.
                *   `ip (Optional[str]`, default: `None`)`: Optionally, the specific IP address of the proxy server. If not provided, it's inferred from the `server` URL.
        *   11.2.3. Key Static Methods:
            *   `from_string(proxy_str: str) -> ProxyConfig`:
                *   Description: Creates a `ProxyConfig` instance from a string representation. Expected format is "ip:port:username:password" or "ip:port".
                *   Returns: `(ProxyConfig)`
            *   `from_dict(proxy_dict: Dict) -> ProxyConfig`:
                *   Description: Creates a `ProxyConfig` instance from a dictionary.
                *   Returns: `(ProxyConfig)`
            *   `from_env(env_var: str = "PROXIES") -> List[ProxyConfig]`:
                *   Description: Loads a list of proxy configurations from a comma-separated string in an environment variable.
                *   Returns: `(List[ProxyConfig])`
        *   11.2.4. Key Methods:
            *   `to_dict(self) -> Dict`: Converts the `ProxyConfig` instance to a dictionary.
            *   `clone(self, **kwargs) -> ProxyConfig`: Creates a copy of the instance, optionally updating attributes with `kwargs`.

    *   **11.3. `ProxyRotationStrategy` (ABC)**
        *   Source: `crawl4ai/proxy_strategy.py`
        *   11.3.1. Purpose: Abstract base class defining the interface for proxy rotation strategies.
        *   11.3.2. Key Abstract Methods:
            *   `async def get_next_proxy(self) -> Optional[ProxyConfig]`: Asynchronously gets the next `ProxyConfig` from the strategy.
            *   `def add_proxies(self, proxies: List[ProxyConfig])`: Adds a list of `ProxyConfig` objects to the strategy's pool.
    *   **11.4. `RoundRobinProxyStrategy`**
        *   Source: `crawl4ai/proxy_strategy.py`
        *   11.4.1. Purpose: A simple proxy rotation strategy that cycles through a list of proxies in a round-robin fashion.
        *   11.4.2. Inheritance: `ProxyRotationStrategy`
        *   11.4.3. Initialization (`__init__`)
            *   11.4.3.1. Signature: `def __init__(self, proxies: List[ProxyConfig] = None):`
            *   11.4.3.2. Parameters:
                *   `proxies (List[ProxyConfig]`, default: `None`)`: An optional initial list of `ProxyConfig` objects.
        *   11.4.4. Key Implemented Methods:
            *   `add_proxies(self, proxies: List[ProxyConfig])`: Adds new proxies to the internal list and reinitializes the cycle.
            *   `async def get_next_proxy(self) -> Optional[ProxyConfig]`: Returns the next proxy from the cycle. Returns `None` if no proxies are available.

## 12. HTML to Markdown Conversion (`crawl4ai.markdown_generation_strategy`)
    *   12.1. `MarkdownGenerationStrategy` (ABC)
        *   Source: `crawl4ai/markdown_generation_strategy.py`
        *   12.1.1. Purpose: Abstract base class defining the interface for strategies that convert HTML content to Markdown.
        *   12.1.2. Key Abstract Methods:
            *   `generate_markdown(self, input_html: str, base_url: str = "", html2text_options: Optional[Dict[str, Any]] = None, content_filter: Optional[RelevantContentFilter] = None, citations: bool = True, **kwargs) -> MarkdownGenerationResult`:
                *   Description: Abstract method to convert the given `input_html` string into a `MarkdownGenerationResult` object.
                *   Parameters:
                    *   `input_html (str)`: The HTML content to convert.
                    *   `base_url (str`, default: `""`)`: The base URL used for resolving relative links within the HTML.
                    *   `html2text_options (Optional[Dict[str, Any]]`, default: `None`)`: Options to pass to the underlying HTML-to-text conversion library.
                    *   `content_filter (Optional[RelevantContentFilter]`, default: `None`)`: An optional filter to apply to the HTML before Markdown conversion, potentially to extract only relevant parts.
                    *   `citations (bool`, default: `True`)`: If `True`, attempts to convert hyperlinks into Markdown citations with a reference list.
                    *   `**kwargs`: Additional keyword arguments.
                *   Returns: `(MarkdownGenerationResult)`
    *   12.2. `DefaultMarkdownGenerator`
        *   Source: `crawl4ai/markdown_generation_strategy.py`
        *   12.2.1. Purpose: The default implementation of `MarkdownGenerationStrategy`. It uses the `CustomHTML2Text` class (an enhanced `html2text.HTML2Text`) for the primary conversion and can optionally apply a `RelevantContentFilter`.
        *   12.2.2. Inheritance: `MarkdownGenerationStrategy`
        *   12.2.3. Initialization (`__init__`)
            *   12.2.3.1. Signature:
                ```python
                def __init__(
                    self,
                    content_filter: Optional[RelevantContentFilter] = None,
                    options: Optional[Dict[str, Any]] = None,
                    content_source: str = "cleaned_html", # "raw_html", "fit_html"
                ):
                ```
            *   12.2.3.2. Parameters:
                *   `content_filter (Optional[RelevantContentFilter]`, default: `None`)`: An instance of a content filter strategy (e.g., `BM25ContentFilter`, `PruningContentFilter`) to be applied to the `input_html` before Markdown conversion. If `None`, no pre-filtering is done.
                *   `options (Optional[Dict[str, Any]]`, default: `None`)`: A dictionary of options to configure the `CustomHTML2Text` converter (e.g., `{"body_width": 0, "ignore_links": False}`).
                *   `content_source (str`, default: `"cleaned_html"`)`: Specifies which HTML source to use for Markdown generation if multiple are available (e.g., from `CrawlResult`). Options: `"cleaned_html"` (default), `"raw_html"`, `"fit_html"`. This parameter is primarily used when the generator is part of a larger crawling pipeline.
        *   12.2.4. Key Methods:
            *   `generate_markdown(self, input_html: str, base_url: str = "", html2text_options: Optional[Dict[str, Any]] = None, content_filter: Optional[RelevantContentFilter] = None, citations: bool = True, **kwargs) -> MarkdownGenerationResult`:
                *   Description: Converts HTML to Markdown. If a `content_filter` is provided (either at init or as an argument), it's applied first to get "fit_html". Then, `CustomHTML2Text` converts the chosen HTML (input_html or fit_html) to raw Markdown. If `citations` is True, links in the raw Markdown are converted to citation format.
                *   Returns: `(MarkdownGenerationResult)`
            *   `convert_links_to_citations(self, markdown: str, base_url: str = "") -> Tuple[str, str]`:
                *   Description: Parses Markdown text, identifies links, replaces them with citation markers (e.g., `[text]^(1)`), and generates a corresponding list of references.
                *   Returns: `(Tuple[str, str])` - A tuple containing the Markdown with citations and the Markdown string of references.

## 13. Content Filtering (`crawl4ai.content_filter_strategy`)
    *   13.1. `RelevantContentFilter` (ABC)
        *   Source: `crawl4ai/content_filter_strategy.py`
        *   13.1.1. Purpose: Abstract base class for strategies that filter HTML content to extract only the most relevant parts, typically before Markdown conversion or further processing.
        *   13.1.2. Key Abstract Methods:
            *   `filter_content(self, html: str) -> List[str]`:
                *   Description: Abstract method that takes an HTML string and returns a list of strings, where each string is a chunk of HTML deemed relevant.
    *   13.2. `BM25ContentFilter`
        *   Source: `crawl4ai/content_filter_strategy.py`
        *   13.2.1. Purpose: Filters HTML content by extracting text chunks and scoring their relevance to a user query (or an inferred page query) using the BM25 algorithm.
        *   13.2.2. Inheritance: `RelevantContentFilter`
        *   13.2.3. Initialization (`__init__`)
            *   13.2.3.1. Signature:
                ```python
                def __init__(
                    self,
                    user_query: Optional[str] = None,
                    bm25_threshold: float = 1.0,
                    language: str = "english",
                ):
                ```
            *   13.2.3.2. Parameters:
                *   `user_query (Optional[str]`, default: `None`)`: The query to compare content against. If `None`, the filter attempts to extract a query from the page's metadata.
                *   `bm25_threshold (float`, default: `1.0`)`: The minimum BM25 score for a text chunk to be considered relevant.
                *   `language (str`, default: `"english"`)`: The language used for stemming tokens.
        *   13.2.4. Key Implemented Methods:
            *   `filter_content(self, html: str, min_word_threshold: int = None) -> List[str]`: Parses HTML, extracts text chunks (paragraphs, list items, etc.), scores them with BM25 against the query, and returns the HTML of chunks exceeding the threshold.
    *   13.3. `PruningContentFilter`
        *   Source: `crawl4ai/content_filter_strategy.py`
        *   13.3.1. Purpose: Filters HTML content by recursively pruning less relevant parts of the DOM tree based on a composite score (text density, link density, tag weights, etc.).
        *   13.3.2. Inheritance: `RelevantContentFilter`
        *   13.3.3. Initialization (`__init__`)
            *   13.3.3.1. Signature:
                ```python
                def __init__(
                    self,
                    user_query: Optional[str] = None,
                    min_word_threshold: Optional[int] = None,
                    threshold_type: str = "fixed", # or "dynamic"
                    threshold: float = 0.48,
                ):
                ```
            *   13.3.3.2. Parameters:
                *   `user_query (Optional[str]`, default: `None`)`: [Not directly used by pruning logic but inherited].
                *   `min_word_threshold (Optional[int]`, default: `None`)`: Minimum word count for an element to be considered for scoring initially (default behavior might be more nuanced).
                *   `threshold_type (str`, default: `"fixed"`)`: Specifies how the `threshold` is applied. "fixed" uses the direct value. "dynamic" adjusts the threshold based on content characteristics.
                *   `threshold (float`, default: `0.48`)`: The score threshold for pruning. Elements below this score are removed.
        *   13.3.4. Key Implemented Methods:
            *   `filter_content(self, html: str, min_word_threshold: int = None) -> List[str]`: Parses HTML, applies the pruning algorithm to the body, and returns the remaining significant HTML blocks as a list of strings.
    *   13.4. `LLMContentFilter`
        *   Source: `crawl4ai/content_filter_strategy.py`
        *   13.4.1. Purpose: Uses a Large Language Model (LLM) to determine the relevance of HTML content chunks based on a given instruction.
        *   13.4.2. Inheritance: `RelevantContentFilter`
        *   13.4.3. Initialization (`__init__`)
            *   13.4.3.1. Signature:
                ```python
                def __init__(
                    self,
                    llm_config: Optional[LLMConfig] = None,
                    instruction: Optional[str] = None,
                    chunk_token_threshold: int = CHUNK_TOKEN_THRESHOLD, # Default from config
                    overlap_rate: float = OVERLAP_RATE,            # Default from config
                    word_token_rate: float = WORD_TOKEN_RATE,        # Default from config
                    verbose: bool = False,
                    logger: Optional[AsyncLogger] = None,
                    ignore_cache: bool = True
                ):
                ```
            *   13.4.3.2. Parameters:
                *   `llm_config (Optional[LLMConfig])`: Configuration for the LLM (provider, API key, model, etc.).
                *   `instruction (Optional[str])`: The instruction given to the LLM to guide content filtering (e.g., "Extract only the main article content, excluding headers, footers, and ads.").
                *   `chunk_token_threshold (int)`: Maximum number of tokens per chunk sent to the LLM.
                *   `overlap_rate (float)`: Percentage of overlap between consecutive chunks.
                *   `word_token_rate (float)`: Estimated ratio of words to tokens, used for chunking.
                *   `verbose (bool`, default: `False`)`: Enables verbose logging for LLM operations.
                *   `logger (Optional[AsyncLogger]`, default: `None`)`: Custom logger instance.
                *   `ignore_cache (bool`, default: `True`)`: If `True`, bypasses any LLM response caching for this operation.
        *   13.4.4. Key Implemented Methods:
            *   `filter_content(self, html: str, ignore_cache: bool = True) -> List[str]`:
                *   Description: Chunks the input HTML. For each chunk, it sends a request to the configured LLM with the chunk and the `instruction`. The LLM is expected to return the relevant part of the chunk. These relevant parts are then collected and returned.
```

---


# Data Extraction - Memory
Source: crawl4ai_extraction_memory_content.llm.md

Okay, I will now generate the "Foundational Memory" document for the `extraction` component of `crawl4ai`, based on the outline you provided and the information I've processed from the codebase and existing documentation.

```markdown
# Detailed Outline for crawl4ai - extraction Component

**Target Document Type:** memory
**Target Output Filename Suggestion:** `llm_memory_extraction.md`
**Library Version Context:** 0.6.3
**Outline Generation Date:** 2024-05-24
---

## 1. Overview of Data Extraction in Crawl4ai

*   1.1. Purpose of the Extraction Component: The extraction component in Crawl4ai is responsible for parsing structured data from web content (HTML, text, Markdown) or PDF documents. It allows users to define how data should be identified and extracted, using various strategies ranging from rule-based (CSS, XPath, Regex) to LLM-powered approaches. Its goal is to transform raw crawled content into usable, structured information.
*   1.2. Core Concepts:
    *   1.2.1. `ExtractionStrategy`: This is an abstract base class (interface) that defines the contract for all specific extraction methods. Each strategy implements how data is extracted from the provided content.
    *   1.2.2. `ChunkingStrategy`: This is an abstract base class (interface) for strategies that preprocess content by splitting it into smaller, manageable chunks. This is particularly relevant for LLM-based extraction strategies that have token limits for their input.
    *   1.2.3. Schemas: Schemas define the structure of the data to be extracted. For non-LLM strategies like `JsonCssExtractionStrategy` or `JsonXPathExtractionStrategy`, schemas are typically dictionary-based, specifying selectors and field types. For `LLMExtractionStrategy`, schemas can be Pydantic models or JSON schema dictionaries that guide the LLM in structuring its output.
    *   1.2.4. `CrawlerRunConfig`: The `CrawlerRunConfig` object allows users to specify which `extraction_strategy` and `chunking_strategy` (if applicable) should be used for a particular crawl operation via its `arun()` method.

## 2. `ExtractionStrategy` Interface

*   2.1. Purpose: The `ExtractionStrategy` class, found in `crawl4ai.extraction_strategy`, serves as an abstract base class (ABC) defining the standard interface for all data extraction strategies within the Crawl4ai library. Implementations of this class provide specific methods for extracting structured data from content.
*   2.2. Key Abstract Methods:
    *   `extract(self, url: str, content: str, *q, **kwargs) -> List[Dict[str, Any]]`:
        *   Description: Abstract method intended to extract meaningful blocks or chunks from the given content. Subclasses must implement this.
        *   Parameters:
            *   `url (str)`: The URL of the webpage.
            *   `content (str)`: The HTML, Markdown, or text content of the webpage.
            *   `*q`: Variable positional arguments.
            *   `**kwargs`: Variable keyword arguments.
        *   Returns: `List[Dict[str, Any]]` - A list of extracted blocks or chunks, typically as dictionaries.
    *   `run(self, url: str, sections: List[str], *q, **kwargs) -> List[Dict[str, Any]]`:
        *   Description: Abstract method to process sections of text, often in parallel by default implementations in subclasses. Subclasses must implement this.
        *   Parameters:
            *   `url (str)`: The URL of the webpage.
            *   `sections (List[str])`: List of sections (strings) to process.
            *   `*q`: Variable positional arguments.
            *   `**kwargs`: Variable keyword arguments.
        *   Returns: `List[Dict[str, Any]]` - A list of processed JSON blocks.
*   2.3. Input Format Property:
    *   `input_format (str)`: [Read-only] - An attribute indicating the expected input format for the content to be processed by the strategy (e.g., "markdown", "html", "fit_html", "text"). Default is "markdown".

## 3. Non-LLM Based Extraction Strategies

*   ### 3.1. Class `NoExtractionStrategy`
    *   3.1.1. Purpose: A baseline `ExtractionStrategy` that performs no actual data extraction. It returns the input content as is, typically useful for scenarios where only raw or cleaned HTML/Markdown is needed without further structuring.
    *   3.1.2. Inheritance: `ExtractionStrategy`
    *   3.1.3. Initialization (`__init__`):
        *   3.1.3.1. Signature: `NoExtractionStrategy(**kwargs)`
        *   3.1.3.2. Parameters:
            *   `**kwargs`: Passed to the base `ExtractionStrategy` initializer.
    *   3.1.4. Key Public Methods:
        *   `extract(self, url: str, html: str, *q, **kwargs) -> List[Dict[str, Any]]`:
            *   Description: Returns the provided `html` content wrapped in a list containing a single dictionary: `[{"index": 0, "content": html}]`.
        *   `run(self, url: str, sections: List[str], *q, **kwargs) -> List[Dict[str, Any]]`:
            *   Description: Returns a list where each input section is wrapped in a dictionary: `[{"index": i, "tags": [], "content": section} for i, section in enumerate(sections)]`.

*   ### 3.2. Class `JsonCssExtractionStrategy`
    *   3.2.1. Purpose: Extracts structured data from HTML content using a JSON schema that defines CSS selectors to locate and extract data for specified fields. It uses BeautifulSoup4 for parsing and selection.
    *   3.2.2. Inheritance: `JsonElementExtractionStrategy` (which inherits from `ExtractionStrategy`)
    *   3.2.3. Initialization (`__init__`):
        *   3.2.3.1. Signature: `JsonCssExtractionStrategy(schema: Dict[str, Any], **kwargs)`
        *   3.2.3.2. Parameters:
            *   `schema (Dict[str, Any])`: The JSON schema defining extraction rules.
            *   `**kwargs`: Passed to the base class initializer. Includes `input_format` (default: "html").
    *   3.2.4. Schema Definition for `JsonCssExtractionStrategy`:
        *   3.2.4.1. `name (str)`: A descriptive name for the schema (e.g., "ProductDetails").
        *   3.2.4.2. `baseSelector (str)`: The primary CSS selector that identifies each root element representing an item to be extracted (e.g., "div.product-item").
        *   3.2.4.3. `fields (List[Dict[str, Any]])`: A list of dictionaries, each defining a field to be extracted from within each `baseSelector` element.
            *   Each field dictionary:
                *   `name (str)`: The key for this field in the output JSON object.
                *   `selector (str)`: The CSS selector for this field, relative to its parent element (either the `baseSelector` or a parent "nested" field).
                *   `type (str)`: Specifies how to extract the data. Common values:
                    *   `"text"`: Extracts the text content of the selected element.
                    *   `"attribute"`: Extracts the value of a specified HTML attribute.
                    *   `"html"`: Extracts the raw inner HTML of the selected element.
                    *   `"list"`: Extracts a list of items. The `fields` sub-key then defines the structure of each item in the list (if objects) or the `selector` directly targets list elements for primitive values.
                    *   `"nested"`: Extracts a nested JSON object. The `fields` sub-key defines the structure of this nested object.
                *   `attribute (str, Optional)`: Required if `type` is "attribute". Specifies the name of the HTML attribute to extract (e.g., "href", "src").
                *   `fields (List[Dict[str, Any]], Optional)`: Required if `type` is "list" (for a list of objects) or "nested". Defines the structure of the nested object or list items.
                *   `transform (str, Optional)`: A string indicating a transformation to apply to the extracted value (e.g., "lowercase", "uppercase", "strip").
                *   `default (Any, Optional)`: A default value to use if the selector does not find an element or the attribute is missing.
    *   3.2.5. Key Public Methods:
        *   `extract(self, url: str, html_content: str, *q, **kwargs) -> List[Dict[str, Any]]`:
            *   Description: Parses the `html_content` and applies the defined schema to extract structured data using CSS selectors.
    *   3.2.6. Features:
        *   3.2.6.1. Nested Extraction: Supports extracting complex, nested JSON objects by defining "nested" type fields within the schema.
        *   3.2.6.2. List Handling: Supports extracting lists of primitive values (e.g., list of strings from multiple `<li>` tags) or lists of structured objects (e.g., a list of product details, each with its own fields).

*   ### 3.3. Class `JsonXPathExtractionStrategy`
    *   3.3.1. Purpose: Extracts structured data from HTML/XML content using a JSON schema that defines XPath expressions to locate and extract data. It uses `lxml` for parsing and XPath evaluation.
    *   3.3.2. Inheritance: `JsonElementExtractionStrategy` (which inherits from `ExtractionStrategy`)
    *   3.3.3. Initialization (`__init__`):
        *   3.3.3.1. Signature: `JsonXPathExtractionStrategy(schema: Dict[str, Any], **kwargs)`
        *   3.3.3.2. Parameters:
            *   `schema (Dict[str, Any])`: The JSON schema defining extraction rules, where selectors are XPath expressions.
            *   `**kwargs`: Passed to the base class initializer. Includes `input_format` (default: "html").
    *   3.3.4. Schema Definition: The schema structure is identical to `JsonCssExtractionStrategy` (see 3.2.4), but the `baseSelector` and field `selector` values must be valid XPath expressions.
    *   3.3.5. Key Public Methods:
        *   `extract(self, url: str, html_content: str, *q, **kwargs) -> List[Dict[str, Any]]`:
            *   Description: Parses the `html_content` using `lxml` and applies the defined schema to extract structured data using XPath expressions.

*   ### 3.4. Class `JsonLxmlExtractionStrategy`
    *   3.4.1. Purpose: Provides an alternative CSS selector-based extraction strategy leveraging the `lxml` library for parsing and selection, which can offer performance benefits over BeautifulSoup4 in some cases.
    *   3.4.2. Inheritance: `JsonCssExtractionStrategy` (and thus `JsonElementExtractionStrategy`, `ExtractionStrategy`)
    *   3.4.3. Initialization (`__init__`):
        *   3.4.3.1. Signature: `JsonLxmlExtractionStrategy(schema: Dict[str, Any], **kwargs)`
        *   3.4.3.2. Parameters:
            *   `schema (Dict[str, Any])`: The JSON schema defining extraction rules, using CSS selectors.
            *   `**kwargs`: Passed to the base class initializer. Includes `input_format` (default: "html").
    *   3.4.4. Schema Definition: Identical to `JsonCssExtractionStrategy` (see 3.2.4).
    *   3.4.5. Key Public Methods:
        *   `extract(self, url: str, html_content: str, *q, **kwargs) -> List[Dict[str, Any]]`:
            *   Description: Parses the `html_content` using `lxml` and applies the defined schema to extract structured data using lxml's CSS selector capabilities (which often translates CSS to XPath internally).

*   ### 3.5. Class `RegexExtractionStrategy`
    *   3.5.1. Purpose: Extracts data from text content (HTML, Markdown, or plain text) using a collection of regular expression patterns. Each match is returned as a structured dictionary.
    *   3.5.2. Inheritance: `ExtractionStrategy`
    *   3.5.3. Initialization (`__init__`):
        *   3.5.3.1. Signature: `RegexExtractionStrategy(patterns: Union[Dict[str, str], List[Tuple[str, str]], "RegexExtractionStrategy._B"] = _B.NOTHING, input_format: str = "fit_html", **kwargs)`
        *   3.5.3.2. Parameters:
            *   `patterns (Union[Dict[str, str], List[Tuple[str, str]], "_B"], default: _B.NOTHING)`:
                *   Description: Defines the regex patterns to use.
                *   Can be a dictionary mapping labels to regex strings (e.g., `{"email": r"..."}`).
                *   Can be a list of (label, regex_string) tuples.
                *   Can be a bitwise OR combination of `RegexExtractionStrategy._B` enum members for using built-in patterns (e.g., `RegexExtractionStrategy.Email | RegexExtractionStrategy.Url`).
            *   `input_format (str, default: "fit_html")`: Specifies the input format for the content. Options: "html" (raw HTML), "markdown" (Markdown from HTML), "text" (plain text from HTML), "fit_html" (content filtered for relevance before regex application).
            *   `**kwargs`: Passed to the base `ExtractionStrategy`.
    *   3.5.4. Built-in Patterns (`RegexExtractionStrategy._B` Enum - an `IntFlag`):
        *   `EMAIL (auto())`: Matches email addresses. Example pattern: `r"[\\w.+-]+@[\\w-]+\\.[\\w.-]+"`
        *   `PHONE_INTL (auto())`: Matches international phone numbers. Example pattern: `r"\\+?\\d[\\d .()-]{7,}\\d"`
        *   `PHONE_US (auto())`: Matches US phone numbers. Example pattern: `r"\\(?\\d{3}\\)?[-. ]?\\d{3}[-. ]?\\d{4}"`
        *   `URL (auto())`: Matches URLs. Example pattern: `r"https?://[^\\s\\'\"<>]+"`
        *   `IPV4 (auto())`: Matches IPv4 addresses. Example pattern: `r"(?:\\d{1,3}\\.){3}\\d{1,3}"`
        *   `IPV6 (auto())`: Matches IPv6 addresses. Example pattern: `r"[A-F0-9]{1,4}(?::[A-F0-9]{1,4}){7}"`
        *   `UUID (auto())`: Matches UUIDs. Example pattern: `r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"`
        *   `CURRENCY (auto())`: Matches currency amounts. Example pattern: `r"(?:USD|EUR|RM|\\$|€|¥|£)\\s?\\d+(?:[.,]\\d{2})?"`
        *   `PERCENTAGE (auto())`: Matches percentages. Example pattern: `r"\\d+(?:\\.\\d+)?%"`
        *   `NUMBER (auto())`: Matches numbers (integers, decimals). Example pattern: `r"\\b\\d{1,3}(?:[,.]?\\d{3})*(?:\\.\\d+)?\\b"`
        *   `DATE_ISO (auto())`: Matches ISO 8601 dates (YYYY-MM-DD). Example pattern: `r"\\d{4}-\\d{2}-\\d{2}"`
        *   `DATE_US (auto())`: Matches US-style dates (MM/DD/YYYY or MM/DD/YY). Example pattern: `r"\\d{1,2}/\\d{1,2}/\\d{2,4}"`
        *   `TIME_24H (auto())`: Matches 24-hour time formats (HH:MM or HH:MM:SS). Example pattern: `r"\\b(?:[01]?\\d|2[0-3]):[0-5]\\d(?:[:.][0-5]\\d)?\\b"`
        *   `POSTAL_US (auto())`: Matches US postal codes (ZIP codes). Example pattern: `r"\\b\\d{5}(?:-\\d{4})?\\b"`
        *   `POSTAL_UK (auto())`: Matches UK postal codes. Example pattern: `r"\\b[A-Z]{1,2}\\d[A-Z\\d]? ?\\d[A-Z]{2}\\b"`
        *   `HTML_COLOR_HEX (auto())`: Matches HTML hex color codes. Example pattern: `r"#[0-9A-Fa-f]{6}\\b"`
        *   `TWITTER_HANDLE (auto())`: Matches Twitter handles. Example pattern: `r"@[\\w]{1,15}"`
        *   `HASHTAG (auto())`: Matches hashtags. Example pattern: `r"#[\\w-]+"`
        *   `MAC_ADDR (auto())`: Matches MAC addresses. Example pattern: `r"(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}"`
        *   `IBAN (auto())`: Matches IBANs. Example pattern: `r"[A-Z]{2}\\d{2}[A-Z0-9]{11,30}"`
        *   `CREDIT_CARD (auto())`: Matches common credit card numbers. Example pattern: `r"\\b(?:4\\d{12}(?:\\d{3})?|5[1-5]\\d{14}|3[47]\\d{13}|6(?:011|5\\d{2})\\d{12})\\b"`
        *   `ALL (_B(-1).value & ~_B.NOTHING.value)`: Includes all built-in patterns except `NOTHING`.
        *   `NOTHING (_B(0).value)`: Includes no built-in patterns.
    *   3.5.5. Key Public Methods:
        *   `extract(self, url: str, content: str, **kwargs) -> List[Dict[str, Any]]`:
            *   Description: Applies all configured regex patterns (built-in and custom) to the input `content`.
            *   Returns: `List[Dict[str, Any]]` - A list of dictionaries, where each dictionary represents a match and contains:
                *   `"url" (str)`: The source URL.
                *   `"label" (str)`: The label of the matching regex pattern.
                *   `"value" (str)`: The actual matched string.
                *   `"span" (Tuple[int, int])`: The start and end indices of the match within the content.
    *   3.5.6. Static Method: `generate_pattern`
        *   3.5.6.1. Signature: `staticmethod generate_pattern(label: str, html: str, query: Optional[str] = None, examples: Optional[List[str]] = None, llm_config: Optional[LLMConfig] = None, **kwargs) -> Dict[str, str]`
        *   3.5.6.2. Purpose: Uses an LLM to automatically generate a Python-compatible regular expression pattern for a given label, based on sample HTML content, an optional natural language query describing the target, and/or examples of desired matches.
        *   3.5.6.3. Parameters:
            *   `label (str)`: A descriptive label for the pattern to be generated (e.g., "product_price", "article_date").
            *   `html (str)`: The HTML content from which the pattern should be inferred.
            *   `query (Optional[str], default: None)`: A natural language description of what kind of data the regex should capture (e.g., "Extract the publication date", "Find all ISBN numbers").
            *   `examples (Optional[List[str]], default: None)`: A list of example strings that the generated regex should successfully match from the provided HTML.
            *   `llm_config (Optional[LLMConfig], default: None)`: Configuration for the LLM to be used. If `None`, uses default `LLMConfig`.
            *   `**kwargs`: Additional arguments passed to the LLM completion request (e.g., `temperature`, `max_tokens`).
        *   3.5.6.4. Returns: `Dict[str, str]` - A dictionary containing the generated pattern, in the format `{label: "regex_pattern_string"}`.

## 4. LLM-Based Extraction Strategies

*   ### 4.1. Class `LLMExtractionStrategy`
    *   4.1.1. Purpose: Employs Large Language Models (LLMs) to extract either structured data according to a schema or relevant blocks of text based on natural language instructions from various content formats (HTML, Markdown, text).
    *   4.1.2. Inheritance: `ExtractionStrategy`
    *   4.1.3. Initialization (`__init__`):
        *   4.1.3.1. Signature: `LLMExtractionStrategy(llm_config: Optional[LLMConfig] = None, instruction: Optional[str] = None, schema: Optional[Union[Dict[str, Any], "BaseModel"]] = None, extraction_type: str = "block", chunk_token_threshold: int = CHUNK_TOKEN_THRESHOLD, overlap_rate: float = OVERLAP_RATE, word_token_rate: float = WORD_TOKEN_RATE, apply_chunking: bool = True, force_json_response: bool = False, **kwargs)`
        *   4.1.3.2. Parameters:
            *   `llm_config (Optional[LLMConfig], default: None)`: Configuration for the LLM. If `None`, a default `LLMConfig` is created.
            *   `instruction (Optional[str], default: None)`: Natural language instructions to guide the LLM's extraction process (e.g., "Extract the main article content", "Summarize the key points").
            *   `schema (Optional[Union[Dict[str, Any], "BaseModel"]], default: None)`: A Pydantic model class or a dictionary representing a JSON schema. Used when `extraction_type` is "schema" to define the desired output structure.
            *   `extraction_type (str, default: "block")`: Determines the extraction mode.
                *   `"block"`: LLM identifies and extracts relevant blocks/chunks of text based on the `instruction`.
                *   `"schema"`: LLM attempts to populate the fields defined in `schema` from the content.
            *   `chunk_token_threshold (int, default: CHUNK_TOKEN_THRESHOLD)`: The target maximum number of tokens for each chunk of content sent to the LLM. `CHUNK_TOKEN_THRESHOLD` is defined in `crawl4ai.config` (default value: 10000).
            *   `overlap_rate (float, default: OVERLAP_RATE)`: The percentage of overlap between consecutive chunks to ensure context continuity. `OVERLAP_RATE` is defined in `crawl4ai.config` (default value: 0.1, i.e., 10%).
            *   `word_token_rate (float, default: WORD_TOKEN_RATE)`: An estimated ratio of words to tokens (e.g., 0.75 words per token). Used for approximating chunk boundaries. `WORD_TOKEN_RATE` is defined in `crawl4ai.config` (default value: 0.75).
            *   `apply_chunking (bool, default: True)`: If `True`, the input content is chunked before being sent to the LLM. If `False`, the entire content is sent (which might exceed token limits for large inputs).
            *   `force_json_response (bool, default: False)`: If `True` and `extraction_type` is "schema", instructs the LLM to strictly adhere to JSON output format.
            *   `**kwargs`: Passed to `ExtractionStrategy` and potentially to the underlying LLM API calls (e.g., `temperature`, `max_tokens` if not set in `llm_config`).
    *   4.1.4. Key Public Methods:
        *   `extract(self, url: str, content: str, *q, **kwargs) -> List[Dict[str, Any]]`:
            *   Description: Processes the input `content`. If `apply_chunking` is `True`, it first chunks the content using the specified `chunking_strategy` (or a default one if `LLMExtractionStrategy` manages it internally). Then, for each chunk (or the whole content if not chunked), it constructs a prompt based on `instruction` and/or `schema` and sends it to the configured LLM.
            *   Returns: `List[Dict[str, Any]]` - A list of dictionaries.
                *   If `extraction_type` is "block", each dictionary typically contains `{"index": int, "content": str, "tags": List[str]}`.
                *   If `extraction_type` is "schema", each dictionary is an instance of the extracted structured data, ideally conforming to the provided `schema`. If the LLM returns multiple JSON objects in a list, they are parsed and returned.
        *   `run(self, url: str, sections: List[str], *q, **kwargs) -> List[Dict[str, Any]]`:
            *   Description: Processes a list of content `sections` in parallel (using `ThreadPoolExecutor`). Each section is passed to the `extract` method logic.
            *   Returns: `List[Dict[str, Any]]` - Aggregated list of results from processing all sections.
    *   4.1.5. `TokenUsage` Tracking:
        *   `total_usage (TokenUsage)`: [Read-only Public Attribute] - An instance of `TokenUsage` that accumulates the token counts (prompt, completion, total) from all LLM API calls made by this `LLMExtractionStrategy` instance.
        *   `usages (List[TokenUsage])`: [Read-only Public Attribute] - A list containing individual `TokenUsage` objects for each separate LLM API call made during the extraction process. This allows for detailed tracking of token consumption per call.

## 5. `ChunkingStrategy` Interface and Implementations

*   ### 5.1. Interface `ChunkingStrategy`
    *   5.1.1. Purpose: The `ChunkingStrategy` class, found in `crawl4ai.chunking_strategy`, is an abstract base class (ABC) that defines the interface for different content chunking algorithms. Chunking is used to break down large pieces of text or HTML into smaller, manageable segments, often before feeding them to an LLM or other processing steps.
    *   5.1.2. Key Abstract Methods:
        *   `chunk(self, content: str) -> List[str]`:
            *   Description: Abstract method that must be implemented by subclasses to split the input `content` string into a list of string chunks.
            *   Parameters:
                *   `content (str)`: The content to be chunked.
            *   Returns: `List[str]` - A list of content chunks.

*   ### 5.2. Class `RegexChunking`
    *   5.2.1. Purpose: Implements `ChunkingStrategy` by splitting content based on a list of regular expression patterns. It can also attempt to merge smaller chunks to meet a target `chunk_size`.
    *   5.2.2. Inheritance: `ChunkingStrategy`
    *   5.2.3. Initialization (`__init__`):
        *   5.2.3.1. Signature: `RegexChunking(patterns: Optional[List[str]] = None, chunk_size: Optional[int] = None, overlap: Optional[int] = None, word_token_ratio: Optional[float] = WORD_TOKEN_RATE, **kwargs)`
        *   5.2.3.2. Parameters:
            *   `patterns (Optional[List[str]], default: None)`: A list of regex patterns used to split the text. If `None`, defaults to paragraph-based splitting (`["\\n\\n+"]`).
            *   `chunk_size (Optional[int], default: None)`: The target token size for each chunk. If specified, the strategy will try to merge smaller chunks created by regex splitting to approximate this size.
            *   `overlap (Optional[int], default: None)`: The target token overlap between consecutive chunks when `chunk_size` is active.
            *   `word_token_ratio (Optional[float], default: WORD_TOKEN_RATE)`: The estimated ratio of words to tokens, used if `chunk_size` or `overlap` are specified. `WORD_TOKEN_RATE` is defined in `crawl4ai.config` (default value: 0.75).
            *   `**kwargs`: Additional keyword arguments.
    *   5.2.4. Key Public Methods:
        *   `chunk(self, content: str) -> List[str]`:
            *   Description: Splits the input `content` using the configured regex patterns. If `chunk_size` is set, it then merges these initial chunks to meet the target size with the specified overlap.

*   ### 5.3. Class `IdentityChunking`
    *   5.3.1. Purpose: A `ChunkingStrategy` that does not perform any actual chunking. It returns the input content as a single chunk in a list.
    *   5.3.2. Inheritance: `ChunkingStrategy`
    *   5.3.3. Initialization (`__init__`):
        *   5.3.3.1. Signature: `IdentityChunking(**kwargs)`
        *   5.3.3.2. Parameters:
            *   `**kwargs`: Additional keyword arguments.
    *   5.3.4. Key Public Methods:
        *   `chunk(self, content: str) -> List[str]`:
            *   Description: Returns the input `content` as a single-element list: `[content]`.

## 6. Defining Schemas for Extraction

*   6.1. Purpose: Schemas provide a structured way to define what data needs to be extracted from content and how it should be organized. This allows for consistent and predictable output from the extraction process.
*   6.2. Schemas for CSS/XPath/LXML-based Extraction (`JsonCssExtractionStrategy`, etc.):
    *   6.2.1. Format: These strategies use a dictionary-based JSON-like schema.
    *   6.2.2. Key elements: As detailed in section 3.2.4 for `JsonCssExtractionStrategy`:
        *   `name (str)`: Name of the schema.
        *   `baseSelector (str)`: CSS selector (for CSS strategies) or XPath expression (for XPath strategy) identifying the repeating parent elements.
        *   `fields (List[Dict[str, Any]])`: A list defining each field to extract. Each field definition includes:
            *   `name (str)`: Output key for the field.
            *   `selector (str)`: CSS/XPath selector relative to the `baseSelector` or parent "nested" element.
            *   `type (str)`: "text", "attribute", "html", "list", "nested".
            *   `attribute (str, Optional)`: Name of HTML attribute (if type is "attribute").
            *   `fields (List[Dict], Optional)`: For "list" (of objects) or "nested" types.
            *   `transform (str, Optional)`: e.g., "lowercase".
            *   `default (Any, Optional)`: Default value if not found.
*   6.3. Schemas for LLM-based Extraction (`LLMExtractionStrategy`):
    *   6.3.1. Format: `LLMExtractionStrategy` accepts schemas in two main formats when `extraction_type="schema"`:
        *   Pydantic models: The Pydantic model class itself.
        *   Dictionary: A Python dictionary representing a valid JSON schema.
    *   6.3.2. Pydantic Models:
        *   Definition: Users can define a Pydantic `BaseModel` where each field represents a piece of data to be extracted. Field types and descriptions are automatically inferred.
        *   Conversion: `LLMExtractionStrategy` internally converts the Pydantic model to its JSON schema representation (`model_json_schema()`) to guide the LLM.
    *   6.3.3. Dictionary-based JSON Schema:
        *   Structure: Users can provide a dictionary that conforms to the JSON Schema specification. This typically includes a `type: "object"` at the root and a `properties` dictionary defining each field, its type (e.g., "string", "number", "array", "object"), and optionally a `description`.
        *   Usage: This schema is passed to the LLM to instruct it on the desired output format.

## 7. Configuration with `CrawlerRunConfig`

*   7.1. Purpose: The `CrawlerRunConfig` class (from `crawl4ai.async_configs`) is used to configure the behavior of a specific `arun()` or `arun_many()` call on an `AsyncWebCrawler` instance. It allows specifying various runtime parameters, including the extraction and chunking strategies.
*   7.2. Key Attributes:
    *   `extraction_strategy (Optional[ExtractionStrategy], default: None)`:
        *   Purpose: Specifies the `ExtractionStrategy` instance to be used for processing the content obtained during the crawl. If `None`, no structured extraction beyond basic Markdown generation occurs (unless a default is applied by the crawler).
        *   Type: An instance of a class inheriting from `ExtractionStrategy`.
    *   `chunking_strategy (Optional[ChunkingStrategy], default: RegexChunking())`:
        *   Purpose: Specifies the `ChunkingStrategy` instance to be used for breaking down content into smaller pieces before it's passed to an `ExtractionStrategy` (particularly `LLMExtractionStrategy`).
        *   Type: An instance of a class inheriting from `ChunkingStrategy`.
        *   Default: An instance of `RegexChunking()` with its default parameters (paragraph-based splitting).

## 8. LLM-Specific Configuration and Models

*   ### 8.1. Class `LLMConfig`
    *   8.1.1. Purpose: The `LLMConfig` class (from `crawl4ai.async_configs`) centralizes configuration parameters for interacting with Large Language Models (LLMs) through various providers.
    *   8.1.2. Initialization (`__init__`):
        *   8.1.2.1. Signature:
            ```python
            class LLMConfig:
                def __init__(
                    self,
                    provider: str = DEFAULT_PROVIDER,
                    api_token: Optional[str] = None,
                    base_url: Optional[str] = None,
                    temperature: Optional[float] = None,
                    max_tokens: Optional[int] = None,
                    top_p: Optional[float] = None,
                    frequency_penalty: Optional[float] = None,
                    presence_penalty: Optional[float] = None,
                    stop: Optional[List[str]] = None,
                    n: Optional[int] = None,
                ): ...
            ```
        *   8.1.2.2. Parameters:
            *   `provider (str, default: DEFAULT_PROVIDER)`: Specifies the LLM provider and model, e.g., "openai/gpt-4o-mini", "ollama/llama3.3". `DEFAULT_PROVIDER` is "openai/gpt-4o-mini".
            *   `api_token (Optional[str], default: None)`: API token for the LLM provider. If `None`, the system attempts to read it from environment variables (e.g., `OPENAI_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY` based on provider). Can also be prefixed with "env:" (e.g., "env:MY_CUSTOM_LLM_KEY").
            *   `base_url (Optional[str], default: None)`: Custom base URL for the LLM API endpoint, for self-hosted or alternative provider endpoints.
            *   `temperature (Optional[float], default: None)`: Controls randomness in LLM generation. Higher values (e.g., 0.8) make output more random, lower (e.g., 0.2) more deterministic.
            *   `max_tokens (Optional[int], default: None)`: Maximum number of tokens the LLM should generate in its response.
            *   `top_p (Optional[float], default: None)`: Nucleus sampling parameter. An alternative to temperature; controls the cumulative probability mass of tokens considered for generation.
            *   `frequency_penalty (Optional[float], default: None)`: Penalizes new tokens based on their existing frequency in the text so far, decreasing repetition.
            *   `presence_penalty (Optional[float], default: None)`: Penalizes new tokens based on whether they have appeared in the text so far, encouraging new topics.
            *   `stop (Optional[List[str]], default: None)`: A list of sequences where the API will stop generating further tokens.
            *   `n (Optional[int], default: None)`: Number of completions to generate for each prompt.
    *   8.1.3. Helper Methods:
        *   `from_kwargs(kwargs: dict) -> LLMConfig`:
            *   Description: [Static method] Creates an `LLMConfig` instance from a dictionary of keyword arguments.
        *   `to_dict() -> dict`:
            *   Description: Converts the `LLMConfig` instance into a dictionary representation.
        *   `clone(**kwargs) -> LLMConfig`:
            *   Description: Creates a new `LLMConfig` instance as a copy of the current one, allowing specific attributes to be overridden with `kwargs`.

*   ### 8.2. Dataclass `TokenUsage`
    *   8.2.1. Purpose: The `TokenUsage` dataclass (from `crawl4ai.models`) is used to store information about the number of tokens consumed during an LLM API call.
    *   8.2.2. Fields:
        *   `completion_tokens (int, default: 0)`: The number of tokens generated by the LLM in the completion.
        *   `prompt_tokens (int, default: 0)`: The number of tokens in the prompt sent to the LLM.
        *   `total_tokens (int, default: 0)`: The sum of `completion_tokens` and `prompt_tokens`.
        *   `completion_tokens_details (Optional[dict], default: None)`: Provider-specific detailed breakdown of completion tokens, if available.
        *   `prompt_tokens_details (Optional[dict], default: None)`: Provider-specific detailed breakdown of prompt tokens, if available.

## 9. PDF Processing and Extraction

*   ### 9.1. Overview of PDF Processing
    *   9.1.1. Purpose: Crawl4ai provides specialized strategies to handle PDF documents, enabling the fetching of PDF content and subsequent extraction of text, images, and metadata. This allows PDFs to be treated as a primary content source similar to HTML web pages.
    *   9.1.2. Key Components:
        *   `PDFCrawlerStrategy`: For fetching/identifying PDF content.
        *   `PDFContentScrapingStrategy`: For processing PDF content using an underlying PDF processor.
        *   `NaivePDFProcessorStrategy`: The default logic for parsing PDF files.

*   ### 9.2. Class `PDFCrawlerStrategy`
    *   9.2.1. Purpose: An implementation of `AsyncCrawlerStrategy` specifically for handling PDF documents. It doesn't perform typical browser interactions but focuses on fetching PDF content and setting the appropriate response headers to indicate a PDF document, which then allows `PDFContentScrapingStrategy` to process it.
    *   9.2.2. Inheritance: `AsyncCrawlerStrategy` (from `crawl4ai.async_crawler_strategy`)
    *   9.2.3. Initialization (`__init__`):
        *   9.2.3.1. Signature: `PDFCrawlerStrategy(logger: Optional[AsyncLogger] = None)`
        *   9.2.3.2. Parameters:
            *   `logger (Optional[AsyncLogger], default: None)`: An optional logger instance for logging messages.
    *   9.2.4. Key Public Methods:
        *   `crawl(self, url: str, **kwargs) -> AsyncCrawlResponse`:
            *   Description: Fetches the content from the given `url`. If the content is identified as a PDF (either by URL extension or `Content-Type` header for remote URLs), it sets `response_headers={"Content-Type": "application/pdf"}` in the returned `AsyncCrawlResponse`. The `html` field of the response will contain a placeholder message as the actual PDF processing happens in the scraping strategy.
        *   `close(self) -> None`:
            *   Description: Placeholder for cleanup, typically does nothing in this strategy.
        *   `__aenter__(self) -> "PDFCrawlerStrategy"`:
            *   Description: Async context manager entry point.
        *   `__aexit__(self, exc_type, exc_val, exc_tb) -> None`:
            *   Description: Async context manager exit point, calls `close()`.

*   ### 9.3. Class `PDFContentScrapingStrategy`
    *   9.3.1. Purpose: An implementation of `ContentScrapingStrategy` designed to process PDF documents. It uses an underlying `PDFProcessorStrategy` (by default, `NaivePDFProcessorStrategy`) to extract text, images, and metadata from the PDF, then formats this information into a `ScrapingResult`.
    *   9.3.2. Inheritance: `ContentScrapingStrategy` (from `crawl4ai.content_scraping_strategy`)
    *   9.3.3. Initialization (`__init__`):
        *   9.3.3.1. Signature: `PDFContentScrapingStrategy(save_images_locally: bool = False, extract_images: bool = False, image_save_dir: Optional[str] = None, batch_size: int = 4, logger: Optional[AsyncLogger] = None)`
        *   9.3.3.2. Parameters:
            *   `save_images_locally (bool, default: False)`: If `True`, extracted images will be saved to the local filesystem.
            *   `extract_images (bool, default: False)`: If `True`, the strategy will attempt to extract images from the PDF.
            *   `image_save_dir (Optional[str], default: None)`: The directory where extracted images will be saved if `save_images_locally` is `True`. If `None`, a default or temporary directory might be used.
            *   `batch_size (int, default: 4)`: The number of PDF pages to process in parallel by the underlying `NaivePDFProcessorStrategy`.
            *   `logger (Optional[AsyncLogger], default: None)`: An optional logger instance.
    *   9.3.4. Key Attributes:
        *   `pdf_processor (NaivePDFProcessorStrategy)`: An instance of `NaivePDFProcessorStrategy` configured with the provided image and batch settings, used to do the actual PDF parsing.
    *   9.3.5. Key Public Methods:
        *   `scrape(self, url: str, html: str, **params) -> ScrapingResult`:
            *   Description: Takes a `url` (which can be a local file path or a remote HTTP/HTTPS URL pointing to a PDF) and processes it. The `html` parameter is typically a placeholder like "Scraper will handle the real work" as the content comes from the PDF file itself. It downloads remote PDFs to a temporary local file before processing.
            *   Returns: `ScrapingResult` containing the extracted PDF data, including `cleaned_html` (concatenated HTML of pages), `media` (extracted images), `links`, and `metadata`.
        *   `ascrape(self, url: str, html: str, **kwargs) -> ScrapingResult`:
            *   Description: Asynchronous version of `scrape`. Internally calls `scrape` using `asyncio.to_thread`.
    *   9.3.6. Internal Methods (Conceptual):
        *   `_get_pdf_path(self, url: str) -> str`:
            *   Description: If `url` is an HTTP/HTTPS URL, downloads the PDF to a temporary file and returns its path. If `url` starts with "file://", it strips the prefix and returns the local path. Otherwise, assumes `url` is already a local path. Handles download timeouts and errors.

*   ### 9.4. Class `NaivePDFProcessorStrategy`
    *   9.4.1. Purpose: The default implementation of `PDFProcessorStrategy` in Crawl4ai. It uses the PyPDF2 library (and Pillow for image processing) to parse PDF files, extract text content page by page, attempt to extract embedded images, and gather document metadata.
    *   9.4.2. Inheritance: `PDFProcessorStrategy` (from `crawl4ai.processors.pdf.processor`)
    *   9.4.3. Dependencies: Requires `PyPDF2` and `Pillow`. These are installed with the `crawl4ai[pdf]` extra.
    *   9.4.4. Initialization (`__init__`):
        *   9.4.4.1. Signature: `NaivePDFProcessorStrategy(image_dpi: int = 144, image_quality: int = 85, extract_images: bool = True, save_images_locally: bool = False, image_save_dir: Optional[Path] = None, batch_size: int = 4)`
        *   9.4.4.2. Parameters:
            *   `image_dpi (int, default: 144)`: DPI used when rendering PDF pages to images (if direct image extraction is not possible or disabled).
            *   `image_quality (int, default: 85)`: Quality setting (1-100) for images saved in lossy formats like JPEG.
            *   `extract_images (bool, default: True)`: If `True`, attempts to extract embedded images directly from the PDF's XObjects.
            *   `save_images_locally (bool, default: False)`: If `True`, extracted images are saved to disk. Otherwise, they are base64 encoded and returned in the `PDFPage.images` data.
            *   `image_save_dir (Optional[Path], default: None)`: If `save_images_locally` is True, this specifies the directory to save images. If `None`, a temporary directory (prefixed `pdf_images_`) is created and used.
            *   `batch_size (int, default: 4)`: The number of pages to process in parallel when using the `process_batch` method.
    *   9.4.5. Key Public Methods:
        *   `process(self, pdf_path: Path) -> PDFProcessResult`:
            *   Description: Processes the PDF specified by `pdf_path` page by page sequentially.
            *   Returns: `PDFProcessResult` containing metadata and a list of `PDFPage` objects.
        *   `process_batch(self, pdf_path: Path) -> PDFProcessResult`:
            *   Description: Processes the PDF specified by `pdf_path` by handling pages in parallel batches using a `ThreadPoolExecutor` with `max_workers` set to `batch_size`.
            *   Returns: `PDFProcessResult` containing metadata and a list of `PDFPage` objects, assembled in the correct page order.
    *   9.4.6. Internal Methods (Conceptual High-Level):
        *   `_process_page(self, page: PyPDF2PageObject, image_dir: Optional[Path]) -> PDFPage`: Extracts text, images (if `extract_images` is True), and links from a single PyPDF2 page object.
        *   `_extract_images(self, page: PyPDF2PageObject, image_dir: Optional[Path]) -> List[Dict]`: Iterates through XObjects on a page, identifies images, decodes them (handling FlateDecode, DCTDecode, CCITTFaxDecode, JPXDecode), and either saves them locally or base64 encodes them.
        *   `_extract_links(self, page: PyPDF2PageObject) -> List[str]`: Extracts URI actions from page annotations to get hyperlinks.
        *   `_extract_metadata(self, pdf_path: Path, reader: PyPDF2PdfReader) -> PDFMetadata`: Reads metadata from the PDF document information dictionary (e.g., /Title, /Author, /CreationDate).

*   ### 9.5. Data Models for PDF Processing
    *   9.5.1. Dataclass `PDFMetadata` (from `crawl4ai.processors.pdf.processor`)
        *   Fields:
            *   `title (Optional[str], default: None)`
            *   `author (Optional[str], default: None)`
            *   `producer (Optional[str], default: None)`
            *   `created (Optional[datetime], default: None)`
            *   `modified (Optional[datetime], default: None)`
            *   `pages (int, default: 0)`
            *   `encrypted (bool, default: False)`
            *   `file_size (Optional[int], default: None)`
    *   9.5.2. Dataclass `PDFPage` (from `crawl4ai.processors.pdf.processor`)
        *   Fields:
            *   `page_number (int)`
            *   `raw_text (str, default: "")`
            *   `markdown (str, default: "")`: Markdown representation of the page's text content, processed by `clean_pdf_text`.
            *   `html (str, default: "")`: HTML representation of the page's text content, processed by `clean_pdf_text_to_html`.
            *   `images (List[Dict], default_factory: list)`: List of image dictionaries. Each dictionary contains:
                *   `format (str)`: e.g., "png", "jpeg", "tiff", "jp2", "bin".
                *   `width (int)`
                *   `height (int)`
                *   `color_space (str)`: e.g., "/DeviceRGB", "/DeviceGray".
                *   `bits_per_component (int)`
                *   `path (str, Optional)`: If `save_images_locally` was True, path to the saved image file.
                *   `data (str, Optional)`: If `save_images_locally` was False, base64 encoded image data.
                *   `page (int)`: The page number this image was extracted from.
            *   `links (List[str], default_factory: list)`: List of hyperlink URLs found on the page.
            *   `layout (List[Dict], default_factory: list)`: List of dictionaries representing text layout elements, primarily: `{"type": "text", "text": str, "x": float, "y": float}`.
    *   9.5.3. Dataclass `PDFProcessResult` (from `crawl4ai.processors.pdf.processor`)
        *   Fields:
            *   `metadata (PDFMetadata)`
            *   `pages (List[PDFPage])`
            *   `processing_time (float, default: 0.0)`: Time in seconds taken to process the PDF.
            *   `version (str, default: "1.1")`: Version of the PDF processor strategy (e.g., "1.1" for current `NaivePDFProcessorStrategy`).

*   ### 9.6. Using PDF Strategies with `AsyncWebCrawler`
    *   9.6.1. Workflow:
        1.  Instantiate `AsyncWebCrawler`. The `crawler_strategy` parameter of `AsyncWebCrawler` should be set to an instance of `PDFCrawlerStrategy` if you intend to primarily crawl PDF URLs or local PDF files directly. If crawling mixed content where PDFs are discovered via links on HTML pages, the default `AsyncPlaywrightCrawlerStrategy` might be used initially, and then a PDF-specific scraping strategy would be applied when a PDF content type is detected.
        2.  In `CrawlerRunConfig`, set the `scraping_strategy` attribute to an instance of `PDFContentScrapingStrategy`. Configure this strategy with desired options like `extract_images`, `save_images_locally`, etc.
        3.  When `crawler.arun(url="path/to/document.pdf", config=run_config)` is called for a PDF URL or local file path:
            *   `PDFCrawlerStrategy` (if used) or the default crawler strategy fetches the file.
            *   `PDFContentScrapingStrategy.scrape()` is invoked. It uses its internal `NaivePDFProcessorStrategy` instance to parse the PDF.
            *   The extracted text, image data, and metadata are populated into the `CrawlResult` object (e.g., `result.markdown`, `result.media["images"]`, `result.metadata`).
    *   9.6.2. Example Snippet:
        ```python
        import asyncio
        from pathlib import Path
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, PDFCrawlerStrategy
        from crawl4ai.content_scraping_strategy import PDFContentScrapingStrategy
        from crawl4ai.processors.pdf import PDFContentScrapingStrategy # Corrected import path

        async def main():
            # Setup for PDF processing
            pdf_crawler_strategy = PDFCrawlerStrategy() # Use if directly targeting PDF URLs
            pdf_scraping_strategy = PDFContentScrapingStrategy(
                extract_images=True,
                save_images_locally=True,
                image_save_dir="./pdf_images_output" # Ensure this directory exists
            )
            Path("./pdf_images_output").mkdir(parents=True, exist_ok=True)

            # If crawling a website that links to PDFs, you might use the default crawler strategy
            # and rely on content-type detection to switch to PDFContentScrapingStrategy if needed.
            # For direct PDF URL:
            async with AsyncWebCrawler(crawler_strategy=pdf_crawler_strategy) as crawler:
                run_config = CrawlerRunConfig(scraping_strategy=pdf_scraping_strategy)
                # Example PDF URL (replace with a real one for testing)
                pdf_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
                result = await crawler.arun(url=pdf_url, config=run_config)

                if result.success:
                    print(f"Successfully processed PDF: {result.url}")
                    if result.markdown:
                         print(f"Markdown content (first 500 chars): {result.markdown.raw_markdown[:500]}")
                    if result.media and result.media.images:
                        print(f"Extracted {len(result.media.images)} images.")
                        for img in result.media.images:
                            print(f"  - Image source/path: {img.src or img.path}, Page: {img.page}")
                    if result.metadata:
                        print(f"PDF Metadata: {result.metadata}")
                else:
                    print(f"Failed to process PDF: {result.url}, Error: {result.error_message}")

        # if __name__ == "__main__":
        #     asyncio.run(main())
        ```
```

---


# Markdown Generation - Memory
Source: crawl4ai_markdown_memory_content.llm.md

Okay, I have processed the instructions and the provided information. I will now generate the detailed "Foundational Memory" document for the `markdown` component of `crawl4ai`, adhering strictly to the outline you've provided and focusing on factual API details.

```markdown
# Detailed Outline for crawl4ai - markdown Component

**Target Document Type:** memory
**Target Output Filename Suggestion:** `llm_memory_markdown.md`
**Library Version Context:** 0.6.3
**Outline Generation Date:** 2025-05-24
---

## 1. Introduction to Markdown Generation in Crawl4ai

*   1.1. Purpose: This section outlines the `markdown` component of the `crawl4ai` library. Its primary role is to convert HTML content, obtained during web crawling, into various Markdown formats. These formats are designed to be suitable for consumption by Large Language Models (LLMs), as well as for other applications requiring structured text from web pages.
*   1.2. Key Abstractions:
    *   `MarkdownGenerationStrategy`: An abstract base class that defines the interface for different markdown generation algorithms and approaches. This allows for customizable Markdown conversion processes.
    *   `DefaultMarkdownGenerator`: The standard, out-of-the-box implementation of `MarkdownGenerationStrategy`. It handles the conversion of HTML to Markdown, including features like link-to-citation conversion and integration with content filtering.
    *   `MarkdownGenerationResult`: A Pydantic data model that encapsulates the various outputs of the markdown generation process, such as raw markdown, markdown with citations, and markdown derived from filtered content.
    *   `CrawlerRunConfig.markdown_generator`: An attribute within the `CrawlerRunConfig` class that allows users to specify which instance of a `MarkdownGenerationStrategy` should be used for a particular crawl operation.
*   1.3. Relationship with Content Filtering: The markdown generation process can be integrated with `RelevantContentFilter` strategies. When a content filter is applied, it first refines the input HTML, and then this filtered HTML is used to produce a `fit_markdown` output, providing a more focused version of the content.

## 2. Core Interface: `MarkdownGenerationStrategy`

*   2.1. Purpose: The `MarkdownGenerationStrategy` class is an abstract base class (ABC) that defines the contract for all markdown generation strategies within `crawl4ai`. It ensures that any custom markdown generator will adhere to a common interface, making them pluggable into the crawling process.
*   2.2. Source File: `crawl4ai/markdown_generation_strategy.py`
*   2.3. Initialization (`__init__`)
    *   2.3.1. Signature:
        ```python
        class MarkdownGenerationStrategy(ABC):
            def __init__(
                self,
                content_filter: Optional[RelevantContentFilter] = None,
                options: Optional[Dict[str, Any]] = None,
                verbose: bool = False,
                content_source: str = "cleaned_html",
            ):
                # ...
        ```
    *   2.3.2. Parameters:
        *   `content_filter (Optional[RelevantContentFilter]`, default: `None`)`: An optional `RelevantContentFilter` instance. If provided, this filter will be used to process the HTML before generating the `fit_markdown` and `fit_html` outputs in the `MarkdownGenerationResult`.
        *   `options (Optional[Dict[str, Any]]`, default: `None`)`: A dictionary for strategy-specific custom options. This allows subclasses to receive additional configuration parameters. Defaults to an empty dictionary if `None`.
        *   `verbose (bool`, default: `False`)`: If `True`, enables verbose logging for the markdown generation process.
        *   `content_source (str`, default: `"cleaned_html"`)`: A string indicating the source of HTML to use for Markdown generation. Common values might include `"raw_html"` (original HTML from the page), `"cleaned_html"` (HTML after initial cleaning by the scraping strategy), or `"fit_html"` (HTML after being processed by `content_filter`). The actual available sources depend on the `ScrapingResult` provided to the markdown generator.
*   2.4. Abstract Methods:
    *   2.4.1. `generate_markdown(self, input_html: str, base_url: str = "", html2text_options: Optional[Dict[str, Any]] = None, content_filter: Optional[RelevantContentFilter] = None, citations: bool = True, **kwargs) -> MarkdownGenerationResult`
        *   Purpose: This abstract method must be implemented by concrete subclasses. It is responsible for taking an HTML string and converting it into various Markdown representations, encapsulated within a `MarkdownGenerationResult` object.
        *   Parameters:
            *   `input_html (str)`: The HTML string content to be converted to Markdown.
            *   `base_url (str`, default: `""`)`: The base URL of the crawled page. This is crucial for resolving relative URLs, especially when converting links to citations.
            *   `html2text_options (Optional[Dict[str, Any]]`, default: `None`)`: A dictionary of options to be passed to the underlying HTML-to-text conversion engine (e.g., `CustomHTML2Text`).
            *   `content_filter (Optional[RelevantContentFilter]`, default: `None`)`: An optional `RelevantContentFilter` instance. If provided, this filter is used to generate `fit_markdown` and `fit_html`. This parameter overrides any filter set during the strategy's initialization for this specific call.
            *   `citations (bool`, default: `True`)`: A boolean flag indicating whether to convert Markdown links into a citation format (e.g., `[text]^[1]^`) with a corresponding reference list.
            *   `**kwargs`: Additional keyword arguments to allow for future extensions or strategy-specific parameters.
        *   Returns: (`MarkdownGenerationResult`) An object containing the results of the Markdown generation, including `raw_markdown`, `markdown_with_citations`, `references_markdown`, and potentially `fit_markdown` and `fit_html`.

## 3. Default Implementation: `DefaultMarkdownGenerator`

*   3.1. Purpose: `DefaultMarkdownGenerator` is the standard concrete implementation of `MarkdownGenerationStrategy`. It provides a robust mechanism for converting HTML to Markdown, featuring link-to-citation conversion and the ability to integrate with `RelevantContentFilter` strategies for focused content output.
*   3.2. Source File: `crawl4ai/markdown_generation_strategy.py`
*   3.3. Inheritance: Inherits from `MarkdownGenerationStrategy`.
*   3.4. Initialization (`__init__`)
    *   3.4.1. Signature:
        ```python
        class DefaultMarkdownGenerator(MarkdownGenerationStrategy):
            def __init__(
                self,
                content_filter: Optional[RelevantContentFilter] = None,
                options: Optional[Dict[str, Any]] = None,
                # content_source parameter from parent is available
                # verbose parameter from parent is available
            ):
                super().__init__(content_filter, options, content_source=kwargs.get("content_source", "cleaned_html"), verbose=kwargs.get("verbose", False))
        ```
        *(Note: The provided code snippet for `DefaultMarkdownGenerator.__init__` does not explicitly list `verbose` and `content_source`, but they are passed to `super().__init__` through `**kwargs` in the actual library code, so their effective signature matches the parent.)*
    *   3.4.2. Parameters:
        *   `content_filter (Optional[RelevantContentFilter]`, default: `None`)`: As defined in `MarkdownGenerationStrategy`.
        *   `options (Optional[Dict[str, Any]]`, default: `None`)`: As defined in `MarkdownGenerationStrategy`.
        *   `verbose (bool`, default: `False`)`: (Passed via `kwargs` to parent) As defined in `MarkdownGenerationStrategy`.
        *   `content_source (str`, default: `"cleaned_html"`)`: (Passed via `kwargs` to parent) As defined in `MarkdownGenerationStrategy`.
*   3.5. Key Class Attributes:
    *   3.5.1. `LINK_PATTERN (re.Pattern)`: A compiled regular expression pattern used to find Markdown links. The pattern is `r'!\[(.[^\]]*)\]\(([^)]*?)(?:\s*\"(.*)\")?\)'`.
*   3.6. Key Public Methods:
    *   3.6.1. `generate_markdown(self, input_html: str, base_url: str = "", html2text_options: Optional[Dict[str, Any]] = None, content_filter: Optional[RelevantContentFilter] = None, citations: bool = True, **kwargs) -> MarkdownGenerationResult`
        *   Purpose: Implements the conversion of HTML to Markdown. It uses `CustomHTML2Text` for the base conversion, handles link-to-citation transformation, and integrates with an optional `RelevantContentFilter` to produce `fit_markdown`.
        *   Parameters:
            *   `input_html (str)`: The HTML content to convert.
            *   `base_url (str`, default: `""`)`: Base URL for resolving relative links.
            *   `html2text_options (Optional[Dict[str, Any]]`, default: `None`)`: Options for the `CustomHTML2Text` converter. If not provided, it uses `self.options`.
            *   `content_filter (Optional[RelevantContentFilter]`, default: `None`)`: Overrides the instance's `content_filter` for this call.
            *   `citations (bool`, default: `True`)`: Whether to convert links to citations.
            *   `**kwargs`: Additional arguments (not currently used by this specific implementation beyond parent class).
        *   Core Logic:
            1.  Instantiates `CustomHTML2Text` using `base_url` and the resolved `html2text_options` (merged from method arg, `self.options`, and defaults).
            2.  Converts `input_html` to `raw_markdown` using the `CustomHTML2Text` instance.
            3.  If `citations` is `True`, calls `self.convert_links_to_citations(raw_markdown, base_url)` to get `markdown_with_citations` and `references_markdown`.
            4.  If `citations` is `False`, `markdown_with_citations` is set to `raw_markdown`, and `references_markdown` is an empty string.
            5.  Determines the active `content_filter` (parameter or instance's `self.content_filter`).
            6.  If an active `content_filter` exists:
                *   Calls `active_filter.filter_content(input_html)` to get a list of filtered HTML strings.
                *   Joins these strings with `\n` and wraps them in `<div>` tags to form `fit_html`.
                *   Uses a new `CustomHTML2Text` instance to convert `fit_html` into `fit_markdown`.
            7.  Otherwise, `fit_html` and `fit_markdown` are set to `None` (or empty strings based on implementation details).
            8.  Constructs and returns a `MarkdownGenerationResult` object with all generated Markdown variants.
    *   3.6.2. `convert_links_to_citations(self, markdown: str, base_url: str = "") -> Tuple[str, str]`
        *   Purpose: Transforms standard Markdown links within the input `markdown` string into a citation format (e.g., `[Link Text]^[1]^`) and generates a corresponding numbered list of references.
        *   Parameters:
            *   `markdown (str)`: The input Markdown string.
            *   `base_url (str`, default: `""`)`: The base URL used to resolve relative link URLs before they are added to the reference list.
        *   Returns: (`Tuple[str, str]`) A tuple where the first element is the Markdown string with links converted to citations, and the second element is a string containing the formatted list of references.
        *   Internal Logic:
            *   Uses the `LINK_PATTERN` regex to find all Markdown links.
            *   For each link, it resolves the URL using `fast_urljoin(base, url)` if `base_url` is provided and the link is relative.
            *   Assigns a unique citation number to each unique URL.
            *   Replaces the original link markup with the citation format (e.g., `[Text]^[Number]^`).
            *   Constructs a Markdown formatted reference list string.
*   3.7. Role of `CustomHTML2Text`:
    *   `CustomHTML2Text` is a customized version of an HTML-to-Markdown converter, likely based on the `html2text` library.
    *   It's instantiated by `DefaultMarkdownGenerator` to perform the core HTML to plain Markdown conversion.
    *   Its behavior is controlled by options passed via `html2text_options` in `generate_markdown` or `self.options` of the `DefaultMarkdownGenerator`. These options can include `body_width`, `ignore_links`, `ignore_images`, etc., influencing the final Markdown output. (Refer to `crawl4ai/html2text.py` for specific options).

## 4. Output Data Model: `MarkdownGenerationResult`

*   4.1. Purpose: `MarkdownGenerationResult` is a Pydantic `BaseModel` designed to structure and encapsulate the various Markdown outputs generated by any `MarkdownGenerationStrategy`. It provides a consistent way to access different versions of the converted content.
*   4.2. Source File: `crawl4ai/models.py`
*   4.3. Fields:
    *   4.3.1. `raw_markdown (str)`: The direct result of converting the input HTML to Markdown, before any citation processing or specific content filtering (by the generator itself) is applied. This represents the most basic Markdown version of the content.
    *   4.3.2. `markdown_with_citations (str)`: Markdown content where hyperlinks have been converted into a citation style (e.g., `[Link Text]^[1]^`). This is typically derived from `raw_markdown`.
    *   4.3.3. `references_markdown (str)`: A string containing a formatted list of references (e.g., numbered list of URLs) corresponding to the citations found in `markdown_with_citations`.
    *   4.3.4. `fit_markdown (Optional[str]`, default: `None`)`: Markdown content generated from HTML that has been processed by a `RelevantContentFilter`. This version is intended to be more concise or focused on relevant parts of the original content. It is `None` if no content filter was applied or if the filter resulted in no content.
    *   4.3.5. `fit_html (Optional[str]`, default: `None`)`: The HTML content that remains after being processed by a `RelevantContentFilter`. `fit_markdown` is generated from this `fit_html`. It is `None` if no content filter was applied or if the filter resulted in no content.
*   4.4. Methods:
    *   4.4.1. `__str__(self) -> str`:
        *   Purpose: Defines the string representation of a `MarkdownGenerationResult` object.
        *   Signature: `__str__(self) -> str`
        *   Returns: (`str`) The content of the `raw_markdown` field.

## 5. Integration with Content Filtering (`RelevantContentFilter`)

*   5.1. Purpose of Integration: `DefaultMarkdownGenerator` allows integration with `RelevantContentFilter` strategies to produce a `fit_markdown` output. This enables generating Markdown from a version of the HTML that has been refined or focused based on relevance criteria defined by the filter (e.g., keywords, semantic similarity, or LLM-based assessment).
*   5.2. Mechanism:
    *   A `RelevantContentFilter` instance can be passed to `DefaultMarkdownGenerator` either during its initialization (via the `content_filter` parameter) or directly to its `generate_markdown` method. The filter passed to `generate_markdown` takes precedence if both are provided.
    *   When an active filter is present, `DefaultMarkdownGenerator.generate_markdown` calls the filter's `filter_content(input_html)` method. This method is expected to return a list of HTML string chunks deemed relevant.
    *   These chunks are then joined (typically with `\n` and wrapped in `<div>` tags) to form the `fit_html` string.
    *   This `fit_html` is then converted to Markdown using `CustomHTML2Text`, and the result is stored as `fit_markdown`.
*   5.3. Impact on `MarkdownGenerationResult`:
    *   If a `RelevantContentFilter` is successfully used:
        *   `MarkdownGenerationResult.fit_markdown` will contain the Markdown derived from the filtered HTML.
        *   `MarkdownGenerationResult.fit_html` will contain the actual filtered HTML string.
    *   If no filter is used, or if the filter returns an empty list of chunks (indicating no content passed the filter), `fit_markdown` and `fit_html` will be `None` (or potentially empty strings, depending on the exact implementation details of joining an empty list).
*   5.4. Supported Filter Types (High-Level Mention):
    *   `PruningContentFilter`: A filter that likely removes irrelevant HTML sections based on predefined rules or structural analysis (e.g., removing common boilerplate like headers, footers, navbars).
    *   `BM25ContentFilter`: A filter that uses the BM25 ranking algorithm to score and select HTML chunks based on their relevance to a user-provided query.
    *   `LLMContentFilter`: A filter that leverages a Large Language Model to assess the relevance of HTML chunks, potentially based on a user query or a general understanding of content importance.
    *   *Note: Detailed descriptions and usage of each filter strategy are covered in their respective documentation sections.*

## 6. Configuration via `CrawlerRunConfig`

*   6.1. `CrawlerRunConfig.markdown_generator`
    *   Purpose: This attribute of the `CrawlerRunConfig` class allows a user to specify a custom `MarkdownGenerationStrategy` instance to be used for the markdown conversion phase of a crawl. This provides flexibility in how HTML content is transformed into Markdown.
    *   Type: `MarkdownGenerationStrategy` (accepts any concrete implementation of this ABC).
    *   Default Value: If not specified, an instance of `DefaultMarkdownGenerator()` is used by default within the `AsyncWebCrawler`'s `aprocess_html` method when `config.markdown_generator` is `None`.
    *   Usage Example:
        ```python
        from crawl4ai import CrawlerRunConfig, DefaultMarkdownGenerator, AsyncWebCrawler
        from crawl4ai.content_filter_strategy import BM25ContentFilter
        import asyncio

        # Example: Configure a markdown generator with a BM25 filter
        bm25_filter = BM25ContentFilter(user_query="Python programming language")
        custom_md_generator = DefaultMarkdownGenerator(content_filter=bm25_filter)

        run_config_with_custom_md = CrawlerRunConfig(
            markdown_generator=custom_md_generator,
            # Other run configurations...
        )

        async def example_crawl():
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(
                    url="https://en.wikipedia.org/wiki/Python_(programming_language)",
                    config=run_config_with_custom_md
                )
                if result.success and result.markdown:
                    print("Raw Markdown (snippet):", result.markdown.raw_markdown[:200])
                    if result.markdown.fit_markdown:
                        print("Fit Markdown (snippet):", result.markdown.fit_markdown[:200])
        
        # asyncio.run(example_crawl())
        ```

## 7. Influencing Markdown Output for LLM Consumption

*   7.1. Role of `DefaultMarkdownGenerator.options` and `html2text_options`:
    *   The `options` parameter in `DefaultMarkdownGenerator.__init__` and the `html2text_options` parameter in its `generate_markdown` method are used to pass configuration settings directly to the underlying `CustomHTML2Text` instance.
    *   `html2text_options` provided to `generate_markdown` will take precedence over `self.options` set during initialization.
    *   These options control various aspects of the HTML-to-Markdown conversion, such as line wrapping, handling of links, images, and emphasis, which can be crucial for preparing text for LLMs.
*   7.2. Key `CustomHTML2Text` Options (via `html2text_options` or `DefaultMarkdownGenerator.options`):
    *   `bodywidth (int`, default: `0` when `DefaultMarkdownGenerator` calls `CustomHTML2Text` for `raw_markdown` and `fit_markdown` if not otherwise specified): Determines the width for wrapping lines. A value of `0` disables line wrapping, which is often preferred for LLM processing as it preserves sentence structure across lines.
    *   `ignore_links (bool`, default: `False` in `CustomHTML2Text`): If `True`, all hyperlinks (`<a>` tags) are removed from the output, leaving only their anchor text.
    *   `ignore_images (bool`, default: `False` in `CustomHTML2Text`): If `True`, all image tags (`<img>`) are removed from the output.
    *   `ignore_emphasis (bool`, default: `False` in `CustomHTML2Text`): If `True`, emphasized text (e.g., `<em>`, `<strong>`) is rendered as plain text without Markdown emphasis characters (like `*` or `_`).
    *   `bypass_tables (bool`, default: `False` in `CustomHTML2Text`): If `True`, tables are not formatted as Markdown tables but are rendered as a series of paragraphs, which might be easier for some LLMs to process.
    *   `default_image_alt (str`, default: `""` in `CustomHTML2Text`): Specifies a default alt text for images that do not have an `alt` attribute.
    *   `protect_links (bool`, default: `False` in `CustomHTML2Text`): If `True`, URLs in links are not processed or modified.
    *   `single_line_break (bool`, default: `True` in `CustomHTML2Text`): If `True`, single newlines in HTML are converted to Markdown line breaks (two spaces then a newline). This can help preserve some formatting.
    *   `mark_code (bool`, default: `True` in `CustomHTML2Text`): If `True`, `<code>` and `<pre>` blocks are appropriately marked in Markdown.
    *   `escape_snob (bool`, default: `False` in `CustomHTML2Text`): If `True`, more aggressive escaping of special Markdown characters is performed.
    *   *Note: This list is based on common `html2text` options; refer to `crawl4ai/html2text.py` for the exact implementation and default behaviors within `CustomHTML2Text`.*
*   7.3. Impact of `citations (bool)` in `generate_markdown`:
    *   When `citations=True` (default in `DefaultMarkdownGenerator.generate_markdown`):
        *   Standard Markdown links `[text](url)` are converted to `[text]^[citation_number]^`.
        *   A `references_markdown` string is generated, listing all unique URLs with their corresponding citation numbers. This helps LLMs trace information back to its source and can reduce token count if URLs are long or repetitive.
    *   When `citations=False`:
        *   Links remain in their original Markdown format `[text](url)`.
        *   `references_markdown` will be an empty string.
        *   This might be preferred if the LLM needs to directly process the URLs or if the citation format is not desired.
*   7.4. Role of `content_source` in `MarkdownGenerationStrategy`:
    *   This parameter (defaulting to `"cleaned_html"` in `DefaultMarkdownGenerator`) specifies which HTML version is used as the primary input for the `generate_markdown` method.
    *   `"cleaned_html"`: Typically refers to HTML that has undergone initial processing by the `ContentScrapingStrategy` (e.g., removal of scripts, styles, and potentially some boilerplate based on the scraping strategy's rules). This is usually the recommended source for general Markdown conversion.
    *   `"raw_html"`: The original, unmodified HTML content fetched from the web page. Using this source would bypass any initial cleaning done by the scraping strategy.
    *   `"fit_html"`: This source is relevant when a `RelevantContentFilter` is used. `fit_html` is the HTML output *after* the `RelevantContentFilter` has processed the `input_html` (which itself is determined by `content_source`). If `content_source` is, for example, `"cleaned_html"`, then `fit_html` is the result of filtering that cleaned HTML. `fit_markdown` is then generated from this `fit_html`.
*   7.5. `fit_markdown` vs. `raw_markdown`/`markdown_with_citations`:
    *   `raw_markdown` (or `markdown_with_citations` if `citations=True`) is generated from the HTML specified by `content_source` (e.g., `"cleaned_html"`). It represents a general conversion of that source.
    *   `fit_markdown` is generated *only if* a `RelevantContentFilter` is active (either set in `DefaultMarkdownGenerator` or passed to `generate_markdown`). It is derived from the `fit_html` (the output of the content filter).
    *   **Choosing which to use for LLMs:**
        *   Use `fit_markdown` when you need a concise, highly relevant subset of the page's content tailored to a specific query or set of criteria defined by the filter. This can reduce noise and token count for the LLM.
        *   Use `raw_markdown` or `markdown_with_citations` when you need a more comprehensive representation of the page's textual content, or when no specific filtering criteria are applied.
```

---

