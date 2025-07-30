import requests
import logging
import re
from typing import Dict, Any, Optional, List
import json

logger = logging.getLogger(__name__)

class FinancialEnrichmentService:
    """
    Service to enrich company data with financial information
    Uses multiple sources to find revenue, market cap, and other financial metrics
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def enrich_companies_with_financial_data(self, companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich a list of companies with financial data
        
        Args:
            companies: List of company dictionaries
            
        Returns:
            List of companies enriched with financial data
        """
        enriched_companies = []
        
        for company in companies:
            try:
                # Extract company name from title or name field
                company_name = self._extract_company_name(company)
                
                # Get financial data
                financial_data = self._get_financial_data(company_name, company.get('snippet', ''))
                
                # Add financial data to company
                enriched_company = company.copy()
                enriched_company.update(financial_data)
                
                enriched_companies.append(enriched_company)
                
            except Exception as e:
                logger.warning(f"Failed to enrich {company.get('name', 'Unknown')}: {str(e)}")
                enriched_companies.append(company)
        
        return enriched_companies
    
    def _extract_company_name(self, company: Dict[str, Any]) -> str:
        """Extract clean company name from various fields"""
        # Try different fields
        name = company.get('name') or company.get('title', '')
        
        # Clean up the name
        name = re.sub(r'\s*\([^)]*\)', '', name)  # Remove parentheses
        name = re.sub(r'\s*-.*$', '', name)       # Remove everything after dash
        name = re.sub(r'\s*\|.*$', '', name)      # Remove everything after pipe
        name = name.strip()
        
        # Extract first few words if it's a long title
        words = name.split()
        if len(words) > 3:
            name = ' '.join(words[:3])
        
        return name
    
    def _get_financial_data(self, company_name: str, snippet: str) -> Dict[str, Any]:
        """
        Get financial data for a company using multiple strategies
        
        Args:
            company_name: Clean company name
            snippet: Company description/snippet
            
        Returns:
            Dictionary with financial data
        """
        financial_data = {
            'revenue': None,
            'market_cap': None,
            'employees': None,
            'industry': None,
            'financial_source': 'estimated'
        }
        
        try:
            # Strategy 1: Extract from snippet
            snippet_data = self._extract_from_snippet(snippet)
            financial_data.update(snippet_data)
            
            # Strategy 2: Use known company patterns
            pattern_data = self._get_from_patterns(company_name)
            if pattern_data:
                financial_data.update(pattern_data)
            
            # Strategy 3: Industry-based estimation
            industry_data = self._estimate_by_industry(company_name, snippet)
            if not financial_data['revenue'] and industry_data:
                financial_data.update(industry_data)
                
        except Exception as e:
            logger.warning(f"Error getting financial data for {company_name}: {str(e)}")
        
        return financial_data
    
    def _extract_from_snippet(self, snippet: str) -> Dict[str, Any]:
        """Extract financial data from company snippet/description"""
        data = {}
        
        # Revenue patterns
        revenue_patterns = [
            r'\$(\d+(?:\.\d+)?)\s*billion',
            r'\$(\d+(?:\.\d+)?)\s*B',
            r'revenue.*?\$(\d+(?:\.\d+)?)\s*billion',
            r'sales.*?\$(\d+(?:\.\d+)?)\s*billion'
        ]
        
        for pattern in revenue_patterns:
            match = re.search(pattern, snippet, re.IGNORECASE)
            if match:
                revenue_billions = float(match.group(1))
                data['revenue'] = f"${revenue_billions:.1f}B"
                break
        
        # Market cap patterns
        market_cap_patterns = [
            r'market cap.*?\$(\d+(?:\.\d+)?)\s*billion',
            r'valued at.*?\$(\d+(?:\.\d+)?)\s*billion',
            r'worth.*?\$(\d+(?:\.\d+)?)\s*billion'
        ]
        
        for pattern in market_cap_patterns:
            match = re.search(pattern, snippet, re.IGNORECASE)
            if match:
                cap_billions = float(match.group(1))
                data['market_cap'] = f"${cap_billions:.1f}B"
                break
        
        # Employee patterns
        employee_patterns = [
            r'(\d+,?\d*)\s*employees',
            r'workforce of (\d+,?\d*)',
            r'employs (\d+,?\d*)'
        ]
        
        for pattern in employee_patterns:
            match = re.search(pattern, snippet, re.IGNORECASE)
            if match:
                employees = match.group(1).replace(',', '')
                data['employees'] = f"{int(employees):,}"
                break
        
        return data
    
    def _get_from_patterns(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Get financial data based on known company patterns"""
        
        # Known major companies with approximate data
        known_companies = {
            'nvidia': {'revenue': '$60.9B', 'market_cap': '$1.8T', 'industry': 'Semiconductors'},
            'rivian': {'revenue': '$4.4B', 'market_cap': '$15.2B', 'industry': 'Electric Vehicles'},
            'lucid': {'revenue': '$0.6B', 'market_cap': '$8.1B', 'industry': 'Electric Vehicles'},
            'nio': {'revenue': '$7.0B', 'market_cap': '$9.8B', 'industry': 'Electric Vehicles'},
            'byd': {'revenue': '$70.2B', 'market_cap': '$95.4B', 'industry': 'Electric Vehicles'},
            'ford': {'revenue': '$176.2B', 'market_cap': '$48.5B', 'industry': 'Automotive'},
            'gm': {'revenue': '$171.8B', 'market_cap': '$54.2B', 'industry': 'Automotive'},
            'volkswagen': {'revenue': '$279.2B', 'market_cap': '$58.9B', 'industry': 'Automotive'},
            'toyota': {'revenue': '$274.5B', 'market_cap': '$245.1B', 'industry': 'Automotive'},
        }
        
        company_lower = company_name.lower()
        for key, data in known_companies.items():
            if key in company_lower or company_lower in key:
                return data
        
        return None
    
    def _estimate_by_industry(self, company_name: str, snippet: str) -> Optional[Dict[str, Any]]:
        """Estimate financial data based on industry and company indicators"""
        
        # Industry patterns and typical ranges
        industry_patterns = {
            'electric vehicle': {
                'industry': 'Electric Vehicles',
                'revenue_range': (0.5, 15.0),  # Billions
                'market_cap_multiplier': 3.0
            },
            'automotive': {
                'industry': 'Automotive',
                'revenue_range': (10.0, 200.0),
                'market_cap_multiplier': 0.8
            },
            'semiconductor': {
                'industry': 'Semiconductors',
                'revenue_range': (1.0, 80.0),
                'market_cap_multiplier': 8.0
            },
            'software': {
                'industry': 'Software',
                'revenue_range': (0.1, 50.0),
                'market_cap_multiplier': 12.0
            }
        }
        
        text = f"{company_name} {snippet}".lower()
        
        for pattern, data in industry_patterns.items():
            if pattern in text:
                # Estimate based on company size indicators
                if 'startup' in text or 'founded 20' in text:
                    revenue = data['revenue_range'][0]
                elif 'billion' in text or 'major' in text or 'leading' in text:
                    revenue = data['revenue_range'][1] * 0.7
                else:
                    revenue = sum(data['revenue_range']) / 2
                
                market_cap = revenue * data['market_cap_multiplier']
                
                return {
                    'revenue': f"${revenue:.1f}B",
                    'market_cap': f"${market_cap:.1f}B",
                    'industry': data['industry'],
                    'financial_source': 'estimated'
                }
        
        return None
