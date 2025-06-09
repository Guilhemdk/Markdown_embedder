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
from datetime import datetime, timezone # Needed for process_pipeline_items

# Adjust path for direct execution vs. module execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from news_scrapper.planner.planner import Planner
    from news_scrapper.pipeline.pipeline import Pipeline
    from news_scrapper.monitor.monitor import Monitor
    # Fetcher and Parser will be accessed via Planner instance
    from news_scrapper.config import SOURCES_CONFIG_PATH
except ImportError as e:
    print(f"Error importing components: {e}. Ensure all components exist and PYTHONPATH is set correctly.")
    print("If running from project root, try 'python -m news_scrapper.main'.")
    sys.exit(1)

def setup_arg_parser():
    """Sets up and returns the argument parser."""
    parser = argparse.ArgumentParser(description="News Scrapper: Discovers, fetches, parses, and stores news articles.")
    # ... (Existing args - no changes here for this step) ...
    parser.add_argument("--config", default=SOURCES_CONFIG_PATH, help=f"Path to sources JSON. Default: {SOURCES_CONFIG_PATH}")
    parser.add_argument("--discover-rss", action="store_true", help="Discover RSS feeds.")
    parser.add_argument("--poll-rss", action="store_true", help="Poll RSS feeds.")
    parser.add_argument("--process-sitemaps", action="store_true", help="Process sitemaps.")
    parser.add_argument("--fallback-crawl", action="store_true", help="Run fallback crawl.")
    parser.add_argument("--run-all-discovery", action="store_true", help="Run all discovery tasks (Poll, Sitemap, Fallback).")
    parser.add_argument("--source-name", type=str, default=None, help="Operate on a single source by name.")
    parser.add_argument("--recency-days", type=int, default=2, help="Days back to consider articles 'new'. Default: 2.")
    parser.add_argument("--auto-save-config", action="store_true", help="Save config changes (e.g., after RSS discovery).")
    parser.add_argument("--list-sources", action="store_true", help="List configured source names and exit.")
    parser.add_argument("--loop-delay-mins", type=int, default=0, help="Loop with this delay in minutes (0 for single run).")
    parser.add_argument(
        "--process-queued-items",
        action="store_true",
        help="After discovery tasks, process items currently in the pipeline queue (fetch full articles, parse, store)."
    )
    return parser

def process_pipeline_items(pipeline, fetcher, parser, monitor, polite_sleep_sec=0.1):
    """
    Processes items from the pipeline queue: fetches full article, parses, and stores.
    Args:
        pipeline (Pipeline): The pipeline instance with queued items.
        fetcher (Fetcher): The fetcher instance for getting article HTML.
        parser (Parser): The parser instance for processing HTML.
        monitor (Monitor): The monitor instance for logging.
        polite_sleep_sec (float): Small delay between processing items.
    """
    monitor.log_event("INFO", f"Starting processing of {len(pipeline.item_queue)} items from pipeline queue.")
    processed_count = 0

    if not fetcher or not parser:
        monitor.log_event("ERROR", "Fetcher or Parser not available in process_pipeline_items. Cannot process queue.")
        return processed_count

    while pipeline.has_pending_items():
        item_metadata = pipeline.get_next_item()
        if not item_metadata: continue # Should not happen if has_pending_items was true

        article_url = item_metadata.get('link') # 'link' is the common key for article URL
        item_id = item_metadata.get('id', article_url) # Use link as fallback ID

        if not article_url:
            monitor.log_event("WARNING", "Skipping item from queue: missing 'link' (article URL).", {"item_id": item_id})
            continue

        monitor.log_event("INFO", f"Processing item from queue: {article_url}", {"item_id": item_id, "title_snippet": item_metadata.get('title', 'N/A')[:50]})

        # Fetcher needs to be primed for the domain of article_url if not done before
        # This is crucial if items came from RSS/Sitemaps from different domains than the source's base_url
        # For simplicity, assuming Planner's priming during discovery was sufficient or fetcher handles it.
        # A more robust priming could be done here: planner.prime_domain_settings(article_url)

        html_content = fetcher.fetch_url(article_url)

        if html_content:
            # parser.parse_content is expected to return a dict with title, text, published_date_utc etc.
            parsed_article_data = parser.parse_content(html_content, article_url)

            if parsed_article_data:
                # Merge original metadata (e.g., from RSS) with newly parsed full content data.
                # Parsed data from full content should ideally take precedence for shared keys like 'title', 'published_date_utc'.
                final_article_data = {**item_metadata, **parsed_article_data}
                final_article_data['processed_timestamp_utc'] = datetime.now(timezone.utc).isoformat()

                pipeline.store_result(final_article_data) # This now saves to a file
                processed_count += 1
                monitor.log_event("INFO", f"Successfully processed and stored article.", {"url": article_url, "id": item_id})
            else:
                monitor.log_event("WARNING", "Failed to parse content for article.", {"url": article_url, "id": item_id})
        else:
            monitor.log_event("WARNING", "Failed to fetch HTML content for article.", {"url": article_url, "id": item_id})

        if polite_sleep_sec > 0:
            time.sleep(polite_sleep_sec) # Be polite if rapidly processing many items

    monitor.log_event("INFO", f"Finished processing pipeline queue. Processed {processed_count} items in this run.")
    return processed_count


def main():
    """Main function to orchestrate the news scraping process."""
    args = setup_arg_parser().parse_args()

    monitor = Monitor(log_to_console=True)
    pipeline = Pipeline(monitor_instance=monitor) # Uses config for RESULTS_DIR

    planner = Planner(config_path=args.config,
                      monitor_instance=monitor,
                      pipeline_instance=pipeline)

    if hasattr(monitor, 'planner_reference') and monitor.planner_reference is None:
         monitor.planner_reference = planner

    if not all([planner.fetcher, planner.parser, planner.pipeline, planner.monitor]):
        monitor.log_event("CRITICAL", "Main: Core components failed to initialize properly. Exiting.")
        return

    monitor.log_event("INFO", "Main: All components initialized successfully.")

    if args.list_sources:
        # ... (existing list_sources logic) ...
        monitor.log_event("INFO", "Listing configured sources:")
        sources = planner.get_targets()
        if not sources: print("  No sources found.")
        else:
            for i, source in enumerate(sources):
                print(f"  {i+1}. Name: {source.get('name', 'N/A')}\n     Base URL: {source.get('base_url', 'N/A')}\n     RSS Feed: {source.get('rss_feed', 'N/A')}")
        return

    tasks_to_run = []
    task_names_log = []
    # ... (existing task definition logic using add_task helper) ...
    def add_task(condition, func, name_template, is_global_task=True): # Simplified from previous version
        if condition:
            actual_func = func
            task_name_to_log = name_template
            if args.source_name and not is_global_task:
                actual_func = lambda: func(args.source_name) # Apply source_name if func expects it
                task_name_to_log = name_template.format(source_name=args.source_name)
            elif is_global_task : # Global tasks
                 task_name_to_log = name_template.format(source_name="ALL")

            tasks_to_run.append(actual_func)
            task_names_log.append(task_name_to_log)


    if args.run_all_discovery:
        monitor.log_event("INFO", "Main: --run-all-discovery specified.")
        add_task(True, lambda: planner.poll_all_rss_feeds(recency_delta_days=args.recency_days), "Poll All RSS Feeds")
        add_task(True, lambda: planner.discover_and_process_all_sitemaps(recency_delta_days=args.recency_days), "Process All Sitemaps")
        add_task(True, lambda: planner.initiate_all_fallback_crawls(recency_delta_days=args.recency_days), "Run All Fallback Crawls")
    else: # Specific tasks or single source operations
        if args.discover_rss:
             add_task(True, lambda: planner.discover_all_rss_feeds(persist_changes=args.auto_save_config) if not args.source_name else planner.discover_rss_feed_for_source(args.source_name, persist_changes=args.auto_save_config),
                     "Discover RSS for {source_name}", is_global_task=(not args.source_name))
        if args.poll_rss:
            add_task(True, lambda: planner.poll_all_rss_feeds(recency_delta_days=args.recency_days) if not args.source_name else planner.poll_rss_feed(args.source_name, recency_delta_days=args.recency_days),
                     "Poll RSS for {source_name}", is_global_task=(not args.source_name))
        if args.process_sitemaps:
            add_task(True, lambda: planner.discover_and_process_all_sitemaps(recency_delta_days=args.recency_days) if not args.source_name else planner.discover_and_process_sitemaps_for_source(args.source_name, recency_delta_days=args.recency_days),
                     "Process Sitemaps for {source_name}", is_global_task=(not args.source_name))
        if args.fallback_crawl:
            add_task(True, lambda: planner.initiate_all_fallback_crawls(recency_delta_days=args.recency_days) if not args.source_name else planner.initiate_fallback_crawl_for_source(args.source_name, recency_delta_days=args.recency_days),
                     "Fallback Crawl for {source_name}", is_global_task=(not args.source_name))


    if not tasks_to_run and not args.process_queued_items: # If no discovery tasks and not just processing queue
        if args.source_name:
             monitor.log_event("WARNING", f"Main: Source '{args.source_name}' provided, but no specific discovery action. Defaulting to all discovery for this source.")
             add_task(True, lambda: planner.poll_rss_feed(args.source_name, recency_delta_days=args.recency_days), "Poll RSS for {source_name}", False)
             add_task(True, lambda: planner.discover_and_process_sitemaps_for_source(args.source_name, recency_delta_days=args.recency_days), "Process Sitemaps for {source_name}", False)
             add_task(True, lambda: planner.initiate_fallback_crawl_for_source(args.source_name, recency_delta_days=args.recency_days), "Fallback Crawl for {source_name}", False)
        else:
            monitor.log_event("INFO", "Main: No specific discovery tasks. Consider --run-all-discovery or task flags. Will check --process-queued-items.")
            if not args.process_queued_items: # If also not processing queue, then print help
                 setup_arg_parser().print_help()
                 return


    run_counter = 0
    try:
        while True:
            run_counter += 1
            monitor.log_event("INFO", f"Main: Starting run cycle #{run_counter}. Discovery tasks: {', '.join(task_names_log) or 'None'}")

            for i, task_func_lambda in enumerate(tasks_to_run):
                task_name_str = task_names_log[i] # task_names_log should be populated correctly by add_task now
                monitor.log_event("INFO", f"Main: Executing discovery task -> {task_name_str}")
                try: task_func_lambda()
                except Exception as e:
                    monitor.log_event("ERROR", f"Main: Error during task '{task_name_str}': {e}",
                                      details={"exception_type": type(e).__name__, "args": str(e.args)})

            monitor.log_event("INFO", f"Main: Discovery tasks for cycle #{run_counter} completed. Pipeline contains {len(pipeline.item_queue)} items.")

            if args.process_queued_items:
                if pipeline.has_pending_items():
                    process_pipeline_items(pipeline, planner.fetcher, planner.parser, monitor)
                else:
                    monitor.log_event("INFO", "Main: No items in pipeline to process.")
            else:
                monitor.log_event("INFO", "Main: --process-queued-items not specified. Skipping item processing stage.")


            if args.loop_delay_mins > 0:
                monitor.log_event("INFO", f"Main: Waiting for {args.loop_delay_mins} minutes before next cycle...")
                time.sleep(args.loop_delay_mins * 60)
            else:
                break
    except KeyboardInterrupt:
        monitor.log_event("INFO", "Main: Keyboard interrupt received. Shutting down.")
    finally:
        monitor.log_event("INFO", "Main: Process finished.")
        queued_items = len(pipeline.item_queue)
        processed_in_memory = pipeline.get_processed_item_count_in_memory()
        processed_on_disk = pipeline.get_processed_item_count_on_disk()

        print(f"\n{'='*30}SUMMARY{'='*30}")
        print(f"Run finished.")
        print(f"Items remaining in queue: {queued_items}")
        print(f"Items processed and stored in memory (this session): {processed_in_memory}")
        print(f"Total items processed and saved to disk (overall): {processed_on_disk}")

        if processed_in_memory > 0:
            print(f"Last few items processed in this session (up to 5, from memory):")
            # Display a few items from processed_results_in_memory
            for i in range(min(processed_in_memory, 5)):
                item = pipeline.processed_results_in_memory[-(i+1)] # Last items
                print(f"  - [{item.get('type','N/A')}] {item.get('title','N/A')[:70]}... ({item.get('link')})")
        elif queued_items > 0 :
             print(f"First few items still in queue (up to 5):")
             for i in range(min(queued_items, 5)):
                item = pipeline.item_queue[i]
                print(f"  - [{item.get('type','N/A')}] {item.get('title','N/A')[:70]}... ({item.get('link')})")

        print(f"{'='*67}")
        monitor.log_event("INFO", f"Main: Final queue size: {queued_items}. In-memory results: {processed_in_memory}. On-disk results: {processed_on_disk}.")

if __name__ == "__main__":
    main()
