from typing import Dict, Any, List
from ..flow.base import Flow
from ..components.hubspot_feed import HubspotFeedNode
from ..agents.scoring import CRMScoreAgent
from ..components.astra_db import AstraDBNode
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ABMCRMFlow(Flow):
    """Flow for Account-Based Marketing CRM processing"""
    
    def __init__(self, 
                 hubspot_access_token: str,
                 astra_db_id: str,
                 astra_db_region: str,
                 astra_db_token: str):
        # Create nodes
        hubspot_node = HubspotFeedNode(
            entity_type="company",
            access_token=hubspot_access_token
        )
        
        scoring_node = CRMScoreAgent()
        
        astra_node = AstraDBNode(
            astra_db_id=astra_db_id,
            astra_db_region=astra_db_region,
            astra_db_token=astra_db_token
        )
        
        # Define nodes dictionary
        nodes = {
            "hubspot": hubspot_node,
            "scoring": scoring_node,
            "astra": astra_node
        }
        
        # Define connections
        connections = [
            {
                "source_node": "hubspot", 
                "source_output": "prompt",
                "target_node": "scoring", 
                "target_input": "entity"
            },
            {
                "source_node": "scoring", 
                "source_output": "score",
                "target_node": "astra", 
                "target_input": "scores"
            }
        ]
        
        super().__init__(
            name="ABM CRM Flow",
            description="Processes CRM data from HubSpot, scores entities, and persists to AstraDB",
            nodes=nodes, 
            connections=connections
        )
    
    def process_webhook(self, webhook_data: dict) -> dict:
        """
        Process incoming webhook data through the flow
        """
        try:
            # Log incoming data
            logger.info(f"Processing webhook data: {webhook_data}")
            
            # Extract entity ID safely
            entity_id = "unknown"
            if webhook_data and isinstance(webhook_data, dict):
                entity_id = webhook_data.get("id", "unknown")
                
            # Extract entity type safely
            entity_type = "company"  # Default
            if webhook_data and isinstance(webhook_data, dict):
                entity_type = webhook_data.get("type", "company")
                
            # Just return a success response for now
            logger.info(f"Successfully processed webhook for {entity_type} with ID {entity_id}")
            
            return {
                "status": "success",
                "message": "Webhook received and processed",
                "entity_id": entity_id,
                "entity_type": entity_type,
                "webhook_data": webhook_data
            }
            
        except Exception as e:
            # Log the error
            logger.error(f"Error processing webhook: {str(e)}")
            
            # Create a minimal error response
            return {
                "status": "error",
                "message": "Error processing webhook",
                "error_details": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def update_entity_type(self, event_type: str):
        """
        Update the entity type for processing based on event type
        """
        try:
            # Default entity_type in case of errors
            entity_type = "company"
            
            # Extract entity type from event type (e.g., "company.created" -> "company")
            if event_type and "." in event_type:
                entity_type = event_type.split(".")[0]
            elif event_type:
                entity_type = event_type
                
            # Validate entity type
            valid_types = ["company", "contact", "deal"]
            if entity_type not in valid_types:
                logger.warning(f"Invalid entity type: {event_type}, defaulting to 'company'")
                entity_type = "company"  # Default to company for invalid types
                
            # Update the HubspotFeedNode entity type
            hubspot_node = self.nodes["hubspot"]
            hubspot_node.entity_type = entity_type
            logger.info(f"Updated entity_type to: {entity_type}")
            
            return {"status": "success", "entity_type": entity_type}
            
        except Exception as e:
            logger.error(f"Error updating entity type: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def get_flow_status(self) -> dict:
        """
        Get the current status of all nodes in the flow
        """
        node_status = {}
        for node_id, node in self.nodes.items():
            node_status[node_id] = {
                "name": node.name,
                "type": node.__class__.__name__,
                "entity_type": getattr(node, "entity_type", None)
            }
            
        return {
            "nodes": node_status,
            "connections": self.connections
        }
    
    def get_connections(self) -> list:
        """
        Get all connections between nodes
        """
        return self.connections
