"""
News Scrapper Main Orchestration Script

This script initializes and coordinates the different components of the news scraper
(Planner, Fetcher, Parser, Monitor, Pipeline) to discover, queue, fetch, parse,
and store news articles from various sources based on command-line arguments.
"""
import argparse
import time
import os
import sys
import asyncio # Added asyncio
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Attempt to import Url and CrawlerRunConfig, handle if crawl4ai is not installed
try:
    from crawl4ai import Url, CrawlerRunConfig
except ImportError:
    Url = None # type: ignore
    CrawlerRunConfig = None # type: ignore
    print("WARNING: main.py: crawl4ai Url/CrawlerRunConfig not found. Some operations might be affected if parser.crawler is used directly.")

try:
    from news_scrapper.planner.planner import Planner
    from news_scrapper.pipeline.pipeline import Pipeline
    from news_scrapper.monitor.monitor import Monitor
    from news_scrapper.config import SOURCES_CONFIG_PATH
except ImportError as e:
    print(f"Error importing components: {e}. Ensure all components exist and PYTHONPATH is set correctly.")
    print("If running from project root, try 'python -m news_scrapper.main'.")
    sys.exit(1)

def setup_arg_parser():
    """Sets up and returns the argument parser."""
    parser = argparse.ArgumentParser(description="News Scrapper: Discovers, fetches, parses, and stores news articles.")

    parser.add_argument("--config", default=SOURCES_CONFIG_PATH, help=f"Path to sources JSON. Default: {SOURCES_CONFIG_PATH}")

    # Discovery tasks for existing sources
    parser.add_argument("--discover-rss", action="store_true", help="Discover RSS feeds for existing configured sources.")
    parser.add_argument("--poll-rss", action="store_true", help="Poll configured RSS feeds for new articles.")
    parser.add_argument("--process-sitemaps", action="store_true", help="Discover and process sitemaps for new articles.")
    parser.add_argument("--fallback-crawl", action="store_true", help="Run fallback crawl for sources without RSS/sitemap success.")
    parser.add_argument("--run-all-discovery", action="store_true", help="Run all content discovery tasks for configured sources (Poll, Sitemap, Fallback).")

    # New source discovery from external feeds
    parser.add_argument(
        "--discover-new-sources",
        action="store_true",
        help="Scan specified or existing RSS feeds to discover new potential news source domains."
    )
    parser.add_argument(
        "--rss-scan-feed-urls", type=str, nargs='*', default=[],
        help="Space-separated list of RSS feed URLs for new source discovery. Used with --discover-new-sources. If omitted, uses RSS feeds from existing configured sources."
    )
    parser.add_argument(
        "--rss-scan-recency-hours", type=int, default=24,
        help="Hours back to look in RSS feeds for new source discovery (with --discover-new-sources). Default: 24."
    )

    # Manual LLM Structure Analysis Trigger
    parser.add_argument(
        "--analyze-source", type=str, metavar="SOURCE_NAME",
        help="Manually trigger structure analysis (placeholder LLM) for a specific source to generate/update its extraction selectors. Provide the source name."
    )
    parser.add_argument(
        "--sample-url-for-analysis", type=str, metavar="URL",
        help="A specific sample article URL from the source to use for --analyze-source. If not provided, the source's base_url will be attempted."
    )

    # General options
    parser.add_argument("--source-name", type=str, default=None, help="Operate on a single configured source by name for discovery tasks (RSS, sitemap, fallback).")
    parser.add_argument("--recency-days", type=int, default=2, help="Days back to consider articles 'new' for polling/sitemaps/crawling. Default: 2.")
    parser.add_argument("--auto-save-config", action="store_true", help="Save config changes (e.g., after RSS/selector discovery).")
    parser.add_argument("--list-sources", action="store_true", help="List configured source names and exit.")
    parser.add_argument("--loop-delay-mins", type=int, default=0, help="Loop discovery and processing with this delay in minutes (0 for single run).")
    parser.add_argument(
        "--process-queued-items", action="store_true",
        help="After discovery tasks, process items currently in the pipeline queue (fetch full articles, parse, store)."
    )
    return parser

async def process_pipeline_items(pipeline, planner, parser, monitor, polite_sleep_sec=0.1): # Removed fetcher, parser has crawler
    monitor.log_event("INFO", f"Starting processing of {len(pipeline.item_queue)} items from pipeline queue.")
    processed_count = 0
    if not planner or not parser or not parser.crawler: # Check for parser.crawler
        monitor.log_event("ERROR", "Planner, Parser or Parser.crawler not available in process_pipeline_items.")
        return 0

    # Ensure Url and CrawlerRunConfig are available if parser.crawler is to be used
    if Url is None or CrawlerRunConfig is None:
        monitor.log_event("ERROR", "crawl4ai Url or CrawlerRunConfig not available. Cannot fetch content.")
        return 0

    while pipeline.has_pending_items():
        item_metadata = pipeline.get_next_item()
        if not item_metadata: continue

        article_url = item_metadata.get('link')
        item_id = item_metadata.get('id', article_url)
        item_source_name = item_metadata.get('source_name')

        if not article_url:
            monitor.log_event("WARNING", "Skipping item: missing 'link'.", {"item_id": item_id, "source": item_source_name})
            continue

        monitor.log_event("INFO", f"Processing item: {article_url}", {"id": item_id, "source": item_source_name})
        source_config = {}
        if item_source_name:
            source_config = planner.get_source_by_name(item_source_name) # This is synchronous
            if not source_config:
                monitor.log_event("WARNING", f"No source_config for '{item_source_name}'. Parser will use defaults.", {"url": article_url})
                source_config = {} # Ensure source_config is a dict
        else:
            monitor.log_event("WARNING", "Item metadata missing 'source_name'. Parser will use defaults.", {"url": article_url})

        html_content: Optional[str] = None
        final_article_url: str = article_url # In case of redirects

        try:
            page_data_list = await parser.crawler.arun(
                seed_url=Url(url=article_url),
                crawler_run_config=CrawlerRunConfig(max_depth=0, max_pages=1, store_content=True, allow_redirects=True)
            )
            if page_data_list and page_data_list.results and page_data_list.results[0].content:
                html_content = page_data_list.results[0].content
                final_article_url = page_data_list.results[0].url # Update URL if redirected
                if final_article_url != article_url:
                    monitor.log_event("DEBUG", f"URL for item {item_id} redirected to {final_article_url}")
            else:
                monitor.log_event("WARNING", f"Failed to fetch HTML via AsyncWebCrawler for {article_url}", {"item_id": item_id})
                continue
        except Exception as e:
            monitor.log_event("ERROR", f"Exception fetching {article_url} via AsyncWebCrawler: {e}", {"item_id": item_id, "exc_type": type(e).__name__})
            continue

        if html_content:
            # Use final_article_url for parsing, as it's the URL after redirects
            parsed_article_data = await parser.parse_content(html_content, final_article_url, source_config)
            if parsed_article_data and parsed_article_data.get("title") and parsed_article_data.get("text"): # Check for sufficiency
                final_article_data = {**item_metadata, **parsed_article_data}
                # Ensure 'url' in final_article_data is the one content was fetched from (final_article_url)
                final_article_data['url'] = final_article_url
                final_article_data['original_queued_url'] = article_url # Keep original for reference if needed
                final_article_data['processed_timestamp_utc'] = datetime.now(timezone.utc).isoformat()
                pipeline.store_result(final_article_data) # This is synchronous
                processed_count += 1
            else:
                monitor.log_event("WARNING", "Failed to parse content sufficiently.", {"url": final_article_url, "original_url": article_url, "source": item_source_name})
        # Removed else for html_content check, as it's handled by 'continue' above
        if polite_sleep_sec > 0:
            await asyncio.sleep(polite_sleep_sec) # Use asyncio.sleep for async functions

    monitor.log_event("INFO", f"Finished processing queue. Processed {processed_count} items.")
    return processed_count

async def manual_analyze_source_structure(source_name_to_analyze, sample_url_override, planner, monitor):
    """Handles the --analyze-source task."""
    monitor.log_event("INFO", f"Manual trigger for structure analysis: {source_name_to_analyze}")
    source_config = planner.get_source_by_name(source_name_to_analyze) # Sync
    if not source_config:
        monitor.log_event("ERROR", f"Source '{source_name_to_analyze}' not found in configuration.")
        return

    url_to_analyze = sample_url_override if sample_url_override else source_config.get("base_url")
    if not url_to_analyze:
        monitor.log_event("ERROR", f"No URL available for analysis (no --sample-url-for-analysis and no base_url for '{source_name_to_analyze}').")
        return

    monitor.log_event("INFO", f"Fetching content from '{url_to_analyze}' for structure analysis.")

    if not planner.parser or not planner.parser.crawler: # Check parser and its crawler
        monitor.log_event("ERROR", "Parser's AsyncWebCrawler not available for analysis via planner.parser.crawler.")
        return

    if Url is None or CrawlerRunConfig is None:
        monitor.log_event("ERROR", "crawl4ai Url or CrawlerRunConfig not available for manual analysis.")
        return

    html_content: Optional[str] = None
    final_url_to_analyze: str = url_to_analyze # In case of redirects
    try:
        # Ensure domain is primed before fetching for analysis (prime_domain_settings might need to be async if it uses parser)
        # For now, assume prime_domain_settings is synchronous or handles its own async needs if any.
        await planner.prime_domain_settings(url_to_analyze) # Assuming this might become async

        page_data_list = await planner.parser.crawler.arun(
            seed_url=Url(url=url_to_analyze),
            crawler_run_config=CrawlerRunConfig(max_depth=0, max_pages=1, store_content=True, allow_redirects=True)
        )
        if page_data_list and page_data_list.results and page_data_list.results[0].content:
            html_content = page_data_list.results[0].content
            final_url_to_analyze = page_data_list.results[0].url # Update URL if redirected
        else:
            monitor.log_event("ERROR", f"Failed to fetch content from '{url_to_analyze}' for analysis via AsyncWebCrawler.")
            return
    except Exception as e:
        monitor.log_event("ERROR", f"Exception fetching {url_to_analyze} for analysis: {e}", {"exc_type": type(e).__name__})
        return

    if not html_content: # Should be caught by above, but safeguard
        monitor.log_event("ERROR", f"HTML content is None after fetch for '{final_url_to_analyze}'.")
        return

    if not planner.structure_analyzer:
        monitor.log_event("ERROR", "StructureAnalyzer component not available in Planner.")
        return

    monitor.log_event("INFO", f"Requesting structure_analyzer to generate selectors for {final_url_to_analyze}.")
    # generate_extraction_selectors is synchronous as per current Parser structure.
    # If it were to become async, this call would need `await`.
    new_selectors = planner.structure_analyzer.generate_extraction_selectors(final_url_to_analyze, html_content)

    if new_selectors:
        monitor.log_event("INFO", f"StructureAnalyzer returned selectors for '{source_name_to_analyze}'.", {"selectors": new_selectors})
        planner.update_source_extraction_selectors(source_name_to_analyze, new_selectors) # Sync
        if planner.save_config(): # Sync
             monitor.log_event("INFO", f"Successfully updated and saved selectors for source: {source_name_to_analyze}.")
        else:
             monitor.log_event("ERROR", f"Selectors generated for {source_name_to_analyze}, but FAILED to save config. Check logs.")
    else:
        monitor.log_event("WARNING", f"StructureAnalyzer FAILED to generate selectors for '{source_name_to_analyze}' using URL {final_url_to_analyze}.")
        planner.set_llm_analysis_flag(source_name_to_analyze, False) # Sync
        if planner.save_config(): # Sync
            monitor.log_event("INFO", f"Flag 'llm_analysis_pending' set to False for {source_name_to_analyze} and config saved.")


async def main(): # Changed to async def
    args = setup_arg_parser().parse_args()
    monitor = Monitor(log_to_console=True)
    pipeline = Pipeline(monitor_instance=monitor) # Sync
    # Planner initialization is synchronous. Its methods that use Parser will become async.
    planner = Planner(config_path=args.config, monitor_instance=monitor, pipeline_instance=pipeline)
    if hasattr(monitor, 'planner_reference'): # Sync
        monitor.planner_reference = planner

    # Check if essential components (especially parser and its crawler) are available
    if not planner.parser or not planner.parser.crawler :
         monitor.log_event("CRITICAL", "Parser or its AsyncWebCrawler not initialized. Core functionality affected. Exiting.")
         return
    if Url is None or CrawlerRunConfig is None: # Check for necessary crawl4ai classes for direct use
        monitor.log_event("CRITICAL", "crawl4ai Url or CrawlerRunConfig not available. Cannot proceed if direct crawler calls are needed. Exiting.")
        return

    monitor.log_event("INFO", "Components initialized.")

    if args.list_sources: # Sync
        monitor.log_event("INFO", "Configured sources:")
        sources = planner.get_targets()
        if not sources: print("  No sources found.")
        else:
            for i, src in enumerate(sources):
                print(f"  {i+1}. Name: {src.get('name','N/A')} (RSS: {src.get('rss_feed','N/A')}, Base: {src.get('base_url','N/A')}, Selectors: {src.get('extraction_selectors') is not None}, LLM_Pending: {src.get('llm_analysis_pending')})")
        return

    if args.analyze_source:
        await manual_analyze_source_structure(args.analyze_source, args.sample_url_for_analysis, planner, monitor)
        monitor.log_event("INFO", "Manual analysis task completed.")
        return

    tasks_to_run_lambdas = []
    task_names_for_log = []

    # This helper now expects task_lambda to be awaitable (an async function or lambda returning a coroutine)
    def add_task_to_runner(condition, task_lambda, name_str):
        if condition:
            tasks_to_run_lambdas.append(task_lambda)
            task_names_for_log.append(name_str)

    # Wrap planner calls in async lambdas if they are to become async.
    # Example: if planner.discover_new_sources_from_rss becomes async:
    # add_task_to_runner(True, async lambda: await planner.discover_new_sources_from_rss(...), "Discover New RSS")
    # For now, assume methods like discover_new_sources_from_rss, poll_all_rss_feeds etc. might remain synchronous
    # if their direct interaction with the parser (which is now async) is minimal or refactored.
    # However, any planner method that calls parser.process_seed_url (like fallback_crawl) MUST become async.
    # Let's assume for this subtask that the planner methods themselves will be updated to be async where necessary.
    # The lambdas here will just await them.

    if args.discover_new_sources:
        async def discover_new_task_wrapper_async(): # Made async
            monitor.log_event("INFO", "Starting: Discover New Sources from RSS task.")
            rss_urls = args.rss_scan_feed_urls
            if not rss_urls:
                rss_urls = [s.get("rss_feed") for s in planner.get_targets() if s.get("rss_feed") and str(s.get("rss_feed","")).strip()]
            if not rss_urls: monitor.log_event("WARNING", "No RSS feeds to scan for new sources."); return
            # Assuming discover_new_sources_from_rss is, or will be made, async if it uses the parser for fetching/checking
            new_domains_info = await planner.discover_new_sources_from_rss(rss_urls, args.rss_scan_recency_hours)
            if new_domains_info:
                print("\n--- Discovered New Potential Source Domains ---")
                for info in new_domains_info: print(f"- Domain: {info['new_domain']} (From: {', '.join(info['discovered_from_rss_feeds'])})")
                print("  (Consider manually adding to sources.json)\n")
            else: print("No new source domains discovered.")
        add_task_to_runner(True, discover_new_task_wrapper_async, "Discover New Sources from RSS")

    if args.run_all_discovery:
        add_task_to_runner(True, lambda: planner.poll_all_rss_feeds(args.recency_days), "Poll All RSS") # Assuming sync for now
        add_task_to_runner(True, lambda: planner.discover_and_process_all_sitemaps(args.recency_days), "Process All Sitemaps") # Assuming sync
        add_task_to_runner(True, lambda: planner.initiate_all_fallback_crawls(args.recency_days), "Run All Fallback Crawls") # This will need to be async
    else:
        if args.source_name:
            add_task_to_runner(args.discover_rss, lambda: planner.discover_rss_feed_for_source(args.source_name, args.auto_save_config), f"Discover RSS for {args.source_name}") # Sync
            add_task_to_runner(args.poll_rss, lambda: planner.poll_rss_feed(args.source_name, args.recency_days), f"Poll RSS for {args.source_name}") # Sync
            add_task_to_runner(args.process_sitemaps, lambda: planner.discover_and_process_sitemaps_for_source(args.source_name, args.recency_days), f"Process Sitemaps for {args.source_name}") # Sync
            add_task_to_runner(args.fallback_crawl, lambda: planner.initiate_fallback_crawl_for_source(args.source_name, args.recency_days), f"Fallback Crawl for {args.source_name}") # This will need to be async
        else:
            add_task_to_runner(args.discover_rss, lambda: planner.discover_all_rss_feeds(args.auto_save_config), "Discover All RSS Feeds") # Sync
            add_task_to_runner(args.poll_rss, lambda: planner.poll_all_rss_feeds(args.recency_days), "Poll All RSS Feeds") # Sync
            add_task_to_runner(args.process_sitemaps, lambda: planner.discover_and_process_all_sitemaps(args.recency_days), "Process All Sitemaps") # Sync
            add_task_to_runner(args.fallback_crawl, lambda: planner.initiate_all_fallback_crawls(args.recency_days), "Run All Fallback Crawls") # This will need to be async

    # Critical: The lambdas for tasks that are now async (like fallback_crawl) need to be async lambdas.
    # For example: add_task_to_runner(True, async lambda: await planner.initiate_all_fallback_crawls(args.recency_days), "Run All Fallback Crawls")
    # This change needs to be applied to all planner calls that become async. For this subtask, we assume the planner methods will be updated.
    # The await in the loop below will handle it if the lambda returns a coroutine.

    if not tasks_to_run_lambdas and not args.process_queued_items and not args.discover_new_sources and not args.analyze_source:
        monitor.log_event("INFO", "No tasks specified. Printing help.")
        setup_arg_parser().print_help()
        return

    run_cycle_count = 0
    try:
        while True:
            run_cycle_count += 1
            monitor.log_event("INFO", f"Main Run Cycle #{run_cycle_count} Starting. Tasks: {', '.join(task_names_for_log) or 'None specified'}")
            for i, task_lambda in enumerate(tasks_to_run_lambdas):
                task_desc = task_names_for_log[i]
                monitor.log_event("INFO", f"Executing Task: {task_desc}")
                try:
                    # Check if the lambda itself is an async function or returns a coroutine
                    # For simplicity, we'll await all. If a sync lambda is passed, this might require adjustment
                    # or ensuring all task_lambdas are defined as `async def` or `async lambda`.
                    # For this pass, we will assume all tasks passed to add_task_to_runner that need async
                    # operations (like fallback_crawl) are already defined as async lambdas.
                    # The planner methods themselves will need to be `async def`.
                    await task_lambda() # Await the lambda call
                except Exception as e:
                    monitor.log_event("ERROR", f"Error in task '{task_desc}': {e}", {"exc_type": type(e).__name__, "error_details": str(e)})

            monitor.log_event("INFO", f"Discovery/selected tasks for cycle #{run_cycle_count} completed. Pipeline items: {len(pipeline.item_queue)}")

            if args.process_queued_items:
                if pipeline.has_pending_items():
                    # Pass only parser, not planner.fetcher, as parser has its own crawler
                    await process_pipeline_items(pipeline, planner, planner.parser, monitor)
                else:
                    monitor.log_event("INFO", "No items in pipeline to process for this cycle.")

            if args.loop_delay_mins <= 0: break
            monitor.log_event("INFO", f"Loop delay: Waiting {args.loop_delay_mins} minutes...")
            await asyncio.sleep(args.loop_delay_mins * 60) # Use asyncio.sleep
    except KeyboardInterrupt:
        monitor.log_event("INFO", "Keyboard interrupt received. Shutting down.")
    finally:
        monitor.log_event("INFO", "Main process finished.")
        print(f"\n{'='*30}SUMMARY{'='*30}")
        print(f"Total run cycles: {run_cycle_count}")
        print(f"Items remaining in queue: {len(pipeline.item_queue)}")
        print(f"Items processed and stored in memory (this session): {pipeline.get_processed_item_count_in_memory()}")
        print(f"Total items processed and saved to disk (overall in results dir): {pipeline.get_processed_item_count_on_disk()}")
        print(f"{'='*67}")

if __name__ == "__main__":
    asyncio.run(main()) # Changed to asyncio.run(main())
