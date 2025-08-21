#!/usr/bin/env python3
"""
Simple test script for AI Product Aggregation Crawler
"""

import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_basic_imports():
    """Test basic module imports."""
    print("Testing basic module imports...")
    
    try:
        # Test config
        from app.config import settings
        print("✓ Config module imported successfully")
        print(f"  - Log level: {settings.log_level}")
        print(f"  - Max concurrent requests: {settings.max_concurrent_requests}")
        
        # Test models
        from app.models import ProductData, ChannelInfo
        print("✓ Models module imported successfully")
        
        # Test utils
        from app.utils import extract_domain, clean_text, extract_price
        print("✓ Utils module imported successfully")
        
        # Test basic functions
        domain = extract_domain("https://www.amazon.com/product/123")
        print(f"  - Domain extraction test: {domain}")
        
        cleaned = clean_text("  Test   Text  ")
        print(f"  - Text cleaning test: '{cleaned}'")
        
        price = extract_price("$999.99")
        print(f"  - Price extraction test: {price}")
        
        return True
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False


async def test_data_models():
    """Test data model creation and validation."""
    print("\nTesting data models...")
    
    try:
        from app.models import ProductData, ChannelInfo
        
        # Test ChannelInfo
        channel = ChannelInfo(
            domain="amazon.com",
            label="marketplace",
            locale="US",
            confidence=0.95
        )
        print("✓ ChannelInfo created successfully")
        print(f"  - Domain: {channel.domain}")
        print(f"  - Label: {channel.label}")
        
        # Test ProductData
        product = ProductData(
            retailer="Amazon",
            product_title="iPhone 15 Pro 256GB",
            url="https://amazon.com/iphone15pro",
            price=999.99,
            currency="USD",
            in_stock="in_stock",
            fetched_at=int(datetime.now().timestamp())
        )
        print("✓ ProductData created successfully")
        print(f"  - Title: {product.product_title}")
        print(f"  - Price: {product.price} {product.currency}")
        print(f"  - Stock: {product.in_stock}")
        
        return True
        
    except Exception as e:
        print(f"✗ Data model test failed: {e}")
        return False


async def test_utils_functions():
    """Test utility functions."""
    print("\nTesting utility functions...")
    
    try:
        from app.utils import (
            extract_domain, normalize_url, extract_price, 
            extract_currency, determine_stock_status,
            calculate_similarity, clean_text
        )
        
        # Test domain extraction
        test_urls = [
            "https://www.amazon.com/product/123",
            "http://bestbuy.com/item/456",
            "walmart.com/deal/789",
            "https://www.target.com/p/abc"
        ]
        
        print("Domain extraction tests:")
        for url in test_urls:
            domain = extract_domain(url)
            print(f"  - {url} → {domain}")
        
        # Test URL normalization
        print("\nURL normalization tests:")
        normalized = normalize_url("/product/123", "amazon.com")
        print(f"  - /product/123 → {normalized}")
        
        # Test price extraction
        print("\nPrice extraction tests:")
        price_texts = ["$999.99", "1,299.99 USD", "€899.99", "£799.99"]
        for text in price_texts:
            price = extract_price(text)
            currency = extract_currency(text)
            print(f"  - {text} → Price: {price}, Currency: {currency}")
        
        # Test stock status
        print("\nStock status tests:")
        stock_texts = [
            "In Stock", "Out of Stock", "Add to Cart", 
            "Currently Unavailable", "Sold Out"
        ]
        for text in stock_texts:
            status = determine_stock_status(text)
            print(f"  - {text} → {status}")
        
        # Test text similarity
        print("\nText similarity tests:")
        text1 = "iPhone 15 Pro 256GB"
        text2 = "iPhone 15 Pro 256GB Space Gray"
        similarity = calculate_similarity(text1, text2)
        print(f"  - Similarity between '{text1}' and '{text2}': {similarity:.2f}")
        
        # Test text cleaning
        print("\nText cleaning tests:")
        dirty_text = "  This   is   a   test   text  "
        cleaned = clean_text(dirty_text)
        print(f"  - Before: '{dirty_text}'")
        print(f"  - After:  '{cleaned}'")
        
        return True
        
    except Exception as e:
        print(f"✗ Utils test failed: {e}")
        return False


async def test_configuration():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    try:
        from app.config import settings, get_llm_api_key, get_search_api_key
        
        print("Configuration loaded successfully:")
        print(f"  - Log level: {settings.log_level}")
        print(f"  - Max concurrent requests: {settings.max_concurrent_requests}")
        print(f"  - Cache TTL: {settings.cache_ttl_minutes} minutes")
        print(f"  - Rate limit per domain: {settings.rate_limit_per_domain}")
        print(f"  - User agent: {settings.user_agent[:50]}...")
        
        # Test API key functions
        llm_key = get_llm_api_key()
        search_key = get_search_api_key()
        
        print(f"  - LLM API key available: {'Yes' if llm_key else 'No'}")
        print(f"  - Search API key available: {'Yes' if search_key else 'No'}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


async def run_simple_tests():
    """Run all simple tests."""
    print("Starting AI Crawler Simple Tests...\n")
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Data Models", test_data_models),
        ("Utility Functions", test_utils_functions),
        ("Configuration", test_configuration)
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
    print("SIMPLE TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("All simple tests passed! 🎉")
        print("\nNext steps:")
        print("1. Set up your API keys in .env file")
        print("2. Install additional dependencies: pip install openai playwright")
        print("3. Run the full test suite: python test_crawler.py")
    else:
        print("Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(run_simple_tests())

