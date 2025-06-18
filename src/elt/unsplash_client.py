"""
Unsplash API client for extracting photos, statistics, and trending data
"""

import os
import time
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import random

logger = logging.getLogger(__name__)


@dataclass
class UnsplashConfig:
    """Configuration for Unsplash API"""
    access_key: str
    secret_key: Optional[str] = None
    base_url: str = "https://api.unsplash.com"
    rate_limit_per_hour: int = 5000
    batch_size: int = 30
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 300.0  # 5 minutes max delay


class RateLimitExceeded(Exception):
    """Custom exception for rate limit exceeded"""
    pass


class UnsplashClient:
    """Client for interacting with Unsplash API with enhanced rate limiting"""
    
    def __init__(self, config: UnsplashConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Client-ID {config.access_key}',
            'Accept-Version': 'v1'
        })
        self.request_count = 0
        self.last_reset = datetime.now()
        self.remaining_requests = config.rate_limit_per_hour
        self.reset_time = None
    
    def _update_rate_limit_from_headers(self, response: requests.Response):
        """Update rate limit info from API response headers"""
        if 'X-Ratelimit-Remaining' in response.headers:
            self.remaining_requests = int(response.headers['X-Ratelimit-Remaining'])
            logger.debug(f"Remaining requests: {self.remaining_requests}")
        
        if 'X-Ratelimit-Limit' in response.headers:
            limit = int(response.headers['X-Ratelimit-Limit'])
            logger.debug(f"Rate limit: {limit}")
    
    def _check_rate_limit(self):
        """Enhanced rate limiting with better tracking"""
        now = datetime.now()
        
        # Reset hourly counter
        if (now - self.last_reset).total_seconds() >= 3600:
            self.request_count = 0
            self.last_reset = now
            logger.info("Rate limit counter reset")
        
        # Check if we're approaching limits
        if self.remaining_requests <= 10:
            logger.warning(f"Low remaining requests: {self.remaining_requests}")
        
        if self.remaining_requests <= 0:
            sleep_time = 3600 - (now - self.last_reset).total_seconds()
            if sleep_time > 0:
                logger.warning(f"Rate limit exhausted. Sleeping for {sleep_time:.1f} seconds")
                time.sleep(sleep_time)
                self.request_count = 0
                self.last_reset = datetime.now()
                self.remaining_requests = self.config.rate_limit_per_hour
    
    def _exponential_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter"""
        delay = min(
            self.config.base_delay * (2 ** attempt), 
            self.config.max_delay
        )
        # Add jitter to avoid thundering herd
        jitter = random.uniform(0.1, 0.3) * delay
        return delay + jitter
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Enhanced API request with exponential backoff and better error handling"""
        self._check_rate_limit()
        
        url = f"{self.config.base_url}/{endpoint}"
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"Making request to {endpoint} (attempt {attempt + 1})")
                response = self.session.get(url, params=params, timeout=30)
                self.request_count += 1
                
                # Update rate limit info from headers
                self._update_rate_limit_from_headers(response)
                
                if response.status_code == 200:
                    if attempt > 0:
                        logger.info(f"Request succeeded after {attempt + 1} attempts")
                    return response.json()
                
                elif response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited by API. Retry after {retry_after} seconds")
                    
                    if attempt < self.config.max_retries - 1:
                        time.sleep(retry_after)
                        continue
                    else:
                        raise RateLimitExceeded(f"Rate limit exceeded after {self.config.max_retries} attempts")
                
                elif response.status_code == 403:
                    if "Rate Limit Exceeded" in response.text:
                        logger.error("Rate limit exceeded (403). Consider upgrading API plan or reducing request frequency")
                        if attempt < self.config.max_retries - 1:
                            delay = self._exponential_backoff(attempt)
                            logger.info(f"Waiting {delay:.1f} seconds before retry...")
                            time.sleep(delay)
                            continue
                        else:
                            raise RateLimitExceeded("Rate limit exceeded (403)")
                    else:
                        logger.error(f"Forbidden: {response.text}")
                        response.raise_for_status()
                
                elif response.status_code >= 500:  # Server errors
                    logger.warning(f"Server error {response.status_code}. Retrying...")
                    if attempt < self.config.max_retries - 1:
                        delay = self._exponential_backoff(attempt)
                        time.sleep(delay)
                        continue
                    else:
                        response.raise_for_status()
                
                else:
                    logger.error(f"API request failed: {response.status_code} - {response.text}")
                    response.raise_for_status()
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1})")
                if attempt < self.config.max_retries - 1:
                    delay = self._exponential_backoff(attempt)
                    time.sleep(delay)
                    continue
                else:
                    raise
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                last_exception = e
                if attempt < self.config.max_retries - 1:
                    delay = self._exponential_backoff(attempt)
                    time.sleep(delay)
                    continue
                else:
                    raise
        
        if last_exception:
            raise last_exception
    
    def get_photos(self, page: int = 1, per_page: int = 30, order_by: str = "latest") -> List[Dict[str, Any]]:
        """Get photos from Unsplash with rate limiting"""
        # Respect batch size limits
        per_page = min(per_page, self.config.batch_size)
        
        params = {
            'page': page,
            'per_page': per_page,
            'order_by': order_by
        }
        
        try:
            response = self._make_request("photos", params)
            return response if isinstance(response, list) else []
        except RateLimitExceeded:
            logger.warning("Rate limit exceeded for get_photos, returning empty list")
            return []
        except Exception as e:
            logger.error(f"Failed to get photos: {e}")
            return []
    
    def get_photo_details(self, photo_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific photo with error handling"""
        try:
            return self._make_request(f"photos/{photo_id}")
        except RateLimitExceeded:
            logger.warning(f"Rate limit exceeded for photo {photo_id}, skipping details")
            return None
        except Exception as e:
            logger.error(f"Failed to get details for photo {photo_id}: {e}")
            return None
    
    def get_photo_statistics(self, photo_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific photo with error handling"""
        try:
            return self._make_request(f"photos/{photo_id}/statistics")
        except RateLimitExceeded:
            logger.warning(f"Rate limit exceeded for photo {photo_id} statistics, skipping")
            return None
        except Exception as e:
            logger.warning(f"Failed to get statistics for photo {photo_id}: {e}")
            return None
    
    def search_photos(self, query: str, page: int = 1, per_page: int = 30, 
                     order_by: str = "relevant") -> Dict[str, Any]:
        """Search for photos with error handling"""
        params = {
            'query': query,
            'page': page,
            'per_page': min(per_page, self.config.batch_size),
            'order_by': order_by
        }
        
        try:
            return self._make_request("search/photos", params)
        except RateLimitExceeded:
            logger.warning(f"Rate limit exceeded for search '{query}', returning empty results")
            return {'results': [], 'total': 0, 'total_pages': 0}
        except Exception as e:
            logger.error(f"Failed to search photos for '{query}': {e}")
            return {'results': [], 'total': 0, 'total_pages': 0}
    
    def get_trending_searches(self) -> List[str]:
        """Get trending search terms (simulated - Unsplash doesn't provide this directly)"""
        # This would need to be implemented by analyzing popular searches
        # For now, return some common trending terms
        trending_terms = [
            "nature", "landscape", "portrait", "architecture", "travel",
            "food", "technology", "business", "fashion", "art",
            "minimal", "abstract", "urban", "vintage", "modern"
        ]
        return trending_terms
    
    def get_collections(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """Get featured collections with error handling"""
        params = {
            'page': page,
            'per_page': min(per_page, self.config.batch_size)
        }
        
        try:
            response = self._make_request("collections", params)
            return response if isinstance(response, list) else []
        except RateLimitExceeded:
            logger.warning("Rate limit exceeded for collections, returning empty list")
            return []
        except Exception as e:
            logger.error(f"Failed to get collections: {e}")
            return []
    
    def get_collection_photos(self, collection_id: str, page: int = 1, 
                            per_page: int = 30) -> List[Dict[str, Any]]:
        """Get photos from a specific collection with error handling"""
        params = {
            'page': page,
            'per_page': min(per_page, self.config.batch_size)
        }
        
        try:
            response = self._make_request(f"collections/{collection_id}/photos", params)
            return response if isinstance(response, list) else []
        except RateLimitExceeded:
            logger.warning(f"Rate limit exceeded for collection {collection_id}, returning empty list")
            return []
        except Exception as e:
            logger.error(f"Failed to get photos from collection {collection_id}: {e}")
            return []
    
    def get_user_photos(self, username: str, page: int = 1, 
                       per_page: int = 30) -> List[Dict[str, Any]]:
        """Get photos by a specific user"""
        params = {
            'page': page,
            'per_page': min(per_page, self.config.batch_size)
        }
        
        response = self._make_request(f"users/{username}/photos", params)
        return response if isinstance(response, list) else []
    
    def get_user_statistics(self, username: str) -> Dict[str, Any]:
        """Get statistics for a specific user"""
        return self._make_request(f"users/{username}/statistics")
    
    def extract_photo_batch(self, batch_size: int = None, order_by: str = "latest") -> List[Dict[str, Any]]:
        """Extract a batch of photos with full details and statistics - Rate limit aware"""
        batch_size = batch_size or self.config.batch_size
        photos = []
        skipped_count = 0
        max_skips = batch_size // 2  # Allow skipping up to half the batch due to rate limits
        
        logger.info(f"Starting photo batch extraction (size: {batch_size})")
        
        # Get basic photo list
        photo_list = self.get_photos(per_page=batch_size, order_by=order_by)
        
        if not photo_list:
            logger.warning("No photos retrieved from initial request")
            return []
        
        for i, photo in enumerate(photo_list):
            try:
                # Check if we should continue (rate limit protection)
                if self.remaining_requests <= 5:
                    logger.warning(f"Low remaining requests ({self.remaining_requests}), stopping early")
                    break
                
                # Get detailed photo information (optional, skip if rate limited)
                photo_details = self.get_photo_details(photo['id'])
                if photo_details is None:
                    skipped_count += 1
                    if skipped_count > max_skips:
                        logger.warning("Too many skipped photos due to rate limits, stopping")
                        break
                    # Use basic photo data if details fail
                    photo_details = photo
                
                # Get photo statistics (optional, skip if rate limited) 
                photo_stats = self.get_photo_statistics(photo['id'])
                if photo_stats:
                    photo_details['statistics'] = photo_stats
                else:
                    photo_details['statistics'] = {}
                
                photos.append(photo_details)
                
                # Progressive delay based on remaining requests
                if self.remaining_requests < 50:
                    time.sleep(0.5)  # Longer delay when low on requests
                elif self.remaining_requests < 100:
                    time.sleep(0.3)
                else:
                    time.sleep(0.1)  # Standard delay
                
                # Progress logging
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(photo_list)} photos, remaining requests: {self.remaining_requests}")
                
            except Exception as e:
                logger.error(f"Failed to process photo {photo.get('id', 'unknown')}: {e}")
                skipped_count += 1
                if skipped_count > max_skips:
                    logger.warning("Too many errors, stopping batch extraction")
                    break
                continue
        
        logger.info(f"Batch extraction complete: {len(photos)} photos extracted, {skipped_count} skipped")
        return photos
    
    def extract_trending_data(self) -> Dict[str, Any]:
        """Extract trending data including popular searches and collections - Rate limit aware"""
        trending_data = {
            'trending_searches': self.get_trending_searches(),
            'featured_collections': [],
            'popular_photos': [],
            'extracted_at': datetime.now().isoformat()
        }
        
        logger.info("Extracting trending data...")
        
        try:
            # Only proceed if we have enough remaining requests
            if self.remaining_requests > 20:
                # Get featured collections
                collections = self.get_collections(per_page=10)
                trending_data['featured_collections'] = collections
                logger.info(f"Retrieved {len(collections)} featured collections")
                
                # Get popular photos (ordered by popularity) 
                if self.remaining_requests > 10:
                    popular_photos = self.get_photos(order_by="popular", per_page=15)
                    trending_data['popular_photos'] = popular_photos
                    logger.info(f"Retrieved {len(popular_photos)} popular photos")
                else:
                    logger.warning("Insufficient remaining requests for popular photos")
            else:
                logger.warning("Insufficient remaining requests for trending data extraction")
            
        except Exception as e:
            logger.error(f"Failed to extract trending data: {e}")
        
        return trending_data


def create_unsplash_client() -> UnsplashClient:
    """Create and configure Unsplash client with enhanced rate limiting"""
    config = UnsplashConfig(
        access_key=os.getenv("UNSPLASH_ACCESS_KEY"),
        secret_key=os.getenv("UNSPLASH_SECRET_KEY"),
        rate_limit_per_hour=int(os.getenv("UNSPLASH_RATE_LIMIT_PER_HOUR", "5000")),
        batch_size=int(os.getenv("BATCH_SIZE", "20")),  # Reduced default batch size
        max_retries=int(os.getenv("UNSPLASH_MAX_RETRIES", "3")),
        base_delay=float(os.getenv("UNSPLASH_BASE_DELAY", "1.0")),
        max_delay=float(os.getenv("UNSPLASH_MAX_DELAY", "300.0"))
    )
    
    if not config.access_key:
        raise ValueError("UNSPLASH_ACCESS_KEY environment variable is required")
    
    logger.info(f"Initialized Unsplash client with rate limit: {config.rate_limit_per_hour}/hour, "
                f"batch size: {config.batch_size}, max retries: {config.max_retries}")
    
    return UnsplashClient(config) 