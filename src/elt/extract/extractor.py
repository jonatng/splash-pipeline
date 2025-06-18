"""
Data Extractor for Unsplash API
"""
import logging
from typing import List, Dict, Any

from ..unsplash_client import UnsplashClient, create_unsplash_client

logger = logging.getLogger(__name__)


class Extractor:
    """Extracts data from the Unsplash API"""

    def __init__(self, client: UnsplashClient = None):
        self.client = client or create_unsplash_client()

    def extract_photos(self, batch_size: int = 50, order_by: str = "latest") -> List[Dict[str, Any]]:
        """
        Extract a batch of photos with details and statistics.
        """
        logger.info(f"Extracting photo batch (size: {batch_size}, order: {order_by})")
        try:
            photos = self.client.extract_photo_batch(batch_size=batch_size, order_by=order_by)
            logger.info(f"Successfully extracted {len(photos)} photos.")
            return photos
        except Exception as e:
            logger.error(f"Failed to extract photo batch: {e}")
            raise

    def extract_trending_data(self) -> Dict[str, Any]:
        """
        Extract trending data, including searches and collections.
        """
        logger.info("Extracting trending data from Unsplash.")
        try:
            trending_data = self.client.extract_trending_data()
            logger.info("Successfully extracted trending data.")
            return trending_data
        except Exception as e:
            logger.error(f"Failed to extract trending data: {e}")
            raise
