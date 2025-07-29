from flask import Flask, request, jsonify
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.http import Request
import requests
from io import StringIO
import sys
import random
import time
from urllib.parse import urlparse
import json

app = Flask(__name__)

class StealthHeaders:
    @staticmethod
    def get_random_user_agent():
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
        return random.choice(user_agents)
    
    @staticmethod
    def get_stealth_headers(url):
        domain = urlparse(url).netloc
        return {
            'User-Agent': StealthHeaders.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Charset': 'UTF-8',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Referer': f'https://www.google.com/search?q={domain}',
        }

class SimpleSpider(scrapy.Spider):
    name = 'simple'
    
    def __init__(self, url=None, *args, **kwargs):
        super(SimpleSpider, self).__init__(*args, **kwargs)
        self.start_urls = [url] if url else []
        self.html_content = ""
    
    def parse(self, response):
        self.html_content = response.text
        return {'html': response.text}

@app.route("/fetch", methods=["GET"])
def fetch_html():
    url = request.args.get("url")
    method = request.args.get("method", "stealth").lower()  # stealth, cloudscraper, selenium, basic
    
    if not url:
        return jsonify({"error": "url 파라미터가 필요해요"}), 400
    
    if method == "cloudscraper":
        return fetch_with_cloudscraper(url)
    elif method == "selenium":
        return fetch_with_selenium(url)
    elif method == "stealth":
        return fetch_with_advanced_stealth(url)
    else:
        return fetch_without_js(url)

def fetch_with_js(url):
    try:
        from requests_html import HTMLSession
        
        session = HTMLSession()
        
        # 스텔스 헤더 적용
        headers = StealthHeaders.get_stealth_headers(url)
        session.headers.update(headers)
        
        # 랜덤 지연
        time.sleep(random.uniform(1, 3))
        
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        # JavaScript 실행
        response.html.render(timeout=20, wait=2)
        
        return jsonify({
            "html": response.html.html,
            "method": "JavaScript enabled"
        })
        
    except ImportError:
        return jsonify({"error": "requests-html not available"}), 500
    except Exception as e:
        return jsonify({"error": f"JS fetch failed: {str(e)}"}), 500

def fetch_without_js(url):
    try:
        # 랜덤 지연 추가 (1-3초)
        time.sleep(random.uniform(1, 3))
        
        # 스텔스 헤더 사용
        headers = StealthHeaders.get_stealth_headers(url)
        
        # 세션 사용으로 쿠키 유지
        session = requests.Session()
        session.headers.update(headers)
        
        # 재시도 로직
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = session.get(
                    url, 
                    timeout=30,
                    allow_redirects=True,
                    verify=True
                )
                response.raise_for_status()
                
                # 응답 검증 (봇 탐지 체크)
                html_content = response.text
                if len(html_content) > 1000 and 'noscript' not in html_content.lower():
                    return jsonify({
                        "html": html_content,
                        "method": "Static HTML"
                    })
                elif attempt < max_retries - 1:
                    # 다른 User-Agent로 재시도
                    session.headers.update({'User-Agent': StealthHeaders.get_random_user_agent()})
                    time.sleep(random.uniform(2, 5))
                    continue
                else:
                    return jsonify({
                        "html": html_content, 
                        "warning": "Content might be blocked by anti-bot",
                        "method": "Static HTML"
                    })
                    
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(1, 3))
                    continue
                else:
                    raise e
                    
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

def fetch_with_cloudscraper(url):
    """Cloudflare 우회용 CloudScraper"""
    try:
        import cloudscraper
        
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        # 랜덤 지연
        time.sleep(random.uniform(2, 5))
        
        response = scraper.get(url, timeout=30)
        response.raise_for_status()
        
        return jsonify({
            "html": response.text,
            "method": "CloudScraper (Cloudflare bypass)"
        })
        
    except ImportError:
        return jsonify({"error": "cloudscraper not available"}), 500
    except Exception as e:
        return jsonify({"error": f"CloudScraper failed: {str(e)}"}), 500

def fetch_with_selenium(url):
    """Undetected Chrome + Selenium Stealth 조합"""
    try:
        import undetected_chromedriver as uc
        from selenium.webdriver.chrome.options import Options
        from selenium_stealth import stealth
        
        # Chrome 옵션 설정
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-javascript")
        chrome_options.add_argument(f"--user-agent={StealthHeaders.get_random_user_agent()}")
        
        # Undetected ChromeDriver 생성
        driver = uc.Chrome(options=chrome_options, version_main=None)
        
        # Stealth 설정 적용
        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
        )
        
        # 페이지 로드
        driver.get(url)
        
        # 랜덤 대기
        time.sleep(random.uniform(3, 7))
        
        # JavaScript 활성화가 필요한 경우
        driver.execute_script("return document.readyState") == "complete"
        
        html_content = driver.page_source
        driver.quit()
        
        return jsonify({
            "html": html_content,
            "method": "Undetected Chrome + Selenium Stealth"
        })
        
    except ImportError as e:
        return jsonify({"error": f"Selenium dependencies not available: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Selenium failed: {str(e)}"}), 500

def fetch_with_advanced_stealth(url):
    """고급 스텔스 모드 (여러 기법 조합)"""
    try:
        from fake_useragent import UserAgent
        
        ua = UserAgent()
        
        # 세션 생성
        session = requests.Session()
        
        # 고급 헤더 설정
        headers = {
            'User-Agent': ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }
        
        session.headers.update(headers)
        
        # TLS 핑거프린팅 우회
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
        
        # 쿠키 시뮬레이션
        session.cookies.set('_ga', f'GA1.1.{random.randint(1000000000, 9999999999)}.{int(time.time())}')
        session.cookies.set('_gid', f'GA1.1.{random.randint(1000000000, 9999999999)}.{int(time.time())}')
        
        # 다단계 접근 시뮬레이션
        domain = urlparse(url).netloc
        
        # 1단계: 홈페이지 방문 시뮬레이션
        try:
            home_url = f"https://{domain}"
            session.get(home_url, timeout=10)
            time.sleep(random.uniform(1, 3))
        except:
            pass
        
        # 2단계: 검색 엔진에서 온 것처럼 Referer 설정
        session.headers.update({
            'Referer': f'https://www.google.com/search?q={domain}'
        })
        
        # 3단계: 실제 페이지 요청
        time.sleep(random.uniform(2, 5))
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        return jsonify({
            "html": response.text,
            "method": "Advanced Stealth (Multi-step)"
        })
        
    except ImportError:
        return jsonify({"error": "fake-useragent not available"}), 500
    except Exception as e:
        return jsonify({"error": f"Advanced stealth failed: {str(e)}"}), 500

@app.route("/")
def home():
    return """
    ✅ Advanced Anti-Bot Scraping API
    
    사용법:
    /fetch?url=URL&method=METHOD
    
    Methods:
    - basic: 기본 요청
    - stealth: 고급 스텔스 모드 (기본값)
    - cloudscraper: Cloudflare 우회
    - selenium: Undetected Chrome + Selenium
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)