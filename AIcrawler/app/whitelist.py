import json
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Try to import OpenAI, but make it optional
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available, using fallback channels only")

from .config import settings, get_llm_api_key
from .models import ChannelInfo
from .cache import cache


class WhitelistGenerator:
    """LLM-driven channel whitelist generator."""
    
    def __init__(self):
        self.api_key = get_llm_api_key()
        if not self.api_key:
            logger.warning("No LLM API key configured, using fallback channels only")
        
        # Set OpenAI API key if available
        if OPENAI_AVAILABLE and settings.openai_api_key:
            openai.api_key = settings.openai_api_key
    
    async def generate_whitelist(
        self, 
        keyword: str, 
        locale: str = "US",
        max_channels: int = 20
    ) -> List[ChannelInfo]:
        """Generate channel whitelist using LLM."""
        
        # Check cache first
        cache_key = f"whitelist:{keyword}:{locale}"
        cached_result = await cache.get(cache_key)
        if cached_result:
            logger.info(f"Using cached whitelist for keyword: {keyword}")
            return [ChannelInfo(**item) for item in cached_result]
        
        try:
            if OPENAI_AVAILABLE and self.api_key:
                channels = await self._call_llm(keyword, locale, max_channels)
                
                # Validate and filter channels
                validated_channels = await self._validate_channels(channels)
                
                # Cache the result
                await cache.set(
                    cache_key, 
                    [channel.dict() for channel in validated_channels],
                    ttl=settings.whitelist_cache_ttl_hours * 3600
                )
                
                return validated_channels
            else:
                logger.info("LLM not available, using fallback channels")
                return await self._get_fallback_channels(keyword, locale)
            
        except Exception as e:
            logger.error(f"Failed to generate whitelist: {e}")
            # Return fallback channels for common categories
            return await self._get_fallback_channels(keyword, locale)
    
    async def _call_llm(
        self, 
        keyword: str, 
        locale: str, 
        max_channels: int
    ) -> List[ChannelInfo]:
        """Call LLM to generate channel whitelist."""
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI not available")
        
        prompt = self._build_prompt(keyword, locale, max_channels)
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert e-commerce analyst. Generate a list of relevant e-commerce domains for product searches."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            return self._parse_llm_response(content)
            
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise
    
    def _build_prompt(self, keyword: str, locale: str, max_channels: int) -> str:
        """Build the prompt for LLM."""
        return f"""
Generate a whitelist of {max_channels} most relevant e-commerce domains for searching: "{keyword}"

Requirements:
- Focus on {locale} market
- Include official stores, major retailers, and specialized platforms
- Exclude content sites, review sites, or C2C platforms
- Only return valid, existing domains
- Do not make up domains

Output format (JSON only):
{{
  "channels": [
    {{
      "domain": "example.com",
      "label": "official|big_box|vertical_electronics|specialized",
      "locale": "{locale}",
      "confidence": 0.95,
      "candidate_reason": "Official brand store"
    }}
  ]
}}

Labels:
- official: Brand's official store
- big_box: Major retail chains (Best Buy, Walmart, Target)
- vertical_electronics: Electronics specialists (Newegg, B&H Photo)
- specialized: Category-specific retailers
- marketplace: Amazon, eBay (if relevant)

Keyword: {keyword}
Locale: {locale}
Max channels: {max_channels}
"""
    
    def _parse_llm_response(self, content: str) -> List[ChannelInfo]:
        """Parse LLM response into ChannelInfo objects."""
        try:
            # Extract JSON from response
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_content = content[json_start:json_end].strip()
            else:
                # Try to find JSON in the response
                start = content.find("{")
                end = content.rfind("}") + 1
                json_content = content[start:end]
            
            data = json.loads(json_content)
            channels_data = data.get("channels", [])
            
            return [ChannelInfo(**channel) for channel in channels_data]
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise ValueError("Invalid LLM response format")
    
    async def _validate_channels(self, channels: List[ChannelInfo]) -> List[ChannelInfo]:
        """Validate and filter generated channels."""
        validated = []
        
        for channel in channels:
            try:
                # Basic validation
                if not channel.domain or "." not in channel.domain:
                    continue
                
                # Remove protocol if present
                domain = channel.domain.replace("https://", "").replace("http://", "")
                if domain.startswith("www."):
                    domain = domain[4:]
                
                channel.domain = domain
                
                # Filter out obvious invalid domains
                if any(word in domain.lower() for word in ["forum", "news", "blog", "wiki", "download"]):
                    continue
                
                validated.append(channel)
                
            except Exception as e:
                logger.warning(f"Failed to validate channel {channel}: {e}")
                continue
        
        # Sort by confidence and return top results
        validated.sort(key=lambda x: x.confidence, reverse=True)
        return validated[:20]
    
    async def _get_fallback_channels(self, keyword: str, locale: str) -> List[ChannelInfo]:
        """Get fallback channels when LLM fails."""
        fallback_channels = {
            "US": [
                ChannelInfo(domain="amazon.com", label="marketplace", locale="US", confidence=0.9),
                ChannelInfo(domain="bestbuy.com", label="big_box", locale="US", confidence=0.9),
                ChannelInfo(domain="walmart.com", label="big_box", locale="US", confidence=0.9),
                ChannelInfo(domain="target.com", label="big_box", locale="US", confidence=0.8),
                ChannelInfo(domain="newegg.com", label="vertical_electronics", locale="US", confidence=0.9),
                ChannelInfo(domain="bhphotovideo.com", label="vertical_electronics", locale="US", confidence=0.8),
            ],
            "UK": [
                ChannelInfo(domain="amazon.co.uk", label="marketplace", locale="UK", confidence=0.9),
                ChannelInfo(domain="currys.co.uk", label="big_box", locale="UK", confidence=0.9),
                ChannelInfo(domain="argos.co.uk", label="big_box", locale="UK", confidence=0.8),
                ChannelInfo(domain="johnlewis.com", label="big_box", locale="UK", confidence=0.8),
            ]
        }
        
        return fallback_channels.get(locale, fallback_channels["US"])
