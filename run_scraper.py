#!/usr/bin/env python3
"""
Production-ready Stealth Web Scraper
Main executable script with configuration support
"""

import json
import sys
from pathlib import Path
from scraper_cli import main as cli_main
from stealth_crawler import StealthCrawler


def load_config(config_path: str = "config.json") -> dict:
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Config file {config_path} not found. Using defaults.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing config file: {e}")
        return {}


def quick_scrape(url: str, output_file: str = None):
    """Quick scrape function for single URL"""
    config = load_config()
    crawler_settings = config.get('crawler_settings', {})
    
    crawler = StealthCrawler(
        delay_range=tuple(crawler_settings.get('delay_range', [2, 5])),
        max_retries=crawler_settings.get('max_retries', 3),
        timeout=crawler_settings.get('timeout', 30)
    )
    
    try:
        selectors = config.get('default_selectors', {})
        result = crawler.crawl_url(url, selectors)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Results saved to {output_file}")
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return result
    
    finally:
        crawler.close()


def main():
    """Main entry point"""
    if len(sys.argv) == 1:
        print("Stealth Web Scraper")
        print("==================")
        print()
        print("Usage:")
        print("  python run_scraper.py <url>              # Quick scrape single URL")
        print("  python scraper_cli.py [options]          # Full CLI interface")
        print()
        print("Examples:")
        print("  python run_scraper.py https://example.com")
        print("  python scraper_cli.py -u https://example.com -o results.json")
        print("  python scraper_cli.py -f urls.txt --format csv -o results.csv")
        print()
        print("For full options, run: python scraper_cli.py --help")
        return
    
    # Quick mode: single URL argument
    if len(sys.argv) == 2 and sys.argv[1].startswith('http'):
        url = sys.argv[1]
        print(f"Quick scraping: {url}")
        quick_scrape(url)
        return
    
    # Pass to full CLI
    cli_main()


if __name__ == "__main__":
    main()