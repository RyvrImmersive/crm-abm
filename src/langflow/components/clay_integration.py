"""
Clay.com integration component for monitoring company changes and updating HubSpot
"""
from typing import Dict, Any, List, Optional
from ..node.types import PythonNode
import requests
import logging
from datetime import datetime
import json
import os
from hubspot import HubSpot

logger = logging.getLogger(__name__)

class ClayIntegrationNode(PythonNode):
    """Node that integrates with Clay.com to monitor company changes"""
    
    def __init__(self, 
                 clay_api_key: str,
                 hubspot_api_key: str,
                 base_url: str = "https://api.clay.com/v1"):
        super().__init__(
            name="ClayIntegrationNode",
            description="""
            Integrates with Clay.com to monitor company changes like news, jobs, funding, etc.
            Updates HubSpot with the latest information.
            """,
            inputs=["company_domain"],
            outputs=["result"]
        )
        self.clay_api_key = clay_api_key
        self.hubspot_api_key = hubspot_api_key
        self.base_url = base_url
        self.hubspot_client = HubSpot(access_token=hubspot_api_key)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Clay API requests"""
        return {
            "Authorization": f"Bearer {self.clay_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def get_company_news(self, domain: str) -> List[Dict[str, Any]]:
        """Get recent news for a company from Clay"""
        try:
            endpoint = f"{self.base_url}/companies/news"
            params = {
                "domain": domain,
                "limit": 10
            }
            
            logger.info(f"Requesting news from Clay API: {endpoint} for domain {domain}")
            
            response = requests.get(
                endpoint,
                headers=self._get_headers(),
                params=params
            )
            
            # Check for 404 specifically
            if response.status_code == 404:
                logger.warning(f"No news found for domain {domain} in Clay API")
                return []
                
            # For other errors, raise the exception
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Retrieved {len(data.get('news', []))} news items for {domain}")
            return data.get("news", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error getting news for {domain}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error getting news for {domain}: {str(e)}")
            return []
    
    def get_company_jobs(self, domain: str) -> List[Dict[str, Any]]:
        """Get recent job postings for a company from Clay"""
        try:
            endpoint = f"{self.base_url}/companies/jobs"
            params = {
                "domain": domain,
                "limit": 20
            }
            
            logger.info(f"Requesting jobs from Clay API: {endpoint} for domain {domain}")
            
            response = requests.get(
                endpoint,
                headers=self._get_headers(),
                params=params
            )
            
            # Check for 404 specifically
            if response.status_code == 404:
                logger.warning(f"No jobs found for domain {domain} in Clay API")
                return []
                
            # For other errors, raise the exception
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Retrieved {len(data.get('jobs', []))} job postings for {domain}")
            return data.get("jobs", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error getting jobs for {domain}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error getting jobs for {domain}: {str(e)}")
            return []
    
    def get_company_funding(self, domain: str) -> List[Dict[str, Any]]:
        """Get funding information for a company from Clay"""
        try:
            endpoint = f"{self.base_url}/companies/funding"
            params = {
                "domain": domain
            }
            
            logger.info(f"Requesting funding from Clay API: {endpoint} for domain {domain}")
            
            response = requests.get(
                endpoint,
                headers=self._get_headers(),
                params=params
            )
            
            # Check for 404 specifically
            if response.status_code == 404:
                logger.warning(f"No funding found for domain {domain} in Clay API")
                return []
                
            # For other errors, raise the exception
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Retrieved {len(data.get('funding_rounds', []))} funding rounds for {domain}")
            return data.get("funding_rounds", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error getting funding for {domain}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error getting funding for {domain}: {str(e)}")
            return []
    
    def get_company_profile(self, domain: str) -> Dict[str, Any]:
        """Get company profile information from Clay"""
        try:
            endpoint = f"{self.base_url}/companies/profile"
            params = {
                "domain": domain
            }
            
            logger.info(f"Requesting company profile from Clay API: {endpoint} for domain {domain}")
            
            response = requests.get(
                endpoint,
                headers=self._get_headers(),
                params=params
            )
            
            # Check for 404 specifically
            if response.status_code == 404:
                logger.warning(f"No company profile found for domain {domain} in Clay API")
                return {}
                
            # For other errors, raise the exception
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Retrieved company profile for {domain}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error getting company profile for {domain}: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Error getting company profile for {domain}: {str(e)}")
            return {}
    
    def find_hubspot_company(self, domain: str) -> Optional[Dict[str, Any]]:
        """Find a company in HubSpot by domain"""
        try:
            # Search for the company by domain
            filter_dict = {"propertyName": "domain", "operator": "EQ", "value": domain}
            
            company_search = self.hubspot_client.crm.companies.search_api.do_search(
                {"filterGroups": [{"filters": [filter_dict]}]}
            )
            
            if company_search.results and len(company_search.results) > 0:
                logger.info(f"Found company in HubSpot with domain {domain}")
                return company_search.results[0].to_dict()
            else:
                logger.warning(f"No company found in HubSpot with domain {domain}")
                return None
        except Exception as e:
            logger.error(f"Error finding company in HubSpot: {str(e)}")
            return None
    
    def get_hubspot_company_properties(self) -> List[str]:
        """Get all available company properties in HubSpot"""
        try:
            # Get all company properties
            properties_page = self.hubspot_client.crm.properties.core_api.get_all(object_type="companies")
            property_names = [prop.name for prop in properties_page.results]
            logger.info(f"Retrieved {len(property_names)} company properties from HubSpot")
            return property_names
        except Exception as e:
            logger.error(f"Error getting company properties from HubSpot: {str(e)}")
            # Return a list of common properties that are likely to exist
            return ["name", "domain", "industry", "description", "hubspot_score", "abm_score"]
    
    def update_hubspot_company(self, company_id: str, properties: Dict[str, Any]) -> bool:
        """Update a company in HubSpot with new properties"""
        try:
            from hubspot.crm.companies import SimplePublicObjectInput
            
            # Get available HubSpot properties
            available_properties = self.get_hubspot_company_properties()
            
            # Filter properties to only include those that exist in HubSpot
            filtered_properties = {}
            for key, value in properties.items():
                if key in available_properties:
                    filtered_properties[key] = value
                else:
                    logger.warning(f"Property '{key}' does not exist in HubSpot and will be skipped")
            
            # If no valid properties, return early
            if not filtered_properties:
                logger.warning(f"No valid properties to update for company {company_id}")
                return False
            
            logger.info(f"Updating company {company_id} with properties: {filtered_properties}")
            
            # Create the SimplePublicObjectInput required by the HubSpot API
            properties_input = SimplePublicObjectInput(properties=filtered_properties)
            
            # Update the company properties
            self.hubspot_client.crm.companies.basic_api.update(
                company_id,
                simple_public_object_input=properties_input
            )
            
            logger.info(f"Successfully updated company {company_id} in HubSpot")
            return True
        except Exception as e:
            logger.error(f"Error updating company in HubSpot: {str(e)}")
            return False
    
    def process_company_data(self, domain: str) -> Dict[str, Any]:
        """Process company data from Clay and update HubSpot"""
        try:
            # Get data from Clay
            news = self.get_company_news(domain)
            jobs = self.get_company_jobs(domain)
            funding = self.get_company_funding(domain)
            profile = self.get_company_profile(domain)
            
            # Find the company in HubSpot
            hubspot_company = self.find_hubspot_company(domain)
            
            if not hubspot_company:
                return {
                    "status": "error",
                    "message": f"Company with domain {domain} not found in HubSpot",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Prepare properties to update in HubSpot
            properties = {}
            
            # Process news
            if news:
                latest_news = news[0]
                properties["recent_news_title"] = latest_news.get("title", "")[:255]  # HubSpot has character limits
                properties["recent_news_url"] = latest_news.get("url", "")
                properties["recent_news_date"] = latest_news.get("published_date", "")
                properties["has_recent_news"] = "true"
            else:
                properties["has_recent_news"] = "false"
            
            # Process jobs
            if jobs:
                properties["job_count"] = str(len(jobs))
                properties["has_open_jobs"] = "true"
                properties["recent_job_title"] = jobs[0].get("title", "")[:255]
                properties["hiring"] = "true"
            else:
                properties["has_open_jobs"] = "false"
                properties["hiring"] = "false"
            
            # Process funding
            if funding:
                latest_funding = funding[0]
                properties["recent_funding_amount"] = str(latest_funding.get("amount", 0))
                properties["recent_funding_date"] = latest_funding.get("date", "")
                properties["recent_funding_round"] = latest_funding.get("round_type", "")
                properties["funding"] = "true"
                
                # Calculate total funding
                total_funding = sum(round.get("amount", 0) for round in funding)
                properties["total_funding"] = str(total_funding)
            else:
                properties["funding"] = "false"
            
            # Process profile data
            if profile:
                if "employee_count" in profile:
                    properties["numberofemployees"] = str(profile.get("employee_count", 0))
                if "industry" in profile:
                    properties["industry"] = profile.get("industry", "")
                if "description" in profile:
                    properties["description"] = profile.get("description", "")[:1000]  # HubSpot has character limits
                if "year_founded" in profile:
                    properties["year_founded"] = str(profile.get("year_founded", ""))
                if "linkedin_url" in profile:
                    properties["linkedin_company_page"] = profile.get("linkedin_url", "")
                if "twitter_url" in profile:
                    properties["twitterhandle"] = profile.get("twitter_url", "")
            
            # Add metadata
            properties["last_clay_update"] = datetime.now().isoformat()
            
            # Update the company in HubSpot
            success = self.update_hubspot_company(hubspot_company["id"], properties)
            
            if success:
                return {
                    "status": "success",
                    "message": f"Updated company {hubspot_company['id']} with data from Clay",
                    "company_id": hubspot_company["id"],
                    "domain": domain,
                    "data_summary": {
                        "news_count": len(news),
                        "jobs_count": len(jobs),
                        "funding_rounds": len(funding),
                        "has_profile": bool(profile)
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to update company {hubspot_company['id']} in HubSpot",
                    "company_id": hubspot_company["id"],
                    "domain": domain,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error processing company data: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing company data: {str(e)}",
                "domain": domain,
                "timestamp": datetime.now().isoformat()
            }
    
    def run(self, company_domain: str) -> Dict[str, Any]:
        """Run the Clay integration for a company domain"""
        try:
            logger.info(f"Processing company with domain: {company_domain}")
            
            # Process the company data
            result = self.process_company_data(company_domain)
            
            return result
        except Exception as e:
            logger.error(f"Error in Clay integration: {str(e)}")
            return {
                "status": "error",
                "message": f"Error in Clay integration: {str(e)}",
                "domain": company_domain,
                "timestamp": datetime.now().isoformat()
            }
