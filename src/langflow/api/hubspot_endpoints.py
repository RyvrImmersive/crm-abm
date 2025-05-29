from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import requests
import os
import logging
from ..components.clay_integration import ClayIntegrationNode

router = APIRouter()

# Initialize logger
logger = logging.getLogger(__name__)

class HubSpotCompany(BaseModel):
    id: str
    properties: Dict[str, Any]
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class HubSpotCompanyResponse(BaseModel):
    results: List[HubSpotCompany]
    total: int
    offset: int

def get_hubspot_api_key():
    """Get the HubSpot API key from environment variables."""
    api_key = os.getenv("HUBSPOT_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="HUBSPOT_API_KEY not set in environment variables")
    return api_key

def get_clay_integration():
    """Get the Clay integration instance."""
    api_key = get_hubspot_api_key()
    return ClayIntegrationNode(hubspot_api_key=api_key)

@router.get("/companies", response_model=HubSpotCompanyResponse)
async def get_companies(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    api_key: str = Depends(get_hubspot_api_key)
):
    """Get a list of companies from HubSpot."""
    try:
        url = f"https://api.hubapi.com/crm/v3/objects/companies"
        params = {
            "limit": limit,
            "offset": offset,
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
        logger.error(f"Error fetching companies from HubSpot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching companies from HubSpot: {str(e)}")

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
            "properties": ["name", "domain", "industry", "numberofemployees", "description", "linkedin_company_page"],
            "limit": 20
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
