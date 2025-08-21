import logging
import asyncio
from typing import List, Dict, Any, Optional
import httpx
from urllib.parse import quote_plus
from app.config import settings, get_search_api_key
from app.models import ChannelInfo

logger = logging.getLogger(__name__)


class SearchEngine:
    """Search engine for domain-restricted product searches."""
    
    def __init__(self):
        self.api_key = get_search_api_key()
        if not self.api_key:
            logger.warning("No search API key configured, using fallback methods")
        
        self.client = httpx.AsyncClient(
            timeout=settings.search_timeout,
            headers={"User-Agent": settings.user_agent}
        )
    
    async def search_products(
        self, 
        keyword: str, 
        channels: List[ChannelInfo],
        max_results_per_channel: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for products across multiple channels."""
        
        search_tasks = []
        for channel in channels:
            task = self._search_channel(keyword, channel, max_results_per_channel)
            search_tasks.append(task)
        
        # Execute searches concurrently with rate limiting
        results = []
        semaphore = asyncio.Semaphore(settings.max_concurrent_requests)
        
        async def limited_search(task):
            async with semaphore:
                return await task
        
        search_results = await asyncio.gather(
            *[limited_search(task) for task in search_tasks],
            return_exceptions=True
        )
        
        for i, result in enumerate(search_results):
            if isinstance(result, Exception):
                logger.error(f"Search failed for {channels[i].domain}: {result}")
                continue
            results.extend(result)
        
        return results
    
    async def _search_channel(
        self, 
        keyword: str, 
        channel: ChannelInfo, 
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Search for products within a specific channel."""
        
        try:
            if self.api_key and settings.serpapi_key:
                return await self._search_with_serpapi(keyword, channel, max_results)
            elif self.api_key and settings.bing_api_key:
                return await self._search_with_bing(keyword, channel, max_results)
            else:
                return await self._search_with_google(keyword, channel, max_results)
                
        except Exception as e:
            logger.error(f"Search failed for {channel.domain}: {e}")
            return []
    
    async def _search_with_serpapi(
        self, 
        keyword: str, 
        channel: ChannelInfo, 
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Search using SerpAPI."""
        
        url = "https://serpapi.com/search"
        params = {
            "api_key": settings.serpapi_key,
            "q": keyword,
            "engine": "google",
            "site": channel.domain,
            "num": min(max_results, 10),
            "gl": channel.locale.lower(),
            "hl": "en"
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return self._parse_serpapi_results(data, channel)
            
        except Exception as e:
            logger.error(f"SerpAPI search failed: {e}")
            return []
    
    async def _search_with_bing(
        self, 
        keyword: str, 
        channel: ChannelInfo, 
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Search using Bing Search API."""
        
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {
            "Ocp-Apim-Subscription-Key": settings.bing_api_key,
            "User-Agent": settings.user_agent
        }
        
        params = {
            "q": f"{keyword} site:{channel.domain}",
            "count": min(max_results, 10),
            "mkt": f"en-{channel.locale}",
            "responseFilter": "Webpages"
        }
        
        try:
            response = await self.client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            return self._parse_bing_results(data, channel)
            
        except Exception as e:
            logger.error(f"Bing search failed: {e}")
            return []
    
    async def _search_with_google(
        self, 
        keyword: str, 
        channel: ChannelInfo, 
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Fallback search using Google (limited functionality)."""
        
        # This is a basic fallback - in production you'd want a proper Google Search API
        search_query = f"{keyword} site:{channel.domain}"
        encoded_query = quote_plus(search_query)
        
        url = f"https://www.google.com/search?q={encoded_query}&num={max_results}"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            
            # Basic parsing - this is limited without proper API access
            return self._parse_google_results(response.text, channel, max_results)
            
        except Exception as e:
            logger.error(f"Google fallback search failed: {e}")
            return []
    
    def _parse_serpapi_results(
        self, 
        data: Dict[str, Any], 
        channel: ChannelInfo
    ) -> List[Dict[str, Any]]:
        """Parse SerpAPI search results."""
        results = []
        
        try:
            organic_results = data.get("organic_results", [])
            
            for result in organic_results:
                if not self._is_product_page(result, channel):
                    continue
                
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "channel": channel.domain,
                    "channel_label": channel.label,
                    "confidence": channel.confidence
                })
                
        except Exception as e:
            logger.error(f"Failed to parse SerpAPI results: {e}")
        
        return results
    
    def _parse_bing_results(
        self, 
        data: Dict[str, Any], 
        channel: ChannelInfo
    ) -> List[Dict[str, Any]]:
        """Parse Bing Search API results."""
        results = []
        
        try:
            web_pages = data.get("webPages", {}).get("value", [])
            
            for page in web_pages:
                if not self._is_product_page(page, channel):
                    continue
                
                results.append({
                    "title": page.get("name", ""),
                    "url": page.get("url", ""),
                    "snippet": page.get("snippet", ""),
                    "channel": channel.domain,
                    "channel_label": channel.label,
                    "confidence": channel.confidence
                })
                
        except Exception as e:
            logger.error(f"Failed to parse Bing results: {e}")
        
        return results
    
    def _parse_google_results(
        self, 
        html_content: str, 
        channel: ChannelInfo, 
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Basic parsing of Google search results HTML."""
        results = []
        
        try:
            # This is a simplified parser - in production you'd use a proper HTML parser
            lines = html_content.split('\n')
            
            for line in lines:
                if len(results) >= max_results:
                    break
                
                if 'href="' in line and channel.domain in line:
                    # Extract URL and title (simplified)
                    url_start = line.find('href="') + 6
                    url_end = line.find('"', url_start)
                    
                    if url_start > 6 and url_end > url_start:
                        url = line[url_start:url_end]
                        
                        # Basic validation
                        if url.startswith('/') or url.startswith('http'):
                            results.append({
                                "title": f"Product from {channel.domain}",
                                "url": url if url.startswith('http') else f"https://{channel.domain}{url}",
                                "snippet": f"Product page from {channel.domain}",
                                "channel": channel.domain,
                                "channel_label": channel.label,
                                "confidence": channel.confidence * 0.7  # Lower confidence for fallback
                            })
                            
        except Exception as e:
            logger.error(f"Failed to parse Google results: {e}")
        
        return results
    
    def _is_product_page(self, result: Dict[str, Any], channel: ChannelInfo) -> bool:
        """Check if a search result is likely a product page."""
        
        url = result.get("url", "").lower()
        title = result.get("title", "").lower()
        
        # Skip non-product pages
        skip_patterns = [
            "/blog/", "/news/", "/article/", "/forum/", "/help/", "/support/",
            "/about/", "/contact/", "/careers/", "/press/", "/legal/"
        ]
        
        if any(pattern in url for pattern in skip_patterns):
            return False
        
        # Look for product indicators
        product_patterns = [
            "/product/", "/item/", "/p/", "/dp/", "/gp/product/",
            "buy", "shop", "purchase", "add to cart", "add to basket"
        ]
        
        return any(pattern in url or pattern in title for pattern in product_patterns)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

