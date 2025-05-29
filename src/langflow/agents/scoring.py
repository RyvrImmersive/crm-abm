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
            - Companies: hiring signals, funding, industry, domain, positive news
            - Contacts: title hierarchy, meeting engagement
            Uses caching to optimize repeated scoring calculations
            """,
            inputs=["entity"],
            outputs=["score"]
        )
        self.cache_manager = CacheManager()
    
    def score_company(self, entity: Dict[str, Any]) -> tuple:
        """Score a company entity with sophisticated logic"""
        # Start with base score
        score = 0.5
        signals = []
        weights = {}
        
        try:
            # Hiring signals (10%)
            if entity.get('hiring') or 'hiring' in str(entity.get('description', '')).lower():
                score += 0.1
                signals.append('hiring')
                weights['hiring'] = 0.1
            
            # Funding signals (10%)
            if entity.get('funding') or any(term in str(entity.get('description', '')).lower() 
                                          for term in ['funding', 'raised', 'investment', 'venture']):
                score += 0.1
                signals.append('funding')
                weights['funding'] = 0.1
            
            # Industry signals (10%)
            if entity.get('industry'):
                score += 0.1
                signals.append('industry')
                weights['industry'] = 0.1
                
            # Domain signals (10%)
            if entity.get('domain'):
                score += 0.1
                signals.append('domain')
                weights['domain'] = 0.1
            
            # Positive news signals (10%)
            news_terms = ['growth', 'expansion', 'success', 'launch', 'partnership', 
                         'award', 'recognition', 'innovation', 'milestone']
            description = str(entity.get('description', '')).lower()
            if any(term in description for term in news_terms):
                score += 0.1
                signals.append('positive_news')
                weights['positive_news'] = 0.1
            
            # Cap the score at 1.0
            score = min(score, 1.0)
            
            logger.info(f"Scored company with signals: {signals}")
            
        except Exception as e:
            logger.warning(f"Error in company scoring: {str(e)}, using default score")
            score = 0.5
            signals = ['default']
            weights = {'default': 1.0}
        
        return score, ScoreComponents(signals=signals, weights=weights)
    
    def score_contact(self, entity: Dict[str, Any]) -> tuple:
        """Score a contact entity with sophisticated logic"""
        # Start with base score
        score = 0.5
        signals = []
        weights = {}
        
        try:
            # Title hierarchy scoring
            title = str(entity.get('title', '')).lower()
            
            # C-level executives (20%)
            if any(term in title for term in ['c-', 'chief', 'ceo', 'cfo', 'cto', 'coo', 'president']):
                score += 0.2
                signals.append('c-level')
                weights['c-level'] = 0.2
            # VP level (15%)
            elif any(term in title for term in ['vp', 'vice president', 'vice-president', 'senior director']):
                score += 0.15
                signals.append('vp-level')
                weights['vp-level'] = 0.15
            # Director level (10%)
            elif 'director' in title:
                score += 0.1
                signals.append('director-level')
                weights['director-level'] = 0.1
            # Manager level (5%)
            elif 'manager' in title:
                score += 0.05
                signals.append('manager-level')
                weights['manager-level'] = 0.05
            
            # Meeting engagement (10%)
            if entity.get('meeting_engagement') or entity.get('last_meeting_date'):
                score += 0.1
                signals.append('meeting_engagement')
                weights['meeting_engagement'] = 0.1
            
            # Email engagement (5%)
            if entity.get('email_engagement') or entity.get('last_email_date'):
                score += 0.05
                signals.append('email_engagement')
                weights['email_engagement'] = 0.05
            
            # Cap the score at 1.0
            score = min(score, 1.0)
            
            logger.info(f"Scored contact with signals: {signals}")
            
        except Exception as e:
            logger.warning(f"Error in contact scoring: {str(e)}, using default score")
            score = 0.5
            signals = ['default']
            weights = {'default': 1.0}
        
        return score, ScoreComponents(signals=signals, weights=weights)
        
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
            
            # Apply sophisticated scoring based on entity type
            score = 0.5  # Default score
            components = ScoreComponents(signals=["default"], weights={"default": 1.0})
            
            if entity_type == "company":
                score, components = self.score_company(entity)
            elif entity_type == "contact":
                score, components = self.score_contact(entity)
            else:
                logger.warning(f"Unknown entity type: {entity_type}, using default scoring")
            
            score_result = {
                "crm_score": score,
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
