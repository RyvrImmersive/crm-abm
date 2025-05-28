from typing import Dict, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class LangflowError(Exception):
    """Base class for all Langflow exceptions"""
    def __init__(self, message: str, context: Dict[str, Any] = None):
        self.message = message
        self.context = context or {}
        super().__init__(message)

class ValidationError(LangflowError):
    """Raised when data validation fails"""
    pass

class IntegrationError(LangflowError):
    """Raised when external service integration fails"""
    pass

class ProcessingError(LangflowError):
    """Raised when data processing fails"""
    pass

class PersistenceError(LangflowError):
    """Raised when data persistence fails"""
    pass

class ErrorContext(BaseModel):
    """Context information for errors"""
    node_type: str
    node_id: str
    timestamp: str
    additional_info: Dict[str, Any] = {}

def log_error(error: Exception, context: Dict[str, Any] = None):
    """Log an error with context information"""
    error_context = ErrorContext(
        node_type=context.get('node_type', 'unknown'),
        node_id=context.get('node_id', 'unknown'),
        timestamp=context.get('timestamp', ''),
        additional_info=context.get('additional_info', {})
    )
    
    logger.error(
        f"Error in {error_context.node_type} ({error_context.node_id}): {str(error)}",
        extra={'error_context': error_context.dict()}
    )
    
    return error_context

def handle_error(error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Handle and format error for API responses"""
    error_context = log_error(error, context)
    
    return {
        "status": "error",
        "message": str(error),
        "error_type": error.__class__.__name__,
        "context": error_context.dict()
    }
