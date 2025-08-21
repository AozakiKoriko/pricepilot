# AI Product Aggregation Crawler (MVP)

An intelligent product price and stock aggregation system that uses LLM-generated whitelists to crawl multiple e-commerce channels.

## Features

- **LLM-Driven Channel Whitelist**: Automatically generates relevant e-commerce domains based on product keywords
- **Multi-Channel Aggregation**: Collects data from multiple retailers simultaneously
- **Intelligent Data Extraction**: Rule-based parsing with LLM fallback
- **Rate Limiting & Compliance**: Respects robots.txt and ai.txt
- **Real-time Data**: Price and stock information with cache expiration

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

2. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run the Application**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **API Usage**
   ```bash
   curl "http://localhost:8000/search?query=iPhone%2015%20Pro%20256GB"
   ```

## Architecture

- **Whitelist Layer**: LLM generates channel whitelist based on keywords
- **Search Layer**: Domain-restricted search using search APIs
- **Fetch Layer**: Page crawling with Playwright/httpx
- **Extract Layer**: Rule-based parsing with LLM fallback
- **Normalize**: Standardized data format
- **Cache**: SQLite/Redis with TTL

## API Endpoints

- `GET /search?query={keyword}`: Search for products across channels
- `GET /health`: Health check
- `GET /channels`: List available channels

## Data Format

```json
[
  {
    "retailer": "BestBuy",
    "product_title": "MSI GeForce RTX 4070 Ti",
    "url": "https://www.bestbuy.com/...",
    "price": 749.99,
    "currency": "USD",
    "in_stock": "in_stock",
    "fetched_at": 1724130000
  }
]
```

## Configuration

- Set your LLM API keys in `.env`
- Configure rate limits and cache TTL in `config.py`
- Add custom site adapters in `app/extract/`

## License

MIT License

