from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field, HttpUrl
import logging
import aiohttp
from bs4 import BeautifulSoup
import asyncio
from urllib.parse import urlparse
import json
import re

from .base_agent import BaseAgent, AgentInput, AgentOutput
from .url_analysis_agent import URLAnalysisAgent, URLMetrics, ContentAnalysis
from config.settings import settings

logger = logging.getLogger(__name__)

class CompetitorAnalysisInput(AgentInput):
    """Input model for competitor analysis agent"""
    target_url: HttpUrl = Field(..., description="The URL to analyze competitors for")
    keywords: List[str] = Field(..., description="List of target keywords")
    max_competitors: int = Field(5, description="Maximum number of competitors to analyze")
    geography: str = Field("us", description="Geography for search (e.g., 'us', 'uk')")
    language: str = Field("en", description="Language code (e.g., 'en', 'es')")

class CompetitorData(BaseModel):
    """Data model for a single competitor"""
    url: str
    domain: str
    title: str
    description: str
    rank: int
    metrics: Optional[URLMetrics] = None
    content_analysis: Optional[ContentAnalysis] = None
    backlinks: Optional[int] = None
    domain_authority: Optional[float] = None
    page_authority: Optional[float] = None
    social_metrics: Optional[Dict[str, int]] = None

class CompetitorAnalysisOutput(AgentOutput):
    """Output model for competitor analysis agent"""
    target_url: str
    keywords: List[str]
    competitors: List[CompetitorData] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True

class CompetitorAnalysisAgent(BaseAgent):
    """Agent for analyzing competitors in search results"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.session = None
        self.url_analyzer = URLAnalysisAgent()
    
    async def _execute_impl(self, input_data: CompetitorAnalysisInput) -> CompetitorAnalysisOutput:
        """Execute competitor analysis"""
        self.session = aiohttp.ClientSession()
        try:
            # Step 1: Find competitors in search results
            competitors = await self._find_competitors(
                input_data.keywords,
                input_data.geography,
                input_data.language,
                input_data.max_competitors
            )
            
            # Step 2: Analyze each competitor
            analyzed_competitors = []
            for i, competitor in enumerate(competitors):
                try:
                    analyzed = await self._analyze_competitor(
                        competitor,
                        rank=i+1,
                        target_keywords=input_data.keywords
                    )
                    analyzed_competitors.append(analyzed)
                except Exception as e:
                    logger.error(f"Error analyzing competitor {competitor}: {str(e)}")
            
            # Step 3: Generate summary
            summary = self._generate_summary(analyzed_competitors, input_data.keywords)
            
            return CompetitorAnalysisOutput(
                success=True,
                target_url=str(input_data.target_url),
                keywords=input_data.keywords,
                competitors=analyzed_competitors,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Error in competitor analysis: {str(e)}", exc_info=True)
            return CompetitorAnalysisOutput(
                success=False,
                target_url=str(input_data.target_url),
                keywords=input_data.keywords,
                error=str(e)
            )
        finally:
            if self.session:
                await self.session.close()
    
    async def _find_competitors(
        self, 
        keywords: List[str], 
        geography: str,
        language: str,
        max_results: int = 5
    ) -> List[str]:
        """Find competitors in search results for given keywords"""
        # Note: In a production environment, you would use a SERP API like SerpAPI, Moz, Ahrefs, etc.
        # This is a simplified version that simulates finding competitors
        
        # For demonstration, we'll return some example competitors
        # In a real implementation, you would make API calls to a search engine
        example_competitors = [
            "https://www.semrush.com/",
            "https://ahrefs.com/",
            "https://moz.com/",
            "https://www.hubspot.com/seo-tools",
            "https://www.wordstream.com/"
        ]
        
        return example_competitors[:max_results]
    
    async def _analyze_competitor(
        self, 
        competitor_url: str, 
        rank: int, 
        target_keywords: List[str]
    ) -> CompetitorData:
        """Analyze a single competitor"""
        try:
            # Get basic page info
            domain = urlparse(competitor_url).netloc
            
            # Fetch and parse the page
            async with self.session.get(competitor_url, timeout=30) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch {competitor_url}: {response.status}")
                
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                # Extract basic info
                title = self._extract_title(soup)
                description = self._extract_meta_description(soup)
                
                # Get URL metrics and content analysis using URL analysis agent
                url_analysis = await self.url_analyzer._execute_impl(
                    type('obj', (object,), {
                        'url': competitor_url,
                        'target_keywords': target_keywords,
                        'analyze_competitors': False
                    })
                )
                
                # Get backlinks and domain authority (simulated)
                backlinks = await self._get_backlink_count(competitor_url)
                domain_auth, page_auth = await self._get_authority_metrics(competitor_url)
                
                # Get social metrics (simulated)
                social_metrics = await self._get_social_metrics(competitor_url)
                
                return CompetitorData(
                    url=competitor_url,
                    domain=domain,
                    title=title,
                    description=description,
                    rank=rank,
                    metrics=url_analysis.metrics if hasattr(url_analysis, 'metrics') else None,
                    content_analysis=url_analysis.metrics.content_analysis if hasattr(url_analysis, 'metrics') else None,
                    backlinks=backlinks,
                    domain_authority=domain_auth,
                    page_authority=page_auth,
                    social_metrics=social_metrics
                )
                
        except Exception as e:
            logger.error(f"Error analyzing competitor {competitor_url}: {str(e)}")
            # Return partial data if available
            return CompetitorData(
                url=competitor_url,
                domain=urlparse(competitor_url).netloc,
                title="",
                description="",
                rank=rank,
                error=str(e)
            )
    
    async def _get_backlink_count(self, url: str) -> Optional[int]:
        """Get number of backlinks (simulated)"""
        # In a real implementation, call an API like Moz, Ahrefs, or Majestic
        await asyncio.sleep(0.1)  # Simulate API call
        return 1000  # Simulated value
    
    async def _get_authority_metrics(self, url: str) -> Tuple[Optional[float], Optional[float]]:
        """Get domain and page authority (simulated)"""
        # In a real implementation, call Moz API or similar
        await asyncio.sleep(0.1)  # Simulate API call
        return 75.0, 65.0  # Simulated values for domain authority and page authority
    
    async def _get_social_metrics(self, url: str) -> Dict[str, int]:
        """Get social media metrics (simulated)"""
        # In a real implementation, call a social media API
        await asyncio.sleep(0.1)  # Simulate API call
        return {
            "facebook_shares": 1000,
            "twitter_shares": 500,
            "linkedin_shares": 200,
            "pinterest_pins": 300
        }
    
    def _generate_summary(
        self, 
        competitors: List[CompetitorData],
        target_keywords: List[str]
    ) -> Dict[str, Any]:
        """Generate a summary of competitor analysis"""
        if not competitors:
            return {}
        
        # Calculate average metrics
        total_da = sum(c.domain_authority or 0 for c in competitors)
        total_pa = sum(c.page_authority or 0 for c in competitors)
        total_backlinks = sum(c.backlinks or 0 for c in competitors)
        
        avg_da = total_da / len(competitors)
        avg_pa = total_pa / len(competitors)
        avg_backlinks = total_backlinks / len(competitors)
        
        # Find top competitors by different metrics
        top_by_da = max(competitors, key=lambda x: x.domain_authority or 0)
        top_by_backlinks = max(competitors, key=lambda x: x.backlinks or 0)
        
        # Analyze content length
        content_lengths = [
            (c.url, c.content_analysis.word_count if c.content_analysis else 0) 
            for c in competitors
        ]
        content_lengths.sort(key=lambda x: x[1], reverse=True)
        
        return {
            "total_competitors_analyzed": len(competitors),
            "average_domain_authority": round(avg_da, 1),
            "average_page_authority": round(avg_pa, 1),
            "average_backlinks": round(avg_backlinks),
            "top_domain_authority": {
                "url": top_by_da.url,
                "score": top_by_da.domain_authority
            },
            "top_backlinks": {
                "url": top_by_backlinks.url,
                "count": top_by_backlinks.backlinks
            },
            "content_length_ranking": [
                {"url": url, "word_count": count} 
                for url, count in content_lengths
            ],
            "recommendations": self._generate_recommendations(competitors, target_keywords)
        }
    
    def _generate_recommendations(
        self, 
        competitors: List[CompetitorData],
        target_keywords: List[str]
    ) -> List[str]:
        """Generate actionable recommendations based on competitor analysis"""
        recommendations = []
        
        # Analyze content length
        content_lengths = [
            c.content_analysis.word_count 
            for c in competitors 
            if c.content_analysis and c.content_analysis.word_count
        ]
        
        if content_lengths:
            avg_content_length = sum(content_lengths) / len(content_lengths)
            recommendations.append(
                f"Aim for content length around {int(avg_content_length)} words, "
                "which is the average among top competitors."
            )
        
        # Analyze backlinks
        backlinks = [c.backlinks or 0 for c in competitors]
        if backlinks:
            avg_backlinks = sum(backlinks) / len(backlinks)
            recommendations.append(
                f"The average competitor has {int(avg_backlinks)} backlinks. "
                "Consider a backlink building strategy to compete effectively."
            )
        
        # Check for common keywords in top competitors' titles and descriptions
        common_terms = self._find_common_terms([c.title for c in competitors])
        if common_terms and target_keywords:
            missing_terms = [t for t in common_terms if t not in ' '.join(target_keywords).lower()]
            if missing_terms:
                recommendations.append(
                    f"Consider including these common terms in your content: {', '.join(missing_terms)}"
                )
        
        return recommendations
    
    @staticmethod
    def _find_common_terms(texts: List[str], top_n: int = 5) -> List[str]:
        """Find most common terms in a list of texts"""
        from collections import Counter
        import re
        
        # Tokenize and count words
        words = []
        for text in texts:
            if not text:
                continue
            words.extend(re.findall(r'\b\w{3,}\b', text.lower()))
        
        # Remove stopwords (simplified)
        stopwords = {'the', 'and', 'or', 'in', 'on', 'at', 'for', 'to', 'of', 'a', 'an', 'is', 'are', 'be', 'this', 'that', 'it', 'with', 'as'}
        filtered_words = [w for w in words if w not in stopwords]
        
        # Get most common terms
        counter = Counter(filtered_words)
        return [term for term, _ in counter.most_common(top_n)]
    
    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> str:
        """Extract page title"""
        if soup.title:
            return soup.title.text.strip()
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()
        h1 = soup.find('h1')
        return h1.text.strip() if h1 else ""
    
    @staticmethod
    def _extract_meta_description(soup: BeautifulSoup) -> str:
        """Extract meta description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'}) or \
                   soup.find('meta', property='og:description')
        return meta_desc['content'].strip() if meta_desc and meta_desc.get('content') else ""
