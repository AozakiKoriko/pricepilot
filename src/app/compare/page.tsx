'use client';
export const runtime = 'edge';

import { useSearchParams } from 'next/navigation';
import React, { useState, useEffect } from 'react';
import { aiCrawlerAPI, ProductData, SearchResponse } from '@/lib/api';

export default function ComparePage() {
  const searchParams = useSearchParams();
  const query = searchParams.get('q') || '';
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [products, setProducts] = useState<ProductData[]>([]);

  useEffect(() => {
    if (query) {
      searchProducts();
    }
  }, [query]);

  const searchProducts = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Check if backend is available
      const isHealthy = await aiCrawlerAPI.healthCheck();
      if (!isHealthy) {
        throw new Error('Backend service is not available');
      }

      const results = await aiCrawlerAPI.searchProducts(query, 20);
      setSearchResults(results);
      setProducts(results.results);
    } catch (err) {
      console.error('Search failed:', err);
      setError(err instanceof Error ? err.message : 'Failed to search products');
      // Fallback to mock data if API fails
      setProducts(getMockProducts());
    } finally {
      setLoading(false);
    }
  };

  const getMockProducts = (): ProductData[] => [
    {
      retailer: 'Amazon',
      product_title: `Search result for: "${query}"`,
      url: 'https://amazon.com/example-product',
      price: 45.99,
      currency: 'USD',
      in_stock: 'in_stock',
      fetched_at: Date.now(),
      image_url: 'https://via.placeholder.com/300x300?text=Product+Image',
    },
    {
      retailer: 'Walmart',
      product_title: `Search result for: "${query}"`,
      url: 'https://walmart.com/example-product',
      price: 48.50,
      currency: 'USD',
      in_stock: 'in_stock',
      fetched_at: Date.now(),
      image_url: 'https://via.placeholder.com/300x300?text=Product+Image',
    },
    {
      retailer: 'Target',
      product_title: `Search result for: "${query}"`,
      url: 'https://target.com/example-product',
      price: 49.00,
      currency: 'USD',
      in_stock: 'in_stock',
      fetched_at: Date.now(),
      image_url: 'https://via.placeholder.com/300x300?text=Product+Image',
    },
  ];

  const formatPrice = (price: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(price);
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleString();
  };

  if (loading) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center px-4 py-10 bg-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold mb-2">Searching for best prices...</h2>
          <p className="text-gray-600">Query: "{query}"</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center px-4 py-10 bg-white">
        <div className="text-center max-w-md">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold mb-2">Search Failed</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <p className="text-sm text-gray-500 mb-4">Showing fallback data instead</p>
          <button
            onClick={searchProducts}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Retry Search
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-4 py-10 bg-white">
      <h1 className="text-2xl font-bold mb-4">
        {searchResults ? `Best prices for: "${query}"` : `Search results for: "${query}"`}
      </h1>
      
      {searchResults && (
        <div className="text-center mb-6 text-sm text-gray-600">
          <p>Found {searchResults.total_results} results in {searchResults.execution_time.toFixed(2)}s</p>
          <p>Searched {searchResults.channels_searched.length} channels</p>
        </div>
      )}

      <div className="w-full max-w-4xl space-y-4">
        {products.map((product, index) => (
          <div key={index} className="flex justify-between items-center border p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center gap-4 flex-1">
              {product.image_url && (
                <img
                  src={product.image_url}
                  alt={product.product_title}
                  className="w-20 h-20 object-cover rounded"
                  onError={(e) => {
                    e.currentTarget.src = 'https://via.placeholder.com/80x80?text=No+Image';
                  }}
                />
              )}
              <div className="flex-1">
                <p className="font-semibold text-lg">{product.product_title}</p>
                <p className="text-gray-700">{product.retailer}</p>
                <p className="text-sm text-gray-500">
                  Last updated: {formatDate(product.fetched_at)}
                </p>
                {product.availability_text && (
                  <p className="text-sm text-gray-600">{product.availability_text}</p>
                )}
              </div>
            </div>
            
            <div className="text-right mr-4">
              <p className="text-2xl font-bold text-green-600">
                {formatPrice(product.price, product.currency)}
              </p>
              {product.original_price && product.original_price > product.price && (
                <p className="text-sm text-gray-500 line-through">
                  {formatPrice(product.original_price, product.currency)}
                </p>
              )}
              <p className={`text-sm ${product.in_stock === 'in_stock' ? 'text-green-600' : 'text-red-600'}`}>
                {product.in_stock === 'in_stock' ? 'In Stock' : 'Out of Stock'}
              </p>
            </div>

            <div className="flex gap-3">
              <a
                href={product.url}
                target="_blank"
                rel="noopener noreferrer"
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Buy now
              </a>
              <button className="bg-gray-300 text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-400 transition-colors">
                Add to wishlist
              </button>
            </div>
          </div>
        ))}
      </div>

      {products.length === 0 && (
        <div className="text-center text-gray-500 mt-8">
          <p>No products found for "{query}"</p>
          <p className="text-sm">Try different keywords or check your search query</p>
        </div>
      )}
    </main>
  );
}