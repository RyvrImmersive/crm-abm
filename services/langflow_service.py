import requests
import logging
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)

class LangflowService:
    """Service class for Langflow API operations"""
    
    def __init__(self, api_key: str, flow_url: str):
        """
        Initialize Langflow service
        
        Args:
            api_key: Langflow API key
            flow_url: Complete URL for the Langflow API endpoint
        """
        self.api_key = api_key
        self.flow_url = flow_url
        
        # Request headers
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key
        }
    
    def trigger_research(self, company_name: str, domain_name: str, use_fallback: bool = True) -> Dict[str, Any]:
        """
        Trigger company research flow in Langflow
        
        Args:
            company_name: Name of the company to research
            domain_name: Domain name of the company
            
        Returns:
            Dictionary with success status and response data
        """
        try:
            # Prepare payload for the research flow
            # Updated format to match your Langflow flow's expected inputs
            payload = {
                "output_type": "text",
                "input_type": "text", 
                "input_value": company_name,
                "tweaks": {
                    "CompanyResearch-company_name": {
                        "company_name": company_name
                    },
                    "CompanyResearch-domain_name": {
                        "domain_name": domain_name
                    }
                }
            }
            
            logger.info(f"Triggering Langflow research for {company_name} - {domain_name}")
            
            # Retry mechanism for API calls with exponential backoff
            max_retries = 2  # Reduced retries to fail faster for unknown companies
            base_retry_delay = 10  # Base delay in seconds
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Attempt {attempt + 1}/{max_retries} for {company_name}")
                    
                    # Make API request with longer timeout
                    response = requests.post(
                        self.flow_url,
                        json=payload,
                        headers=self.headers,
                        timeout=60  # 1 minute timeout for research flows
                    )
                    
                    # If successful, break out of retry loop
                    response.raise_for_status()
                    break
                    
                except requests.exceptions.Timeout:
                    retry_delay = base_retry_delay * (2 ** attempt)  # Exponential backoff
                    if attempt < max_retries - 1:
                        logger.warning(f"Timeout on attempt {attempt + 1}, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        error_msg = f"Langflow API timed out after {max_retries} attempts for {company_name}"
                        logger.error(error_msg)
                        return {
                            "success": False,
                            "error": error_msg,
                            "error_type": "timeout_exhausted",
                            "suggestion": "The Langflow API is overloaded. Please try again in a few minutes."
                        }
                        
                except requests.exceptions.RequestException as e:
                    retry_delay = base_retry_delay * (2 ** attempt)  # Exponential backoff
                    should_retry = (
                        attempt < max_retries - 1 and 
                        (not hasattr(e, 'response') or 
                         (e.response and e.response.status_code >= 500) or
                         (e.response and e.response.status_code == 429))  # Rate limiting
                    )
                    
                    if should_retry:
                        status_code = e.response.status_code if hasattr(e, 'response') and e.response else 'N/A'
                        logger.warning(f"API error (status: {status_code}) on attempt {attempt + 1}, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise
            
            # Check response status
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            logger.info(f"Langflow research triggered successfully for {company_name}")
            
            return {
                "success": True,
                "response": response_data,
                "status_code": response.status_code,
                "company_name": company_name,
                "domain_name": domain_name
            }
            
        except requests.exceptions.Timeout:
            error_msg = f"Langflow API request timed out for {company_name}"
            logger.error(error_msg)
            
            if use_fallback:
                logger.info(f"Using fallback data for {company_name} due to API timeout")
                return self._generate_fallback_response(company_name, domain_name, "timeout")
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "timeout"
            }
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"Langflow API HTTP error for {company_name}: {e.response.status_code}"
            logger.error(f"{error_msg} - Response: {e.response.text}")
            return {
                "success": False,
                "error": error_msg,
                "error_type": "http_error",
                "status_code": e.response.status_code,
                "response_text": e.response.text
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Langflow API request error for {company_name}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_type": "request_error"
            }
            
        except ValueError as e:
            error_msg = f"Failed to parse Langflow response for {company_name}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_type": "parse_error"
            }
            
        except Exception as e:
            error_msg = f"Unexpected error in Langflow request for {company_name}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }
    
    def get_flow_status(self, flow_id: str = None) -> Dict[str, Any]:
        """
        Get status of a Langflow flow (if supported by your Langflow instance)
        
        Args:
            flow_id: Optional flow ID to check status for
            
        Returns:
            Dictionary with flow status information
        """
        try:
            # This would depend on your Langflow setup
            # For now, return a basic status
            return {
                "success": True,
                "status": "available",
                "flow_url": self.flow_url
            }
            
        except Exception as e:
            logger.error(f"Error getting flow status: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status": "unknown"
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Langflow API
        
        Returns:
            Dictionary with connection test results
        """
        try:
            # Simple test payload
            test_payload = {
                "output_type": "text",
                "input_type": "text",
                "input_value": "test connection"
            }
            
            response = requests.post(
                self.flow_url,
                json=test_payload,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "status": "connected",
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {
                    "success": False,
                    "status": "connection_failed",
                    "status_code": response.status_code,
                    "error": response.text
                }
                
        except Exception as e:
            return {
                "success": False,
                "status": "connection_error",
                "error": str(e)
            }
    
    def trigger_contact_research(self, company_name: str, domain_name: str) -> Dict[str, Any]:
        """
        Trigger contact research flow (for future implementation)
        
        Args:
            company_name: Name of the company
            domain_name: Domain name of the company
            
        Returns:
            Dictionary with success status and response data
        """
        # Placeholder for future contact research functionality
        return {
            "success": False,
            "error": "Contact research not yet implemented",
            "feature": "coming_soon"
        }
    
    def trigger_lookalike_search(self, company_name: str, domain_name: str, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger look-alike company search (for future implementation)
        
        Args:
            company_name: Name of the reference company
            domain_name: Domain name of the reference company
            criteria: Search criteria for finding similar companies
            
        Returns:
            Dictionary with success status and response data
        """
        # Placeholder for future look-alike search functionality
        return {
            "success": False,
            "error": "Look-alike search not yet implemented",
            "feature": "coming_soon"
        }
    
    def _generate_fallback_response(self, company_name: str, domain_name: str, reason: str) -> Dict[str, Any]:
        """
        Generate fallback response when Langflow API is unavailable
        
        Args:
            company_name: Name of the company
            domain_name: Domain name of the company
            reason: Reason for fallback (timeout, error, etc.)
            
        Returns:
            Dictionary with fallback response that triggers mock data storage
        """
        from datetime import datetime
        import uuid
        
        # Generate realistic mock data based on company name
        mock_data = self._generate_mock_company_data(company_name, domain_name)
        
        return {
            "success": True,
            "fallback": True,
            "fallback_reason": reason,
            "response": {
                "message": f"Generated mock data for {company_name} due to API unavailability",
                "data": mock_data,
                "timestamp": datetime.now().isoformat(),
                "source": "fallback_generator"
            },
            "status_code": 200,
            "company_name": company_name,
            "domain_name": domain_name,
            "note": "This is mock data generated due to Langflow API unavailability. Real data will be available when the API is restored."
        }
    
    def _generate_mock_company_data(self, company_name: str, domain_name: str) -> Dict[str, Any]:
        """
        Generate realistic mock company data
        
        Args:
            company_name: Name of the company
            domain_name: Domain name of the company
            
        Returns:
            Dictionary with mock company data
        """
        import random
        from datetime import datetime
        
        # Generate realistic data based on company name patterns
        industries = ["Technology", "Healthcare", "Finance", "Manufacturing", "Retail", "Consulting"]
        
        # Simple heuristics based on company name
        if any(tech_word in company_name.lower() for tech_word in ['tech', 'soft', 'data', 'ai', 'digital']):
            industry = "Technology"
        elif any(health_word in company_name.lower() for health_word in ['health', 'medical', 'pharma', 'bio']):
            industry = "Healthcare"
        elif any(fin_word in company_name.lower() for fin_word in ['bank', 'finance', 'capital', 'invest']):
            industry = "Finance"
        else:
            industry = random.choice(industries)
        
        # Generate revenue based on company name hash for consistency
        name_hash = hash(company_name) % 1000
        revenue_base = (name_hash % 50) + 10  # 10-60B range
        revenue = f"{revenue_base}.{random.randint(1, 9)}B"
        
        employees = random.choice(["1K-5K", "5K-10K", "10K-50K", "50K+"])
        
        cities = ["San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX", "Boston, MA", "Chicago, IL"]
        headquarters = random.choice(cities)
        
        return {
            "company_name": f"{company_name} - {domain_name}",
            "industry": industry,
            "revenue": revenue,
            "employees": employees,
            "headquarters": headquarters,
            "domain_name": domain_name,
            "timestamp": datetime.now().isoformat(),
            "data_source": "fallback_mock",
            "status": "success",
            "company_info": {
                "name": company_name,
                "domain": domain_name,
                "description": f"Mock data for {company_name} - a {industry.lower()} company"
            },
            "note": "This is mock data generated due to API unavailability"
        }
