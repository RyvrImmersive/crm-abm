from typing import Dict, Any, List
from ..flow.base import Flow
from ..components.hubspot_feed import HubspotFeedNode
from ..agents.scoring import CRMScoreAgent
from ..components.astra_db import AstraDBNode

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
            # Start with HubSpot feed
            prompt = self.hubspot_feed.run(webhook_data)
            
            # Process through the flow
            crm_score = self.crm_score_agent.run(prompt)
            industry_score = self.industry_score_agent.run(prompt)
            final_score = self.merge_score_agent.run(crm_score, industry_score)
            
            # Persist to AstraDB
            result = self.astra_db.run(webhook_data, final_score)
            
            return {
                "status": "success",
                "entity_id": webhook_data.get("id"),
                "scores": final_score,
                "persistence": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "entity_id": webhook_data.get("id")
            }
    
    def update_entity_type(self, entity_type: str):
        """
        Update the entity type for processing
        """
        if entity_type not in ["company", "contact", "deal"]:
            raise ValueError(f"Invalid entity type: {entity_type}")
            
        self.hubspot_feed.entity_type = entity_type
    
    def get_flow_status(self) -> dict:
        """
        Get the current status of all nodes in the flow
        """
        return {
            "nodes": {
                "hubspot_feed": self.hubspot_feed.status,
                "crm_score_agent": self.crm_score_agent.status,
                "industry_score_agent": self.industry_score_agent.status,
                "merge_score_agent": self.merge_score_agent.status,
                "astra_db": self.astra_db.status
            },
            "connections": self.get_connections()
        }
    
    def get_connections(self) -> list:
        """
        Get all connections between nodes
        """
        return [
            {
                "source": "hubspot_feed",
                "target": "crm_score_agent"
            },
            {
                "source": "hubspot_feed",
                "target": "industry_score_agent"
            },
            {
                "source": "crm_score_agent",
                "target": "merge_score_agent"
            },
            {
                "source": "industry_score_agent",
                "target": "merge_score_agent"
            },
            {
                "source": "merge_score_agent",
                "target": "astra_db"
            }
        ]
