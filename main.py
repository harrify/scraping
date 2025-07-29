from flask import Flask, request, jsonify
from scrapling.fetchers import PlayWrightFetcher
import subprocess
import os

app = Flask(__name__)

def initialize_playwright():
    try:
        print("Installing Playwright browsers...")
        result = subprocess.run(['playwright', 'install'], 
                              check=True, 
                              capture_output=True, 
                              text=True, 
                              timeout=300)
        print("Playwright browsers installed successfully")
        print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Playwright installation failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        print("Playwright installation timed out")
        return False
    except FileNotFoundError:
        print("Playwright not found in PATH")
        return False

playwright_ready = initialize_playwright()

@app.route("/fetch", methods=["GET"])
def fetch_html():
    global playwright_ready
    
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "url 파라미터가 필요해요"}), 400
    
    if not playwright_ready:
        return jsonify({"error": "Playwright is not initialized. Please try again later."}), 503
    
    try:
        page = PlayWrightFetcher.fetch(
            url,
            headless=True,
            network_idle=True,
            stealth=True,
            hide_canvas=True,
            disable_webgl=True,
            google_search=True,
            timeout=30000
        )
        html = page.body
        return jsonify({"html": html})
    except Exception as e:
        error_msg = str(e)
        if "Executable doesn't exist" in error_msg or "playwright install" in error_msg:
            playwright_ready = initialize_playwright()
            if playwright_ready:
                try:
                    page = PlayWrightFetcher.fetch(
                        url,
                        headless=True,
                        network_idle=True,
                        stealth=True,
                        hide_canvas=True,
                        disable_webgl=True,
                        google_search=True,
                        timeout=30000
                    )
                    html = page.body
                    return jsonify({"html": html})
                except Exception as retry_e:
                    return jsonify({"error": f"Retry failed: {str(retry_e)}"}), 500
        return jsonify({"error": error_msg}), 500

@app.route("/")
def home():
    return "✅ Scrapling REST API is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)