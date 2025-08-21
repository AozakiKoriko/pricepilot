#!/usr/bin/env python3
"""
Test script for AI Product Aggregation Crawler
"""

import asyncio
import logging
from app.whitelist import WhitelistGenerator
from app.search import SearchEngine
from app.fetcher import PageFetcher
from app.normalize import DataNormalizer
from app.extract.generic_llm import GenericLLMExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_whitelist_generation():
    """Test whitelist generation."""
    print("Testing whitelist generation...")
    
    try:
        generator = WhitelistGenerator()
        channels = await generator.generate_whitelist("iPhone 15 Pro", "US", 10)
        
        print(f"Generated {len(channels)} channels:")
        for channel in channels:
            print(f"  - {channel.domain} ({channel.label}) - Confidence: {channel.confidence}")
        
        return True
    except Exception as e:
        print(f"Whitelist generation failed: {e}")
        return False


async def test_search_engine():
    """Test search engine."""
    print("\nTesting search engine...")
    
    try:
        search_engine = SearchEngine()
        
        # Test with a simple query
        results = await search_engine.search_products(
            keyword="iPhone 15 Pro",
            channels=[],  # Empty channels for basic test
            max_results_per_channel=3
        )
        
        print(f"Search returned {len(results)} results")
        return True
    except Exception as e:
        print(f"Search engine test failed: {e}")
        return False


async def test_page_fetcher():
    """Test page fetcher."""
    print("\nTesting page fetcher...")
    
    try:
        async with PageFetcher() as fetcher:
            # Test with a simple URL
            test_urls = ["https://httpbin.org/html"]
            results = await fetcher.fetch_pages(test_urls, use_browser=False)
            
            print(f"Fetched {len(results)} pages")
            for result in results:
                if result and result.get('success'):
                    print(f"  - {result['url']}: {len(result['content'])} characters")
                else:
                    print(f"  - {result.get('url', 'unknown')}: Failed")
        
        return True
    except Exception as e:
        print(f"Page fetcher test failed: {e}")
        return False


async def test_data_normalizer():
    """Test data normalizer."""
    print("\nTesting data normalizer...")
    
    try:
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
        print(f"Normalized {len(normalized)} products")
        
        return True
    except Exception as e:
        print(f"Data normalizer test failed: {e}")
        return False


async def test_llm_extractor():
    """Test LLM extractor."""
    print("\nTesting LLM extractor...")
    
    try:
        # This test requires an API key
        extractor = GenericLLMExtractor("test.com")
        
        # Simple HTML content for testing
        test_html = """
        <html>
            <head><title>Test Product</title></head>
            <body>
                <h1>iPhone 15 Pro 256GB</h1>
                <p>Price: $999.99</p>
                <p>In Stock</p>
            </body>
        </html>
        """
        
        result = await extractor.extract_product_data(test_html, "https://test.com/product")
        
        if result:
            print(f"Extracted product: {result.product_title}")
            print(f"Price: {result.price} {result.currency}")
            print(f"Stock: {result.in_stock}")
        else:
            print("No product data extracted")
        
        return True
    except Exception as e:
        print(f"LLM extractor test failed: {e}")
        return False


async def run_all_tests():
    """Run all tests."""
    print("Starting AI Crawler tests...\n")
    
    tests = [
        ("Whitelist Generation", test_whitelist_generation),
        ("Search Engine", test_search_engine),
        ("Page Fetcher", test_page_fetcher),
        ("Data Normalizer", test_data_normalizer),
        ("LLM Extractor", test_llm_extractor)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"{test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! 🎉")
    else:
        print("Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(run_all_tests())

