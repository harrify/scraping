from flask import Flask, request, jsonify
from scrapling.fetchers import StealthyFetcher
import subprocess
import os

app = Flask(__name__)

def initialize_camoufox():
    try:
        subprocess.run(['camoufox', 'fetch'], check=True, capture_output=True)
        print("Camoufox initialized successfully")
    except subprocess.CalledProcessError as e:
        print(f"Camoufox initialization failed: {e}")
    except FileNotFoundError:
        print("Camoufox not found in PATH")

initialize_camoufox()

@app.route("/fetch", methods=["GET"])
def fetch_html():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "url 파라미터가 필요해요"}), 400

    try:
        scraper = StealthyFetcher.fetch(url, headless=True, network_idle=True)
        html = scraper.body  
        return jsonify({"html": html})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return "✅ Scrapling REST API is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)