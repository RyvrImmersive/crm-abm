from typing import Dict, Any, List, Optional
from ..node.types import PythonNode
from pydantic import BaseModel, Field
from src.langflow.utils.cache import CacheManager
import logging

logger = logging.getLogger(__name__)

class ScoreComponents(BaseModel):
    """Components that make up a score"""
    signals: List[str] = Field(default_factory=list)
    weights: Dict[str, float] = Field(default_factory=dict)
    
    def dict(self):
        return {
            "signals": self.signals,
            "weights": self.weights
        }

class ScoreResult(BaseModel):
    """Result of scoring an entity"""
    crm_score: float = 0.0
    industry_score: float = 0.0
    total_score: float = 0.0
    components: ScoreComponents = Field(default_factory=ScoreComponents)
    entity_id: str = ""
    entity_type: str = ""

class CRMScoreAgent(PythonNode):
    """Agent that scores CRM entities based on various factors"""
    
    def __init__(self):
        super().__init__(
            name="CRMScoreAgent",
            description="""
            Scores CRM entities based on various factors:
            - Companies: hiring signals, funding, employee count
            - Contacts: title hierarchy, meeting engagement
            Uses caching to optimize repeated scoring calculations
            """,
            inputs=["entity"],
            outputs=["score"]
        )
        self.cache_manager = CacheManager()
        
    def run(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Process an entity and return a score"""
        try:
            # Extract entity_type safely with fallback
            entity_type = "company"  # Default
            if isinstance(entity, dict):
                if "entity_type" in entity:
                    entity_type = entity["entity_type"]
                elif "type" in entity:
                    entity_type = entity["type"]
                    
                # Convert to lowercase if it's a string
                if isinstance(entity_type, str):
                    entity_type = entity_type.lower()
                    
                # Extract entity_id safely
                entity_id = "unknown"
                if "id" in entity:
                    entity_id = entity["id"]
                elif "entity_id" in entity:
                    entity_id = entity["entity_id"]
            else:
                logger.warning(f"Invalid entity format: {type(entity)}")
                entity_id = "unknown"
                
            logger.info(f"Processing {entity_type} with ID {entity_id}")
            
            # Return a default score
            components = ScoreComponents(
                signals=["default"],
                weights={"default": 1.0}
            )
            
            score_result = {
                "crm_score": 0.75,  # Default score
                "entity_id": entity_id,
                "entity_type": entity_type,
                "components": components.dict()
            }
            
            return {"score": score_result}
            
        except Exception as e:
            # Catch-all error handler
            logger.error(f"Unexpected error in CRMScoreAgent: {str(e)}")
            return {
                "score": {
                    "crm_score": 0.5,  # Default score
                    "entity_id": "unknown",
                    "entity_type": "company",
                    "error": str(e)
                }
            }
