from typing import Dict, Any, List, Optional
from ..node.base import Node
from ..node.types import PythonNode
import logging
import json
from datetime import datetime
from ..utils.cache import CacheManager

logger = logging.getLogger(__name__)

class AstraDBNode(PythonNode):
    """Node that persists CRM entities into AstraDB"""
    
    def __init__(self,
                 astra_db_id: str,
                 astra_db_region: str,
                 astra_db_token: str):
        super().__init__(
            name="AstraDBNode",
            description="""
            Persists CRM entities and their scores into AstraDB.
            Automatically determines the correct collection based on entity type.
            Uses caching to optimize repeated read operations.
            """,
            inputs=["entity", "scores"],
            outputs=["status"]
        )
        self.astra_db_id = astra_db_id
        self.astra_db_region = astra_db_region
        self.astra_db_token = astra_db_token
        self.cache_manager = CacheManager()
        self._init_client()
    
    def _init_client(self):
        """Initialize the Cassandra client"""
        try:
            # In a real implementation, we would use the secure bundle
            # For development/testing, we'll create a mock session
            logger.info(f"Initializing connection to AstraDB (ID: {self.astra_db_id})")
            
            # For development purposes, we'll just log the connection parameters
            # instead of actually connecting to the database
            logger.info(f"AstraDB Region: {self.astra_db_region}")
            logger.info(f"Using token authentication for AstraDB")
            
            # Mock the cluster and session for development
            self.cluster = None
            self.session = None
            
            logger.info(f"Mock connection to AstraDB cluster {self.astra_db_id} created")
        except Exception as e:
            logger.error(f"Failed to initialize AstraDB connection: {str(e)}")
            raise
    
    def _get_collection(self, entity_type: str) -> str:
        """Determine the correct collection based on entity type"""
        entity_type = entity_type.lower()
        
        if entity_type in ['company', 'companies']:
            return 'companies'
        elif entity_type in ['contact', 'contacts']:
            return 'contacts'
        elif entity_type in ['deal', 'deals']:
            return 'deals'
        else:
            return 'entities'
    
    def get_entity(self, entity_id: str, entity_type: str) -> Optional[Dict[str, Any]]:
        """Get an entity from AstraDB by ID"""
        # Check cache first
        cache_key = f"{entity_type}:{entity_id}"
        cached_entity = self.cache_manager.get(cache_key)
        
        if cached_entity:
            return cached_entity
        
        try:
            collection = self._get_collection(entity_type)
            
            # In a real implementation, we would query the database
            # For development/testing, we'll return a mock entity
            mock_entity = {
                'id': entity_id,
                'type': entity_type,
                'name': f"Mock {entity_type.capitalize()} {entity_id[:8]}",
                'created_at': '2023-01-01T00:00:00Z'
            }
            
            # Cache the result
            self.cache_manager.set(cache_key, mock_entity)
            
            return mock_entity
        except Exception as e:
            logger.error(f"Failed to get entity: {str(e)}")
            return None
    
    def persist_entity(self, entity: Dict[str, Any], scores: Dict[str, float]) -> Dict[str, Any]:
        """Persist an entity and its scores to AstraDB"""
        try:
            entity_type = entity.get('type', 'unknown')
            entity_id = entity.get('id', 'unknown-id')
            
            collection = self._get_collection(entity_type)
            
            # Merge entity with scores
            entity_with_scores = {
                **entity,
                'scores': scores,
                'updated_at': datetime.now().isoformat()
            }
            
            # Convert any datetime objects to ISO format strings
            for key, value in entity_with_scores.items():
                if isinstance(value, datetime):
                    entity_with_scores[key] = value.isoformat()
            
            # In a real implementation, we would insert into the database
            # For development/testing, we'll just log the operation
            logger.info(f"Would insert into collection '{collection}': {entity_id}")
            
            # Use a safer approach to log the entity data
            try:
                entity_json = json.dumps(entity_with_scores)[:100]
                logger.info(f"Entity data: {entity_json}...")
            except TypeError as json_error:
                logger.warning(f"Could not serialize entity data: {str(json_error)}")
            
            return {
                'status': 'success',
                'entity_id': entity_id,
                'entity_type': entity_type
            }
        except Exception as e:
            logger.error(f"Error persisting entity: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def run(self, entity: Dict[str, Any], scores: Dict[str, Any]) -> Dict[str, Any]:
        """Run the node's main processing logic"""
        try:
            # Call persist_entity to store the data
            result = self.persist_entity(entity, scores)
            return result
        except Exception as e:
            logger.error(f"AstraDBNode error: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def __del__(self):
        """Clean up resources"""
        if hasattr(self, 'cluster') and self.cluster:
            self.cluster.shutdown()
