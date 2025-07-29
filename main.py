from flask import Flask, request, jsonify
from scrapling.fetchers import StealthyFetcher
import subprocess
import os

app = Flask(__name__)

def initialize_camoufox():
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = subprocess.run(['camoufox', 'fetch'], 
                                  check=True, 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=120)
            print(f"Camoufox initialized successfully on attempt {attempt + 1}")
            print(f"Output: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Camoufox initialization failed on attempt {attempt + 1}: {e}")
            print(f"Error output: {e.stderr}")
        except subprocess.TimeoutExpired:
            print(f"Camoufox fetch timed out on attempt {attempt + 1}")
        except FileNotFoundError:
            print("Camoufox not found in PATH")
            break
    
    print("All Camoufox initialization attempts failed")
    return False

camoufox_ready = initialize_camoufox()

@app.route("/fetch", methods=["GET"])
def fetch_html():
    global camoufox_ready
    
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "url 파라미터가 필요해요"}), 400

    if not camoufox_ready:
        return jsonify({"error": "Camoufox is not initialized. Please try again later."}), 503
    
    try:
        scraper = StealthyFetcher.fetch(url, headless=True, network_idle=True)
        html = scraper.body  
        return jsonify({"html": html})
    except Exception as e:
        error_msg = str(e)
        if "version.json" in error_msg and "camoufox fetch" in error_msg:
            camoufox_ready = initialize_camoufox()
            if camoufox_ready:
                try:
                    scraper = StealthyFetcher.fetch(url, headless=True, network_idle=True)
                    html = scraper.body  
                    return jsonify({"html": html})
                except Exception as retry_e:
                    return jsonify({"error": f"Retry failed: {str(retry_e)}"}), 500
            else:
                try:
                    scraper = StealthyFetcher.fetch(url, headless=True, network_idle=True, browser='chromium')
                    html = scraper.body  
                    return jsonify({"html": html, "note": "Used fallback browser"})
                except Exception as fallback_e:
                    return jsonify({"error": f"Fallback also failed: {str(fallback_e)}"}), 500
        return jsonify({"error": error_msg}), 500

@app.route("/")
def home():
    return "✅ Scrapling REST API is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)