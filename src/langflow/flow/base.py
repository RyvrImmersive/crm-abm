from typing import Dict, Any, List, Optional
from ..node.base import Node
from ..utils.errors import ValidationError, ProcessingError
import logging

logger = logging.getLogger(__name__)

class Flow:
    """A flow of nodes that process data"""
    
    def __init__(self, name: str, description: str, nodes: Dict[str, Node], connections: List[Dict[str, Any]]):
        self.name = name
        self.description = description
        self.nodes = nodes
        self.connections = connections
    
    def process_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a webhook request through the flow"""
        try:
            # Validate connections
            self._validate_connections()
            
            # Initialize node outputs
            node_outputs = {}
            
            # Process each node in order
            for node_id, node in self.nodes.items():
                # Get inputs for this node from connections
                node_inputs = self._get_node_inputs(node_id, node_outputs, data)
                
                # Validate inputs
                node.validate_input(node_inputs)
                
                # Run the node
                node_result = node.run(**node_inputs)
                
                # Store the result
                node_outputs[node_id] = node_result
            
            # Return the final output
            return node_outputs
        except (ValidationError, ProcessingError) as e:
            logger.error(f"Error processing webhook: {str(e)}")
            raise
    
    def _validate_connections(self) -> None:
        """Validate that all connections reference existing nodes"""
        for connection in self.connections:
            source_node = connection.get('source_node')
            target_node = connection.get('target_node')
            
            if source_node not in self.nodes:
                raise ValidationError(f"Source node '{source_node}' not found")
            
            if target_node not in self.nodes:
                raise ValidationError(f"Target node '{target_node}' not found")
    
    def _get_node_inputs(self, node_id: str, node_outputs: Dict[str, Any], 
                        initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get inputs for a node from connections and initial data"""
        inputs = {}
        
        # Add initial data if this is the first node
        if not any(conn.get('target_node') == node_id for conn in self.connections):
            inputs.update(initial_data)
        
        # Add data from connected nodes
        for connection in self.connections:
            if connection.get('target_node') == node_id:
                source_node = connection.get('source_node')
                source_output = connection.get('source_output')
                target_input = connection.get('target_input')
                
                if source_node in node_outputs and source_output in node_outputs[source_node]:
                    inputs[target_input] = node_outputs[source_node][source_output]
        
        return inputs
