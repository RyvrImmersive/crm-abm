"""
API endpoints for Clay.com integration
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import os
from ..components.clay_integration import ClayIntegrationNode

logger = logging.getLogger(__name__)

# Initialize Clay integration
clay_integration = ClayIntegrationNode(
    clay_api_key=os.getenv("CLAY_API_KEY", ""),
    hubspot_api_key=os.getenv("HUBSPOT_ACCESS_TOKEN", ""),
    base_url=os.getenv("CLAY_API_BASE_URL", "https://api.clay.com/v1")
)

router = APIRouter(
    prefix="/clay",
    tags=["clay"],
    responses={404: {"description": "Not found"}},
)

class CompanyDomain(BaseModel):
    domain: str

class CompanyDomainList(BaseModel):
    domains: List[str]
    force_update: bool = False

class ClayWebhookPayload(BaseModel):
    event_type: str
    company: Dict[str, Any]
    data: Dict[str, Any]

@router.post("/process-company")
async def process_company(company: CompanyDomain, background_tasks: BackgroundTasks):
    """Process a single company from Clay and update HubSpot"""
    try:
        # Run in background to avoid blocking the response
        background_tasks.add_task(clay_integration.run, company.domain)
        
        return {
            "status": "success",
            "message": f"Processing company {company.domain} in background",
            "domain": company.domain,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error processing company: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-companies")
async def process_companies(payload: CompanyDomainList, background_tasks: BackgroundTasks):
    """Process multiple companies from Clay and update HubSpot"""
    try:
        # Process each company in the background
        for domain in payload.domains:
            background_tasks.add_task(clay_integration.run, domain)
        
        return {
            "status": "success",
            "message": f"Processing {len(payload.domains)} companies in background",
            "domains": payload.domains,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error processing companies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def clay_webhook(payload: ClayWebhookPayload, background_tasks: BackgroundTasks):
    """Handle webhooks from Clay"""
    try:
        # Extract domain from the company data
        domain = payload.company.get("domain")
        
        if not domain:
            return {
                "status": "error",
                "message": "No domain provided in webhook payload",
                "timestamp": datetime.now().isoformat()
            }
        
        # Process the company in the background
        background_tasks.add_task(clay_integration.run, domain)
        
        return {
            "status": "success",
            "message": f"Processing webhook for {domain}",
            "event_type": payload.event_type,
            "domain": domain,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error processing Clay webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/company-news/{domain}")
async def get_company_news(domain: str):
    """Get recent news for a company from Clay"""
    try:
        news = clay_integration.get_company_news(domain)
        
        return {
            "status": "success",
            "domain": domain,
            "news_count": len(news),
            "news": news,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting company news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/company-jobs/{domain}")
async def get_company_jobs(domain: str):
    """Get recent job postings for a company from Clay"""
    try:
        jobs = clay_integration.get_company_jobs(domain)
        
        return {
            "status": "success",
            "domain": domain,
            "jobs_count": len(jobs),
            "jobs": jobs,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting company jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/company-funding/{domain}")
async def get_company_funding(domain: str):
    """Get funding information for a company from Clay"""
    try:
        funding = clay_integration.get_company_funding(domain)
        
        return {
            "status": "success",
            "domain": domain,
            "funding_rounds": len(funding),
            "funding": funding,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting company funding: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/company-profile/{domain}")
async def get_company_profile(domain: str):
    """Get company profile information from Clay"""
    try:
        profile = clay_integration.get_company_profile(domain)
        
        return {
            "status": "success",
            "domain": domain,
            "profile": profile,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting company profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync-to-hubspot/{domain}")
async def sync_to_hubspot(domain: str, background_tasks: BackgroundTasks):
    """Sync company data from Clay to HubSpot"""
    try:
        # Process the company in the background
        background_tasks.add_task(clay_integration.run, domain)
        
        return {
            "status": "success",
            "message": f"Syncing data for {domain} from Clay to HubSpot",
            "domain": domain,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error syncing to HubSpot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
