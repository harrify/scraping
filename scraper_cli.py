#!/usr/bin/env python3
"""
Stealth Web Scraper CLI
A professional stealth web scraper with BeautifulSoup
"""

import argparse
import json
import csv
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import urlparse

from stealth_crawler import StealthCrawler


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('scraper.log')
        ]
    )


def load_urls_from_file(file_path: str) -> List[str]:
    """Load URLs from a text file (one URL per line)"""
    try:
        with open(file_path, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return urls
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return []


def save_results_json(results: List[Dict], output_file: str):
    """Save results to JSON file"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logging.info(f"Results saved to {output_file}")
    except Exception as e:
        logging.error(f"Error saving JSON: {e}")


def save_results_csv(results: List[Dict], output_file: str):
    """Save results to CSV file"""
    if not results:
        logging.warning("No results to save")
        return
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            if results and 'data' in results[0]:
                # Flatten the data structure for CSV
                flattened_results = []
                for result in results:
                    flat_result = {'url': result['url'], 'status': result.get('status', 'unknown')}
                    if 'data' in result:
                        flat_result.update(result['data'])
                    flattened_results.append(flat_result)
                
                if flattened_results:
                    fieldnames = flattened_results[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(flattened_results)
        
        logging.info(f"Results saved to {output_file}")
    except Exception as e:
        logging.error(f"Error saving CSV: {e}")


def validate_url(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def create_default_selectors() -> Dict[str, str]:
    """Create default CSS selectors for common data extraction"""
    return {
        'title': 'title',
        'description': 'meta[name="description"]',
        'keywords': 'meta[name="keywords"]',
        'h1': 'h1',
        'h2': 'h2',
        'links_count': 'a[href]',
        'images_count': 'img[src]'
    }


def main():
    parser = argparse.ArgumentParser(
        description="Professional Stealth Web Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -u https://example.com
  %(prog)s -f urls.txt -o results.json
  %(prog)s -u https://example.com --delay 2 5 --retries 5
  %(prog)s -f urls.txt -o results.csv --format csv --verbose
        """
    )
    
    # URL input options
    url_group = parser.add_mutually_exclusive_group(required=True)
    url_group.add_argument('-u', '--url', help='Single URL to scrape')
    url_group.add_argument('-f', '--file', help='File containing URLs (one per line)')
    
    # Output options
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('--format', choices=['json', 'csv'], default='json',
                       help='Output format (default: json)')
    
    # Crawler options
    parser.add_argument('--delay', nargs=2, type=float, default=[1, 3],
                       metavar=('MIN', 'MAX'), help='Delay range in seconds (default: 1 3)')
    parser.add_argument('--retries', type=int, default=3,
                       help='Max retries per URL (default: 3)')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Request timeout in seconds (default: 30)')
    
    # Proxy options
    parser.add_argument('--proxy', action='append',
                       help='Proxy server (can be used multiple times)')
    
    # Custom selectors
    parser.add_argument('--selectors', help='JSON file with custom CSS selectors')
    
    # Other options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose logging')
    parser.add_argument('--no-delay', action='store_true',
                       help='Disable random delays (not recommended)')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Prepare URLs
    urls = []
    if args.url:
        if not validate_url(args.url):
            logging.error(f"Invalid URL: {args.url}")
            sys.exit(1)
        urls = [args.url]
    elif args.file:
        urls = load_urls_from_file(args.file)
        if not urls:
            logging.error("No valid URLs found")
            sys.exit(1)
    
    # Load custom selectors if provided
    selectors = create_default_selectors()
    if args.selectors:
        try:
            with open(args.selectors, 'r') as f:
                custom_selectors = json.load(f)
                selectors.update(custom_selectors)
        except Exception as e:
            logging.error(f"Error loading selectors: {e}")
            sys.exit(1)
    
    # Setup crawler
    delay_range = (0, 0) if args.no_delay else tuple(args.delay)
    proxy_list = args.proxy if args.proxy else []
    
    crawler = StealthCrawler(
        delay_range=delay_range,
        max_retries=args.retries,
        timeout=args.timeout,
        use_proxies=bool(proxy_list),
        proxy_list=proxy_list
    )
    
    try:
        logging.info(f"Starting to scrape {len(urls)} URLs...")
        
        results = []
        for i, url in enumerate(urls, 1):
            logging.info(f"Processing {i}/{len(urls)}: {url}")
            
            result = crawler.crawl_url(url, selectors)
            results.append(result)
            
            if result.get('status') == 'success':
                logging.info(f"✓ Successfully scraped: {url}")
            else:
                logging.warning(f"✗ Failed to scrape: {url}")
        
        # Output results
        if args.output:
            if args.format == 'csv':
                save_results_csv(results, args.output)
            else:
                save_results_json(results, args.output)
        else:
            # Print to stdout
            if args.format == 'csv':
                logging.info("CSV output requires --output file")
            else:
                print(json.dumps(results, indent=2, ensure_ascii=False))
        
        # Summary
        successful = sum(1 for r in results if r.get('status') == 'success')
        logging.info(f"Scraping completed: {successful}/{len(urls)} successful")
        
    except KeyboardInterrupt:
        logging.info("Scraping interrupted by user")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        crawler.close()


if __name__ == "__main__":
    main()