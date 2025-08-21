import logging
from typing import List, Dict, Any, Optional
from .models import ProductData
from .utils import extract_price, extract_currency, determine_stock_status, clean_text, deduplicate_products

logger = logging.getLogger(__name__)


class DataNormalizer:
    """Normalize and standardize product data from different sources."""
    
    def __init__(self):
        self.currency_conversion_rates = {
            "USD": 1.0,
            "EUR": 0.85,
            "GBP": 0.73,
            "JPY": 110.0,
            "CAD": 1.25,
            "AUD": 1.35,
            "CHF": 0.92,
            "CNY": 6.45,
            "INR": 74.0
        }
    
    async def normalize_products(
        self, 
        raw_products: List[Dict[str, Any]], 
        target_currency: str = "USD"
    ) -> List[ProductData]:
        """Normalize a list of raw product data."""
        
        if not raw_products:
            return []
        
        normalized_products = []
        
        for raw_product in raw_products:
            try:
                normalized = await self._normalize_single_product(raw_product, target_currency)
                if normalized:
                    normalized_products.append(normalized)
            except Exception as e:
                logger.error(f"Failed to normalize product {raw_product.get('url', 'unknown')}: {e}")
                continue
        
        # Remove duplicates
        normalized_products = deduplicate_products(normalized_products)
        
        # Sort by price (if available) and confidence
        normalized_products.sort(
            key=lambda x: (
                x.price or float('inf'), 
                getattr(x, 'confidence', 0)
            )
        )
        
        return normalized_products
    
    async def _normalize_single_product(
        self, 
        raw_product: Dict[str, Any], 
        target_currency: str
    ) -> Optional[ProductData]:
        """Normalize a single product."""
        
        try:
            # Extract basic fields
            retailer = self._extract_retailer(raw_product)
            title = self._extract_title(raw_product)
            url = self._extract_url(raw_product)
            
            if not title or not url:
                logger.warning(f"Missing title or URL for product: {raw_product}")
                return None
            
            # Extract and normalize price
            price, currency = self._extract_and_normalize_price(raw_product, target_currency)
            
            # Extract stock status
            stock_status = self._extract_stock_status(raw_product)
            
            # Extract additional fields
            original_price = self._extract_original_price(raw_product, target_currency)
            availability_text = self._extract_availability_text(raw_product)
            description = self._extract_description(raw_product)
            image_url = self._extract_image_url(raw_product)
            
            # Create normalized ProductData
            return ProductData(
                retailer=retailer,
                product_title=clean_text(title),
                url=url,
                price=price,
                currency=currency,
                in_stock=stock_status,
                fetched_at=int(__import__('time').time()),
                original_price=original_price,
                availability_text=clean_text(availability_text) if availability_text else None,
                description=clean_text(description) if description else None,
                image_url=image_url
            )
            
        except Exception as e:
            logger.error(f"Product normalization failed: {e}")
            return None
    
    def _extract_retailer(self, raw_product: Dict[str, Any]) -> str:
        """Extract retailer name."""
        retailer = raw_product.get('retailer') or raw_product.get('channel') or raw_product.get('domain', 'unknown')
        
        # Clean up retailer name
        if isinstance(retailer, str):
            retailer = retailer.replace('www.', '').replace('https://', '').replace('http://', '')
            if '.' in retailer:
                retailer = retailer.split('.')[0]
            retailer = retailer.title()
        
        return retailer
    
    def _extract_title(self, raw_product: Dict[str, Any]) -> Optional[str]:
        """Extract product title."""
        title = (
            raw_product.get('product_title') or 
            raw_product.get('title') or 
            raw_product.get('name')
        )
        
        if not title:
            return None
        
        # Clean up title
        title = clean_text(title)
        
        # Remove common retailer suffixes
        suffixes_to_remove = [
            ' - Amazon.com',
            ' | Amazon.com',
            ' - Best Buy',
            ' | Best Buy',
            ' - Walmart',
            ' | Walmart'
        ]
        
        for suffix in suffixes_to_remove:
            if title.endswith(suffix):
                title = title[:-len(suffix)]
                break
        
        return title.strip()
    
    def _extract_url(self, raw_product: Dict[str, Any]) -> Optional[str]:
        """Extract and validate URL."""
        url = raw_product.get('url') or raw_product.get('link')
        
        if not url:
            return None
        
        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        
        return url
    
    def _extract_and_normalize_price(
        self, 
        raw_product: Dict[str, Any], 
        target_currency: str
    ) -> tuple[Optional[float], str]:
        """Extract price and normalize to target currency."""
        
        # Try to get price from various fields
        price = None
        currency = target_currency
        
        # Direct price field
        if 'price' in raw_product and raw_product['price'] is not None:
            price = self._parse_price(raw_product['price'])
            currency = raw_product.get('currency', target_currency)
        
        # Price from text fields
        if price is None:
            price_text = (
                raw_product.get('price_text') or 
                raw_product.get('price_string') or 
                raw_product.get('snippet', '')
            )
            if price_text:
                price = extract_price(price_text)
                currency = extract_currency(price_text)
        
        if price is None:
            return None, target_currency
        
        # Convert currency if needed
        if currency != target_currency:
            price = self._convert_currency(price, currency, target_currency)
            currency = target_currency
        
        return price, currency
    
    def _extract_original_price(
        self, 
        raw_product: Dict[str, Any], 
        target_currency: str
    ) -> Optional[float]:
        """Extract original price if available."""
        
        original_price = raw_product.get('original_price')
        if original_price is None:
            return None
        
        price = self._parse_price(original_price)
        if price is None:
            return None
        
        # Convert currency if needed
        currency = raw_product.get('currency', target_currency)
        if currency != target_currency:
            price = self._convert_currency(price, currency, target_currency)
        
        return price
    
    def _extract_stock_status(self, raw_product: Dict[str, Any]) -> str:
        """Extract and normalize stock status."""
        
        # Direct stock status
        stock_status = raw_product.get('in_stock') or raw_product.get('stock_status')
        if stock_status:
            if stock_status in ['in_stock', 'out_of_stock', 'unknown']:
                return stock_status
        
        # Extract from text
        availability_text = self._extract_availability_text(raw_product)
        if availability_text:
            return determine_stock_status(availability_text)
        
        return "unknown"
    
    def _extract_availability_text(self, raw_product: Dict[str, Any]) -> Optional[str]:
        """Extract availability text."""
        return (
            raw_product.get('availability_text') or 
            raw_product.get('stock_text') or 
            raw_product.get('snippet', '')
        )
    
    def _extract_description(self, raw_product: Dict[str, Any]) -> Optional[str]:
        """Extract product description."""
        return (
            raw_product.get('description') or 
            raw_product.get('snippet') or 
            raw_product.get('summary')
        )
    
    def _extract_image_url(self, raw_product: Dict[str, Any]) -> Optional[str]:
        """Extract product image URL."""
        image_url = (
            raw_product.get('image_url') or 
            raw_product.get('image') or 
            raw_product.get('thumbnail')
        )
        
        if not image_url:
            return None
        
        # Ensure URL has protocol
        if not image_url.startswith(('http://', 'https://')):
            image_url = f"https://{image_url}"
        
        return image_url
    
    def _parse_price(self, price_value: Any) -> Optional[float]:
        """Parse price value to float."""
        if price_value is None:
            return None
        
        if isinstance(price_value, (int, float)):
            return float(price_value)
        
        if isinstance(price_value, str):
            return extract_price(price_value)
        
        return None
    
    def _convert_currency(
        self, 
        amount: float, 
        from_currency: str, 
        to_currency: str
    ) -> float:
        """Convert amount between currencies."""
        
        if from_currency == to_currency:
            return amount
        
        # Get conversion rates
        from_rate = self.currency_conversion_rates.get(from_currency.upper(), 1.0)
        to_rate = self.currency_conversion_rates.get(to_currency.upper(), 1.0)
        
        if from_rate == 0:
            logger.warning(f"Cannot convert from {from_currency} (rate is 0)")
            return amount
        
        # Convert to USD first, then to target currency
        usd_amount = amount / from_rate
        target_amount = usd_amount * to_rate
        
        return round(target_amount, 2)
    
    def update_conversion_rates(self, rates: Dict[str, float]):
        """Update currency conversion rates."""
        self.currency_conversion_rates.update(rates)
        logger.info(f"Updated currency conversion rates: {list(rates.keys())}")
    
    def get_supported_currencies(self) -> List[str]:
        """Get list of supported currencies."""
        return list(self.currency_conversion_rates.keys())
