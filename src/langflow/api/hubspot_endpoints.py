from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import requests
import os
import logging
import json
from ..components.clay_integration import ClayIntegrationNode
from enum import Enum

# Define relationship status options
class RelationshipStatus(str, Enum):
    CURRENT_CUSTOMER = "Current Customer"
    SALES_PROSPECT = "Sales Prospect"
    MARKETING_PROSPECT = "Marketing Prospect"
    DO_NOT_CALL = "Do Not Call"
    CURRENT_OPPORTUNITY = "Current Opportunity"
    COMPETITION = "Competition"
    INFLUENCER = "Influencer"

router = APIRouter(tags=["hubspot"])

# Initialize logger
logger = logging.getLogger(__name__)

# Set up more detailed logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Function to get the HubSpot API key from environment variables
def get_hubspot_api_key():
    """Get the HubSpot API key from environment variables."""
    api_key = os.getenv("HUBSPOT_API_KEY")
    if not api_key:
        logger.error("HUBSPOT_API_KEY not set in environment variables")
        raise HTTPException(status_code=500, detail="HUBSPOT_API_KEY not set in environment variables")
    
    logger.info("HubSpot API key retrieved successfully")
    return api_key

# Add a simple test endpoint to verify the router is working
@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify the router is working."""
    return {"status": "ok", "message": "HubSpot endpoints are working"}

@router.get("/test-api-key")
async def test_api_key(api_key: str = Depends(get_hubspot_api_key)):
    """Test endpoint to verify the HubSpot API key is working."""
    try:
        # Make a simple API call to verify the key works
        url = "https://api.hubapi.com/crm/v3/properties/companies"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return {
                "status": "ok", 
                "message": "HubSpot API key is valid"
            }
        else:
            return {
                "status": "error", 
                "message": "HubSpot API key is not working",
                "status_code": response.status_code
            }
    except Exception as e:
        return {
            "status": "error", 
            "message": "Error testing HubSpot API key"
        }

class HubSpotCompany(BaseModel):
    id: str
    properties: Dict[str, Any]
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class HubSpotCompanyResponse(BaseModel):
    results: List[HubSpotCompany] = []
    total: int = 0
    offset: int = 0
    
    class Config:
        # Allow extra fields in the response
        extra = "allow"

def get_clay_integration():
    """Get the Clay integration instance."""
    api_key = get_hubspot_api_key()
    return ClayIntegrationNode(hubspot_api_key=api_key)

@router.get("/companies")
async def get_companies(
    limit: int = Query(100, ge=1, le=100),  # Default to maximum limit
    offset: int = Query(0, ge=0),
    api_key: str = Depends(get_hubspot_api_key)
):
    """Get a list of companies from HubSpot."""
    url = "https://api.hubapi.com/crm/v3/objects/companies"
    
    # Log the request with the API key (masked for security)
    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if api_key else "[NO KEY]"
    logger.info(f"Fetching companies from HubSpot with limit={limit}, offset={offset}, API Key: {masked_key}")
    
    try:
        # Log the full request URL and headers (without the actual API key)
        params = {
            "limit": limit,
            "offset": offset,
            "properties": ["name", "domain", "phone", "city", "state", "country", "industry"],
            "archived": "false"
        }
        logger.info(f"Request URL: {url}")
        logger.info(f"Request params: {params}")
        
        # Make the API request to HubSpot
        response = requests.get(
            url,
            params=params,
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        # Log the response status code and headers
        logger.info(f"HubSpot API response status code: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        # Check for errors
        response.raise_for_status()
        
        # Process successful response
        data = response.json()
        results = data.get('results', [])
        total = data.get('total', 0)
        
        logger.info(f"Successfully retrieved {len(results)} companies from HubSpot (total: {total})")
        
        # Log first few companies for debugging
        if results:
            logger.info(f"First company: {json.dumps(results[0], indent=2, default=str)}")
        
        # Return the raw response data directly without any modifications
        return data
        
    except requests.exceptions.HTTPError as http_err:
        error_msg = f"HTTP error occurred: {http_err}"
        if hasattr(http_err, 'response') and http_err.response is not None:
            error_msg += f"\nResponse status: {http_err.response.status_code}"
            try:
                error_data = http_err.response.json()
                error_msg += f"\nError details: {json.dumps(error_data, indent=2)}"
            except ValueError:
                error_msg += f"\nResponse text: {http_err.response.text}"
        logger.error(error_msg)
        return {"results": [], "total": 0, "offset": offset, "error": error_msg}
        
    except requests.RequestException as e:
        error_msg = f"Error fetching companies from HubSpot: {str(e)}"
        logger.error(error_msg)
        return {"results": [], "total": 0, "offset": offset, "error": error_msg}
    
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"results": [], "total": 0, "offset": offset, "error": error_msg}

@router.get("/companies/{company_id}")
async def get_company(
    company_id: str,
    api_key: str = Depends(get_hubspot_api_key)
):
    """Get a specific company from HubSpot by ID."""
    try:
        url = f"https://api.hubapi.com/crm/v3/objects/companies/{company_id}"
        params = {
            "properties": "name,domain,industry,numberofemployees,description,linkedin_company_page,relationship_status,clay_score,last_clay_update,website,phone,address,city,state,country"
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching company {company_id} from HubSpot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching company from HubSpot: {str(e)}")

@router.get("/companies/search")
async def search_companies(
    query: str = Query(..., min_length=1),
    api_key: str = Depends(get_hubspot_api_key)
):
    """Search for companies in HubSpot."""
    try:
        url = "https://api.hubapi.com/crm/v3/objects/companies/search"
        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "name",
                            "operator": "CONTAINS_TOKEN",
                            "value": query
                        }
                    ]
                }
            ],
            "properties": ["name", "domain", "industry", "relationship_status"],
            "limit": 10
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error searching companies in HubSpot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching companies in HubSpot: {str(e)}")

@router.get("/properties")
async def get_properties(
    api_key: str = Depends(get_hubspot_api_key)
):
    """Get all company properties from HubSpot."""
    try:
        url = f"https://api.hubapi.com/properties/v1/companies/properties"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching properties from HubSpot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching properties from HubSpot: {str(e)}")

@router.post("/properties/create-relationship-status")
async def create_relationship_status_property(
    api_key: str = Depends(get_hubspot_api_key)
):
    """Create a relationship status property in HubSpot if it doesn't exist."""
    try:
        # First check if the property already exists
        properties = await get_properties(api_key)
        
        # Check if relationship_status property already exists
        if any(prop.get('name') == 'relationship_status' for prop in properties):
            return {"status": "exists", "message": "Relationship status property already exists"}
        
        # Property doesn't exist, create it
        url = "https://api.hubapi.com/properties/v1/companies/properties"
        
        # Define the property
        property_data = {
            "name": "relationship_status",
            "label": "Relationship Status",
            "description": "The current relationship status with this company",
            "groupName": "companyinformation",
            "type": "enumeration",
            "fieldType": "select",
            "options": [
                {"label": status.value, "value": status.value, "displayOrder": i} 
                for i, status in enumerate(RelationshipStatus)
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=property_data, headers=headers)
        response.raise_for_status()
        
        return {"status": "created", "message": "Relationship status property created successfully"}
    except requests.RequestException as e:
        logger.error(f"Error creating relationship status property: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating relationship status property: {str(e)}")

class UpdateRelationshipStatusRequest(BaseModel):
    company_id: str
    status: RelationshipStatus

@router.post("/companies/update-relationship-status")
async def update_relationship_status(
    request: UpdateRelationshipStatusRequest,
    api_key: str = Depends(get_hubspot_api_key)
):
    """Update the relationship status for a company."""
    try:
        # Ensure the property exists
        await create_relationship_status_property(api_key)
        
        # Update the company property
        url = f"https://api.hubapi.com/crm/v3/objects/companies/{request.company_id}"
        
        payload = {
            "properties": {
                "relationship_status": request.status.value
            }
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.patch(url, json=payload, headers=headers)
        response.raise_for_status()
        
        return {"status": "updated", "message": f"Relationship status updated to {request.status.value}"}
    except requests.RequestException as e:
        logger.error(f"Error updating relationship status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating relationship status: {str(e)}")
