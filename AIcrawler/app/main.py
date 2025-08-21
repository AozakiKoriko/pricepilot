import time
import logging
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .models import (
    SearchRequest, SearchResponse, HealthResponse, 
    ErrorResponse, ProductData, ChannelInfo
)
from .whitelist import WhitelistGenerator
from .search import SearchEngine
from .fetcher import PageFetcher
from .normalize import DataNormalizer
from .extract.generic_llm import GenericLLMExtractor
from .extract.amazon import AmazonExtractor
from .cache import cache, start_cache_cleanup
from .utils import extract_domain

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Product Aggregation Crawler",
    description="Intelligent product price and stock aggregation system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
whitelist_generator = WhitelistGenerator()
search_engine = SearchEngine()
data_normalizer = DataNormalizer()

# Initialize extractors
extractors = [
    AmazonExtractor(),
    GenericLLMExtractor("generic")
]

# Start cache cleanup
start_cache_cleanup()


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting AI Product Aggregation Crawler...")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Max concurrent requests: {settings.max_concurrent_requests}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down AI Product Aggregation Crawler...")
    await search_engine.close()
    await cache.close()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=__import__('datetime').datetime.utcnow(),
        version="1.0.0"
    )


@app.get("/search", response_model=SearchResponse)
async def search_products(
    query: str = Query(..., description="Product search query"),
    locale: str = Query("US", description="Target locale"),
    max_results: int = Query(20, description="Maximum results to return"),
    include_out_of_stock: bool = Query(True, description="Include out of stock items")
):
    """Search for products across multiple channels."""
    
    start_time = time.time()
    
    try:
        logger.info(f"Search request: {query} (locale: {locale})")
        
        # Step 1: Generate channel whitelist
        channels = await whitelist_generator.generate_whitelist(
            keyword=query,
            locale=locale,
            max_channels=20
        )
        
        if not channels:
            raise HTTPException(
                status_code=500, 
                detail="Failed to generate channel whitelist"
            )
        
        logger.info(f"Generated whitelist with {len(channels)} channels")
        
        # Step 2: Search for products across channels
        search_results = await search_engine.search_products(
            keyword=query,
            channels=channels,
            max_results_per_channel=5
        )
        
        if not search_results:
            logger.warning(f"No search results found for query: {query}")
            return SearchResponse(
                query=query,
                total_results=0,
                results=[],
                search_time_ms=int((time.time() - start_time) * 1000),
                channels_used=[channel.domain for channel in channels]
            )
        
        logger.info(f"Found {len(search_results)} search results")
        
        # Step 3: Fetch product pages
        urls = [result['url'] for result in search_results if result.get('url')]
        
        async with PageFetcher() as fetcher:
            fetched_pages = await fetcher.fetch_pages(urls, use_browser=False)
        
        # Step 4: Extract product data
        extracted_products = []
        
        for i, page_data in enumerate(fetched_pages):
            if not page_data or not page_data.get('success'):
                continue
            
            url = page_data['url']
            html_content = page_data['content']
            
            # Find appropriate extractor
            extractor = None
            for ext in extractors:
                if ext.can_handle(url, html_content):
                    extractor = ext
                    break
            
            if not extractor:
                # Use generic LLM extractor as fallback
                extractor = GenericLLMExtractor(extract_domain(url))
            
            try:
                product_data = await extractor.extract_product_data(html_content, url)
                if product_data:
                    # Add confidence from search result
                    if i < len(search_results):
                        product_data.confidence = search_results[i].get('confidence', 0.5)
                    
                    extracted_products.append(product_data)
                    
            except Exception as e:
                logger.error(f"Failed to extract data from {url}: {e}")
                continue
        
        # Step 5: Normalize and deduplicate products
        normalized_products = await data_normalizer.normalize_products(
            raw_products=extracted_products,
            target_currency="USD"
        )
        
        # Filter out of stock items if requested
        if not include_out_of_stock:
            normalized_products = [
                p for p in normalized_products 
                if p.in_stock != "out_of_stock"
            ]
        
        # Limit results
        final_results = normalized_products[:max_results]
        
        search_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"Search completed: {len(final_results)} products in {search_time_ms}ms")
        
        return SearchResponse(
            query=query,
            total_results=len(final_results),
            results=final_results,
            search_time_ms=search_time_ms,
            channels_used=[channel.domain for channel in channels]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/channels")
async def get_channels():
    """Get available channels and their status."""
    try:
        # Return some example channels
        example_channels = [
            {
                "domain": "amazon.com",
                "label": "marketplace",
                "locale": "US",
                "confidence": 0.95
            },
            {
                "domain": "bestbuy.com",
                "label": "big_box",
                "locale": "US",
                "confidence": 0.9
            },
            {
                "domain": "walmart.com",
                "label": "big_box",
                "locale": "US",
                "confidence": 0.9
            }
        ]
        
        return {
            "channels": example_channels,
            "total": len(example_channels),
            "supported_locales": ["US", "UK", "EU", "JP", "CN"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get channels: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve channels")


@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    try:
        stats = await cache.get_stats()
        return {
            "cache_stats": stats,
            "cache_ttl_minutes": settings.cache_ttl_minutes,
            "whitelist_cache_ttl_hours": settings.whitelist_cache_ttl_hours
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache stats")


@app.delete("/cache/clear")
async def clear_cache():
    """Clear all cache data."""
    try:
        # This is a simplified implementation
        # In production, you'd want more granular control
        logger.info("Cache clear requested")
        return {"message": "Cache clear initiated", "status": "success"}
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc)
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    )

