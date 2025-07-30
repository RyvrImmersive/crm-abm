#!/usr/bin/env python3
"""
Look-alike Companies Service
Integrates with Exa and Tavily APIs to find similar companies based on growth patterns,
industry characteristics, and business models.
"""

import os
import requests
import logging
import time
from typing import Dict, Any, List, Optional
from .financial_enrichment_service import FinancialEnrichmentService
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LookalikeService:
    """Service for finding look-alike companies using Exa and Tavily APIs"""
    
    def __init__(self, exa_api_key: Optional[str] = None, tavily_api_key: Optional[str] = None):
        """
        Initialize the LookalikeService
        
        Args:
            exa_api_key: Exa API key for web search
            tavily_api_key: Tavily API key for research
        """
        self.exa_api_key = exa_api_key or os.getenv('EXA_API_KEY')
        self.tavily_api_key = tavily_api_key or os.getenv('TAVILY_API_KEY')
        
        self.exa_base_url = "https://api.exa.ai"
        self.tavily_base_url = "https://api.tavily.com"
        
        # API endpoints
        self.exa_search_url = f"{self.exa_base_url}/search"
        self.tavily_search_url = f"{self.tavily_base_url}/search"
        
        # Initialize financial enrichment service
        self.financial_service = FinancialEnrichmentService()
    
    def find_lookalike_companies(self, target_company: Dict[str, Any], 
                                num_results: int = 10) -> Dict[str, Any]:
        """
        Find companies similar to the target company
        
        Args:
            target_company: Dictionary containing target company data
            num_results: Number of similar companies to return
            
        Returns:
            Dictionary with lookalike companies and analysis
        """
        try:
            # Extract key characteristics from target company
            characteristics = self._extract_company_characteristics(target_company)
            
            # Search for similar companies using both APIs
            exa_results = self._search_with_exa(characteristics, num_results // 2)
            tavily_results = self._search_with_tavily(characteristics, num_results // 2)
            
            # Combine and rank results
            combined_results = self._combine_and_rank_results(
                exa_results, tavily_results, characteristics
            )
            
            # Analyze similarity patterns
            similarity_analysis = self._analyze_similarity_patterns(
                target_company, combined_results
            )
            
            # Enrich companies with financial data
            logger.info(f"Enriching {len(combined_results[:num_results])} companies with financial data")
            enriched_companies = self.financial_service.enrich_companies_with_financial_data(
                combined_results[:num_results]
            )
            
            return {
                "target_company": {
                    "name": target_company.get('metadata', {}).get('company_name', 'Unknown'),
                    "industry": target_company.get('metadata', {}).get('company_info', {}).get('industry', 'Unknown'),
                    "characteristics": characteristics
                },
                "lookalike_companies": enriched_companies,
                "similarity_analysis": similarity_analysis,
                "search_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "exa_results_count": len(exa_results),
                    "tavily_results_count": len(tavily_results),
                    "total_candidates": len(combined_results)
                }
            }
            
        except Exception as e:
            logger.error(f"Error finding lookalike companies: {str(e)}")
            return {
                "target_company": {"name": "Unknown", "industry": "Unknown"},
                "lookalike_companies": [],
                "similarity_analysis": {"error": str(e)},
                "search_metadata": {"error": str(e)}
            }
    
    def _extract_company_characteristics(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key characteristics from company data for similarity matching
        
        Args:
            company_data: Company data dictionary
            
        Returns:
            Dictionary of key characteristics
        """
        metadata = company_data.get('metadata', {})
        company_info = metadata.get('company_info', {})
        financial_data = metadata.get('financial_data', {})
        hiring_data = metadata.get('hiring_data', {})
        
        # Extract industry and business model indicators
        industry = company_info.get('industry', '').lower()
        description = company_info.get('description', '').lower()
        
        # Extract financial scale
        revenue = financial_data.get('revenue', '')
        revenue_scale = self._categorize_revenue_scale(revenue)
        
        # Extract growth indicators
        hiring_status = hiring_data.get('hiring_status', '').lower()
        expansion_plans = hiring_data.get('expansion_plans', '').lower()
        
        # Extract technology/business model keywords
        tech_keywords = self._extract_tech_keywords(industry, description)
        
        return {
            "industry": industry,
            "revenue_scale": revenue_scale,
            "tech_keywords": tech_keywords,
            "growth_stage": self._determine_growth_stage(hiring_status, expansion_plans, revenue_scale),
            "business_model": self._infer_business_model(industry, description),
            "company_size": self._categorize_company_size(financial_data, company_info)
        }
    
    def _search_with_exa(self, characteristics: Dict[str, Any], num_results: int) -> List[Dict[str, Any]]:
        """
        Search for similar companies using Exa API
        
        Args:
            characteristics: Company characteristics for matching
            num_results: Number of results to return
            
        Returns:
            List of similar companies from Exa
        """
        if not self.exa_api_key:
            logger.warning("Exa API key not available, skipping Exa search")
            return []
        
        try:
            # Build search query based on characteristics
            query = self._build_exa_search_query(characteristics)
            
            headers = {
                "Authorization": f"Bearer {self.exa_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "query": query,
                "num_results": num_results,
                "include_domains": ["crunchbase.com", "linkedin.com", "bloomberg.com", "reuters.com", "finance.yahoo.com", "sec.gov"],
                "start_crawl_date": "2023-01-01",
                "end_crawl_date": "2024-12-31",
                "type": "keyword",
                "contents": {
                    "text": True
                }
            }
            
            response = requests.post(self.exa_search_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                results = response.json().get('results', [])
                return self._process_exa_results(results, characteristics)
            else:
                logger.error(f"Exa API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching with Exa: {str(e)}")
            return []
    
    def _search_with_tavily(self, characteristics: Dict[str, Any], num_results: int) -> List[Dict[str, Any]]:
        """
        Search for similar companies using Tavily API
        
        Args:
            characteristics: Company characteristics for matching
            num_results: Number of results to return
            
        Returns:
            List of similar companies from Tavily
        """
        if not self.tavily_api_key:
            logger.warning("Tavily API key not available, skipping Tavily search")
            return []
        
        try:
            # Build search query based on characteristics
            query = self._build_tavily_search_query(characteristics)
            
            payload = {
                "api_key": self.tavily_api_key,
                "query": query,
                "search_depth": "advanced",
                "max_results": num_results,
                "include_domains": ["crunchbase.com", "pitchbook.com", "techcrunch.com", "forbes.com"],
                "exclude_domains": ["wikipedia.org"]
            }
            
            response = requests.post(self.tavily_search_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                results = response.json().get('results', [])
                return self._process_tavily_results(results, characteristics)
            else:
                logger.error(f"Tavily API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching with Tavily: {str(e)}")
            return []
    
    def _build_exa_search_query(self, characteristics: Dict[str, Any]) -> str:
        """Build optimized search query for Exa API"""
        industry = characteristics.get('industry', '')
        tech_keywords = characteristics.get('tech_keywords', [])
        business_model = characteristics.get('business_model', '')
        revenue_scale = characteristics.get('revenue_scale', '')
        
        query_parts = []
        
        if industry:
            query_parts.append(f"{industry} companies")
        
        if tech_keywords:
            query_parts.append(" ".join(tech_keywords[:3]))  # Top 3 keywords
        
        if business_model:
            query_parts.append(business_model)
        
        if revenue_scale in ['large', 'enterprise']:
            query_parts.append("billion revenue")
        elif revenue_scale == 'medium':
            query_parts.append("million revenue")
        
        query_parts.append("similar companies competitors")
        
        return " ".join(query_parts)
    
    def _build_tavily_search_query(self, characteristics: Dict[str, Any]) -> str:
        """Build optimized search query for Tavily API"""
        industry = characteristics.get('industry', '')
        growth_stage = characteristics.get('growth_stage', '')
        company_size = characteristics.get('company_size', '')
        
        query_parts = []
        
        if industry:
            query_parts.append(f"{industry} industry")
        
        if growth_stage:
            query_parts.append(f"{growth_stage} companies")
        
        if company_size:
            query_parts.append(f"{company_size} companies")
        
        query_parts.extend(["competitors", "similar companies", "market leaders"])
        
        return " ".join(query_parts)
    
    def _process_exa_results(self, results: List[Dict], characteristics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process and score Exa search results"""
        processed = []
        
        for result in results:
            company_name = self._extract_company_name_from_result(result)
            if company_name:
                similarity_score = self._calculate_similarity_score(result, characteristics)
                
                processed.append({
                    "name": company_name,
                    "url": result.get('url', ''),
                    "title": result.get('title', ''),
                    "snippet": result.get('text', '')[:200] + "...",
                    "similarity_score": similarity_score,
                    "source": "exa",
                    "published_date": result.get('publishedDate', ''),
                    "domain": result.get('url', '').split('/')[2] if result.get('url') else ''
                })
        
        return sorted(processed, key=lambda x: x['similarity_score'], reverse=True)
    
    def _process_tavily_results(self, results: List[Dict], characteristics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process and score Tavily search results"""
        processed = []
        
        for result in results:
            company_name = self._extract_company_name_from_result(result)
            if company_name:
                similarity_score = self._calculate_similarity_score(result, characteristics)
                
                processed.append({
                    "name": company_name,
                    "url": result.get('url', ''),
                    "title": result.get('title', ''),
                    "snippet": result.get('content', '')[:200] + "...",
                    "similarity_score": similarity_score,
                    "source": "tavily",
                    "published_date": result.get('published_date', ''),
                    "domain": result.get('url', '').split('/')[2] if result.get('url') else ''
                })
        
        return sorted(processed, key=lambda x: x['similarity_score'], reverse=True)
    
    def _extract_company_name_from_result(self, result: Dict) -> Optional[str]:
        """Extract company name from search result"""
        title = result.get('title', '')
        url = result.get('url', '')
        
        # Try to extract company name from title
        if title:
            # Remove common suffixes and prefixes
            cleaned_title = title.replace(' - Crunchbase', '').replace(' | LinkedIn', '')
            cleaned_title = cleaned_title.replace(' - Company Profile', '').replace(' Inc.', '')
            
            # Take first part before common separators
            for separator in [' -', ' |', ' (', ' Company']:
                if separator in cleaned_title:
                    cleaned_title = cleaned_title.split(separator)[0]
                    break
            
            return cleaned_title.strip()
        
        return None
    
    def _calculate_similarity_score(self, result: Dict, characteristics: Dict[str, Any]) -> float:
        """Calculate similarity score for a search result"""
        score = 0.0
        text = (result.get('title', '') + ' ' + result.get('text', '') + ' ' + result.get('content', '')).lower()
        
        # Industry match
        industry = characteristics.get('industry', '')
        if industry and industry in text:
            score += 0.3
        
        # Technology keywords match
        tech_keywords = characteristics.get('tech_keywords', [])
        for keyword in tech_keywords:
            if keyword.lower() in text:
                score += 0.1
        
        # Business model match
        business_model = characteristics.get('business_model', '')
        if business_model and business_model in text:
            score += 0.2
        
        # Growth stage indicators
        growth_stage = characteristics.get('growth_stage', '')
        if growth_stage and growth_stage in text:
            score += 0.15
        
        # Revenue scale indicators
        revenue_scale = characteristics.get('revenue_scale', '')
        if revenue_scale == 'large' and any(word in text for word in ['billion', 'large', 'enterprise']):
            score += 0.1
        elif revenue_scale == 'medium' and any(word in text for word in ['million', 'medium', 'mid-size']):
            score += 0.1
        
        # Domain authority bonus
        domain = result.get('url', '').split('/')[2] if result.get('url') else ''
        if domain in ['crunchbase.com', 'linkedin.com', 'bloomberg.com', 'forbes.com']:
            score += 0.15
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _combine_and_rank_results(self, exa_results: List[Dict], tavily_results: List[Dict], 
                                 characteristics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Combine results from both APIs and remove duplicates"""
        combined = []
        seen_companies = set()
        
        # Combine results
        all_results = exa_results + tavily_results
        
        # Remove duplicates and rank by similarity score
        for result in sorted(all_results, key=lambda x: x['similarity_score'], reverse=True):
            company_name = result['name'].lower().strip()
            
            # Skip if we've already seen this company
            if company_name in seen_companies:
                continue
            
            seen_companies.add(company_name)
            combined.append(result)
        
        return combined
    
    def _analyze_similarity_patterns(self, target_company: Dict[str, Any], 
                                   lookalike_companies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in the lookalike companies"""
        if not lookalike_companies:
            return {"patterns": [], "insights": "No similar companies found"}
        
        # Analyze common domains
        domains = {}
        for company in lookalike_companies:
            domain = company.get('domain', '')
            domains[domain] = domains.get(domain, 0) + 1
        
        # Analyze similarity score distribution
        scores = [company['similarity_score'] for company in lookalike_companies]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Generate insights
        insights = []
        
        if avg_score > 0.6:
            insights.append("High-quality matches found with strong similarity indicators")
        elif avg_score > 0.4:
            insights.append("Moderate similarity matches found")
        else:
            insights.append("Limited similarity matches - consider broader search criteria")
        
        top_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)[:3]
        if top_domains:
            insights.append(f"Primary data sources: {', '.join([d[0] for d in top_domains])}")
        
        return {
            "average_similarity_score": avg_score,
            "total_matches": len(lookalike_companies),
            "top_data_sources": top_domains,
            "insights": insights
        }
    
    # Helper methods for characteristic extraction
    def _categorize_revenue_scale(self, revenue: str) -> str:
        """Categorize revenue scale"""
        if not revenue or revenue in ['N/A', 'Not found']:
            return 'unknown'
        
        revenue_lower = revenue.lower()
        if 'trillion' in revenue_lower:
            return 'enterprise'
        elif 'billion' in revenue_lower:
            return 'large'
        elif 'million' in revenue_lower:
            return 'medium'
        else:
            return 'small'
    
    def _extract_tech_keywords(self, industry: str, description: str) -> List[str]:
        """Extract technology-related keywords"""
        text = (industry + ' ' + description).lower()
        
        tech_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'cloud', 'saas', 'software',
            'fintech', 'blockchain', 'cryptocurrency', 'mobile', 'app', 'platform',
            'data', 'analytics', 'cybersecurity', 'iot', 'automation', 'robotics',
            'biotech', 'healthcare', 'medtech', 'cleantech', 'renewable', 'electric'
        ]
        
        found_keywords = []
        for keyword in tech_keywords:
            if keyword in text:
                found_keywords.append(keyword)
        
        return found_keywords[:5]  # Return top 5
    
    def _determine_growth_stage(self, hiring_status: str, expansion_plans: str, revenue_scale: str) -> str:
        """Determine company growth stage"""
        if 'actively hiring' in hiring_status and expansion_plans in ['yes', 'true', 'expanding']:
            return 'high-growth'
        elif 'hiring' in hiring_status:
            return 'growing'
        elif revenue_scale in ['large', 'enterprise']:
            return 'mature'
        else:
            return 'stable'
    
    def _infer_business_model(self, industry: str, description: str) -> str:
        """Infer business model from industry and description"""
        text = (industry + ' ' + description).lower()
        
        if any(word in text for word in ['saas', 'software', 'platform', 'subscription']):
            return 'saas'
        elif any(word in text for word in ['marketplace', 'platform', 'network']):
            return 'marketplace'
        elif any(word in text for word in ['manufacturing', 'hardware', 'device']):
            return 'hardware'
        elif any(word in text for word in ['service', 'consulting', 'agency']):
            return 'services'
        else:
            return 'traditional'
    
    def _categorize_company_size(self, financial_data: Dict, company_info: Dict) -> str:
        """Categorize company size"""
        employees = company_info.get('employees', '')
        revenue = financial_data.get('revenue', '')
        
        # Try to extract employee count
        if employees and employees not in ['N/A', 'Not specified']:
            try:
                emp_count = int(employees.replace(',', ''))
                if emp_count > 10000:
                    return 'enterprise'
                elif emp_count > 1000:
                    return 'large'
                elif emp_count > 100:
                    return 'medium'
                else:
                    return 'small'
            except:
                pass
        
        # Fallback to revenue
        revenue_scale = self._categorize_revenue_scale(revenue)
        if revenue_scale == 'enterprise':
            return 'enterprise'
        elif revenue_scale == 'large':
            return 'large'
        elif revenue_scale == 'medium':
            return 'medium'
        else:
            return 'small'
