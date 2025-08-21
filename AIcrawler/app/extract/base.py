from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.models import ProductData


class BaseExtractor(ABC):
    """Base class for all data extractors."""
    
    def __init__(self, domain: str):
        self.domain = domain
    
    @abstractmethod
    async def extract_product_data(self, html_content: str, url: str) -> Optional[ProductData]:
        """Extract product data from HTML content."""
        pass
    
    @abstractmethod
    def can_handle(self, url: str, html_content: str) -> bool:
        """Check if this extractor can handle the given URL/content."""
        pass
    
    def get_extractor_name(self) -> str:
        """Get the name of this extractor."""
        return self.__class__.__name__
    
    def get_domain(self) -> str:
        """Get the domain this extractor handles."""
        return self.domain


class ExtractionResult:
    """Result of data extraction attempt."""
    
    def __init__(self, success: bool, data: Optional[ProductData] = None, error: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error
    
    @classmethod
    def success(cls, data: ProductData) -> 'ExtractionResult':
        """Create a successful extraction result."""
        return cls(success=True, data=data)
    
    @classmethod
    def failure(cls, error: str) -> 'ExtractionResult':
        """Create a failed extraction result."""
        return cls(success=False, error=error)
    
    def __bool__(self) -> bool:
        return self.success

