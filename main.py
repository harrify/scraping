from flask import Flask, request, jsonify
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.http import Request
import requests
from io import StringIO
import sys

app = Flask(__name__)

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
    if not url:
        return jsonify({"error": "url 파라미터가 필요해요"}), 400
    
    try:
        # requests를 사용한 간단한 방법 (Scrapy는 비동기라서 Flask와 함께 사용하기 복잡함)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        return jsonify({"html": response.text})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return "✅ Scrapy REST API is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)