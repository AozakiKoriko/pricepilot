import re
import hashlib
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin
from difflib import SequenceMatcher


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain
    except Exception:
        return url.lower()


def normalize_url(url: str, base_domain: str = "") -> str:
    """Normalize URL by adding protocol if missing."""
    if not url.startswith(('http://', 'https://')):
        if url.startswith('//'):
            return f"https:{url}"
        elif url.startswith('/'):
            return f"https://{base_domain}{url}"
        else:
            return f"https://{url}"
    return url


def extract_price(text: str) -> Optional[float]:
    """Extract price from text."""
    if not text:
        return None
    
    # Common price patterns
    price_patterns = [
        r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',  # $1,234.56
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*USD',  # 1,234.56 USD
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*dollars',  # 1,234.56 dollars
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*\$',  # 1,234.56 $
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            price_str = match.group(1).replace(',', '')
            try:
                return float(price_str)
            except ValueError:
                continue
    
    return None


def extract_currency(text: str) -> str:
    """Extract currency from text."""
    if not text:
        return "USD"
    
    currency_patterns = {
        r'\$': "USD",
        r'USD': "USD",
        r'US\$': "USD",
        r'€': "EUR",
        r'EUR': "EUR",
        r'£': "GBP",
        r'GBP': "GBP",
        r'¥': "JPY",
        r'JPY': "JPY",
        r'₹': "INR",
        r'INR': "INR",
    }
    
    for pattern, currency in currency_patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            return currency
    
    return "USD"


def determine_stock_status(text: str) -> str:
    """Determine stock status from text."""
    if not text:
        return "unknown"
    
    text_lower = text.lower()
    
    # In stock indicators
    in_stock_patterns = [
        r'in stock',
        r'available',
        r'add to cart',
        r'add to basket',
        r'buy now',
        r'purchase',
        r'order now',
        r'pickup today',
        r'ship to store',
        r'free shipping'
    ]
    
    # Out of stock indicators
    out_of_stock_patterns = [
        r'out of stock',
        r'unavailable',
        r'sold out',
        r'currently unavailable',
        r'backordered',
        r'pre-order',
        r'coming soon',
        r'notify when available'
    ]
    
    for pattern in in_stock_patterns:
        if re.search(pattern, text_lower):
            return "in_stock"
    
    for pattern in out_of_stock_patterns:
        if re.search(pattern, text_lower):
            return "out_of_stock"
    
    return "unknown"


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts using SequenceMatcher."""
    if not text1 or not text2:
        return 0.0
    
    # Normalize texts
    text1_norm = re.sub(r'[^\w\s]', '', text1.lower())
    text2_norm = re.sub(r'[^\w\s]', '', text2.lower())
    
    return SequenceMatcher(None, text1_norm, text2_norm).ratio()


def deduplicate_products(products: List[Any], similarity_threshold: float = 0.8) -> List[Any]:
    """Remove duplicate products based on title similarity."""
    if not products:
        return []
    
    # Sort by confidence/price to prioritize better results
    sorted_products = sorted(
        products, 
        key=lambda x: (getattr(x, 'price', 0) or 0, getattr(x, 'confidence', 0)), 
        reverse=True
    )
    
    unique_products = []
    seen_titles = set()
    
    for product in sorted_products:
        # Handle both dict and object types
        if hasattr(product, 'product_title'):
            title = product.product_title.lower()
        elif isinstance(product, dict):
            title = product.get('product_title', '').lower()
        else:
            title = str(product).lower()
        
        # Check if this product is similar to any existing one
        is_duplicate = False
        for existing_title in seen_titles:
            if calculate_similarity(title, existing_title) > similarity_threshold:
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_products.append(product)
            seen_titles.add(title)
    
    return unique_products


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove common HTML entities
    html_entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&nbsp;': ' '
    }
    
    for entity, replacement in html_entities.items():
        text = text.replace(entity, replacement)
    
    return text


def extract_product_attributes(text: str) -> Dict[str, Any]:
    """Extract common product attributes from text."""
    attributes = {}
    
    if not text:
        return attributes
    
    # Extract capacity/size
    capacity_patterns = [
        r'(\d+)\s*GB',
        r'(\d+)\s*TB',
        r'(\d+)\s*MB',
        r'(\d+)\s*inch',
        r'(\d+)\s*"',
        r'(\d+)\s*cm'
    ]
    
    for pattern in capacity_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            attributes['capacity'] = match.group(1)
            break
    
    # Extract color
    color_patterns = [
        r'(black|white|red|blue|green|yellow|silver|gold|pink|purple|orange|brown|gray|grey)',
        r'(space gray|space grey|midnight|starlight|rose gold|titanium)'
    ]
    
    for pattern in color_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            attributes['color'] = match.group(1)
            break
    
    # Extract model/generation
    model_patterns = [
        r'(iPhone\s+\d+)',
        r'(iPad\s+\w+)',
        r'(MacBook\s+\w+)',
        r'(RTX\s+\d+)',
        r'(GTX\s+\d+)',
        r'(Ryzen\s+\d+)',
        r'(Intel\s+i\d+)'
    ]
    
    for pattern in model_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            attributes['model'] = match.group(1)
            break
    
    return attributes


def generate_cache_key(*args) -> str:
    """Generate a cache key from arguments."""
    key_string = "|".join(str(arg) for arg in args)
    return hashlib.md5(key_string.encode()).hexdigest()


def is_valid_url(url: str) -> bool:
    """Check if URL is valid."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to specified length."""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length].rsplit(' ', 1)[0] + "..."
