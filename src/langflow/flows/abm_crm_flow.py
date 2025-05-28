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
            # Extract entity data and ensure it has a type
            entity_data = webhook_data
            
            # Make sure entity_data has a type field
            if "type" not in entity_data:
                # Default to company if no type is provided
                entity_data["type"] = "company"
                logger.info(f"No entity type provided, defaulting to 'company'")
            
            # Log incoming data
            logger.info(f"Processing webhook data: {entity_data}")
            
            # Update the HubspotFeedNode entity type to match the data
            hubspot_node = self.nodes["hubspot"]
            hubspot_node.entity_type = entity_data["type"]
            logger.info(f"Set HubspotFeedNode entity_type to: {hubspot_node.entity_type}")
            
            # Start with HubSpot feed node
            prompt_result = hubspot_node.run(entity=entity_data)
            
            # Process through scoring node
            scoring_node = self.nodes["scoring"]
            score_result = scoring_node.run(entity=prompt_result["prompt"])
            
            # Persist to AstraDB node
            astra_node = self.nodes["astra"]
            persistence_result = astra_node.run(entity=entity_data, scores=score_result["score"])
            
            return {
                "status": "success",
                "entity_id": entity_data.get("id"),
                "entity_type": entity_data.get("type"),
                "scores": score_result.get("score", {}),
                "persistence": persistence_result
            }
            
        except Exception as e:
            # Create a simple error context
            error_context = {
                'node_type': 'ABMCRMFlow',
                'node_id': 'process_webhook',
                'timestamp': datetime.now().isoformat(),
                'error_type': e.__class__.__name__,
                'additional_info': {
                    'webhook_data': str(webhook_data)[:100] + '...' if len(str(webhook_data)) > 100 else str(webhook_data)
                }
            }
            
            # Log the error
            logger.error(f"Error processing webhook: {str(e)}")
            
            # Return error response
            return {
                "status": "error",
                "message": str(e),
                "entity_id": webhook_data.get("id"),
                "error_context": error_context
            }
    
    def update_entity_type(self, event_type: str):
        """
        Update the entity type for processing based on event type
        """
        # Extract entity type from event type (e.g., "company.created" -> "company")
        if "." in event_type:
            entity_type = event_type.split(".")[0]
        else:
            entity_type = event_type
            
        # Validate entity type
        valid_types = ["company", "contact", "deal"]
        if entity_type not in valid_types:
            raise ValueError(f"Invalid entity type: {event_type}")
            
        # Update the HubspotFeedNode entity type
        hubspot_node = self.nodes["hubspot"]
        hubspot_node.entity_type = entity_type
        
        return {"status": "success", "entity_type": entity_type}
    
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
