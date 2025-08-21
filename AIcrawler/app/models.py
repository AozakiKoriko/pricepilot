from typing import Optional, List, Literal
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime


class ChannelInfo(BaseModel):
    """Channel information for whitelist generation."""
    domain: str = Field(..., description="Domain name without protocol")
    label: str = Field(..., description="Channel type label")
    locale: str = Field(..., description="Locale/region code")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    candidate_reason: Optional[str] = Field(None, description="Reason for inclusion")


class ProductData(BaseModel):
    """Standardized product data output."""
    retailer: str = Field(..., description="Retailer name")
    product_title: str = Field(..., description="Product title/name")
    url: HttpUrl = Field(..., description="Product URL")
    price: Optional[float] = Field(None, description="Product price")
    currency: str = Field(default="USD", description="Currency code")
    in_stock: Literal["in_stock", "out_of_stock", "unknown"] = Field(
        default="unknown", description="Stock status"
    )
    fetched_at: int = Field(..., description="Unix timestamp of fetch time")
    original_price: Optional[float] = Field(None, description="Original price if on sale")
    availability_text: Optional[str] = Field(None, description="Raw availability text")
    image_url: Optional[HttpUrl] = Field(None, description="Product image URL")
    description: Optional[str] = Field(None, description="Product description")


class SearchRequest(BaseModel):
    """Search request model."""
    query: str = Field(..., description="Product search query")
    locale: Optional[str] = Field(default="US", description="Target locale")
    max_results: Optional[int] = Field(default=20, description="Maximum results to return")
    include_out_of_stock: Optional[bool] = Field(default=True, description="Include out of stock items")


class SearchResponse(BaseModel):
    """Search response model."""
    query: str = Field(..., description="Original search query")
    total_results: int = Field(..., description="Total results found")
    results: List[ProductData] = Field(..., description="Product results")
    search_time_ms: int = Field(..., description="Search execution time in milliseconds")
    channels_used: List[str] = Field(..., description="Channels that were searched")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current timestamp")
    version: str = Field(default="1.0.0", description="API version")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

