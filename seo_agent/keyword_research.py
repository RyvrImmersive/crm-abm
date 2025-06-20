from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
import logging
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import time
import random
import logging
import threading
from datetime import datetime, timedelta
from functools import wraps
import logging
import time
from typing import TypeVar, Type, Any, Callable, Optional, Dict, List, TypeVar, Union, Tuple
from google.api_core.exceptions import ResourceExhausted, RetryError, GoogleAPICallError
from ratelimit import limits, sleep_and_retry
import backoff
import grpc

# Set up logging
logger = logging.getLogger(__name__)

# Type variable for generic function typing
F = TypeVar('F', bound=Callable[..., Any])

class RateLimiter:
    """A rate limiter that respects Google Ads API rate limits."""
    
    def __init__(self, calls: int = 1, period: float = 1.0):
        """Initialize the rate limiter.
        
        Args:
            calls: Number of calls allowed per period
            period: Period in seconds
        """
        self.calls = calls
        self.period = period
        self.timestamps: List[float] = []
        self.lock = threading.Lock()
    
    def __call__(self, func: F) -> F:
        """Decorator to rate limit function calls."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.lock:
                now = time.time()
                # Remove timestamps older than the period
                self.timestamps = [t for t in self.timestamps if now - t < self.period]
                
                if len(self.timestamps) >= self.calls:
                    # Calculate how long to sleep
                    sleep_time = self.period - (now - self.timestamps[0])
                    if sleep_time > 0:
                        logger.debug(f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds...")
                        time.sleep(sleep_time)
                
                # Record this call
                self.timestamps.append(time.time())
            
            return func(*args, **kwargs)
        return wrapper  # type: ignore

def is_retriable_error(exception: Exception) -> bool:
    """Check if the exception is retriable."""
    if isinstance(exception, (ResourceExhausted, GoogleAPICallError)):
        return True
    
    # Check for gRPC errors
    if isinstance(exception, grpc.RpcError):
        code = exception.code()
        return code in [
            grpc.StatusCode.RESOURCE_EXHAUSTED,
            grpc.StatusCode.UNAVAILABLE,
            grpc.StatusCode.ABORTED,
            grpc.StatusCode.DEADLINE_EXCEEDED,
            grpc.StatusCode.INTERNAL,
        ]
    
    return False

# Configure backoff for rate limiting
def backoff_hdlr(details):
    logger.warning(
        "Backing off {wait:0.1f} seconds after {tries} tries "
        "calling function {target} with args {args} and kwargs "
        "{kwargs}".format(**details)
    )

def rate_limit_error_handler(details):
    logger.warning(
        "Rate limit reached. Waiting {wait:0.1f} seconds before retrying...".format(
            wait=details['wait']
        )
    )

def retry_on_quota_error(max_retries: int = 5) -> Callable[[F], F]:
    """A decorator that retries a function when it hits rate limits.
    
    This version uses the backoff library for more sophisticated retry logic
    and better handling of rate limits.
    """
    def decorator(func: F) -> F:
        @backoff.on_exception(
            backoff.expo,
            (ResourceExhausted, GoogleAPICallError, grpc.RpcError),
            max_tries=max_retries,
            max_time=300,  # 5 minutes max total time
            jitter=backoff.full_jitter,
            on_backoff=[backoff_hdlr],
            giveup=lambda e: not is_retriable_error(e)
        )
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if is_retriable_error(e):
                    logger.warning(f"Retriable error: {str(e)}")
                    raise
                logger.error(f"Non-retriable error: {str(e)}")
                raise
        return wrapper  # type: ignore
    return decorator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["keyword-research"])

class KeywordRequest(BaseModel):
    keywords: List[str]
    location_id: int = 2356  # Default to India
    language_id: int = 1000  # Default to English
    customer_id: Optional[str] = None

class KeywordResult(BaseModel):
    keyword: str
    avg_monthly_searches: int
    competition: str

@retry_on_quota_error(max_retries=5)
async def get_keyword_ideas(
    keywords: List[str],
    location_id: int = 1022378,  # Default to India
    language_id: int = 1000,  # Default to English
    client: Optional[GoogleAdsClient] = None,
    customer_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get keyword ideas from Google Ads API with automatic retry on rate limits.
    
    Args:
        keywords: List of seed keywords to get ideas for
        location_id: Location ID (geographic target)
        language_id: Language ID
        client: Optional GoogleAdsClient instance
        customer_id: Optional Google Ads customer ID (will use GOOGLE_ADS_CUSTOMER_ID env var if not provided)
        
    Returns:
        List of keyword ideas with metrics
        
    Raises:
        ValueError: If required parameters are missing
        GoogleAdsException: For Google Ads API specific errors
        Exception: For other unexpected errors
    """
    logger.info(f"Starting keyword research for {len(keywords)} keywords")
    
    # Validate inputs
    if not keywords:
        raise ValueError("At least one keyword is required")
    if len(keywords) > 10:  # Limit number of keywords to avoid rate limiting
        logger.warning(f"Too many keywords ({len(keywords)}), using first 10")
        keywords = keywords[:10]
    
    try:
        # Use sync version for now to avoid asyncio issues
        return await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: get_keyword_ideas_sync(
                keywords=keywords,
                location_id=location_id,
                language_id=language_id,
                client=client,
                customer_id=customer_id,
            ),
        )
    except Exception as e:
        logger.error(f"Error in get_keyword_ideas: {str(e)}")
        raise

def get_keyword_ideas_sync(
    keywords: List[str],
    location_id: int = 2356,  # Default to India
    language_id: int = 1000,  # Default to English
    client: Optional[GoogleAdsClient] = None,
    customer_id: Optional[str] = None,
    max_retries: int = 3,
) -> List[Dict[str, Any]]:
    """Get keyword ideas from Google Ads API - synchronous version."""
    try:
        logger.info(f"Starting keyword research with {len(keywords)} keywords")
        logger.info(f"Location ID: {location_id}, Language ID: {language_id}")
        logger.info(f"Will use up to {max_retries} retries with exponential backoff")
        
        # Log the first few keywords (don't log all to avoid sensitive data exposure)
        if len(keywords) > 5:
            logger.info(f"Keywords (first 5): {keywords[:5]}...")
        else:
            logger.info(f"Keywords: {keywords}")
        
        # Validate inputs
        if not keywords:
            logger.error("No keywords provided")
            raise ValueError("At least one keyword is required")
        
        # Initialize client if not provided
        if client is None:
            logger.info("Initializing Google Ads client from google-ads.yaml")
            try:
                client = GoogleAdsClient.load_from_storage("google-ads.yaml")
                logger.info("Successfully initialized Google Ads client")
            except Exception as e:
                logger.error(f"Failed to initialize Google Ads client: {str(e)}")
                raise
        
        # Get customer ID if not provided
        if customer_id is None:
            logger.info("Customer ID not provided, checking environment variables")
            customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID")
            if not customer_id:
                error_msg = "No customer ID provided and GOOGLE_ADS_CUSTOMER_ID environment variable not set"
                logger.error(error_msg)
                raise ValueError(error_msg)
        
        # Initialize services
        keyword_plan_idea_service = client.get_service("KeywordPlanIdeaService")
        google_ads_service = client.get_service("GoogleAdsService")
        
        # Prepare the request
        request = client.get_type("GenerateKeywordIdeasRequest")
        request.customer_id = customer_id
        
        # Set language
        request.language = f"languageConstants/{language_id}"
        logger.debug(f"Set language to: {language_id}")
        
        # Set location
        geo_target = client.get_type("LocationInfo")
        geo_target.geo_target_constant = f"geoTargetConstants/{location_id}"
        request.geo_target_constants = [geo_target.geo_target_constant]
        logger.debug(f"Set location to: {location_id}")
        
        # Set keyword seeds
        keyword_and_url_seed = client.get_type("KeywordAndUrlSeed")
        keyword_and_url_seed.keywords = keywords[:10]
        keyword_and_url_seed.url = "https://www.example.com"  # Set a valid URL
        request.keyword_and_url_seed = keyword_and_url_seed
        
        # Set the keyword plan network
        request.keyword_plan_network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH_AND_PARTNERS
        
        # Include adult keywords and ensure metrics are returned
        request.include_adult_keywords = False
        
        logger.info(f"Making API request for keywords: {keywords[:10]}")
        logger.info(f"Request details - Customer: {customer_id}, Location: {location_id}, Language: {language_id}")
        
        # Make the API call
        response = keyword_plan_idea_service.generate_keyword_ideas(request=request)
            
        # Process the response
        results = []
        logger.info(f"Processing {len(response.results)} keyword ideas from API response")
        
        for i, idea in enumerate(response.results):
            # Debug: Log the structure of the response (only for first few items to avoid spam)
            if i < 3:
                logger.info(f"Sample idea {i+1}: {idea}")
            
            # Extract keyword text
            keyword_text = getattr(idea, 'text', 'Unknown')
            
            # Extract metrics with proper error handling
            avg_monthly_searches = 0
            competition = 'UNSPECIFIED'
            competition_index = 0
            
            try:
                if hasattr(idea, 'keyword_idea_metrics') and idea.keyword_idea_metrics:
                    metrics = idea.keyword_idea_metrics
                    
                    # Get average monthly searches
                    if hasattr(metrics, 'avg_monthly_searches') and metrics.avg_monthly_searches is not None:
                        avg_monthly_searches = int(metrics.avg_monthly_searches)
                    
                    # Get competition level
                    if hasattr(metrics, 'competition') and metrics.competition:
                        competition = metrics.competition.name if hasattr(metrics.competition, 'name') else str(metrics.competition)
                    
                    # Get competition index
                    if hasattr(metrics, 'competition_index') and metrics.competition_index is not None:
                        competition_index = float(metrics.competition_index)
                        
                    if i < 3:  # Log details for first few items
                        logger.info(f"Extracted metrics for '{keyword_text}' - Searches: {avg_monthly_searches}, Competition: {competition}")
                else:
                    if i < 3:  # Log missing metrics for first few items
                        logger.warning(f"No keyword_idea_metrics found for '{keyword_text}'")
                    
            except Exception as metric_error:
                logger.warning(f"Error extracting metrics for keyword '{keyword_text}': {metric_error}")
            
            result = {
                'keyword': keyword_text,
                'avg_monthly_searches': avg_monthly_searches,
                'competition': competition,
                'competition_index': competition_index,
            }
            results.append(result)
        
        logger.info(f"Successfully processed {len(results)} keyword results")
        return results
            
    except Exception as e:
        logger.error(f"Error generating keyword ideas: {str(e)}")
        raise
        
    except GoogleAdsException as ex:
        logger.error(f"Request ID: {ex.request_id}")
        for error in ex.failure.errors:
            logger.error(f"Error: {error.message}")
            if error.location:
                for field_path_element in error.location.field_path_elements:
                    logger.error(f"Field: {field_path_element.field_name}")
        raise Exception(f"Google Ads API error: {ex.failure.errors[0].message if ex.failure.errors else 'Unknown error'}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise

async def get_keyword_ideas(
    keywords: List[str],
    location_id: int = 2356,
    language_id: int = 1000,
    client: Optional[GoogleAdsClient] = None,
    customer_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Async wrapper for get_keyword_ideas_sync"""
    return get_keyword_ideas_sync(keywords, location_id, language_id, client, customer_id)

@router.post("/keyword-research", response_model=List[KeywordResult])
async def keyword_research(request: KeywordRequest):
    """API endpoint for keyword research"""
    try:
        results = await get_keyword_ideas(
            keywords=request.keywords,
            location_id=request.location_id,
            language_id=request.language_id,
            customer_id=request.customer_id
        )
        
        return [KeywordResult(**result) for result in results]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Langflow integration function
def get_keyword_ideas_for_langflow(keywords: List[str], **kwargs) -> List[Dict[str, Any]]:
    """
    Wrapper function for Langflow integration
    """
    try:
        client = GoogleAdsClient.load_from_storage("google-ads.yaml")
        customer_service = client.get_service("CustomerService")
        accessible_customers = customer_service.list_accessible_customers()
        
        if not accessible_customers.resource_names:
            raise ValueError("No accessible customer accounts found")
            
        customer_id = accessible_customers.resource_names[0].split('/')[-1]
        
        return get_keyword_ideas_sync(
            client=client,
            customer_id=customer_id,
            keywords=keywords,
            location_id=kwargs.get('location_id', 2356),
            language_id=kwargs.get('language_id', 1000)
        )
    except Exception as e:
        logger.error(f"Error in Langflow integration: {str(e)}")
        raise

# Test function
def test_keyword_ideas():
    """Test function to verify the API connection"""
    try:
        # Test with sample keywords
        test_keywords = ["digital marketing", "seo services", "web development"]
        
        results = get_keyword_ideas_sync(
            keywords=test_keywords,
            location_id=2356,  # India
            language_id=1000   # English
        )
        
        # Print results
        print(f"\nFound {len(results)} keyword ideas:\n")
        for result in results[:10]:  # Show first 10
            print(f"Keyword: {result['keyword']}")
            print(f"Avg Monthly Searches: {result['avg_monthly_searches']:,}")
            print(f"Competition: {result['competition']}")
            print("-" * 50)
            
        return results
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        return None

# For backward compatibility
app = router

if __name__ == "__main__":
    print("Running keyword research test...")
    test_keyword_ideas()