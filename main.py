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
    js_enabled = request.args.get("js", "false").lower() == "true"
    
    if not url:
        return jsonify({"error": "url 파라미터가 필요해요"}), 400
    
    if js_enabled:
        return fetch_with_js(url)
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

@app.route("/")
def home():
    return "✅ Scrapy REST API is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)