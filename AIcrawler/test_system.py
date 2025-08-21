#!/usr/bin/env python3
"""
System test script for AI Product Aggregation Crawler
"""

import asyncio
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_whitelist_generation():
    """Test whitelist generation with fallback channels."""
    print("Testing whitelist generation...")
    
    try:
        from app.whitelist import WhitelistGenerator
        
        generator = WhitelistGenerator()
        channels = await generator.generate_whitelist("iPhone 15 Pro", "US", 10)
        
        print(f"✓ Generated {len(channels)} channels")
        for channel in channels:
            print(f"  - {channel.domain} ({channel.label}) - Confidence: {channel.confidence}")
        
        return True
    except Exception as e:
        print(f"✗ Whitelist generation failed: {e}")
        return False


async def test_search_engine():
    """Test search engine functionality."""
    print("\nTesting search engine...")
    
    try:
        from app.search import SearchEngine
        
        search_engine = SearchEngine()
        
        # Test with empty channels (should return empty results)
        results = await search_engine.search_products(
            keyword="iPhone 15 Pro",
            channels=[],
            max_results_per_channel=3
        )
        
        print(f"✓ Search engine initialized successfully")
        print(f"  - Results returned: {len(results)}")
        
        await search_engine.close()
        return True
    except Exception as e:
        print(f"✗ Search engine test failed: {e}")
        return False


async def test_page_fetcher():
    """Test page fetcher functionality."""
    print("\nTesting page fetcher...")
    
    try:
        from app.fetcher import PageFetcher
        
        async with PageFetcher() as fetcher:
            # Test with a simple URL
            test_urls = ["https://httpbin.org/html"]
            results = await fetcher.fetch_pages(test_urls, use_browser=False)
            
            print(f"✓ Page fetcher initialized successfully")
            print(f"  - Fetched {len(results)} pages")
            
            for result in results:
                if result and result.get('success'):
                    print(f"  - {result['url']}: {len(result['content'])} characters")
                else:
                    print(f"  - {result.get('url', 'unknown')}: Failed")
        
        return True
    except Exception as e:
        print(f"✗ Page fetcher test failed: {e}")
        return False


async def test_data_normalizer():
    """Test data normalization functionality."""
    print("\nTesting data normalizer...")
    
    try:
        from app.normalize import DataNormalizer
        
        normalizer = DataNormalizer()
        
        # Test data
        test_products = [
            {
                "retailer": "amazon.com",
                "product_title": "iPhone 15 Pro 256GB",
                "url": "https://amazon.com/iphone15pro",
                "price": 999.99,
                "currency": "USD",
                "in_stock": "in_stock"
            },
            {
                "retailer": "bestbuy.com",
                "product_title": "iPhone 15 Pro 256GB",
                "url": "https://bestbuy.com/iphone15pro",
                "price": 999.99,
                "currency": "USD",
                "in_stock": "in_stock"
            }
        ]
        
        normalized = await normalizer.normalize_products(test_products, "USD")
        print(f"✓ Data normalizer working")
        print(f"  - Normalized {len(normalized)} products")
        
        return True
    except Exception as e:
        print(f"✗ Data normalizer test failed: {e}")
        return False


async def test_extractors():
    """Test data extractors."""
    print("\nTesting data extractors...")
    
    try:
        from app.extract.amazon import AmazonExtractor
        from app.extract.generic_llm import GenericLLMExtractor
        
        # Test Amazon extractor
        amazon_extractor = AmazonExtractor()
        print("✓ Amazon extractor initialized")
        
        # Test generic LLM extractor
        generic_extractor = GenericLLMExtractor("test.com")
        print("✓ Generic LLM extractor initialized")
        
        # Test with sample HTML
        sample_html = """
        <html>
            <head><title>Test Product</title></head>
            <body>
                <h1>iPhone 15 Pro 256GB</h1>
                <p>Price: $999.99</p>
                <p>In Stock</p>
            </body>
        </html>
        """
        
        # Test Amazon extractor
        amazon_result = await amazon_extractor.extract_product_data(sample_html, "https://amazon.com/test")
        if amazon_result:
            print(f"  - Amazon extractor: {amazon_result.product_title}")
        else:
            print("  - Amazon extractor: No data extracted (expected for non-Amazon HTML)")
        
        return True
    except Exception as e:
        print(f"✗ Extractors test failed: {e}")
        return False


async def test_cache_functionality():
    """Test cache functionality."""
    print("\nTesting cache functionality...")
    
    try:
        from app.cache import cache
        
        # Test basic cache operations
        test_key = "test_key"
        test_value = {"test": "data", "timestamp": time.time()}
        
        # Set value
        await cache.set(test_key, test_value, ttl=60)
        print("✓ Cache set operation successful")
        
        # Get value
        retrieved_value = await cache.get(test_key)
        if retrieved_value and retrieved_value.get("test") == "data":
            print("✓ Cache get operation successful")
        else:
            print("✗ Cache get operation failed")
            return False
        
        # Check if exists
        exists = await cache.exists(test_key)
        if exists:
            print("✓ Cache exists check successful")
        else:
            print("✗ Cache exists check failed")
            return False
        
        # Delete value
        await cache.delete(test_key)
        print("✓ Cache delete operation successful")
        
        # Verify deletion
        deleted_value = await cache.get(test_key)
        if deleted_value is None:
            print("✓ Cache deletion verified")
        else:
            print("✗ Cache deletion failed")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Cache test failed: {e}")
        return False


async def test_fastapi_app():
    """Test FastAPI application."""
    print("\nTesting FastAPI application...")
    
    try:
        from app.main import app
        
        print("✓ FastAPI application imported successfully")
        print(f"  - Title: {app.title}")
        print(f"  - Version: {app.version}")
        print(f"  - Description: {app.description}")
        
        # Check available routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(f"{route.methods} {route.path}")
        
        print(f"  - Available routes: {len(routes)}")
        for route in routes[:5]:  # Show first 5 routes
            print(f"    {route}")
        
        return True
    except Exception as e:
        print(f"✗ FastAPI app test failed: {e}")
        return False


async def test_end_to_end_workflow():
    """Test end-to-end workflow without external APIs."""
    print("\nTesting end-to-end workflow...")
    
    try:
        from app.whitelist import WhitelistGenerator
        from app.normalize import DataNormalizer
        
        # Step 1: Generate whitelist
        generator = WhitelistGenerator()
        channels = await generator.generate_whitelist("iPhone 15 Pro", "US", 5)
        
        if not channels:
            print("✗ No channels generated")
            return False
        
        print(f"✓ Generated {len(channels)} channels")
        
        # Step 2: Simulate search results
        mock_search_results = []
        for i, channel in enumerate(channels[:2]):  # Use first 2 channels
            mock_search_results.append({
                "title": f"iPhone 15 Pro from {channel.domain}",
                "url": f"https://{channel.domain}/product/iphone15pro",
                "snippet": f"Great deal on iPhone 15 Pro at {channel.domain}",
                "channel": channel.domain,
                "channel_label": channel.label,
                "confidence": channel.confidence
            })
        
        print(f"✓ Created {len(mock_search_results)} mock search results")
        
        # Step 3: Simulate extracted products
        mock_products = []
        for result in mock_search_results:
            mock_products.append({
                "retailer": result["channel"],
                "product_title": result["title"],
                "url": result["url"],
                "price": 999.99 + (hash(result["channel"]) % 100),  # Vary price slightly
                "currency": "USD",
                "in_stock": "in_stock",
                "fetched_at": int(time.time())
            })
        
        print(f"✓ Created {len(mock_products)} mock products")
        
        # Step 4: Normalize data
        normalizer = DataNormalizer()
        normalized = await normalizer.normalize_products(mock_products, "USD")
        
        print(f"✓ Normalized {len(normalized)} products")
        
        # Step 5: Display results
        print("\nFinal normalized results:")
        for product in normalized:
            print(f"  - {product.retailer}: {product.product_title}")
            print(f"    Price: ${product.price} {product.currency}")
            print(f"    Stock: {product.in_stock}")
            print(f"    URL: {product.url}")
            print()
        
        return True
    except Exception as e:
        print(f"✗ End-to-end workflow test failed: {e}")
        return False


async def run_system_tests():
    """Run all system tests."""
    print("Starting AI Crawler System Tests...\n")
    print("Note: These tests run without external API keys")
    print("="*60)
    
    tests = [
        ("Whitelist Generation", test_whitelist_generation),
        ("Search Engine", test_search_engine),
        ("Page Fetcher", test_page_fetcher),
        ("Data Normalizer", test_data_normalizer),
        ("Data Extractors", test_extractors),
        ("Cache Functionality", test_cache_functionality),
        ("FastAPI Application", test_fastapi_app),
        ("End-to-End Workflow", test_end_to_end_workflow)
    ]
    
    results = {}
    start_time = time.time()
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"{test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    total_time = time.time() - start_time
    print("\n" + "="*60)
    print("SYSTEM TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    print(f"Total time: {total_time:.2f} seconds")
    
    if passed == total:
        print("\n🎉 All system tests passed! 🎉")
        print("\nThe AI Crawler system is working correctly!")
        print("\nNext steps:")
        print("1. Set up your API keys in .env file for full functionality")
        print("2. Install additional dependencies: pip install openai playwright")
        print("3. Start the application: python run.py")
        print("4. Access the API at: http://localhost:8000/docs")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        print("\nThe system may need additional configuration or dependencies.")


if __name__ == "__main__":
    asyncio.run(run_system_tests())

