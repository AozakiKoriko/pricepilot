'use client';
export const runtime = 'edge';

import { useSearchParams } from 'next/navigation';
import React from 'react';

export default function ComparePage() {
  const searchParams = useSearchParams();
  const query = searchParams.get('q') || '';

  const mockProduct = {
    title: `Best prices for: "${query}"`,
    image: 'https://via.placeholder.com/300x300?text=Product+Image',
  };

  const mockPrices = [
    {
      store: 'Amazon',
      price: '$45.99',
      url: 'https://amazon.com/example-product',
    },
    {
      store: 'Walmart',
      price: '$48.50',
      url: 'https://walmart.com/example-product',
    },
    {
      store: 'Target',
      price: '$49.00',
      url: 'https://target.com/example-product',
    },
  ];

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-4 py-10 bg-white">
      <h1 className="text-2xl font-bold mb-4">{mockProduct.title}</h1>
      <img
        src={mockProduct.image}
        alt="Product"
        className="w-60 h-60 object-cover rounded-lg mb-6"
      />

      <div className="w-full max-w-xl space-y-4">
        {mockPrices.map((item, index) => (
          <div key={index} className="flex justify-between items-center border p-4 rounded-lg shadow-sm">
            <div>
              <p className="font-semibold">{item.store}</p>
              <p className="text-gray-700">{item.price}</p>
            </div>
            <div className="flex gap-3">
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              >
                Buy now
              </a>
              <button className="bg-gray-300 text-gray-800 px-4 py-2 rounded-lg">
                Add to wishlist
              </button>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}