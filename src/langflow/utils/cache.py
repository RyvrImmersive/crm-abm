from typing import Any, Dict, Optional
from functools import lru_cache
from datetime import datetime, timedelta
import json
import hashlib
from cachetools import TTLCache, LRUCache
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class CacheConfig(BaseModel):
    """Configuration for caching"""
    # HubSpot cache settings
    hubspot_ttl: int = 3600  # 1 hour
    hubspot_maxsize: int = 1000
    
    # Scoring cache settings
    scoring_ttl: int = 86400  # 24 hours
    scoring_maxsize: int = 5000
    
    # Prompt cache settings
    prompt_ttl: int = 3600  # 1 hour
    prompt_maxsize: int = 1000

class CacheManager:
    """
    Centralized cache manager for the ABM CRM system
    Uses different cache strategies for different types of data
    """
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        
        # Initialize caches
        self.hubspot_cache = TTLCache(
            maxsize=self.config.hubspot_maxsize,
            ttl=self.config.hubspot_ttl
        )
        
        self.scoring_cache = TTLCache(
            maxsize=self.config.scoring_maxsize,
            ttl=self.config.scoring_ttl
        )
        
        self.prompt_cache = TTLCache(
            maxsize=self.config.prompt_maxsize,
            ttl=self.config.prompt_ttl
        )
    
    def get_cache_key(self, data: Any, cache_type: str) -> str:
        """Generate a cache key based on the data and cache type"""
        key = json.dumps({
            'data': data,
            'type': cache_type,
            'timestamp': datetime.now().isoformat()
        }, sort_keys=True)
        return hashlib.md5(key.encode()).hexdigest()
    
    def cache_hubspot_data(self, entity_id: str, entity_type: str, data: Any) -> None:
        """Cache HubSpot entity data"""
        key = self.get_cache_key({
            'entity_id': entity_id,
            'entity_type': entity_type
        }, 'hubspot')
        self.hubspot_cache[key] = data
    
    def get_cached_hubspot_data(self, entity_id: str, entity_type: str) -> Optional[Any]:
        """Get cached HubSpot entity data"""
        key = self.get_cache_key({
            'entity_id': entity_id,
            'entity_type': entity_type
        }, 'hubspot')
        return self.hubspot_cache.get(key)
    
    def cache_scoring_result(self, entity_id: str, entity_type: str, score: Any) -> None:
        """Cache scoring result"""
        key = self.get_cache_key({
            'entity_id': entity_id,
            'entity_type': entity_type
        }, 'scoring')
        self.scoring_cache[key] = score
    
    def get_cached_scoring_result(self, entity_id: str, entity_type: str) -> Optional[Any]:
        """Get cached scoring result"""
        key = self.get_cache_key({
            'entity_id': entity_id,
            'entity_type': entity_type
        }, 'scoring')
        return self.scoring_cache.get(key)
    
    def cache_prompt(self, entity_id: str, entity_type: str, prompt: str) -> None:
        """Cache generated prompt"""
        key = self.get_cache_key({
            'entity_id': entity_id,
            'entity_type': entity_type
        }, 'prompt')
        self.prompt_cache[key] = prompt
    
    def get_cached_prompt(self, entity_id: str, entity_type: str) -> Optional[str]:
        """Get cached prompt"""
        key = self.get_cache_key({
            'entity_id': entity_id,
            'entity_type': entity_type
        }, 'prompt')
        return self.prompt_cache.get(key)
    
    def clear_cache(self, cache_type: str = None) -> None:
        """Clear specific or all caches"""
        if cache_type == 'hubspot':
            self.hubspot_cache.clear()
        elif cache_type == 'scoring':
            self.scoring_cache.clear()
        elif cache_type == 'prompt':
            self.prompt_cache.clear()
        else:
            self.hubspot_cache.clear()
            self.scoring_cache.clear()
            self.prompt_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about cache usage"""
        return {
            'hubspot': {
                'size': len(self.hubspot_cache),
                'maxsize': self.hubspot_cache.maxsize,
                'ttl': self.hubspot_cache.ttl
            },
            'scoring': {
                'size': len(self.scoring_cache),
                'maxsize': self.scoring_cache.maxsize,
                'ttl': self.scoring_cache.ttl
            },
            'prompt': {
                'size': len(self.prompt_cache),
                'maxsize': self.prompt_cache.maxsize,
                'ttl': self.prompt_cache.ttl
            }
        }
