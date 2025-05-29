"""
Scheduler utility for running periodic tasks
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Callable, Dict, Any, List, Optional
import threading

logger = logging.getLogger(__name__)

class TaskScheduler:
    """Scheduler for running periodic tasks"""
    
    def __init__(self):
        self.tasks = {}
        self.running = False
        self.scheduler_thread = None
        logger.info("TaskScheduler initialized")
    
    def add_task(self, task_id: str, func: Callable, interval_seconds: int, **kwargs) -> bool:
        """
        Add a task to the scheduler
        
        Args:
            task_id: Unique identifier for the task
            func: Function to call
            interval_seconds: Interval between calls in seconds
            **kwargs: Arguments to pass to the function
        
        Returns:
            bool: True if task was added, False if task_id already exists
        """
        if task_id in self.tasks:
            logger.warning(f"Task {task_id} already exists")
            return False
        
        self.tasks[task_id] = {
            "func": func,
            "interval": interval_seconds,
            "last_run": 0,  # Never run
            "kwargs": kwargs,
            "running": False,
            "error_count": 0
        }
        
        logger.info(f"Added task {task_id} with interval {interval_seconds}s")
        return True
    
    def remove_task(self, task_id: str) -> bool:
        """
        Remove a task from the scheduler
        
        Args:
            task_id: Unique identifier for the task
        
        Returns:
            bool: True if task was removed, False if task_id doesn't exist
        """
        if task_id not in self.tasks:
            logger.warning(f"Task {task_id} does not exist")
            return False
        
        del self.tasks[task_id]
        logger.info(f"Removed task {task_id}")
        return True
    
    def update_task(self, task_id: str, interval_seconds: Optional[int] = None, **kwargs) -> bool:
        """
        Update a task's interval or kwargs
        
        Args:
            task_id: Unique identifier for the task
            interval_seconds: New interval between calls in seconds
            **kwargs: New arguments to pass to the function
        
        Returns:
            bool: True if task was updated, False if task_id doesn't exist
        """
        if task_id not in self.tasks:
            logger.warning(f"Task {task_id} does not exist")
            return False
        
        if interval_seconds is not None:
            self.tasks[task_id]["interval"] = interval_seconds
        
        if kwargs:
            self.tasks[task_id]["kwargs"].update(kwargs)
        
        logger.info(f"Updated task {task_id}")
        return True
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a task
        
        Args:
            task_id: Unique identifier for the task
        
        Returns:
            dict: Task status or empty dict if task_id doesn't exist
        """
        if task_id not in self.tasks:
            logger.warning(f"Task {task_id} does not exist")
            return {}
        
        task = self.tasks[task_id]
        
        return {
            "task_id": task_id,
            "interval": task["interval"],
            "last_run": task["last_run"],
            "last_run_formatted": datetime.fromtimestamp(task["last_run"]).isoformat() if task["last_run"] > 0 else "Never",
            "running": task["running"],
            "error_count": task["error_count"]
        }
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """
        Get the status of all tasks
        
        Returns:
            list: List of task statuses
        """
        return [self.get_task_status(task_id) for task_id in self.tasks]
    
    def _run_task(self, task_id: str):
        """Run a task and handle errors"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        
        if task["running"]:
            logger.warning(f"Task {task_id} is already running, skipping")
            return
        
        try:
            task["running"] = True
            logger.info(f"Running task {task_id}")
            
            # Call the task function with its arguments
            task["func"](**task["kwargs"])
            
            # Update last run time
            task["last_run"] = time.time()
            
        except Exception as e:
            logger.error(f"Error running task {task_id}: {str(e)}")
            task["error_count"] += 1
        finally:
            task["running"] = False
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        logger.info("Scheduler loop started")
        
        while self.running:
            current_time = time.time()
            
            for task_id, task in self.tasks.items():
                # Check if task should run (if enough time has passed since last run)
                if current_time - task["last_run"] >= task["interval"]:
                    # Run in a separate thread to avoid blocking the scheduler
                    threading.Thread(target=self._run_task, args=(task_id,)).start()
            
            # Sleep for a short time to avoid high CPU usage
            time.sleep(1)
        
        logger.info("Scheduler loop stopped")
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.daemon = True  # Allow the thread to be terminated when the main program exits
        self.scheduler_thread.start()
        
        logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.running:
            logger.warning("Scheduler is not running")
            return
        
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)  # Wait for the thread to terminate
        
        logger.info("Scheduler stopped")

# Create a global scheduler instance
scheduler = TaskScheduler()
