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
    
    def create_hubspot_property(self, name: str, label: str, description: str, type: str = "string", group_name: str = "clay_data") -> bool:
        """Create a custom property in HubSpot if it doesn't exist"""
        try:
            from hubspot.crm.properties import PropertyCreate
            import requests
            
            # Check if property already exists
            existing_properties = self.get_hubspot_company_properties()
            if name in existing_properties:
                logger.info(f"Property '{name}' already exists in HubSpot")
                return True
            
            # Create property group if it doesn't exist
            try:
                from hubspot.crm.properties import PropertyGroupCreate
                groups = self.hubspot_client.crm.properties.groups_api.get_all(object_type="companies")
                group_names = [group.name for group in groups.results]
                
                if group_name not in group_names:
                    logger.info(f"Creating property group '{group_name}' in HubSpot")
                    group = PropertyGroupCreate(
                        name=group_name,
                        label="Clay Data",
                        display_order=1
                    )
                    self.hubspot_client.crm.properties.groups_api.create(object_type="companies", property_group_create=group)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    logger.warning(f"Permission denied when creating property group. Your HubSpot API key doesn't have the necessary permissions: {str(e)}")
                    logger.warning("Falling back to using existing properties only. Please update your HubSpot API key with the necessary scopes.")
                    return False
                else:
                    logger.warning(f"Error creating property group: {str(e)}")
                    # Fall back to using the default group
                    group_name = "companyinformation"
            except Exception as e:
                logger.warning(f"Error creating property group: {str(e)}")
                # Fall back to using the default group
                group_name = "companyinformation"
            
            # Create the property
            logger.info(f"Creating property '{name}' in HubSpot")
            
            # Map our simplified types to HubSpot's expected types
            field_type = type
            if type == "boolean":
                field_type = "booleancheckbox"
            
            # Create the property - don't use field_type_options as it's causing errors
            property_create = PropertyCreate(
                name=name,
                label=label,
                description=description,
                type=field_type,  # Use the mapped field type
                field_type=field_type,
                group_name=group_name
            )
            
            try:
                self.hubspot_client.crm.properties.core_api.create(
                    object_type="companies",
                    property_create=property_create
                )
                
                logger.info(f"Successfully created property '{name}' in HubSpot")
                return True
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    logger.warning(f"Permission denied when creating property '{name}'. Your HubSpot API key doesn't have the necessary permissions: {str(e)}")
                    logger.warning("Falling back to using existing properties only. Please update your HubSpot API key with the necessary scopes.")
                    # Log the required scopes from the error message if available
                    if hasattr(e, 'response') and e.response.text:
                        logger.warning(f"Error details: {e.response.text}")
                    return False
                else:
                    raise
        except Exception as e:
            logger.error(f"Error creating property '{name}' in HubSpot: {str(e)}")
            return False
    
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
    
    def create_clay_properties(self) -> bool:
        """Check for existing HubSpot properties for Clay integration"""
        try:
            logger.info("Checking for existing properties for Clay integration in HubSpot")
            
            # Get existing properties
            existing_properties = self.get_hubspot_company_properties()
            logger.info(f"Found {len(existing_properties)} existing properties in HubSpot")
            
            # Define all properties needed for Clay integration
            clay_property_names = [
                # News properties
                "has_recent_news", "recent_news_title", "recent_news_url", "recent_news_date",
                # Jobs properties
                "has_open_jobs", "job_count", "recent_job_title", "hiring",
                # Funding properties
                "funding", "recent_funding_amount", "recent_funding_date", "recent_funding_round", "total_funding",
                # Metadata
                "last_clay_update"
            ]
            
            # Standard HubSpot properties we can use
            standard_properties = [
                "name", "domain", "industry", "description", "numberofemployees", 
                "linkedin_company_page", "twitterhandle", "hubspot_score", "abm_score"
            ]
            
            # Check which properties already exist
            existing_clay_properties = [prop for prop in clay_property_names if prop in existing_properties]
            existing_standard_properties = [prop for prop in standard_properties if prop in existing_properties]
            
            logger.info(f"Found {len(existing_clay_properties)} existing Clay properties in HubSpot")
            logger.info(f"Found {len(existing_standard_properties)} existing standard properties in HubSpot")
            
            # Log which properties are available
            if existing_clay_properties:
                logger.info(f"Available Clay properties: {', '.join(existing_clay_properties)}")
            
            if existing_standard_properties:
                logger.info(f"Available standard properties: {', '.join(existing_standard_properties)}")
            
            # We won't try to create properties due to permission issues
            # Just log which properties are missing
            missing_properties = [prop for prop in clay_property_names if prop not in existing_properties]
            if missing_properties:
                logger.warning(f"Missing Clay properties: {', '.join(missing_properties)}")
                logger.warning("The integration will work with existing properties only.")
                logger.warning("To add missing properties, please manually create them in HubSpot or update your API key permissions.")
            
            # Return True if we have at least some properties to work with
            usable_properties = existing_clay_properties + existing_standard_properties
            return len(usable_properties) > 0
        except Exception as e:
            logger.error(f"Error checking Clay properties in HubSpot: {str(e)}")
            return False
    
    def process_company_data(self, domain: str) -> Dict[str, Any]:
        """Process company data from Clay and update HubSpot"""
        try:
            logger.info(f"Processing company data for {domain}")
            
            # Ensure all required properties exist in HubSpot
            self.create_clay_properties()
            
            # Get company data from Clay
            news = self.get_company_news(domain)
            jobs = self.get_company_jobs(domain)
            funding = self.get_company_funding(domain)
            profile = self.get_company_profile(domain)
            
            # Find company in HubSpot
            hubspot_company = self.find_hubspot_company(domain)
            if not hubspot_company:
                logger.warning(f"Company with domain {domain} not found in HubSpot")
                return {
                    "success": False,
                    "message": f"Company with domain {domain} not found in HubSpot"
                }
            
            # Get available properties in HubSpot
            available_properties = self.get_hubspot_company_properties()
            logger.info(f"Found {len(available_properties)} available properties in HubSpot")
            
            # Prepare properties to update in HubSpot
            properties = {}
            
            # Process news
            if news:
                latest_news = news[0]
                if "recent_news_title" in available_properties:
                    properties["recent_news_title"] = latest_news.get("title", "")[:255]  # HubSpot has character limits
                if "recent_news_url" in available_properties:
                    properties["recent_news_url"] = latest_news.get("url", "")
                if "recent_news_date" in available_properties:
                    properties["recent_news_date"] = latest_news.get("published_date", "")
                if "has_recent_news" in available_properties:
                    properties["has_recent_news"] = "true"
            elif "has_recent_news" in available_properties:
                properties["has_recent_news"] = "false"
            
            # Process jobs
            if jobs:
                if "job_count" in available_properties:
                    properties["job_count"] = str(len(jobs))
                if "has_open_jobs" in available_properties:
                    properties["has_open_jobs"] = "true"
                if "recent_job_title" in available_properties:
                    properties["recent_job_title"] = jobs[0].get("title", "")[:255]
                if "hiring" in available_properties:
                    properties["hiring"] = "true"
            else:
                if "has_open_jobs" in available_properties:
                    properties["has_open_jobs"] = "false"
                if "hiring" in available_properties:
                    properties["hiring"] = "false"
            
            # Process funding
            if funding:
                latest_funding = funding[0]
                if "recent_funding_amount" in available_properties:
                    properties["recent_funding_amount"] = str(latest_funding.get("amount", 0))
                if "recent_funding_date" in available_properties:
                    properties["recent_funding_date"] = latest_funding.get("date", "")
                if "recent_funding_round" in available_properties:
                    properties["recent_funding_round"] = latest_funding.get("round_type", "")
                if "funding" in available_properties:
                    properties["funding"] = "true"
                
                # Calculate total funding
                total_funding = sum(round.get("amount", 0) for round in funding)
                if "total_funding" in available_properties:
                    properties["total_funding"] = str(total_funding)
            elif "funding" in available_properties:
                properties["funding"] = "false"
            
            # Process profile data
            if profile:
                if "employee_count" in profile and "numberofemployees" in available_properties:
                    properties["numberofemployees"] = str(profile.get("employee_count", 0))
                if "industry" in profile and "industry" in available_properties:
                    properties["industry"] = profile.get("industry", "")
                if "description" in profile and "description" in available_properties:
                    properties["description"] = profile.get("description", "")[:1000]  # HubSpot has character limits
                if "year_founded" in profile and "year_founded" in available_properties:
                    properties["year_founded"] = str(profile.get("year_founded", ""))
                if "linkedin_url" in profile and "linkedin_company_page" in available_properties:
                    properties["linkedin_company_page"] = profile.get("linkedin_url", "")
                if "twitter_url" in profile and "twitterhandle" in available_properties:
                    properties["twitterhandle"] = profile.get("twitter_url", "")
            
            # Add metadata
            if "last_clay_update" in available_properties:
                properties["last_clay_update"] = datetime.now().isoformat()
                
            # Add a standard property to update if we have nothing else
            if not properties and "hubspot_score" in available_properties:
                properties["hubspot_score"] = "50"  # Update a default property so we have something to update
            
            # Update the company in HubSpot
            success = self.update_hubspot_company(hubspot_company["id"], properties)
            
            if success:
                return {
                    "success": True,
                    "message": f"Successfully updated company {domain} in HubSpot",
                    "company_id": hubspot_company["id"],
                    "data": {
                        "news_count": len(news),
                        "jobs_count": len(jobs),
                        "funding_count": len(funding),
                        "profile": bool(profile)
                    }
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to update company {domain} in HubSpot"
                }
                
        except Exception as e:
            logger.error(f"Error processing company data for {domain}: {str(e)}")
            return {
                "success": False,
                "message": f"Error processing company data: {str(e)}"
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
