from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time
from datetime import datetime, timedelta
import uuid
import logging

router = APIRouter()

# Initialize logger
logger = logging.getLogger(__name__)

# In-memory storage for scheduler tasks
# In a production app, this would be stored in a database
scheduler_status = "stopped"
scheduled_tasks = []

class SchedulerTask(BaseModel):
    id: str = None
    name: str
    task_type: str
    interval: int  # in seconds
    enabled: bool = True
    parameters: Dict[str, Any] = {}
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None

class SchedulerStatus(BaseModel):
    status: str
    tasks: List[SchedulerTask] = []
    last_run: Optional[datetime] = None
    processed_count: int = 0
    success_rate: float = 0

@router.get("/status", response_model=SchedulerStatus)
async def get_scheduler_status():
    """Get the current status of the scheduler and its tasks."""
    return SchedulerStatus(
        status=scheduler_status,
        tasks=scheduled_tasks,
        last_run=scheduled_tasks[0].last_run if scheduled_tasks else None,
        processed_count=len([task for task in scheduled_tasks if task.last_run]),
        success_rate=100.0  # Placeholder, would be calculated from actual success/failure data
    )

@router.post("/start")
async def start_scheduler(background_tasks: BackgroundTasks):
    """Start the scheduler."""
    global scheduler_status
    
    if scheduler_status == "running":
        raise HTTPException(status_code=400, detail="Scheduler is already running")
    
    scheduler_status = "running"
    
    # In a real implementation, you would start a background task or service
    # For now, we'll just update the status
    logger.info("Scheduler started")
    
    return {"status": "started"}

@router.post("/stop")
async def stop_scheduler():
    """Stop the scheduler."""
    global scheduler_status
    
    if scheduler_status == "stopped":
        raise HTTPException(status_code=400, detail="Scheduler is already stopped")
    
    scheduler_status = "stopped"
    
    # In a real implementation, you would stop the background task or service
    logger.info("Scheduler stopped")
    
    return {"status": "stopped"}

@router.post("/add-task", response_model=SchedulerTask)
async def add_task(task: SchedulerTask):
    """Add a new task to the scheduler."""
    # Generate a unique ID if not provided
    if not task.id:
        task.id = str(uuid.uuid4())
    
    # Calculate next run time
    if task.enabled:
        task.next_run = datetime.now() + timedelta(seconds=task.interval)
    
    # Add to scheduled tasks
    scheduled_tasks.append(task)
    
    logger.info(f"Added task: {task.name} (ID: {task.id})")
    
    return task

@router.delete("/remove-task/{task_id}")
async def remove_task(task_id: str):
    """Remove a task from the scheduler."""
    global scheduled_tasks
    
    # Find the task
    task_index = next((i for i, task in enumerate(scheduled_tasks) if task.id == task_id), None)
    
    if task_index is None:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    # Remove the task
    removed_task = scheduled_tasks.pop(task_index)
    
    logger.info(f"Removed task: {removed_task.name} (ID: {removed_task.id})")
    
    return {"status": "removed", "task_id": task_id}
