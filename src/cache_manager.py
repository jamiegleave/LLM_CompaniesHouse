import redis
import json
from datetime import timedelta
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 0)),
            password=os.getenv('REDIS_PASSWORD'),
            decode_responses=True
        )
        self.expire_seconds = int(timedelta(
            hours=int(os.getenv('REDIS_EXPIRE_HOURS', 24))
        ).total_seconds())

    def get_company_data(self, company_number: str):
        """Retrieve company data from cache"""
        try:
            data = self.redis_client.get(f"company:{company_number}")
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Redis get error: {str(e)}")
            return None

    def set_company_data(self, company_number: str, company_details: dict, statements: dict):
        """Store company data in cache"""
        try:
            data = {
                "company_details": company_details,
                "statements": statements
            }
            self.redis_client.setex(
                f"company:{company_number}",
                self.expire_seconds,
                json.dumps(data)
            )
            logger.info(f"Cached data for company {company_number}")
            return True
        except Exception as e:
            logger.error(f"Redis set error: {str(e)}")
            return False

    def is_healthy(self):
        """Check if Redis connection is working"""
        try:
            return self.redis_client.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return False 