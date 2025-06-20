from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field, HttpUrl
import logging
import aiohttp
from bs4 import BeautifulSoup
import asyncio
from urllib.parse import urlparse, urljoin
import re
from dataclasses import dataclass

from .base_agent import BaseAgent, AgentInput, AgentOutput
from config.settings import settings

logger = logging.getLogger(__name__)

class URLAnalysisInput(AgentInput):
    """Input model for URL analysis agent"""
    url: HttpUrl = Field(..., description="URL to analyze")
    target_keywords: List[str] = Field(default_factory=list, description="Target keywords for optimization")
    analyze_competitors: bool = Field(False, description="Whether to analyze top competitors")

@dataclass
class ContentAnalysis:
    """Content analysis results"""
    word_count: int = 0
    keyword_density: Dict[str, float] = None  # {keyword: density}
    headings: Dict[str, List[str]] = None  # {h1: [], h2: [], ...}
    images: List[Dict[str, str]] = None  # [{"src": "...", "alt": "..."}]
    internal_links: List[str] = None
    external_links: List[str] = None

class URLMetrics(BaseModel):
    """URL metrics and analysis"""
    status_code: Optional[int] = None
    load_time: Optional[float] = None  # in seconds
    page_size: Optional[int] = None  # in bytes
    title: Optional[str] = None
    meta_description: Optional[str] = None
    canonical_url: Optional[str] = None
    content_analysis: Optional[ContentAnalysis] = None
    seo_issues: List[str] = Field(default_factory=list)
    optimization_opportunities: List[str] = Field(default_factory=list)

class URLAnalysisOutput(AgentOutput):
    """Output model for URL analysis agent"""
    url: str
    metrics: URLMetrics
    keyword_analysis: Dict[str, Any] = Field(default_factory=dict)
    competitor_analysis: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True

class URLAnalysisAgent(BaseAgent):
    """Agent for analyzing and optimizing URLs for SEO"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.session = None
    
    async def _execute_impl(self, input_data: URLAnalysisInput) -> URLAnalysisOutput:
        """Execute URL analysis"""
        self.session = aiohttp.ClientSession()
        try:
            # Step 1: Fetch and analyze the URL
            html_content, response_metrics = await self._fetch_url(str(input_data.url))
            
            # Step 2: Parse and analyze the HTML content
            soup = BeautifulSoup(html_content, 'lxml')
            content_analysis = self._analyze_content(soup, input_data.url)
            
            # Step 3: Check for SEO issues
            seo_issues = self._check_seo_issues(soup, content_analysis)
            
            # Step 4: Generate optimization opportunities
            optimization_ops = self._generate_optimization_opportunities(
                soup, content_analysis, input_data.target_keywords
            )
            
            # Step 5: (Optional) Analyze competitors
            competitor_analysis = {}
            if input_data.analyze_competitors:
                competitor_analysis = await self._analyze_competitors(
                    str(input_data.url), input_data.target_keywords
                )
            
            # Compile metrics
            metrics = URLMetrics(
                status_code=response_metrics.get('status'),
                load_time=response_metrics.get('load_time'),
                page_size=response_metrics.get('size'),
                title=self._get_page_title(soup),
                meta_description=self._get_meta_description(soup),
                canonical_url=self._get_canonical_url(soup, str(input_data.url)),
                content_analysis=content_analysis,
                seo_issues=seo_issues,
                optimization_opportunities=optimization_ops
            )
            
            return URLAnalysisOutput(
                success=True,
                url=str(input_data.url),
                metrics=metrics,
                keyword_analysis=await self._analyze_keywords(
                    soup, input_data.target_keywords
                ),
                competitor_analysis=competitor_analysis
            )
            
        except Exception as e:
            logger.error(f"Error analyzing URL {input_data.url}: {str(e)}", exc_info=True)
            return URLAnalysisOutput(
                success=False,
                url=str(input_data.url),
                error=str(e),
                metrics=URLMetrics()
            )
        finally:
            if self.session:
                await self.session.close()
    
    async def _fetch_url(self, url: str) -> Tuple[str, Dict[str, Any]]:
        """Fetch URL and return HTML content with metrics"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with self.session.get(url, timeout=30) as response:
                content = await response.text()
                end_time = asyncio.get_event_loop().time()
                
                return content, {
                    'status': response.status,
                    'load_time': end_time - start_time,
                    'size': len(content.encode('utf-8')),
                    'content_type': response.content_type
                }
        except asyncio.TimeoutError:
            raise Exception(f"Timeout while fetching URL: {url}")
        except Exception as e:
            raise Exception(f"Error fetching URL {url}: {str(e)}")
    
    def _analyze_content(self, soup: BeautifulSoup, base_url: str) -> ContentAnalysis:
        """Analyze page content and extract SEO-relevant information"""
        analysis = ContentAnalysis(
            headings={"h1": [], "h2": [], "h3": [], "h4": [], "h5": [], "h6": []},
            images=[],
            internal_links=[],
            external_links=[]
        )
        
        # Count words in main content (excluding nav, footer, etc.)
        main_content = soup.find('main') or soup.find('article') or soup.body or soup
        if main_content:
            text = main_content.get_text()
            analysis.word_count = len(re.findall(r'\w+', text))
        
        # Extract headings
        for level in range(1, 7):
            tag = f'h{level}'
            analysis.headings[tag] = [h.get_text().strip() for h in main_content.find_all(tag)]
        
        # Analyze images
        for img in main_content.find_all('img', src=True):
            analysis.images.append({
                'src': urljoin(base_url, img['src']),
                'alt': img.get('alt', '').strip(),
                'title': img.get('title', '').strip()
            })
        
        # Analyze links
        base_domain = urlparse(base_url).netloc
        for a in main_content.find_all('a', href=True):
            href = a['href']
            if not href or href.startswith('#'):
                continue
                
            full_url = urljoin(base_url, href)
            parsed_url = urlparse(full_url)
            
            if not parsed_url.netloc:  # Relative URL
                analysis.internal_links.append(full_url)
            elif parsed_url.netloc == base_domain:  # Same domain
                analysis.internal_links.append(full_url)
            else:  # External domain
                analysis.external_links.append(full_url)
        
        return analysis
    
    def _check_seo_issues(self, soup: BeautifulSoup, content: ContentAnalysis) -> List[str]:
        """Check for common SEO issues"""
        issues = []
        
        # Check title
        title = self._get_page_title(soup)
        if not title:
            issues.append("Missing <title> tag")
        elif len(title) > 60:
            issues.append(f"Title is too long ({len(title)} characters). Recommended max is 60.")
        
        # Check meta description
        meta_desc = self._get_meta_description(soup)
        if not meta_desc:
            issues.append("Missing meta description")
        elif len(meta_desc) > 160:
            issues.append(f"Meta description is too long ({len(meta_desc)} characters). Recommended max is 160.")
        
        # Check headings
        if not content.headings['h1']:
            issues.append("No H1 heading found")
        elif len(content.headings['h1']) > 1:
            issues.append("Multiple H1 headings found. Recommended to have only one H1 per page.")
        
        # Check images
        for img in content.images:
            if not img['alt']:
                issues.append(f"Image missing alt text: {img['src']}")
        
        # Check word count
        if content.word_count < 300:
            issues.append(f"Low word count ({content.word_count}). Consider adding more content for better SEO.")
        
        return issues
    
    async def _analyze_keywords(self, soup: BeautifulSoup, target_keywords: List[str]) -> Dict[str, Any]:
        """Analyze keywords on the page"""
        if not target_keywords:
            return {}
            
        text = ' '.join([soup.get_text()])
        text_lower = text.lower()
        
        keyword_analysis = {}
        for keyword in target_keywords:
            kw_lower = keyword.lower()
            count = text_lower.count(kw_lower)
            keyword_analysis[keyword] = {
                'count': count,
                'in_title': kw_lower in (soup.title.text.lower() if soup.title else ''),
                'in_h1': any(kw_lower in h1.lower() for h1 in [h.get_text() for h in soup.find_all('h1')]),
                'in_url': kw_lower in soup.find('meta', {'property': 'og:url', 'content': True})['content'].lower() if soup.find('meta', {'property': 'og:url'}) else False
            }
        
        return keyword_analysis
    
    async def _analyze_competitors(self, url: str, keywords: List[str]) -> Dict[str, Any]:
        """Analyze top competitors for the given URL and keywords"""
        # TODO: Implement competitor analysis using SERP API or similar
        return {"message": "Competitor analysis not implemented yet"}
    
    def _generate_optimization_opportunities(
        self, 
        soup: BeautifulSoup, 
        content: ContentAnalysis,
        target_keywords: List[str]
    ) -> List[str]:
        """Generate optimization opportunities based on analysis"""
        opportunities = []
        
        # Title optimization
        title = self._get_page_title(soup)
        if title and target_keywords and not any(kw.lower() in title.lower() for kw in target_keywords):
            opportunities.append("Include target keywords in the page title")
        
        # Meta description optimization
        meta_desc = self._get_meta_description(soup)
        if meta_desc and target_keywords and not any(kw.lower() in meta_desc.lower() for kw in target_keywords):
            opportunities.append("Include target keywords in the meta description")
        
        # Header optimization
        for kw in target_keywords:
            kw_lower = kw.lower()
            in_headers = any(
                kw_lower in h.lower() 
                for header_list in content.headings.values() 
                for h in header_list
            )
            if not in_headers:
                opportunities.append(f"Consider using the keyword '{kw}' in one of your headings")
        
        # Internal linking
        if len(content.internal_links) < 5:
            opportunities.append("Add more internal links to improve site structure and SEO")
        
        # External links
        if not content.external_links:
            opportunities.append("Consider adding relevant outbound links to authoritative sources")
        
        # Image optimization
        for img in content.images:
            if not img['alt']:
                opportunities.append(f"Add descriptive alt text to image: {img['src']}")
        
        # Content length
        if content.word_count < 1000:
            opportunities.append("Consider expanding the content with more detailed information")
        
        return opportunities
    
    @staticmethod
    def _get_page_title(soup: BeautifulSoup) -> str:
        """Extract page title"""
        if soup.title:
            return soup.title.text.strip()
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()
        return ""
    
    @staticmethod
    def _get_meta_description(soup: BeautifulSoup) -> str:
        """Extract meta description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'}) or \
                   soup.find('meta', property='og:description')
        return meta_desc['content'].strip() if meta_desc and meta_desc.get('content') else ""
    
    @staticmethod
    def _get_canonical_url(soup: BeautifulSoup, current_url: str) -> str:
        """Extract canonical URL"""
        canonical = soup.find('link', rel='canonical')
        if canonical and canonical.get('href'):
            return urljoin(current_url, canonical['href'])
        return current_url
