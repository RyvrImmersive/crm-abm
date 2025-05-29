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
            
            # Extract entity data safely
            if not webhook_data or not isinstance(webhook_data, dict):
                logger.warning("Invalid webhook data format")
                return {
                    "status": "error",
                    "message": "Invalid webhook data format"
                }
                
            # Extract entity ID and type safely
            entity_id = webhook_data.get("id", "unknown")
            entity_type = webhook_data.get("type", "company")
            
            # Update the HubspotFeedNode entity type to match the data
            try:
                hubspot_node = self.nodes["hubspot"]
                hubspot_node.entity_type = entity_type
                logger.info(f"Set HubspotFeedNode entity_type to: {entity_type}")
                
                # Start with HubSpot feed node to generate prompt
                prompt_result = hubspot_node.run(entity=webhook_data)
                logger.info("Successfully generated prompt from HubSpot data")
                
                # Process through scoring node
                try:
                    scoring_node = self.nodes["scoring"]
                    score_result = scoring_node.run(entity=prompt_result["prompt"])
                    logger.info(f"Successfully scored entity: {score_result}")
                    
                    # Persist to AstraDB node
                    try:
                        astra_node = self.nodes["astra"]
                        # Log the score_result structure for debugging
                        logger.info(f"Score result structure: {score_result}")
                        
                        # Check if score_result has the expected structure
                        if not isinstance(score_result, dict):
                            logger.error(f"Score result is not a dictionary: {type(score_result)}")
                            return {
                                "status": "partial_success",
                                "message": "Webhook scored but persistence failed",
                                "error_details": f"Score result is not a dictionary: {type(score_result)}",
                                "entity_id": entity_id,
                                "entity_type": entity_type,
                                "scores": score_result
                            }
                        
                        # Pass the entire score_result as scores
                        persistence_result = astra_node.run(entity=webhook_data, scores=score_result)
                        logger.info(f"Successfully persisted to AstraDB: {persistence_result}")
                        
                        return {
                            "status": "success",
                            "message": "Webhook processed with scoring and persisted to AstraDB",
                            "entity_id": entity_id,
                            "entity_type": entity_type,
                            "scores": score_result,
                            "persistence": persistence_result
                        }
                    except Exception as astra_error:
                        logger.error(f"Error in AstraDB persistence: {str(astra_error)}")
                        
                        # Create a safer error response
                        try:
                            error_details = str(astra_error)
                        except:
                            error_details = "Unknown error in AstraDB persistence"
                            
                        try:
                            scores_data = score_result
                            if not isinstance(scores_data, dict):
                                scores_data = {"value": str(scores_data)}
                        except:
                            scores_data = {}
                            
                        return {
                            "status": "partial_success",
                            "message": "Webhook scored but persistence failed",
                            "error_details": error_details,
                            "entity_id": entity_id,
                            "entity_type": entity_type,
                            "scores": scores_data
                        }
                    
                except Exception as scoring_error:
                    logger.error(f"Error in scoring: {str(scoring_error)}")
                    return {
                        "status": "partial_success",
                        "message": "Webhook received but scoring failed",
                        "error_details": str(scoring_error),
                        "entity_id": entity_id,
                        "entity_type": entity_type,
                        "webhook_data": webhook_data
                    }
                    
            except Exception as hubspot_error:
                logger.error(f"Error in HubSpot processing: {str(hubspot_error)}")
                return {
                    "status": "partial_success",
                    "message": "Webhook received but HubSpot processing failed",
                    "error_details": str(hubspot_error),
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
