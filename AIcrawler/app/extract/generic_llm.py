import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Try to import OpenAI, but make it optional
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available, LLM extraction will not work")

from bs4 import BeautifulSoup
from app.extract.base import BaseExtractor, ExtractionResult
from app.models import ProductData
from app.config import settings, get_llm_api_key
from app.utils import extract_price, extract_currency, determine_stock_status, clean_text


class GenericLLMExtractor(BaseExtractor):
    """Generic LLM-based data extractor for fallback scenarios."""
    
    def __init__(self, domain: str):
        super().__init__(domain)
        self.api_key = get_llm_api_key()
        if not self.api_key:
            logger.warning("No LLM API key configured, LLM extraction will not work")
        
        # Set OpenAI API key if available
        if OPENAI_AVAILABLE and settings.openai_api_key:
            openai.api_key = settings.openai_api_key
    
    def can_handle(self, url: str, html_content: str) -> bool:
        """This extractor can handle any content as a fallback."""
        return True
    
    async def extract_product_data(self, html_content: str, url: str) -> Optional[ProductData]:
        """Extract product data using LLM."""
        
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI not available, cannot perform LLM extraction")
            return None
        
        try:
            # Parse HTML and extract relevant content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract main content areas
            content_sections = self._extract_content_sections(soup)
            
            # Prepare prompt for LLM
            prompt = self._build_extraction_prompt(content_sections, url)
            
            # Call LLM
            extracted_data = await self._call_llm(prompt)
            
            if not extracted_data:
                return None
            
            # Create ProductData object
            return self._create_product_data(extracted_data, url)
            
        except Exception as e:
            logger.error(f"LLM extraction failed for {url}: {e}")
            return None
    
    def _extract_content_sections(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract relevant content sections from HTML."""
        sections = {}
        
        # Try to find main content areas
        selectors = [
            'main',
            '[role="main"]',
            '.main-content',
            '.product-content',
            '.product-details',
            '.product-info',
            '#content',
            '#main',
            '.content'
        ]
        
        main_content = None
        for selector in selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            # Fallback to body content
            main_content = soup.body or soup
        
        # Extract text content
        if main_content:
            sections['main_content'] = clean_text(main_content.get_text())
        
        # Extract title
        title_elem = soup.find('title')
        if title_elem:
            sections['title'] = clean_text(title_elem.get_text())
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            sections['meta_description'] = clean_text(meta_desc.get('content'))
        
        # Extract structured data (JSON-LD)
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') == 'Product':
                    sections['json_ld'] = json.dumps(data, indent=2)
                    break
            except (json.JSONDecodeError, AttributeError):
                continue
        
        # Limit content length to avoid token limits
        for key, content in sections.items():
            if len(content) > 2000:
                sections[key] = content[:2000] + "..."
        
        return sections
    
    def _build_extraction_prompt(self, content_sections: Dict[str, str], url: str) -> str:
        """Build the prompt for LLM extraction."""
        
        content_text = "\n\n".join([
            f"{key.upper()}:\n{content}" 
            for key, content in content_sections.items()
        ])
        
        return f"""
Extract product information from the following webpage content. Return ONLY a valid JSON object with the specified fields.

URL: {url}

Content:
{content_text}

Extract the following information and return as JSON:
{{
  "product_title": "Full product name/title",
  "price": 0.00,
  "currency": "USD",
  "in_stock": "in_stock|out_of_stock|unknown",
  "original_price": 0.00,
  "availability_text": "Raw availability text found",
  "description": "Product description if available"
}}

Rules:
- price: Extract the main selling price as a number (no currency symbol)
- currency: Extract the currency code (USD, EUR, GBP, etc.)
- in_stock: Determine from availability text
- original_price: Only if there's a sale/discount
- availability_text: Raw text about stock status
- description: Brief product description if available
- If a field cannot be determined, use null

Return ONLY the JSON object, no other text.
"""
    
    async def _call_llm(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call LLM API for data extraction."""
        
        if not OPENAI_AVAILABLE:
            logger.error("OpenAI not available for LLM extraction")
            return None
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a product data extraction specialist. Extract product information from webpage content and return it as JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = content[json_start:json_end]
                return json.loads(json_content)
            else:
                logger.warning("No JSON found in LLM response")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return None
    
    def _create_product_data(self, extracted_data: Dict[str, Any], url: str) -> ProductData:
        """Create ProductData object from extracted data."""
        
        # Extract basic fields
        title = extracted_data.get('product_title', '')
        price = extracted_data.get('price')
        currency = extracted_data.get('currency', 'USD')
        stock_status = extracted_data.get('in_stock', 'unknown')
        original_price = extracted_data.get('original_price')
        availability_text = extracted_data.get('availability_text', '')
        description = extracted_data.get('description', '')
        
        # Validate and clean data
        if price is not None and not isinstance(price, (int, float)):
            try:
                price = float(price)
            except (ValueError, TypeError):
                price = None
        
        if original_price is not None and not isinstance(original_price, (int, float)):
            try:
                original_price = float(original_price)
            except (ValueError, TypeError):
                original_price = None
        
        # Create ProductData object
        return ProductData(
            retailer=self.domain,
            product_title=clean_text(title) if title else f"Product from {self.domain}",
            url=url,
            price=price,
            currency=currency.upper() if currency else "USD",
            in_stock=stock_status if stock_status in ["in_stock", "out_of_stock", "unknown"] else "unknown",
            fetched_at=int(__import__('time').time()),
            original_price=original_price,
            availability_text=clean_text(availability_text) if availability_text else None,
            description=clean_text(description) if description else None
        )
