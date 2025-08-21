import logging
import asyncio
from typing import Dict, Any, Optional, List
import httpx

logger = logging.getLogger(__name__)

# Try to import Playwright, but make it optional
try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available, browser-based fetching will not work")

from urllib.parse import urljoin, urlparse
from app.config import settings
from app.utils import extract_domain


class PageFetcher:
    """Page fetcher with rate limiting and compliance."""
    
    def __init__(self):
        self.rate_limiters: Dict[str, asyncio.Semaphore] = {}
        self.browser: Optional['Browser'] = None
        self.playwright = None
        
        # HTTP client for static pages
        self.http_client = httpx.AsyncClient(
            timeout=settings.request_timeout,
            headers={"User-Agent": settings.user_agent},
            follow_redirects=True
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        if PLAYWRIGHT_AVAILABLE:
            await self._init_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _init_browser(self):
        """Initialize Playwright browser."""
        if not PLAYWRIGHT_AVAILABLE:
            return
            
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--no-first-run",
                    "--no-zygote",
                    "--single-process"
                ]
            )
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            self.browser = None
    
    async def fetch_pages(
        self, 
        urls: List[str], 
        use_browser: bool = False
    ) -> List[Dict[str, Any]]:
        """Fetch multiple pages with rate limiting."""
        
        if not urls:
            return []
        
        # Group URLs by domain for rate limiting
        domain_groups = {}
        for url in urls:
            domain = extract_domain(url)
            if domain not in domain_groups:
                domain_groups[domain] = []
            domain_groups[domain].append(url)
        
        # Fetch pages concurrently with domain-level rate limiting
        all_results = []
        
        for domain, domain_urls in domain_groups.items():
            # Get or create rate limiter for this domain
            if domain not in self.rate_limiters:
                self.rate_limiters[domain] = asyncio.Semaphore(settings.rate_limit_per_domain)
            
            # Fetch pages for this domain
            domain_results = await self._fetch_domain_pages(
                domain_urls, 
                domain, 
                use_browser
            )
            all_results.extend(domain_results)
        
        return all_results
    
    async def _fetch_domain_pages(
        self, 
        urls: List[str], 
        domain: str, 
        use_browser: bool
    ) -> List[Dict[str, Any]]:
        """Fetch pages for a specific domain with rate limiting."""
        
        results = []
        semaphore = self.rate_limiters[domain]
        
        async def fetch_single(url: str) -> Optional[Dict[str, Any]]:
            async with semaphore:
                try:
                    if use_browser and self.browser and PLAYWRIGHT_AVAILABLE:
                        return await self._fetch_with_browser(url)
                    else:
                        return await self._fetch_with_http(url)
                except Exception as e:
                    logger.error(f"Failed to fetch {url}: {e}")
                    return None
        
        # Fetch pages with controlled concurrency
        tasks = [fetch_single(url) for url in urls]
        fetch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in fetch_results:
            if isinstance(result, dict):
                results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Fetch task failed: {result}")
        
        return results
    
    async def _fetch_with_http(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch page using HTTP client."""
        
        try:
            response = await self.http_client.get(url)
            response.raise_for_status()
            
            return {
                "url": url,
                "content": response.text,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "fetch_method": "http",
                "success": True
            }
            
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error for {url}: {e.response.status_code}")
            return {
                "url": url,
                "content": "",
                "status_code": e.response.status_code,
                "headers": dict(e.response.headers),
                "fetch_method": "http",
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"HTTP fetch failed for {url}: {e}")
            return {
                "url": url,
                "content": "",
                "status_code": 0,
                "headers": {},
                "fetch_method": "http",
                "success": False,
                "error": str(e)
            }
    
    async def _fetch_with_browser(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch page using Playwright browser."""
        
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not available, falling back to HTTP")
            return await self._fetch_with_http(url)
        
        if not self.browser:
            logger.warning("Browser not available, falling back to HTTP")
            return await self._fetch_with_http(url)
        
        page: Optional['Page'] = None
        
        try:
            page = await self.browser.new_page()
            
            # Set viewport and user agent
            await page.set_viewport_size({"width": 1280, "height": 720})
            await page.set_extra_http_headers({"User-Agent": settings.user_agent})
            
            # Navigate to page
            response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            if not response:
                raise Exception("No response from page")
            
            # Wait for content to load
            await page.wait_for_timeout(2000)
            
            # Get page content
            content = await page.content()
            
            # Extract additional metadata
            title = await page.title()
            
            return {
                "url": url,
                "content": content,
                "status_code": response.status,
                "headers": dict(response.headers),
                "fetch_method": "browser",
                "success": True,
                "title": title,
                "final_url": page.url
            }
            
        except Exception as e:
            logger.error(f"Browser fetch failed for {url}: {e}")
            return {
                "url": url,
                "content": "",
                "status_code": 0,
                "headers": {},
                "fetch_method": "browser",
                "success": False,
                "error": str(e)
            }
        finally:
            if page:
                await page.close()
    
    async def check_robots_txt(self, domain: str) -> Dict[str, Any]:
        """Check robots.txt for a domain."""
        
        try:
            robots_url = f"https://{domain}/robots.txt"
            response = await self.http_client.get(robots_url, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                return {
                    "domain": domain,
                    "exists": True,
                    "content": content,
                    "allows_crawling": self._parse_robots_txt(content)
                }
            else:
                return {
                    "domain": domain,
                    "exists": False,
                    "allows_crawling": True  # Default to allowing if no robots.txt
                }
                
        except Exception as e:
            logger.warning(f"Failed to check robots.txt for {domain}: {e}")
            return {
                "domain": domain,
                "exists": False,
                "allows_crawling": True  # Default to allowing if check fails
            }
    
    def _parse_robots_txt(self, content: str) -> bool:
        """Parse robots.txt content to check if crawling is allowed."""
        
        lines = content.lower().split('\n')
        user_agent = "ai-crawler"
        
        for line in lines:
            line = line.strip()
            if line.startswith('user-agent:'):
                agent = line.split(':', 1)[1].strip()
                if agent == '*' or agent == user_agent:
                    # Check next line for Disallow
                    continue
            elif line.startswith('disallow:'):
                path = line.split(':', 1)[1].strip()
                if path == '/' or path == '':
                    return False
        
        return True
    
    async def close(self):
        """Close all resources."""
        
        # Close HTTP client
        await self.http_client.aclose()
        
        # Close browser
        if self.browser and PLAYWRIGHT_AVAILABLE:
            await self.browser.close()
        
        if self.playwright and PLAYWRIGHT_AVAILABLE:
            await self.playwright.stop()
