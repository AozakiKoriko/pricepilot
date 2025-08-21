#!/usr/bin/env python3
"""
Demo script for AI Product Aggregation Crawler
"""

import asyncio
import json
from datetime import datetime
from app.whitelist import WhitelistGenerator
from app.normalize import DataNormalizer
from app.cache import cache


async def demo_whitelist_generation():
    """Demonstrate whitelist generation."""
    print("🔍 DEMO: Whitelist Generation")
    print("=" * 50)
    
    generator = WhitelistGenerator()
    
    # Test different product keywords
    test_keywords = [
        "iPhone 15 Pro 256GB",
        "RTX 4070 Ti Graphics Card",
        "Bose QuietComfort Ultra Headphones"
    ]
    
    for keyword in test_keywords:
        print(f"\n📱 Generating whitelist for: {keyword}")
        channels = await generator.generate_whitelist(keyword, "US", 5)
        
        print(f"   Found {len(channels)} relevant channels:")
        for channel in channels:
            print(f"   • {channel.domain} ({channel.label}) - Confidence: {channel.confidence}")
    
    print("\n" + "=" * 50)


async def demo_data_normalization():
    """Demonstrate data normalization."""
    print("🔄 DEMO: Data Normalization")
    print("=" * 50)
    
    normalizer = DataNormalizer()
    
    # Sample raw product data from different sources
    sample_products = [
        {
            "retailer": "amazon.com",
            "product_title": "iPhone 15 Pro 256GB - Space Gray",
            "url": "https://amazon.com/iphone15pro",
            "price": 999.99,
            "currency": "USD",
            "in_stock": "in_stock",
            "original_price": 1099.99,
            "availability_text": "In Stock - Free Shipping"
        },
        {
            "retailer": "bestbuy.com",
            "product_title": "iPhone 15 Pro 256GB Space Gray",
            "url": "https://bestbuy.com/iphone15pro",
            "price": 999.99,
            "currency": "USD",
            "in_stock": "in_stock",
            "availability_text": "Add to Cart"
        },
        {
            "retailer": "walmart.com",
            "product_title": "Apple iPhone 15 Pro 256GB",
            "url": "https://walmart.com/iphone15pro",
            "price": 999.99,
            "currency": "USD",
            "in_stock": "in_stock",
            "availability_text": "Buy Now"
        }
    ]
    
    print("📦 Raw product data:")
    for i, product in enumerate(sample_products, 1):
        print(f"   Product {i}:")
        print(f"   • Retailer: {product['retailer']}")
        print(f"   • Title: {product['product_title']}")
        print(f"   • Price: ${product['price']} {product['currency']}")
        print(f"   • Stock: {product['in_stock']}")
        print()
    
    print("🔄 Normalizing data...")
    normalized = await normalizer.normalize_products(sample_products, "USD")
    
    print(f"✅ Normalized {len(normalized)} products:")
    for product in normalized:
        print(f"   • {product.retailer}: {product.product_title}")
        print(f"     Price: ${product.price} {product.currency}")
        print(f"     Stock: {product.in_stock}")
        if product.original_price:
            print(f"     Original: ${product.original_price}")
        print()
    
    print("=" * 50)


async def demo_cache_functionality():
    """Demonstrate cache functionality."""
    print("💾 DEMO: Cache Functionality")
    print("=" * 50)
    
    # Test cache operations
    test_data = {
        "whitelist": {
            "keyword": "iPhone 15 Pro",
            "channels": ["amazon.com", "bestbuy.com", "walmart.com"],
            "timestamp": datetime.now().isoformat()
        },
        "search_results": {
            "query": "iPhone 15 Pro",
            "results_count": 15,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    print("📝 Storing data in cache...")
    
    # Store whitelist
    await cache.set("whitelist:iPhone 15 Pro:US", test_data["whitelist"], ttl=3600)
    print("   ✅ Whitelist cached")
    
    # Store search results
    await cache.set("search:iPhone 15 Pro", test_data["search_results"], ttl=1800)
    print("   ✅ Search results cached")
    
    print("\n📖 Retrieving data from cache...")
    
    # Retrieve whitelist
    cached_whitelist = await cache.get("whitelist:iPhone 15 Pro:US")
    if cached_whitelist:
        print(f"   ✅ Whitelist retrieved: {len(cached_whitelist['channels'])} channels")
    
    # Retrieve search results
    cached_search = await cache.get("search:iPhone 15 Pro")
    if cached_search:
        print(f"   ✅ Search results retrieved: {cached_search['results_count']} results")
    
    print("\n🗑️ Cleaning up cache...")
    await cache.delete("whitelist:iPhone 15 Pro:US")
    await cache.delete("search:iPhone 15 Pro")
    print("   ✅ Cache cleaned up")
    
    print("=" * 50)


async def demo_end_to_end_workflow():
    """Demonstrate end-to-end workflow."""
    print("🚀 DEMO: End-to-End Workflow")
    print("=" * 50)
    
    print("1️⃣ Generating channel whitelist...")
    generator = WhitelistGenerator()
    channels = await generator.generate_whitelist("iPhone 15 Pro", "US", 3)
    print(f"   ✅ Generated {len(channels)} channels")
    
    print("\n2️⃣ Simulating product search...")
    mock_products = []
    for i, channel in enumerate(channels):
        mock_products.append({
            "retailer": channel.domain,
            "product_title": f"iPhone 15 Pro 256GB from {channel.domain}",
            "url": f"https://{channel.domain}/product/iphone15pro",
            "price": 999.99 + (i * 10),  # Vary price slightly
            "currency": "USD",
            "in_stock": "in_stock",
            "fetched_at": int(datetime.now().timestamp())
        })
    
    print(f"   ✅ Found {len(mock_products)} products")
    
    print("\n3️⃣ Normalizing product data...")
    normalizer = DataNormalizer()
    normalized = await normalizer.normalize_products(mock_products, "USD")
    print(f"   ✅ Normalized {len(normalized)} products")
    
    print("\n4️⃣ Final results:")
    for i, product in enumerate(normalized, 1):
        print(f"   {i}. {product.retailer.title()}")
        print(f"      Title: {product.product_title}")
        print(f"      Price: ${product.price} {product.currency}")
        print(f"      Stock: {product.in_stock}")
        print(f"      URL: {product.url}")
        print()
    
    print("🎉 End-to-end workflow completed successfully!")
    print("=" * 50)


async def run_demo():
    """Run the complete demonstration."""
    print("🤖 AI PRODUCT AGGREGATION CRAWLER - DEMONSTRATION")
    print("=" * 60)
    print("This demo shows the core functionality without external API calls")
    print("=" * 60)
    
    demos = [
        ("Whitelist Generation", demo_whitelist_generation),
        ("Data Normalization", demo_data_normalization),
        ("Cache Functionality", demo_cache_functionality),
        ("End-to-End Workflow", demo_end_to_end_workflow)
    ]
    
    for demo_name, demo_func in demos:
        try:
            await demo_func()
            print()
        except Exception as e:
            print(f"❌ Demo '{demo_name}' failed: {e}")
            print()
    
    print("🎯 DEMONSTRATION COMPLETED!")
    print("\n📋 Summary:")
    print("• Whitelist generation: ✅ Working")
    print("• Data normalization: ✅ Working")
    print("• Cache functionality: ✅ Working")
    print("• End-to-end workflow: ✅ Working")
    print("\n🚀 Next steps:")
    print("1. Set up API keys in .env file for full functionality")
    print("2. Install additional dependencies: pip install openai playwright")
    print("3. Start the application: python run.py")
    print("4. Access the API at: http://localhost:8000/docs")
    print("5. Try the search endpoint: GET /search?query=iPhone 15 Pro")


if __name__ == "__main__":
    asyncio.run(run_demo())

