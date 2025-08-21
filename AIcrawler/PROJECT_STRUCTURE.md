# AI Product Aggregation Crawler - Project Structure

## Overview
This project implements an intelligent product price and stock aggregation system that uses LLM-generated whitelists to crawl multiple e-commerce channels.

## Directory Structure
```
ai-crawler-mvp/
├── app/                           # Main application package
│   ├── __init__.py               # Package initialization
│   ├── main.py                   # FastAPI application entry point
│   ├── config.py                 # Configuration and settings
│   ├── models.py                 # Pydantic data models
│   ├── whitelist.py              # LLM-driven channel whitelist generator
│   ├── search.py                 # Search engine for domain-restricted queries
│   ├── fetcher.py                # Page fetching with rate limiting
│   ├── normalize.py              # Data normalization and standardization
│   ├── cache.py                  # Caching layer (SQLite + Redis)
│   ├── utils.py                  # Utility functions and helpers
│   └── extract/                  # Data extraction modules
│       ├── __init__.py           # Extractors package
│       ├── base.py               # Base extractor interface
│       ├── generic_llm.py        # LLM-based fallback extractor
│       └── amazon.py             # Amazon-specific extractor
├── requirements.txt               # Python dependencies
├── env.example                   # Environment variables template
├── README.md                     # Project documentation
├── run.py                        # Application runner script
├── test_crawler.py               # Test suite
├── install.sh                    # Linux/Mac installation script
├── install.bat                   # Windows installation script
└── PROJECT_STRUCTURE.md          # This file
```

## Core Components

### 1. Whitelist Layer (`app/whitelist.py`)
- **Purpose**: Generates relevant e-commerce domain whitelists using LLM
- **Key Features**:
  - LLM-driven channel selection based on product keywords
  - Domain validation and filtering
  - Caching for performance
  - Fallback to predefined channels

### 2. Search Layer (`app/search.py`)
- **Purpose**: Performs domain-restricted product searches
- **Key Features**:
  - Support for multiple search APIs (SerpAPI, Bing, Google)
  - Domain-specific search using `site:` operator
  - Rate limiting and error handling
  - Result filtering and validation

### 3. Fetch Layer (`app/fetcher.py`)
- **Purpose**: Crawls product pages with compliance and rate limiting
- **Key Features**:
  - Dual-mode fetching (HTTP + Playwright)
  - Domain-level rate limiting
  - Robots.txt compliance
  - Concurrent page fetching

### 4. Extract Layer (`app/extract/`)
- **Purpose**: Extracts product data from HTML content
- **Key Features**:
  - Rule-based extractors for major sites
  - LLM fallback for unknown sites
  - Structured data extraction (JSON-LD)
  - Multiple extraction strategies

### 5. Normalize Layer (`app/normalize.py`)
- **Purpose**: Standardizes data from different sources
- **Key Features**:
  - Currency conversion
  - Data cleaning and validation
  - Duplicate removal
  - Consistent output format

### 6. Cache Layer (`app/cache.py`)
- **Purpose**: Provides caching for performance and cost reduction
- **Key Features**:
  - Dual storage (SQLite + Redis)
  - TTL-based expiration
  - Automatic cleanup
  - Fallback mechanisms

## Data Flow

```
User Query → Whitelist Generation → Domain Search → Page Fetching → Data Extraction → Normalization → Results
     ↓              ↓                    ↓              ↓              ↓              ↓
  Product      Channel List        Search Results   HTML Content   Raw Data      Final Results
  Keywords     (LLM Generated)     (Filtered)      (Fetched)      (Extracted)   (Standardized)
```

## API Endpoints

### Core Endpoints
- `GET /search` - Main product search endpoint
- `GET /health` - Health check
- `GET /channels` - Available channels
- `GET /cache/stats` - Cache statistics
- `DELETE /cache/clear` - Clear cache

### Search Parameters
- `query` - Product search query (required)
- `locale` - Target market (default: US)
- `max_results` - Maximum results (default: 20)
- `include_out_of_stock` - Include out of stock items (default: true)

## Configuration

### Environment Variables
- **LLM APIs**: OpenAI, Anthropic, Google
- **Search APIs**: SerpAPI, Bing, Google Search
- **Cache**: Redis URL, TTL settings
- **Rate Limiting**: Concurrent requests, domain limits
- **User Agent**: Custom user agent string

### Key Settings
- `MAX_CONCURRENT_REQUESTS`: 5 (default)
- `RATE_LIMIT_PER_DOMAIN`: 2 (default)
- `CACHE_TTL_MINUTES`: 30 (default)
- `WHITELIST_CACHE_TTL_HOURS`: 24 (default)

## Data Models

### Core Models
- `ChannelInfo` - Channel/domain information
- `ProductData` - Standardized product data
- `SearchRequest` - Search parameters
- `SearchResponse` - Search results
- `HealthResponse` - Health check response

### Product Data Structure
```json
{
  "retailer": "Amazon",
  "product_title": "iPhone 15 Pro 256GB",
  "url": "https://amazon.com/...",
  "price": 999.99,
  "currency": "USD",
  "in_stock": "in_stock",
  "fetched_at": 1724130000,
  "original_price": 1099.99,
  "availability_text": "In Stock",
  "image_url": "https://...",
  "description": "Product description..."
}
```

## Error Handling

### Error Types
- **Configuration Errors**: Missing API keys, invalid settings
- **Network Errors**: Timeouts, connection failures
- **Parsing Errors**: Invalid HTML, extraction failures
- **Rate Limiting**: API quota exceeded, too many requests

### Fallback Mechanisms
- LLM whitelist → Predefined channels
- Search API → Basic web scraping
- Rule extraction → LLM extraction
- Redis cache → SQLite cache

## Performance Considerations

### Optimization Strategies
- **Caching**: Whitelist and product data caching
- **Concurrency**: Async/await for I/O operations
- **Rate Limiting**: Domain-level request throttling
- **Resource Management**: Connection pooling, browser reuse

### Monitoring
- Search execution time
- Cache hit rates
- Extraction success rates
- API usage and costs

## Security & Compliance

### Best Practices
- User agent identification
- Robots.txt compliance
- Rate limiting and throttling
- API key management
- Error message sanitization

### Legal Considerations
- Terms of service compliance
- Data usage policies
- Rate limiting adherence
- Respect for site policies

## Deployment

### Requirements
- Python 3.8+
- Virtual environment
- API keys for LLM and search services
- Optional: Redis server

### Installation
```bash
# Linux/Mac
chmod +x install.sh
./install.sh

# Windows
install.bat

# Manual
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate.bat
pip install -r requirements.txt
playwright install
```

### Running
```bash
# Development
python run.py

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Testing
python test_crawler.py
```

## Future Enhancements

### Planned Features
- Multi-language support
- Advanced product matching
- Historical price tracking
- User preference learning
- Mobile app integration

### Scalability Improvements
- Microservices architecture
- Database optimization
- CDN integration
- Load balancing
- Container deployment

