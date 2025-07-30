from __future__ import annotations

import asyncio
from uuid import uuid4
from typing import Dict, List, Optional
import json

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import HTMLResponse

import crawlee

from crawler import lifespan

app = FastAPI(lifespan=lifespan, title='Stealth Crawler API')


class ScrapeRequest(BaseModel):
    url: str
    selectors: Optional[Dict[str, str]] = None
    delay_range: Optional[List[float]] = None
    max_retries: Optional[int] = None
    timeout: Optional[int] = None


class BatchScrapeRequest(BaseModel):
    urls: List[str]
    selectors: Optional[Dict[str, str]] = None
    delay_range: Optional[List[float]] = None
    max_retries: Optional[int] = None
    timeout: Optional[int] = None


@app.get('/', response_class=HTMLResponse)
def index() -> str:
    return """
<!DOCTYPE html>
<html>
<body>
    <h1>Stealth Crawler API</h1>
    <h2>Endpoints:</h2>
    <ul>
        <li><strong>GET /scrape</strong> - Basic scraping (legacy)</li>
        <li><strong>POST /stealth-scrape</strong> - Advanced stealth scraping</li>
        <li><strong>POST /batch-scrape</strong> - Batch URL processing</li>
        <li><strong>GET /health</strong> - Health check</li>
    </ul>
    
    <h3>Examples:</h3>
    <p>Basic: <a href="/scrape?url=https://www.example.com">/scrape?url=https://www.example.com</a></p>
    <p>Stealth: POST /stealth-scrape with JSON body</p>
    
    <h3>API Documentation:</h3>
    <p><a href="/docs">Interactive API Docs</a></p>
</body>
</html>
"""


@app.get('/health')
async def health_check():
    return {'status': 'healthy', 'service': 'stealth-crawler-api'}


@app.get('/scrape')
async def scrape_url(request: Request, url: str | None = None) -> dict:
    """Legacy basic scraping endpoint"""
    if not url:
        return {'url': 'missing', 'scrape result': 'no results'}

    # Generate random unique key for the request
    unique_key = str(uuid4())

    # Set the result future in the result dictionary so that it can be awaited
    request.state.requests_to_results[unique_key] = asyncio.Future[dict[str, str]]()

    # Add the request to the crawler queue
    await request.state.crawler.add_requests(
        [crawlee.Request.from_url(url, unique_key=unique_key)]
    )

    # Wait for the result future to be finished
    result = await request.state.requests_to_results[unique_key]

    # Clean the result from the result dictionary to free up memory
    request.state.requests_to_results.pop(unique_key)

    # Return the result
    return {'url': url, 'scrape result': result}


@app.post('/stealth-scrape')
async def stealth_scrape(request: Request, scrape_req: ScrapeRequest) -> dict:
    """Advanced stealth scraping with customizable options"""
    try:
        # Run stealth crawler in thread pool
        loop = asyncio.get_event_loop()
        
        # Create custom crawler instance if needed
        stealth_crawler = request.state.stealth_crawler
        
        # Default selectors
        selectors = scrape_req.selectors or {
            'title': 'title',
            'description': 'meta[name="description"]',
            'h1': 'h1',
            'content': 'p, div.content, main, article'
        }
        
        # Run in executor to avoid blocking
        result = await loop.run_in_executor(
            request.state.executor,
            stealth_crawler.crawl_url,
            scrape_req.url,
            selectors
        )
        
        return {
            'success': True,
            'data': result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


@app.post('/batch-scrape')
async def batch_scrape(request: Request, batch_req: BatchScrapeRequest) -> dict:
    """Batch processing of multiple URLs"""
    if len(batch_req.urls) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 URLs allowed per batch")
    
    try:
        loop = asyncio.get_event_loop()
        stealth_crawler = request.state.stealth_crawler
        
        # Default selectors
        selectors = batch_req.selectors or {
            'title': 'title',
            'description': 'meta[name="description"]',
            'h1': 'h1'
        }
        
        # Process URLs in batches to avoid overwhelming
        results = []
        for url in batch_req.urls:
            result = await loop.run_in_executor(
                request.state.executor,
                stealth_crawler.crawl_url,
                url,
                selectors
            )
            results.append(result)
        
        successful = sum(1 for r in results if r.get('status') == 'success')
        
        return {
            'success': True,
            'total_urls': len(batch_req.urls),
            'successful': successful,
            'failed': len(batch_req.urls) - successful,
            'results': results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch scraping failed: {str(e)}")


@app.get('/config')
async def get_config():
    """Get current crawler configuration"""
    return {
        'delay_range': [1, 3],
        'max_retries': 3,
        'timeout': 30,
        'max_batch_size': 50,
        'default_selectors': {
            'title': 'title',
            'description': 'meta[name="description"]',
            'h1': 'h1'
        }
    }


@app.get('/status')
async def get_status(request: Request):
    """Get crawler status and statistics"""
    stealth_crawler = request.state.stealth_crawler
    
    return {
        'status': 'running',
        'visited_urls_count': len(stealth_crawler.visited_urls),
        'service': 'stealth-crawler-api',
        'version': '1.0.0'
    }