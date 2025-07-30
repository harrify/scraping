import asyncio
import random
import time
from typing import Optional, Dict, List
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


class StealthCrawler:
    def __init__(self, 
                 delay_range: tuple = (1, 3),
                 max_retries: int = 3,
                 timeout: int = 30,
                 use_proxies: bool = False,
                 proxy_list: Optional[List[str]] = None):
        
        self.ua = UserAgent()
        self.session = requests.Session()
        self.delay_range = delay_range
        self.max_retries = max_retries
        self.timeout = timeout
        self.use_proxies = use_proxies
        self.proxy_list = proxy_list or []
        self.visited_urls = set()
        
        self._setup_headers()
    
    def _setup_headers(self):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }
        self.session.headers.update(headers)
    
    def _get_random_user_agent(self) -> str:
        return self.ua.random
    
    def _get_random_proxy(self) -> Optional[Dict[str, str]]:
        if not self.use_proxies or not self.proxy_list:
            return None
        
        proxy = random.choice(self.proxy_list)
        return {
            'http': proxy,
            'https': proxy
        }
    
    def _random_delay(self):
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        if url in self.visited_urls:
            return None
        
        for attempt in range(self.max_retries):
            try:
                self.session.headers['User-Agent'] = self._get_random_user_agent()
                
                proxies = self._get_random_proxy()
                
                response = self.session.get(
                    url,
                    proxies=proxies,
                    timeout=self.timeout,
                    allow_redirects=True
                )
                
                response.raise_for_status()
                
                self.visited_urls.add(url)
                
                soup = BeautifulSoup(response.content, 'html.parser')
                return soup
                
            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    self._random_delay()
                    continue
                else:
                    print(f"Failed to fetch {url} after {self.max_retries} attempts")
                    return None
        
        return None
    
    def fetch_raw_html(self, url: str) -> Optional[str]:
        """Fetch raw HTML content without parsing"""        
        for attempt in range(self.max_retries):
            try:
                # Update headers for each request
                self.session.headers.update({
                    'User-Agent': self._get_random_user_agent(),
                    'Referer': 'https://www.google.com/',
                    'Origin': 'https://www.skyscanner.co.kr' if 'skyscanner' in url else None
                })
                
                # Remove None values
                self.session.headers = {k: v for k, v in self.session.headers.items() if v is not None}
                
                proxies = self._get_random_proxy()
                
                # Add random delay before request
                self._random_delay()
                
                response = self.session.get(
                    url,
                    proxies=proxies,
                    timeout=self.timeout,
                    allow_redirects=True,
                    verify=True
                )
                
                print(f"Response status: {response.status_code}")
                print(f"Response headers: {dict(response.headers)}")
                
                response.raise_for_status()
                
                self.visited_urls.add(url)
                
                return response.text
                
            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1} failed for {url}: {e}")
                if hasattr(e.response, 'status_code'):
                    print(f"Status code: {e.response.status_code}")
                    if e.response.status_code == 403:
                        print("Access forbidden - likely bot detection")
                    elif e.response.status_code == 503:
                        print("Service unavailable - rate limited")
                
                if attempt < self.max_retries - 1:
                    # Longer delay on failure
                    time.sleep(random.uniform(3, 8))
                    continue
                else:
                    print(f"Failed to fetch {url} after {self.max_retries} attempts")
                    return None
        
        return None
    
    def extract_data(self, soup: BeautifulSoup, selectors: Dict[str, str]) -> Dict[str, str]:
        data = {}
        
        for key, selector in selectors.items():
            try:
                if selector.startswith('//'):
                    continue
                
                element = soup.select_one(selector)
                if element:
                    data[key] = element.get_text(strip=True)
                else:
                    data[key] = ""
                    
            except Exception as e:
                print(f"Error extracting {key} with selector {selector}: {e}")
                data[key] = ""
        
        return data
    
    def get_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            if urlparse(full_url).netloc:
                links.append(full_url)
        
        return links
    
    def crawl_url(self, url: str, selectors: Dict[str, str] = None) -> Dict:
        if selectors is None:
            selectors = {
                'title': 'title',
                'description': 'meta[name="description"]',
                'h1': 'h1'
            }
        
        self._random_delay()
        
        soup = self.fetch_page(url)
        if not soup:
            return {'url': url, 'error': 'Failed to fetch page'}
        
        data = self.extract_data(soup, selectors)
        links = self.get_links(soup, url)
        
        return {
            'url': url,
            'data': data,
            'links': links[:20],
            'status': 'success'
        }
    
    def crawl_multiple(self, urls: List[str], selectors: Dict[str, str] = None) -> List[Dict]:
        results = []
        
        for url in urls:
            result = self.crawl_url(url, selectors)
            results.append(result)
            
        return results
    
    def close(self):
        self.session.close()