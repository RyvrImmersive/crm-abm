from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, HttpUrl
import logging
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from .base_agent import BaseAgent, AgentInput, AgentOutput
from config.settings import settings

logger = logging.getLogger(__name__)

class KeywordResearchInput(AgentInput):
    """Input model for keyword research agent"""
    geography: str = Field(..., description="Target geography (e.g., 'US', 'GB')")
    seed_keywords: List[str] = Field(..., description="List of seed keywords to expand")
    max_keywords: int = Field(50, description="Maximum number of keywords to return")
    language_code: str = Field("en", description="Language code (e.g., 'en', 'es')")

class KeywordData(BaseModel):
    """Model for keyword data"""
    keyword: str
    avg_monthly_searches: Optional[int] = None
    competition: Optional[str] = None  # LOW, MEDIUM, HIGH
    competition_index: Optional[float] = None  # 0.0 to 1.0
    cpc_bid_micros: Optional[int] = None  # Micros (1,000,000 micros = 1 unit)

class KeywordResearchOutput(AgentOutput):
    """Output model for keyword research agent"""
    keywords: List[KeywordData] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class KeywordResearchAgent(BaseAgent):
    """Agent for keyword research and expansion"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.google_ads_client = self._initialize_google_ads_client()
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    def _initialize_google_ads_client(self) -> GoogleAdsClient:
        """Initialize and return Google Ads client"""
        credentials = {
            'developer_token': settings.GOOGLE_ADS_DEVELOPER_TOKEN,
            'refresh_token': settings.GOOGLE_ADS_REFRESH_TOKEN,
            'client_id': settings.GOOGLE_ADS_CLIENT_ID,
            'client_secret': settings.GOOGLE_ADS_CLIENT_SECRET,
            'login_customer_id': settings.GOOGLE_ADS_LOGIN_CUSTOMER_ID,
            'use_proto_plus': True
        }
        return GoogleAdsClient.load_from_dict(credentials, version="v16")
    
    async def _execute_impl(self, input_data: KeywordResearchInput) -> KeywordResearchOutput:
        """Execute keyword research"""
        # Step 1: Expand seed keywords using LLM
        expanded_keywords = await self._expand_keywords(
            input_data.seed_keywords, 
            input_data.max_keywords
        )
        
        # Step 2: Get search volume data from Google Ads
        keywords_with_volume = await self._get_keyword_metrics(
            expanded_keywords,
            input_data.geography,
            input_data.language_code
        )
        
        return KeywordResearchOutput(
            success=True,
            keywords=keywords_with_volume,
            metadata={
                "total_keywords": len(keywords_with_volume),
                "geography": input_data.geography,
                "language_code": input_data.language_code,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def _expand_keywords(self, seed_keywords: List[str], max_keywords: int) -> List[str]:
        """Expand seed keywords using LLM"""
        # TODO: Implement keyword expansion using Langflow/OpenAI
        # For now, return the seed keywords as is
        return seed_keywords[:max_keywords]
    
    async def _get_keyword_metrics(
        self, 
        keywords: List[str], 
        location_id: str, 
        language_id: str = "1000"  # English
    ) -> List[KeywordData]:
        """Get keyword metrics from Google Ads API"""
        if not keywords:
            return []
            
        # Google Ads API requires keywords to be unique and have length between 1 and 80
        unique_keywords = list({k.strip() for k in keywords if 1 <= len(k.strip()) <= 80})
        
        # Process in batches of 1000 (Google Ads API limit)
        batch_size = 1000
        all_keyword_data = []
        
        for i in range(0, len(unique_keywords), batch_size):
            batch = unique_keywords[i:i + batch_size]
            try:
                # Run synchronous Google Ads API calls in a thread pool
                loop = asyncio.get_event_loop()
                batch_results = await loop.run_in_executor(
                    self.executor,
                    self._fetch_keyword_metrics_sync,
                    batch,
                    location_id,
                    language_id
                )
                all_keyword_data.extend(batch_results)
            except Exception as e:
                self.logger.error(f"Error fetching metrics for batch {i//batch_size + 1}: {str(e)}")
                continue
                
        return all_keyword_data
    
    def _fetch_keyword_metrics_sync(
        self, 
        keywords: List[str], 
        location_id: str, 
        language_id: str
    ) -> List[KeywordData]:
        """Synchronous method to fetch keyword metrics"""
        try:
            # Initialize Google Ads client for this thread
            client = self._initialize_google_ads_client()
            keyword_plan_idea_service = client.get_service("KeywordPlanIdeaService")
            
            # Create keyword plan location
            location_rns = [f"geoTargets/{location_id}"]
            
            # Create keyword plan network settings
            network_settings = client.get_type("KeywordPlanNetworkSettings")
            network_settings.target_google_search = True
            network_settings.target_search_network = True
            
            # Create keyword seed
            keyword_seed = client.get_type("KeywordSeed")
            for keyword in keywords:
                keyword_info = client.get_type("KeywordInfo")
                keyword_info.text = keyword
                keyword_info.match_type = client.enums.KeywordMatchTypeEnum.EXACT
                keyword_seed.keywords.append(keyword_info)
            
            # Create request
            request = client.get_type("GenerateKeywordIdeasRequest")
            request.customer_id = settings.GOOGLE_ADS_LOGIN_CUSTOMER_ID
            request.language = f"languageConstants/{language_id}"
            request.geo_target_constants = location_rns
            request.include_adult_keywords = False
            request.keyword_seed = keyword_seed
            request.keyword_plan_network = network_settings
            
            # Make the request
            response = keyword_plan_idea_service.generate_keyword_ideas(request=request)
            
            # Process results
            keyword_data = []
            for result in response:
                keyword_text = result.text
                metrics = result.keyword_idea_metrics
                
                if not metrics:
                    continue
                    
                keyword_data.append(KeywordData(
                    keyword=keyword_text,
                    avg_monthly_searches=metrics.avg_monthly_searches,
                    competition=client.enums.KeywordPlanCompetitionLevelEnum.KeywordPlanCompetitionLevel.Name(
                        metrics.competition
                    ).split('_')[-1].capitalize(),
                    competition_index=metrics.competition_index / 100,  # Convert to 0-1 scale
                    cpc_bid_micros=metrics.average_cpc_micros
                ))
                
            return keyword_data
            
        except GoogleAdsException as ex:
            self.logger.error(f"Google Ads API error: {ex}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in _fetch_keyword_metrics_sync: {str(e)}")
            raise
