from stealth_crawler import StealthCrawler

def example_usage():
    crawler = StealthCrawler(
        delay_range=(2, 5),
        max_retries=3,
        timeout=30,
        use_proxies=False
    )
    
    try:
        url = "https://example.com"
        
        custom_selectors = {
            'title': 'title',
            'heading': 'h1',
            'description': 'meta[name="description"]',
            'paragraphs': 'p'
        }
        
        result = crawler.crawl_url(url, custom_selectors)
        
        print("Crawl Result:")
        print(f"URL: {result['url']}")
        print(f"Status: {result.get('status', 'unknown')}")
        
        if 'data' in result:
            print("\nExtracted Data:")
            for key, value in result['data'].items():
                print(f"  {key}: {value[:100]}...")
        
        if 'links' in result:
            print(f"\nFound {len(result['links'])} links:")
            for link in result['links'][:5]:
                print(f"  - {link}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        crawler.close()

if __name__ == "__main__":
    example_usage()