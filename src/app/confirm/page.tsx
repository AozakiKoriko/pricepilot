'use client';

import { useSearchParams, useRouter } from 'next/navigation';
import React, { useState, useEffect } from 'react';
import { aiCrawlerAPI, ProductData } from '@/lib/api';

export const dynamic = 'force-dynamic'; // 强制动态渲染，防止预渲染报错
export const runtime = 'edge'; // 指定运行时为 edge，确保不参与 server 构建

export default function ConfirmPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const query = searchParams.get('q') || '';

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [previewProduct, setPreviewProduct] = useState<ProductData | null>(null);

  useEffect(() => {
    if (query) {
      fetchPreviewData();
    }
  }, [query]);

  const fetchPreviewData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Check if backend is available
      const isHealthy = await aiCrawlerAPI.healthCheck();
      if (!isHealthy) {
        throw new Error('Backend service is not available');
      }

      // Get a preview of search results
      const results = await aiCrawlerAPI.searchProducts(query, 1);
      if (results.results.length > 0) {
        setPreviewProduct(results.results[0]);
      } else {
        // Fallback to mock data
        setPreviewProduct(getMockProduct());
      }
    } catch (err) {
      console.error('Preview fetch failed:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch preview');
      // Fallback to mock data
      setPreviewProduct(getMockProduct());
    } finally {
      setLoading(false);
    }
  };

  const getMockProduct = (): ProductData => ({
    retailer: 'Preview',
    product_title: `Search result for: "${query}"`,
    url: 'https://via.placeholder.com/300x300?text=Product+Preview',
    price: 49.99,
    currency: 'USD',
    in_stock: 'in_stock',
    fetched_at: Date.now(),
    image_url: 'https://via.placeholder.com/300x300?text=Product+Preview',
  });

  const formatPrice = (price: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(price);
  };

  if (loading) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center px-4 bg-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold mb-2">Loading preview...</h2>
          <p className="text-gray-600">Query: "{query}"</p>
        </div>
      </main>
    );
  }

  if (error && !previewProduct) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center px-4 bg-white">
        <div className="text-center max-w-md">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold mb-2">Preview Failed</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <p className="text-sm text-gray-500 mb-4">Showing fallback data instead</p>
          <button
            onClick={fetchPreviewData}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-4 bg-white">
      <h2 className="text-2xl font-semibold mb-4">Is this the product you want?</h2>
      
      {previewProduct && (
        <>
          {previewProduct.image_url && (
            <img 
              src={previewProduct.image_url} 
              alt="Product" 
              className="rounded-lg w-60 h-60 object-cover mb-4"
              onError={(e) => {
                e.currentTarget.src = 'https://via.placeholder.com/300x300?text=Product+Preview';
              }}
            />
          )}
          <p className="text-lg font-medium mb-2">{previewProduct.product_title}</p>
          <p className="text-gray-600 mb-2">{previewProduct.retailer}</p>
          <p className="text-2xl font-bold text-green-600 mb-2">
            {formatPrice(previewProduct.price, previewProduct.currency)}
          </p>
          <p className={`text-sm mb-6 ${previewProduct.in_stock === 'in_stock' ? 'text-green-600' : 'text-red-600'}`}>
            {previewProduct.in_stock === 'in_stock' ? 'In Stock' : 'Out of Stock'}
          </p>
        </>
      )}

      <div className="flex gap-4">
        <button
          className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors"
          onClick={() => router.push(`/compare?q=${encodeURIComponent(query)}`)}
        >
          Yes, continue
        </button>
        <button
          className="bg-gray-300 text-gray-800 px-6 py-2 rounded-lg hover:bg-gray-400 transition-colors"
          onClick={() => router.push('/')}
        >
          No, go back
        </button>
      </div>
    </main>
  );
}