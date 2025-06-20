from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class AgentInput(BaseModel):
    """Base input model for all agents"""
    pass

class AgentOutput(BaseModel):
    """Base output model for all agents"""
    success: bool = Field(..., description="Whether the agent execution was successful")
    data: Dict[str, Any] = Field(default_factory=dict, description="Agent output data")
    error: Optional[str] = Field(None, description="Error message if execution failed")

class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """Execute the agent with error handling"""
        try:
            self.logger.info(f"Starting {self.__class__.__name__} execution")
            result = await self._execute_impl(input_data)
            self.logger.info(f"Completed {self.__class__.__name__} execution successfully")
            return result
        except Exception as e:
            error_msg = f"Error in {self.__class__.__name__}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return AgentOutput(success=False, error=error_msg)
    
    @abstractmethod
    async def _execute_impl(self, input_data: AgentInput) -> AgentOutput:
        """Implementation of agent execution"""
        pass
