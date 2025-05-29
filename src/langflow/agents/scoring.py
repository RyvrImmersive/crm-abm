from typing import Dict, Any, List, Optional
from ..node.types import PythonNode
from pydantic import BaseModel, Field
from src.langflow.utils.cache import CacheManager
import logging
import json

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
            # Ensure entity is a dictionary
            if not isinstance(entity, dict):
                logger.warning(f"Entity is not a dictionary: {type(entity)}")
                return score, ScoreComponents(signals=['default'], weights={'default': 1.0})
                
            # Extract properties from the entity structure
            properties = {}
            
            # Check if properties are in the main entity
            if 'properties' in entity and isinstance(entity['properties'], dict):
                properties = entity['properties']
                logger.info(f"Found properties in entity: {properties}")
            # Check if properties are directly in the entity
            elif any(key in entity for key in ['industry', 'domain', 'description']):
                properties = entity
                logger.info(f"Using entity directly as properties")
            else:
                logger.info(f"No properties found in entity, using empty properties")
            
            # Hiring signals (10%)
            hiring_value = False
            try:
                hiring_value = (properties.get('hiring') == 'true' or 
                              entity.get('hiring') == 'true' or 
                              'hiring' in str(properties.get('description', '')).lower())
            except Exception as e:
                logger.warning(f"Error checking hiring signal: {str(e)}")
                
            if hiring_value:
                score += 0.1
                signals.append('hiring')
                weights['hiring'] = 0.1
                logger.info("Added hiring signal")
            
            # Funding signals (10%)
            funding_value = False
            funding_terms = ['funding', 'raised', 'investment', 'venture']
            try:
                funding_value = (properties.get('funding') == 'true' or 
                               entity.get('funding') == 'true' or 
                               any(term in str(properties.get('description', '')).lower() for term in funding_terms))
            except Exception as e:
                logger.warning(f"Error checking funding signal: {str(e)}")
                
            if funding_value:
                score += 0.1
                signals.append('funding')
                weights['funding'] = 0.1
                logger.info("Added funding signal")
            
            # Industry signals (10%)
            industry_value = False
            try:
                industry_value = bool(properties.get('industry') or entity.get('industry'))
            except Exception as e:
                logger.warning(f"Error checking industry signal: {str(e)}")
                
            if industry_value:
                score += 0.1
                signals.append('industry')
                weights['industry'] = 0.1
                logger.info("Added industry signal")
                
            # Domain signals (10%)
            domain_value = False
            try:
                domain_value = bool(properties.get('domain') or entity.get('domain'))
            except Exception as e:
                logger.warning(f"Error checking domain signal: {str(e)}")
                
            if domain_value:
                score += 0.1
                signals.append('domain')
                weights['domain'] = 0.1
                logger.info("Added domain signal")
            
            # Positive news signals (10%)
            news_value = False
            news_terms = ['growth', 'expansion', 'success', 'launch', 'partnership', 
                         'award', 'recognition', 'innovation', 'milestone']
            try:
                description = str(properties.get('description', entity.get('description', ''))).lower()
                news_value = any(term in description for term in news_terms)
            except Exception as e:
                logger.warning(f"Error checking news signal: {str(e)}")
                
            if news_value:
                score += 0.1
                signals.append('positive_news')
                weights['positive_news'] = 0.1
                logger.info("Added positive news signal")
            
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
            # Ensure entity is a dictionary
            if not isinstance(entity, dict):
                logger.warning(f"Entity is not a dictionary: {type(entity)}")
                return score, ScoreComponents(signals=['default'], weights={'default': 1.0})
                
            # Extract properties from the entity structure
            properties = {}
            
            # Check if properties are in the main entity
            if 'properties' in entity and isinstance(entity['properties'], dict):
                properties = entity['properties']
                logger.info(f"Found properties in entity: {properties}")
            # Check if properties are directly in the entity
            elif any(key in entity for key in ['title', 'firstname', 'lastname']):
                properties = entity
                logger.info(f"Using entity directly as properties")
            else:
                logger.info(f"No properties found in entity, using empty properties")
            
            # Title hierarchy scoring
            title = ''
            try:
                title = str(properties.get('title', entity.get('title', ''))).lower()
                logger.info(f"Contact title: {title}")
            except Exception as e:
                logger.warning(f"Error getting title: {str(e)}")
            
            # C-level executives (20%)
            if any(term in title for term in ['c-', 'chief', 'ceo', 'cfo', 'cto', 'coo', 'president']):
                score += 0.2
                signals.append('c-level')
                weights['c-level'] = 0.2
                logger.info("Added c-level signal")
            # VP level (15%)
            elif any(term in title for term in ['vp', 'vice president', 'vice-president', 'senior director']):
                score += 0.15
                signals.append('vp-level')
                weights['vp-level'] = 0.15
                logger.info("Added vp-level signal")
            # Director level (10%)
            elif 'director' in title:
                score += 0.1
                signals.append('director-level')
                weights['director-level'] = 0.1
                logger.info("Added director-level signal")
            # Manager level (5%)
            elif 'manager' in title:
                score += 0.05
                signals.append('manager-level')
                weights['manager-level'] = 0.05
                logger.info("Added manager-level signal")
            
            # Meeting engagement (10%)
            meeting_value = False
            try:
                meeting_value = (properties.get('meeting_engagement') or properties.get('last_meeting_date') or
                               entity.get('meeting_engagement') or entity.get('last_meeting_date'))
            except Exception as e:
                logger.warning(f"Error checking meeting engagement: {str(e)}")
                
            if meeting_value:
                score += 0.1
                signals.append('meeting_engagement')
                weights['meeting_engagement'] = 0.1
                logger.info("Added meeting engagement signal")
            
            # Email engagement (5%)
            email_value = False
            try:
                email_value = (properties.get('email_engagement') or properties.get('last_email_date') or
                             entity.get('email_engagement') or entity.get('last_email_date'))
            except Exception as e:
                logger.warning(f"Error checking email engagement: {str(e)}")
                
            if email_value:
                score += 0.05
                signals.append('email_engagement')
                weights['email_engagement'] = 0.05
                logger.info("Added email engagement signal")
            
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
            # Log the entire entity for debugging
            try:
                logger.info(f"Received entity data: {json.dumps(entity, default=str)[:500]}...")
            except Exception as e:
                logger.warning(f"Could not log entity data: {str(e)}")
                logger.info(f"Entity type: {type(entity)}")
            
            # Ensure entity is a dictionary
            if not isinstance(entity, dict):
                logger.error(f"Entity is not a dictionary: {type(entity)}")
                return {
                    "crm_score": 0.5,
                    "entity_id": "unknown",
                    "entity_type": "unknown",
                    "error": f"Entity is not a dictionary: {type(entity)}",
                    "components": {"signals": ["default"], "weights": {"default": 1.0}}
                }
            
            # Extract entity_type safely with fallback
            entity_type = "company"  # Default
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
                
            logger.info(f"Processing {entity_type} with ID {entity_id}")
            
            # Check for data in the webhook structure
            score_entity = None
            if "data" in entity and isinstance(entity["data"], dict):
                logger.info(f"Found data field in entity, using it for scoring")
                # Use the data field for scoring
                score_entity = entity["data"]
            else:
                logger.info(f"No data field found, using entire entity for scoring")
                score_entity = entity
                
            # Apply sophisticated scoring based on entity type
            score = 0.5  # Default score
            components = ScoreComponents(signals=["default"], weights={"default": 1.0})
            
            try:
                if entity_type == "company":
                    logger.info(f"Scoring as company type")
                    score, components = self.score_company(score_entity)
                elif entity_type == "contact":
                    logger.info(f"Scoring as contact type")
                    score, components = self.score_contact(score_entity)
                else:
                    logger.warning(f"Unknown entity type: {entity_type}, using default scoring")
            except Exception as e:
                logger.error(f"Error during scoring: {str(e)}")
                return {
                    "crm_score": 0.5,
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "error": str(e),
                    "components": {"signals": ["default"], "weights": {"default": 1.0}}
                }
            
            logger.info(f"Final score: {score}, with signals: {components.signals}")
            
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
