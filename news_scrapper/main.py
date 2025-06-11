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
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from planner.planner import Planner
    from pipeline.pipeline import Pipeline
    from monitor.monitor import Monitor
    from config import SOURCES_CONFIG_PATH
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

def process_pipeline_items(pipeline, planner, fetcher, parser, monitor, polite_sleep_sec=0.1):
    monitor.log_event("INFO", f"Starting processing of {len(pipeline.item_queue)} items from pipeline queue.")
    processed_count = 0
    if not planner or not fetcher or not parser:
        monitor.log_event("ERROR", "Planner, Fetcher or Parser not available in process_pipeline_items.")
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
            source_config = planner.get_source_by_name(item_source_name)
            if not source_config:
                monitor.log_event("WARNING", f"No source_config for '{item_source_name}'. Parser will use defaults.", {"url": article_url})
                source_config = {}
        else:
            monitor.log_event("WARNING", "Item metadata missing 'source_name'. Parser will use defaults.", {"url": article_url})

        html_content = fetcher.fetch_url(article_url)
        if html_content:
            parsed_article_data = parser.parse_content(html_content, article_url, source_config)
            if parsed_article_data:
                final_article_data = {**item_metadata, **parsed_article_data}
                final_article_data['processed_timestamp_utc'] = datetime.now(timezone.utc).isoformat()
                pipeline.store_result(final_article_data)
                processed_count += 1
            else: monitor.log_event("WARNING", "Failed to parse content.", {"url": article_url, "source": item_source_name})
        else: monitor.log_event("WARNING", "Failed to fetch HTML.", {"url": article_url, "source": item_source_name})
        if polite_sleep_sec > 0: time.sleep(polite_sleep_sec)
    monitor.log_event("INFO", f"Finished processing queue. Processed {processed_count} items.")
    return processed_count

def manual_analyze_source_structure(source_name_to_analyze, sample_url_override, planner, monitor):
    """Handles the --analyze-source task."""
    monitor.log_event("INFO", f"Manual trigger for structure analysis: {source_name_to_analyze}")
    source_config = planner.get_source_by_name(source_name_to_analyze)
    if not source_config:
        monitor.log_event("ERROR", f"Source '{source_name_to_analyze}' not found in configuration.")
        return

    url_to_analyze = sample_url_override if sample_url_override else source_config.get("base_url")
    if not url_to_analyze:
        monitor.log_event("ERROR", f"No URL available for analysis (no --sample-url-for-analysis and no base_url for '{source_name_to_analyze}').")
        return

    monitor.log_event("INFO", f"Fetching content from '{url_to_analyze}' for structure analysis.")
    # Ensure domain is primed before fetching for analysis
    planner.prime_domain_settings(url_to_analyze)
    html_content = planner.fetcher.fetch_url(url_to_analyze)

    if not html_content:
        monitor.log_event("ERROR", f"Failed to fetch content from '{url_to_analyze}' for analysis.")
        return

    if not planner.structure_analyzer:
        monitor.log_event("ERROR", "StructureAnalyzer component not available in Planner.")
        return

    monitor.log_event("INFO", f"Requesting structure_analyzer to generate selectors for {url_to_analyze}.")
    # For now, assuming generate_extraction_selectors is what we want for manual trigger.
    # Could be extended to also call generate_index_page_selectors if a different flag is used.
    new_selectors = planner.structure_analyzer.generate_extraction_selectors(url_to_analyze, html_content)

    if new_selectors:
        monitor.log_event("INFO", f"StructureAnalyzer returned selectors for '{source_name_to_analyze}'.", {"selectors": new_selectors})
        planner.update_source_extraction_selectors(source_name_to_analyze, new_selectors)
        if planner.save_config(): # save_config should ideally return True/False or raise error
             monitor.log_event("INFO", f"Successfully updated and saved selectors for source: {source_name_to_analyze}.")
        else: # This else branch might not be hit if save_config logs its own errors
             monitor.log_event("ERROR", f"Selectors generated for {source_name_to_analyze}, but FAILED to save config. Check logs.")
    else:
        monitor.log_event("WARNING", f"StructureAnalyzer FAILED to generate selectors for '{source_name_to_analyze}' using URL {url_to_analyze}.")
        # Optionally set llm_analysis_pending to False here too, even on failure, to prevent immediate auto-retries
        planner.set_llm_analysis_flag(source_name_to_analyze, False)
        if planner.save_config():
            monitor.log_event("INFO", f"Flag 'llm_analysis_pending' set to False for {source_name_to_analyze} and config saved.")


def main():
    args = setup_arg_parser().parse_args()
    monitor = Monitor(log_to_console=True)
    pipeline = Pipeline(monitor_instance=monitor)
    planner = Planner(config_path=args.config, monitor_instance=monitor, pipeline_instance=pipeline)
    if hasattr(monitor, 'planner_reference'): monitor.planner_reference = planner

    if not all([planner.fetcher, planner.parser, planner.pipeline, planner.monitor, planner.structure_analyzer]):
        monitor.log_event("CRITICAL", "Core components failed to initialize. Exiting.")
        return
    monitor.log_event("INFO", "Components initialized.")

    if args.list_sources:
        monitor.log_event("INFO", "Configured sources:")
        sources = planner.get_targets()
        if not sources: print("  No sources found.")
        else:
            for i, src in enumerate(sources):
                print(f"  {i+1}. Name: {src.get('name','N/A')} (RSS: {src.get('rss_feed','N/A')}, Base: {src.get('base_url','N/A')}, Selectors: {src.get('extraction_selectors') is not None}, LLM_Pending: {src.get('llm_analysis_pending')})")
        return

    # --- Handle Manual Structure Analysis (Exclusive Task) ---
    if args.analyze_source:
        manual_analyze_source_structure(args.analyze_source, args.sample_url_for_analysis, planner, monitor)
        monitor.log_event("INFO", "Manual analysis task completed.")
        return # Typically, manual analysis is a standalone action.

    tasks_to_run_lambdas = []
    task_names_for_log = []
    def add_task_to_runner(condition, task_lambda, name_str): # Renamed from add_task to avoid conflict
        if condition:
            tasks_to_run_lambdas.append(task_lambda)
            task_names_for_log.append(name_str)

    if args.discover_new_sources: # ... (same as before)
        def discover_new_task_wrapper():
            monitor.log_event("INFO", "Starting: Discover New Sources from RSS task.")
            rss_urls = args.rss_scan_feed_urls
            if not rss_urls:
                rss_urls = [s.get("rss_feed") for s in planner.get_targets() if s.get("rss_feed") and str(s.get("rss_feed","")).strip()]
            if not rss_urls: monitor.log_event("WARNING", "No RSS feeds to scan for new sources."); return
            new_domains_info = planner.discover_new_sources_from_rss(rss_urls, args.rss_scan_recency_hours)
            if new_domains_info:
                print("\n--- Discovered New Potential Source Domains ---")
                for info in new_domains_info: print(f"- Domain: {info['new_domain']} (From: {', '.join(info['discovered_from_rss_feeds'])})")
                print("  (Consider manually adding to sources.json)\n")
            else: print("No new source domains discovered.")
        add_task_to_runner(True, discover_new_task_wrapper, "Discover New Sources from RSS")

    if args.run_all_discovery: # ... (same as before)
        add_task_to_runner(True, lambda: planner.poll_all_rss_feeds(args.recency_days), "Poll All RSS")
        add_task_to_runner(True, lambda: planner.discover_and_process_all_sitemaps(args.recency_days), "Process All Sitemaps")
        add_task_to_runner(True, lambda: planner.initiate_all_fallback_crawls(args.recency_days), "Run All Fallback Crawls")
    else: # ... (same as before for specific tasks)
        if args.source_name:
            add_task_to_runner(args.discover_rss, lambda: planner.discover_rss_feed_for_source(args.source_name, args.auto_save_config), f"Discover RSS for {args.source_name}")
            add_task_to_runner(args.poll_rss, lambda: planner.poll_rss_feed(args.source_name, args.recency_days), f"Poll RSS for {args.source_name}")
            add_task_to_runner(args.process_sitemaps, lambda: planner.discover_and_process_sitemaps_for_source(args.source_name, args.recency_days), f"Process Sitemaps for {args.source_name}")
            add_task_to_runner(args.fallback_crawl, lambda: planner.initiate_fallback_crawl_for_source(args.source_name, args.recency_days), f"Fallback Crawl for {args.source_name}")
        else:
            add_task_to_runner(args.discover_rss, lambda: planner.discover_all_rss_feeds(args.auto_save_config), "Discover All RSS Feeds")
            add_task_to_runner(args.poll_rss, lambda: planner.poll_all_rss_feeds(args.recency_days), "Poll All RSS Feeds")
            add_task_to_runner(args.process_sitemaps, lambda: planner.discover_and_process_all_sitemaps(args.recency_days), "Process All Sitemaps")
            add_task_to_runner(args.fallback_crawl, lambda: planner.initiate_all_fallback_crawls(args.recency_days), "Run All Fallback Crawls")

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
                try: task_lambda()
                except Exception as e: monitor.log_event("ERROR", f"Error in task '{task_desc}': {e}", {"exc_type": type(e).__name__})

            monitor.log_event("INFO", f"Discovery/selected tasks for cycle #{run_cycle_count} completed. Pipeline items: {len(pipeline.item_queue)}")

            if args.process_queued_items:
                if pipeline.has_pending_items():
                    process_pipeline_items(pipeline, planner, planner.fetcher, planner.parser, monitor)
                else: monitor.log_event("INFO", "No items in pipeline to process for this cycle.")

            if args.loop_delay_mins <= 0: break
            monitor.log_event("INFO", f"Loop delay: Waiting {args.loop_delay_mins} minutes...")
            time.sleep(args.loop_delay_mins * 60)
    except KeyboardInterrupt:
        monitor.log_event("INFO", "Keyboard interrupt received. Shutting down.")
    finally:
        monitor.log_event("INFO", "Main process finished.")
        print(f"\n{'='*30}SUMMARY{'='*30}")
        # ... (summary print logic - same as before) ...
        print(f"Total run cycles: {run_cycle_count}")
        print(f"Items remaining in queue: {len(pipeline.item_queue)}")
        print(f"Items processed and stored in memory (this session): {pipeline.get_processed_item_count_in_memory()}")
        print(f"Total items processed and saved to disk (overall in results dir): {pipeline.get_processed_item_count_on_disk()}")
        print(f"{'='*67}")

if __name__ == "__main__":
    main()
