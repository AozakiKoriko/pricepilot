'use client';

import React, { useState } from 'react';

export default function Home() {
  const [input, setInput] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('User input:', input);
    // Future: Send input to API for product detection
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-gray-50 px-4">
      <h1 className="text-3xl md:text-4xl font-bold mb-6 text-center">
        Never miss a deal again.
      </h1>

      <form onSubmit={handleSearch} className="w-full max-w-xl flex flex-col items-center gap-4">
        <input
          type="text"
          placeholder="Paste a product link or enter keywords"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg text-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg text-lg"
        >
          Search
        </button>
      </form>
    </main>
  );
}