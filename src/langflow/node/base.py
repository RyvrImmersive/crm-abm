from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from ..utils.errors import ValidationError, ProcessingError, handle_error
import logging

logger = logging.getLogger(__name__)

class NodeConfig:
    """Configuration for a node"""
    def __init__(self, name: str, description: str, inputs: List[str], outputs: List[str]):
        self.name = name
        self.description = description
        self.inputs = inputs
        self.outputs = outputs

class Node(ABC):
    """Base class for all nodes in the flow"""
    
    def __init__(self, name: str, description: str, inputs: List[str], outputs: List[str]):
        self.config = NodeConfig(name, description, inputs, outputs)
    
    @property
    def name(self) -> str:
        return self.config.name
    
    @property
    def description(self) -> str:
        return self.config.description
    
    @property
    def inputs(self) -> List[str]:
        return self.config.inputs
    
    @property
    def outputs(self) -> List[str]:
        return self.config.outputs
    
    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """Run the node's main processing logic"""
        pass
    
    def validate_input(self, data: Dict[str, Any]) -> None:
        """Validate input data against node's inputs"""
        for input_field in self.inputs:
            if input_field not in data:
                raise ValidationError(
                    f"Missing required input: {input_field}",
                    context={
                        'node_name': self.name,
                        'missing_field': input_field
                    }
                )
    
    def handle_error(self, e: Exception, context: Dict[str, Any]) -> None:
        """Handle errors with proper logging and context"""
        error_context = handle_error(
            e,
            context=context
        )
        logger.error(f"Error in node {self.name}: {str(e)}", extra=error_context)
        raise ProcessingError(
            f"Failed to process in node {self.name}: {str(e)}",
            context=error_context
        )
