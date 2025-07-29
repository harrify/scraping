from flask import Flask, request, jsonify
from scrapling.fetchers import PlayWrightFetcher

app = Flask(__name__)

@app.route("/fetch", methods=["GET"])
def fetch_html():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "url 파라미터가 필요해요"}), 400
    
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
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return "✅ Scrapling REST API is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)