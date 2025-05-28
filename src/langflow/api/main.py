from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
from src.langflow.flows.abm_crm_flow import ABMCRMFlow
from src.langflow.utils.cache import CacheManager
import logging
import os

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ABM CRM API",
    description="API for ABM CRM system with HubSpot integration and scoring",
    version="1.0.0"
)

# Initialize flow with environment variables
flow = ABMCRMFlow(
    hubspot_access_token=os.getenv("HUBSPOT_ACCESS_TOKEN"),
    astra_db_id=os.getenv("ASTRA_DB_ID"),
    astra_db_region=os.getenv("ASTRA_DB_REGION"),
    astra_db_token=os.getenv("ASTRA_DB_TOKEN")
)

class WebhookPayload(BaseModel):
    event_type: str
    data: Dict[str, Any]

class CacheStats(BaseModel):
    hubspot: Dict[str, Any]
    scoring: Dict[str, Any]
    prompt: Dict[str, Any]

class FlowStatus(BaseModel):
    nodes: Dict[str, Any]
    connections: List[Dict[str, str]]
    cache_stats: CacheStats

@app.post("/hubspot-webhook")
async def handle_hubspot_webhook(payload: WebhookPayload):
    """Handle incoming HubSpot webhook events"""
    try:
        # First, update entity type if provided
        if payload.event_type:
            # Extract entity type from event type (e.g., "company.created" -> "company")
            if "." in payload.event_type:
                entity_type = payload.event_type.split(".")[0]
            else:
                entity_type = payload.event_type
                
            # Make sure data has the correct type
            if "type" not in payload.data:
                payload.data["type"] = entity_type
        
        # Process the webhook data through the flow
        result = flow.process_webhook(payload.data)
        
        return result
        
    except Exception as e:
        # Log the error
        logging.error(f"Webhook error: {str(e)}")
        
        # Create simple error context
        error_context = {
            'endpoint': '/hubspot-webhook',
            'event_type': payload.event_type,
            'error_type': e.__class__.__name__,
            'timestamp': datetime.now().isoformat()
        }
        
        # Return error response
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "context": error_context
            }
        )

@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    return CacheStats(
        hubspot=flow.cache_manager.get_cache_stats()['hubspot'],
        scoring=flow.cache_manager.get_cache_stats()['scoring'],
        prompt=flow.cache_manager.get_cache_stats()['prompt']
    )

@app.post("/cache/clear")
async def clear_cache(cache_type: Optional[str] = None):
    """Clear cache (all or specific type)"""
    try:
        if cache_type:
            flow.cache_manager.clear_cache(cache_type)
        else:
            flow.cache_manager.clear_cache()
        
        return {"status": "success", "cache_type": cache_type}
        
    except Exception as e:
        # Log the error
        logger.error(f"Cache clear error: {str(e)}")
        
        # Create simple error context
        error_context = {
            'endpoint': '/cache/clear',
            'cache_type': cache_type,
            'error_type': e.__class__.__name__,
            'timestamp': datetime.now().isoformat()
        }
        
        # Return error response
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "context": error_context
            }
        )

@app.get("/flow/status")
async def get_flow_status():
    """Get current flow status and cache stats"""
    try:
        flow_status = flow.get_flow_status()
        return FlowStatus(
            nodes=flow_status['nodes'],
            connections=flow_status['connections'],
            cache_stats=CacheStats(
                hubspot=flow.cache_manager.get_cache_stats()['hubspot'],
                scoring=flow.cache_manager.get_cache_stats()['scoring'],
                prompt=flow.cache_manager.get_cache_stats()['prompt']
            )
        )
        
    except Exception as e:
        # Log the error
        logger.error(f"Flow status error: {str(e)}")
        
        # Create simple error context
        error_context = {
            'endpoint': '/flow/status',
            'error_type': e.__class__.__name__,
            'timestamp': datetime.now().isoformat()
        }
        
        # Return error response
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "context": error_context
            }
        )

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "ABM CRM API",
        "version": "1.0.0",
        "description": "API for ABM CRM system with HubSpot integration and scoring",
        "endpoints": [
            {
                "path": "/",
                "method": "GET",
                "description": "This information"
            },
            {
                "path": "/health",
                "method": "GET",
                "description": "Health check endpoint"
            },
            {
                "path": "/hubspot-webhook",
                "method": "POST",
                "description": "Handle incoming HubSpot webhook events"
            },
            {
                "path": "/cache/stats",
                "method": "GET",
                "description": "Get cache statistics"
            },
            {
                "path": "/cache/clear",
                "method": "POST",
                "description": "Clear cache (all or specific type)"
            },
            {
                "path": "/flow/status",
                "method": "GET",
                "description": "Get current flow status and cache stats"
            }
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
