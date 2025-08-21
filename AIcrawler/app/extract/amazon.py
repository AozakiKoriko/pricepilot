import logging
from typing import Optional
from bs4 import BeautifulSoup
from .base import BaseExtractor
from ..models import ProductData
from ..utils import extract_price, extract_currency, determine_stock_status, clean_text

logger = logging.getLogger(__name__)


class AmazonExtractor(BaseExtractor):
    """Amazon-specific product data extractor."""
    
    def __init__(self):
        super().__init__("amazon.com")
    
    def can_handle(self, url: str, html_content: str) -> bool:
        """Check if this extractor can handle the given URL/content."""
        return "amazon.com" in url.lower() or "amazon." in url.lower()
    
    async def extract_product_data(self, html_content: str, url: str) -> Optional[ProductData]:
        """Extract product data from Amazon page."""
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract product title
            title = self._extract_title(soup)
            if not title:
                logger.warning(f"No title found for Amazon product: {url}")
                return None
            
            # Extract price
            price = self._extract_price(soup)
            original_price = self._extract_original_price(soup)
            
            # Extract stock status
            stock_status = self._extract_stock_status(soup)
            
            # Extract description
            description = self._extract_description(soup)
            
            # Extract image URL
            image_url = self._extract_image_url(soup)
            
            # Create ProductData object
            return ProductData(
                retailer=self.domain,
                product_title=clean_text(title),
                url=url,
                price=price,
                currency="USD",  # Amazon US default
                in_stock=stock_status,
                fetched_at=int(__import__('time').time()),
                original_price=original_price,
                description=clean_text(description) if description else None,
                image_url=image_url
            )
            
        except Exception as e:
            logger.error(f"Amazon extraction failed for {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product title from Amazon page."""
        
        # Try multiple selectors for product title
        title_selectors = [
            '#productTitle',
            'h1.a-size-large',
            'h1.a-size-base-plus',
            '.product-title',
            'h1[data-automation-id="product-title"]'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text().strip()
                if title:
                    return title
        
        # Fallback to page title
        title_elem = soup.find('title')
        if title_elem:
            title = title_elem.get_text().strip()
            # Remove Amazon suffix
            if 'Amazon.com' in title:
                title = title.split('Amazon.com')[0].strip()
            return title
        
        return None
    
    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract current price from Amazon page."""
        
        # Try multiple selectors for price
        price_selectors = [
            '.a-price-whole',
            '.a-price .a-offscreen',
            '.a-price-current .a-offscreen',
            '.a-price-current .a-price-whole',
            '#priceblock_ourprice',
            '#priceblock_dealprice',
            '.a-price-range .a-offscreen'
        ]
        
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text().strip()
                price = extract_price(price_text)
                if price:
                    return price
        
        # Try to find price in span elements
        price_spans = soup.find_all('span', class_=lambda x: x and 'price' in x.lower())
        for span in price_spans:
            price_text = span.get_text().strip()
            price = extract_price(price_text)
            if price:
                return price
        
        return None
    
    def _extract_original_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract original price if there's a discount."""
        
        # Look for original price indicators
        original_price_selectors = [
            '.a-text-strike',
            '.a-price.a-text-price .a-offscreen',
            '.a-price.a-text-price .a-price-whole'
        ]
        
        for selector in original_price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text().strip()
                price = extract_price(price_text)
                if price:
                    return price
        
        return None
    
    def _extract_stock_status(self, soup: BeautifulSoup) -> str:
        """Extract stock status from Amazon page."""
        
        # Check for out of stock indicators
        out_of_stock_selectors = [
            '#availability .a-color-state',
            '#availability .a-color-price',
            '.a-color-state',
            '.a-color-price'
        ]
        
        for selector in out_of_stock_selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text().lower().strip()
                if any(word in text for word in ['out of stock', 'unavailable', 'sold out']):
                    return "out_of_stock"
        
        # Check for in stock indicators
        in_stock_selectors = [
            '#availability .a-color-success',
            '.a-color-success'
        ]
        
        for selector in in_stock_selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text().lower().strip()
                if any(word in text for word in ['in stock', 'available', 'add to cart']):
                    return "in_stock"
        
        # Check for add to cart button
        add_to_cart = soup.find('input', {'id': 'add-to-cart-button'})
        if add_to_cart and not add_to_cart.get('disabled'):
            return "in_stock"
        
        return "unknown"
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product description from Amazon page."""
        
        # Try multiple selectors for description
        desc_selectors = [
            '#productDescription p',
            '#feature-bullets .a-list-item',
            '.a-expander-content p',
            '.a-expander-content .a-list-item'
        ]
        
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                desc = desc_elem.get_text().strip()
                if desc and len(desc) > 10:
                    return desc
        
        # Try to get feature bullets
        feature_bullets = soup.select('#feature-bullets .a-list-item')
        if feature_bullets:
            features = []
            for bullet in feature_bullets[:5]:  # Limit to first 5 features
                text = bullet.get_text().strip()
                if text and len(text) > 5:
                    features.append(text)
            
            if features:
                return "Features: " + "; ".join(features)
        
        return None
    
    def _extract_image_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product image URL from Amazon page."""
        
        # Try multiple selectors for product image
        image_selectors = [
            '#landingImage',
            '#main-image',
            '.a-dynamic-image',
            'img[data-old-hires]'
        ]
        
        for selector in image_selectors:
            img_elem = soup.select_one(selector)
            if img_elem:
                src = img_elem.get('src') or img_elem.get('data-src')
                if src and src.startswith('http'):
                    return src
        
        return None

