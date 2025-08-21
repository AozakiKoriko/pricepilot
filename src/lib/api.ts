// API service for communicating with AIcrawler backend

const API_BASE_URL = 'http://localhost:8000';

export interface ProductData {
  retailer: string;
  product_title: string;
  url: string;
  price: number;
  currency: string;
  in_stock: string;
  fetched_at: number;
  original_price?: number;
  availability_text?: string;
  image_url?: string;
  description?: string;
}

export interface SearchResponse {
  query: string;
  results: ProductData[];
  total_results: number;
  execution_time: number;
  channels_searched: string[];
}

export interface ChannelInfo {
  domain: string;
  name: string;
  relevance_score: number;
  search_results_count: number;
}

export class AICrawlerAPI {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  async searchProducts(query: string, maxResults: number = 20): Promise<SearchResponse> {
    try {
      const response = await fetch(
        `${this.baseURL}/search?query=${encodeURIComponent(query)}&max_results=${maxResults}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error searching products:', error);
      throw error;
    }
  }

  async getChannels(): Promise<ChannelInfo[]> {
    try {
      const response = await fetch(`${this.baseURL}/channels`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting channels:', error);
      throw error;
    }
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL}/health`);
      return response.ok;
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }
}

// Create a default instance
export const aiCrawlerAPI = new AICrawlerAPI();
