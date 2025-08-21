import json
import sqlite3
import asyncio
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Try to import Redis, but make it optional
try:
    import aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using SQLite only")

from .config import settings


class Cache:
    """Unified cache interface supporting both SQLite and Redis."""
    
    def __init__(self):
        self.redis_client = None
        self.sqlite_path = "cache.db"
        self._init_sqlite()
        if REDIS_AVAILABLE:
            self._init_redis()
    
    def _init_sqlite(self):
        """Initialize SQLite database."""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            # Create cache table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    ttl INTEGER,
                    created_at INTEGER
                )
            """)
            
            # Create index for TTL cleanup
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_ttl 
                ON cache(ttl, created_at)
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to initialize SQLite cache: {e}")
    
    async def _init_redis(self):
        """Initialize Redis client."""
        if not REDIS_AVAILABLE:
            return
            
        try:
            if settings.redis_url:
                self.redis_client = aioredis.from_url(settings.redis_url)
                # Test connection
                await self.redis_client.ping()
                logger.info("Redis cache initialized successfully")
            else:
                logger.info("Redis not configured, using SQLite only")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis cache: {e}")
            self.redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            # Try Redis first
            if self.redis_client and REDIS_AVAILABLE:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
            
            # Fallback to SQLite
            return self._get_sqlite(key)
            
        except Exception as e:
            logger.error(f"Cache get failed for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 0) -> bool:
        """Set value in cache with TTL."""
        try:
            # Try Redis first
            if self.redis_client and REDIS_AVAILABLE and ttl > 0:
                await self.redis_client.setex(
                    key, 
                    ttl, 
                    json.dumps(value, default=str)
                )
                return True
            
            # Fallback to SQLite
            return self._set_sqlite(key, value, ttl)
            
        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            # Try Redis first
            if self.redis_client and REDIS_AVAILABLE:
                await self.redis_client.delete(key)
            
            # Also delete from SQLite
            return self._delete_sqlite(key)
            
        except Exception as e:
            logger.error(f"Cache delete failed for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            # Try Redis first
            if self.redis_client and REDIS_AVAILABLE:
                return await self.redis_client.exists(key) > 0
            
            # Fallback to SQLite
            return self._exists_sqlite(key)
            
        except Exception as e:
            logger.error(f"Cache exists check failed for key {key}: {e}")
            return False
    
    def _get_sqlite(self, key: str) -> Optional[Any]:
        """Get value from SQLite cache."""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT value, ttl, created_at FROM cache 
                WHERE key = ?
            """, (key,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return None
            
            value, ttl, created_at = result
            
            # Check TTL
            if ttl > 0:
                current_time = int(datetime.now().timestamp())
                if current_time - created_at > ttl:
                    # Expired, delete it
                    self._delete_sqlite(key)
                    return None
            
            return json.loads(value) if value else None
            
        except Exception as e:
            logger.error(f"SQLite get failed: {e}")
            return None
    
    def _set_sqlite(self, key: str, value: Any, ttl: int = 0) -> bool:
        """Set value in SQLite cache."""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            current_time = int(datetime.now().timestamp())
            
            cursor.execute("""
                INSERT OR REPLACE INTO cache (key, value, ttl, created_at)
                VALUES (?, ?, ?, ?)
            """, (key, json.dumps(value, default=str), ttl, current_time))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"SQLite set failed: {e}")
            return False
    
    def _delete_sqlite(self, key: str) -> bool:
        """Delete value from SQLite cache."""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"SQLite delete failed: {e}")
            return False
    
    def _exists_sqlite(self, key: str) -> bool:
        """Check if key exists in SQLite cache."""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT 1 FROM cache WHERE key = ?", (key,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result is not None
            
        except Exception as e:
            logger.error(f"SQLite exists check failed: {e}")
            return False
    
    async def cleanup_expired(self):
        """Clean up expired cache entries."""
        try:
            # Clean up SQLite expired entries
            self._cleanup_sqlite_expired()
            
            # Redis handles TTL automatically
            
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")
    
    def _cleanup_sqlite_expired(self):
        """Clean up expired entries in SQLite."""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            current_time = int(datetime.now().timestamp())
            
            # Delete expired entries
            cursor.execute("""
                DELETE FROM cache 
                WHERE ttl > 0 AND (created_at + ttl) < ?
            """, (current_time,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired cache entries")
                
        except Exception as e:
            logger.error(f"SQLite cleanup failed: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            stats = {
                "sqlite_entries": 0,
                "redis_entries": 0,
                "total_size": 0
            }
            
            # SQLite stats
            try:
                conn = sqlite3.connect(self.sqlite_path)
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM cache")
                stats["sqlite_entries"] = cursor.fetchone()[0]
                
                conn.close()
            except Exception:
                pass
            
            # Redis stats
            if self.redis_client and REDIS_AVAILABLE:
                try:
                    stats["redis_entries"] = await self.redis_client.dbsize()
                except Exception:
                    pass
            
            stats["total_size"] = stats["sqlite_entries"] + stats["redis_entries"]
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
    
    async def close(self):
        """Close cache connections."""
        try:
            if self.redis_client and REDIS_AVAILABLE:
                await self.redis_client.close()
        except Exception as e:
            logger.error(f"Failed to close Redis connection: {e}")


# Global cache instance
cache = Cache()


async def cleanup_cache_periodically():
    """Periodically clean up expired cache entries."""
    while True:
        try:
            await asyncio.sleep(300)  # Every 5 minutes
            await cache.cleanup_expired()
        except Exception as e:
            logger.error(f"Periodic cache cleanup failed: {e}")


# Start cleanup task
def start_cache_cleanup():
    """Start the cache cleanup task."""
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(cleanup_cache_periodically())
    except RuntimeError:
        # No event loop running, skip
        pass
