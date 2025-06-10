'use client';

import { useSearchParams, useRouter } from 'next/navigation';
import React from 'react';

export default function ConfirmPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const query = searchParams.get('q') || '';

  // 模拟搜索返回的商品数据
  const mockProduct = {
    title: `Search result for: "${query}"`,
    image: 'https://via.placeholder.com/300x300?text=Product+Preview',
    price: '$49.99',
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-4 bg-white">
      <h2 className="text-2xl font-semibold mb-4">Is this the product you want?</h2>
      <img src={mockProduct.image} alt="Product" className="rounded-lg w-60 h-60 object-cover mb-4" />
      <p className="text-lg font-medium mb-2">{mockProduct.title}</p>
      <p className="text-gray-600 mb-6">{mockProduct.price}</p>

      <div className="flex gap-4">
        <button
          className="bg-green-600 text-white px-6 py-2 rounded-lg"
          onClick={() => router.push(`/compare?q=${encodeURIComponent(query)}`)}
        >
          Yes, continue
        </button>
        <button
          className="bg-gray-300 text-gray-800 px-6 py-2 rounded-lg"
          onClick={() => router.push('/')}
        >
          No, go back
        </button>
      </div>
    </main>
  );
}