'use client';
export const runtime = 'edge';

import React from 'react';

const mockWishlist = [
  {
    title: 'Apple AirPods Pro',
    image: 'https://via.placeholder.com/300x300?text=AirPods',
    price: '$199.99',
    url: 'https://amazon.com/example-airpods',
  },
  {
    title: 'Nintendo Switch',
    image: 'https://via.placeholder.com/300x300?text=Switch',
    price: '$289.00',
    url: 'https://walmart.com/example-switch',
  },
];

export default function WishlistPage() {
  return (
    <main className="min-h-screen bg-white px-4 py-10 flex flex-col items-center">
      <h1 className="text-3xl font-bold mb-6">Your Wishlist</h1>

      <div className="w-full max-w-3xl space-y-6">
        {mockWishlist.map((item, index) => (
          <div key={index} className="flex items-center justify-between border p-4 rounded-lg shadow-sm">
            <div className="flex items-center gap-4">
              <img
                src={item.image}
                alt={item.title}
                className="w-20 h-20 object-cover rounded"
              />
              <div>
                <p className="text-lg font-semibold">{item.title}</p>
                <p className="text-gray-700">Lowest price: {item.price}</p>
              </div>
            </div>
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              Buy now
            </a>
          </div>
        ))}
      </div>
    </main>
  );
}