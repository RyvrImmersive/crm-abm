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

router = APIRouter(prefix="/hubspot", tags=["hubspot"])

# Initialize logger
logger = logging.getLogger(__name__)

# Set up more detailed logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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

def get_hubspot_api_key():
    """Get the HubSpot API key from environment variables."""
    api_key = os.getenv("HUBSPOT_API_KEY")
    if not api_key:
        logger.error("HUBSPOT_API_KEY not set in environment variables")
        raise HTTPException(status_code=500, detail="HUBSPOT_API_KEY not set in environment variables")
    
    logger.info("HubSpot API key retrieved successfully")
    return api_key

def get_clay_integration():
    """Get the Clay integration instance."""
    api_key = get_hubspot_api_key()
    return ClayIntegrationNode(hubspot_api_key=api_key)

@router.get("/companies")
async def get_companies(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    api_key: str = Depends(get_hubspot_api_key)
):
    """Get a list of companies from HubSpot."""
    try:
        logger.info(f"Fetching companies from HubSpot with limit={limit}, offset={offset}")
        url = "https://api.hubapi.com/crm/v3/objects/companies"
        params = {
            "limit": limit,
            "offset": offset,
            "properties": "name,domain,industry,numberofemployees,description,linkedin_company_page,relationship_status,clay_score,last_clay_update,website,phone,address,city,state,country"
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        logger.debug(f"Making request to HubSpot API: {url}")
        
        response = requests.get(url, params=params, headers=headers)
        
        # Log the response status and headers for debugging
        logger.debug(f"HubSpot API response status: {response.status_code}")
        logger.debug(f"HubSpot API response headers: {response.headers}")
        
        # Check if the response contains an error message
        if response.status_code != 200:
            error_detail = "Unknown error"
            try:
                error_data = response.json()
                if 'message' in error_data:
                    error_detail = error_data['message']
                elif 'detail' in error_data:
                    error_detail = error_data['detail']
                logger.error(f"HubSpot API error: {error_detail}")
            except Exception as e:
                logger.error(f"HubSpot API returned non-JSON error response: {response.text}")
                logger.error(f"Exception parsing error response: {str(e)}")
            
            # Log basic error information
            logger.error(f"HubSpot API request failed - Status: {response.status_code}")
            
            raise HTTPException(status_code=response.status_code, 
                              detail=f"HubSpot API error: {error_detail}")
        
        # Process successful response
        data = response.json()
        logger.info(f"Successfully retrieved {len(data.get('results', []))} companies from HubSpot")
        
        # Return the raw response data directly
        # This is what worked before our changes
        return data
        
    except requests.RequestException as e:
        logger.error(f"Error fetching companies from HubSpot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching companies from HubSpot: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in get_companies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/companies/{company_id}", response_model=HubSpotCompany)
async def get_company(
    company_id: str,
    api_key: str = Depends(get_hubspot_api_key)
):
    """Get a specific company from HubSpot by ID."""
    try:
        url = f"https://api.hubapi.com/crm/v3/objects/companies/{company_id}"
        params = {
            "properties": "name,domain,industry,numberofemployees,description,linkedin_company_page"
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching company from HubSpot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching company from HubSpot: {str(e)}")

@router.get("/companies/search", response_model=HubSpotCompanyResponse)
async def search_companies(
    query: str = Query(..., min_length=1),
    api_key: str = Depends(get_hubspot_api_key)
):
    """Search for companies in HubSpot."""
    try:
        url = f"https://api.hubapi.com/crm/v3/objects/companies/search"
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
            "properties": ["name", "domain", "industry", "numberofemployees", "description", "linkedin_company_page", "relationship_status", "clay_score", "last_clay_update", "website", "phone", "address", "city", "state", "country"],
            "limit": 50
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
