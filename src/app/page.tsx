'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { aiCrawlerAPI } from '@/lib/api';
import { backendStatusManager, BackendStatus } from '@/lib/status';

export default function Home() {
  const [input, setInput] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [backendStatus, setBackendStatus] = useState<BackendStatus>({
    isConnected: false,
    lastCheck: null,
    error: null,
    channels: [],
  });
  const router = useRouter();

  useEffect(() => {
    // Subscribe to backend status updates
    const unsubscribe = backendStatusManager.subscribe(setBackendStatus);
    
    // Check backend status on mount
    checkBackendStatus();
    
    return unsubscribe;
  }, []);

  const checkBackendStatus = async () => {
    try {
      const isHealthy = await aiCrawlerAPI.healthCheck();
      if (isHealthy) {
        const channels = await aiCrawlerAPI.getChannels();
        backendStatusManager.updateStatus({
          isConnected: true,
          lastCheck: new Date(),
          error: null,
          channels: channels.map(c => c.name),
        });
      } else {
        backendStatusManager.updateStatus({
          isConnected: false,
          lastCheck: new Date(),
          error: 'Backend service is not responding',
          channels: [],
        });
      }
    } catch (error) {
      backendStatusManager.updateStatus({
        isConnected: false,
        lastCheck: new Date(),
        error: error instanceof Error ? error.message : 'Connection failed',
        channels: [],
      });
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    setIsSearching(true);
    try {
      // Navigate to confirm page
      router.push(`/confirm?q=${encodeURIComponent(input.trim())}`);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-gray-50 px-4">
      {/* Backend Status Indicator */}
      <div className="absolute top-4 right-4">
        <div className={`flex items-center gap-2 px-3 py-2 rounded-full text-sm ${
          backendStatus.isConnected 
            ? 'bg-green-100 text-green-800' 
            : 'bg-red-100 text-red-800'
        }`}>
          <div className={`w-2 h-2 rounded-full ${
            backendStatus.isConnected ? 'bg-green-500' : 'bg-red-500'
          }`}></div>
          <span>
            {backendStatus.isConnected ? 'AI Service Online' : 'AI Service Offline'}
          </span>
        </div>
      </div>

      <div className="text-center max-w-2xl">
        <h1 className="text-4xl md:text-5xl font-bold mb-6 text-center bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          Never miss a deal again.
        </h1>
        
        <p className="text-lg text-gray-600 mb-8">
          AI-powered price comparison across multiple retailers. Find the best prices instantly.
        </p>

        <form onSubmit={handleSearch} className="w-full max-w-xl mx-auto flex flex-col items-center gap-4">
          <div className="relative w-full">
            <input
              type="text"
              placeholder="Paste a product link or enter keywords"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="w-full px-4 py-4 border border-gray-300 rounded-lg text-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
              disabled={isSearching}
            />
            {isSearching && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
              </div>
            )}
          </div>
          
          <button
            type="submit"
            disabled={isSearching || !input.trim()}
            className={`w-full px-8 py-4 rounded-lg text-lg font-semibold transition-all duration-200 ${
              isSearching || !input.trim()
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl transform hover:-translate-y-0.5'
            }`}
          >
            {isSearching ? 'Searching...' : 'Find Best Prices'}
          </button>
        </form>

        {/* Backend Info */}
        {backendStatus.isConnected && backendStatus.channels.length > 0 && (
          <div className="mt-8 p-4 bg-white rounded-lg shadow-sm border">
            <p className="text-sm text-gray-600 mb-2">
              Connected to {backendStatus.channels.length} retailers
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {backendStatus.channels.slice(0, 5).map((channel, index) => (
                <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                  {channel}
                </span>
              ))}
              {backendStatus.channels.length > 5 && (
                <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                  +{backendStatus.channels.length - 5} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* Error Message */}
        {backendStatus.error && (
          <div className="mt-4 p-3 bg-red-100 text-red-800 rounded-lg text-sm">
            <p>⚠️ {backendStatus.error}</p>
            <button
              onClick={checkBackendStatus}
              className="mt-2 text-red-700 underline hover:no-underline"
            >
              Retry connection
            </button>
          </div>
        )}
      </div>
    </main>
  );
}