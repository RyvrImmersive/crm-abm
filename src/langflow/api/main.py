from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
from src.langflow.flows.abm_crm_flow import ABMCRMFlow
from src.langflow.utils.cache import CacheManager
from src.langflow.utils.scheduler import scheduler
from src.langflow.components.hubspot_updater import HubspotUpdaterNode
from src.langflow.api.clay_endpoints import router as clay_router
import logging
import os

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ABM CRM API",
    description="API for ABM CRM system with HubSpot integration and scoring",
    version="1.0.0"
)

# Include the Clay router
app.include_router(clay_router)

# Initialize flow with environment variables
flow = ABMCRMFlow(
    hubspot_access_token=os.getenv("HUBSPOT_ACCESS_TOKEN"),
    astra_db_id=os.getenv("ASTRA_DB_ID"),
    astra_db_region=os.getenv("ASTRA_DB_REGION"),
    astra_db_token=os.getenv("ASTRA_DB_TOKEN")
)

# Initialize HubSpot updater
hubspot_updater = HubspotUpdaterNode(
    access_token=os.getenv("HUBSPOT_ACCESS_TOKEN"),
    batch_size=25,
    max_entities=100
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

class ScheduleTask(BaseModel):
    interval_minutes: int
    entity_types: List[str] = ["company", "contact"]
    batch_size: Optional[int] = None
    max_entities: Optional[int] = None

class ScheduleStatus(BaseModel):
    task_id: str
    interval: int
    last_run: float
    last_run_formatted: str
    running: bool
    error_count: int

@app.post("/hubspot-webhook")
async def handle_hubspot_webhook(payload: WebhookPayload):
    """Handle incoming HubSpot webhook events"""
    try:
        # Create a copy of the data to avoid modifying the original
        data = dict(payload.data)
        
        # Extract entity type from event_type if provided
        if payload.event_type and "." in payload.event_type:
            entity_type = payload.event_type.split(".")[0]
        elif payload.event_type:
            entity_type = payload.event_type
        else:
            entity_type = "company"  # Default to company
            
        # Always set the type in the data
        data["type"] = entity_type
        
        logger.info(f"Processing webhook with entity_type: {entity_type}")
        
        # Process the webhook data through the flow
        result = flow.process_webhook(data)
        
        return result
        
    except Exception as e:
        # Log the error
        logger.error(f"Webhook error: {str(e)}")
        
        # Create simple error context
        error_context = {
            'endpoint': '/hubspot-webhook',
            'event_type': payload.event_type,
            'entity_type': entity_type if 'entity_type' in locals() else "unknown",
            'error_type': e.__class__.__name__,
            'timestamp': datetime.now().isoformat(),
            'payload_data': str(payload.data)[:100] + '...' if len(str(payload.data)) > 100 else str(payload.data)
        }
        
        # Return error response
        return {
            "status": "error",
            "message": str(e),
            "error_context": error_context
        }

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
            },
            {
                "path": "/scheduler/start",
                "method": "POST",
                "description": "Start the scheduler"
            },
            {
                "path": "/scheduler/stop",
                "method": "POST",
                "description": "Stop the scheduler"
            },
            {
                "path": "/scheduler/status",
                "method": "GET",
                "description": "Get scheduler status"
            },
            {
                "path": "/scheduler/hubspot-update",
                "method": "POST",
                "description": "Schedule HubSpot updates"
            },
            {
                "path": "/scheduler/hubspot-update",
                "method": "DELETE",
                "description": "Remove scheduled HubSpot updates"
            },
            {
                "path": "/hubspot/update-now",
                "method": "POST",
                "description": "Run HubSpot update immediately"
            },
            {
                "path": "/clay/process-company",
                "method": "POST",
                "description": "Process a single company from Clay and update HubSpot"
            },
            {
                "path": "/clay/process-companies",
                "method": "POST",
                "description": "Process multiple companies from Clay and update HubSpot"
            },
            {
                "path": "/clay/webhook",
                "method": "POST",
                "description": "Handle webhooks from Clay"
            },
            {
                "path": "/clay/company-news/{domain}",
                "method": "GET",
                "description": "Get recent news for a company from Clay"
            },
            {
                "path": "/clay/company-jobs/{domain}",
                "method": "GET",
                "description": "Get recent job postings for a company from Clay"
            },
            {
                "path": "/clay/company-funding/{domain}",
                "method": "GET",
                "description": "Get funding information for a company from Clay"
            },
            {
                "path": "/clay/company-profile/{domain}",
                "method": "GET",
                "description": "Get company profile information from Clay"
            },
            {
                "path": "/clay/sync-to-hubspot/{domain}",
                "method": "POST",
                "description": "Sync company data from Clay to HubSpot"
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

# Scheduler endpoints
@app.post("/scheduler/start")
async def start_scheduler():
    """Start the scheduler"""
    try:
        scheduler.start()
        return {"status": "success", "message": "Scheduler started"}
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the scheduler"""
    try:
        scheduler.stop()
        return {"status": "success", "message": "Scheduler stopped"}
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status"""
    try:
        tasks = scheduler.get_all_tasks()
        return {
            "status": "success",
            "running": scheduler.running,
            "tasks": tasks
        }
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scheduler/hubspot-update")
async def schedule_hubspot_update(task: ScheduleTask):
    """Schedule HubSpot updates"""
    try:
        # Convert minutes to seconds
        interval_seconds = task.interval_minutes * 60
        
        # Update batch size and max entities if provided
        if task.batch_size is not None:
            hubspot_updater.batch_size = task.batch_size
        
        if task.max_entities is not None:
            hubspot_updater.max_entities = task.max_entities
        
        # Define the task function
        def update_hubspot_task():
            logger.info("Running scheduled HubSpot update")
            result = hubspot_updater.run()
            logger.info(f"Scheduled HubSpot update completed: {result['status']}")
            return result
        
        # Add the task to the scheduler
        task_id = "hubspot_update"
        
        # Remove existing task if it exists
        scheduler.remove_task(task_id)
        
        # Add the new task
        scheduler.add_task(
            task_id=task_id,
            func=update_hubspot_task,
            interval_seconds=interval_seconds
        )
        
        # Make sure the scheduler is running
        if not scheduler.running:
            scheduler.start()
        
        return {
            "status": "success",
            "message": f"HubSpot update scheduled every {task.interval_minutes} minutes",
            "task_id": task_id,
            "interval_seconds": interval_seconds
        }
    except Exception as e:
        logger.error(f"Error scheduling HubSpot update: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/scheduler/hubspot-update")
async def remove_hubspot_update():
    """Remove scheduled HubSpot updates"""
    try:
        task_id = "hubspot_update"
        result = scheduler.remove_task(task_id)
        
        if result:
            return {"status": "success", "message": "HubSpot update schedule removed"}
        else:
            return {"status": "warning", "message": "No HubSpot update schedule found"}
    except Exception as e:
        logger.error(f"Error removing HubSpot update schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/hubspot/update-now")
async def update_hubspot_now(background_tasks: BackgroundTasks):
    """Run HubSpot update immediately"""
    try:
        # Run the update in the background
        background_tasks.add_task(hubspot_updater.run)
        
        return {
            "status": "success",
            "message": "HubSpot update started in background"
        }
    except Exception as e:
        logger.error(f"Error starting HubSpot update: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Start the scheduler when the app starts
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up the application")
    scheduler.start()

# Stop the scheduler when the app shuts down
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down the application")
    scheduler.stop()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
