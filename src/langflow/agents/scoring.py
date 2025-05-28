from typing import Dict, Any, Optional, List
from ..node.base import Node
from ..node.types import PythonNode
from pydantic import BaseModel, Field, ValidationError as PydanticValidationError
from src.langflow.schemas.crm import ScoreComponents, ScoreResult
from src.langflow.utils.errors import ValidationError, ProcessingError, handle_error
from src.langflow.utils.cache import CacheManager
import logging

logger = logging.getLogger(__name__)

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
    
    def score_company(self, entity: Dict[str, Any]) -> float:
        score = 0
        components = []
        weights = {}
        
        # Hiring signals
        if entity.get('hiring'):
            score += 0.3
            components.append('hiring')
            weights['hiring'] = 0.3
        
        # Funding signals
        if entity.get('funding'):
            score += 0.25
            components.append('funding')
            weights['funding'] = 0.25
        
        # Employee count normalization
        if entity.get('employee_count'):
            normalized = min(entity['employee_count'] / 1000, 1)
            score += normalized * 0.45
            components.append('employee_count')
            weights['employee_count'] = 0.45
        
        return score, ScoreComponents(signals=components, weights=weights)
    
    def score_contact(self, entity: Dict[str, Any]) -> float:
        score = 0
        components = []
        weights = {}
        
        # Title hierarchy scoring
        title = entity.get('title', '').lower()
        if 'c-' in title or 'chief' in title:
            score += 0.6
            components.append('c-level')
            weights['c-level'] = 0.6
        elif 'vp' in title or 'vice' in title:
            score += 0.4
            components.append('vp')
            weights['vp'] = 0.4
        elif 'director' in title:
            score += 0.3
            components.append('director')
            weights['director'] = 0.3
        
        # Meeting engagement
        if entity.get('meeting_engagement'):
            score += 0.2
            components.append('meeting_engagement')
            weights['meeting_engagement'] = 0.2
        
        return score, ScoreComponents(signals=components, weights=weights)
    
    def run(self, entity: Dict[str, Any]) -> ScoreResult:
        try:
            entity_type = entity.get('entity_type', '').lower()
            
            if not entity_type or entity_type not in ['company', 'contact']:
                raise ValidationError(
                    "Invalid entity type",
                    context={
                        'node_type': 'CRMScoreAgent',
                        'entity_type': entity_type
                    }
                )
            
            if not entity.get('id'):
                raise ValidationError(
                    "Entity ID is required",
                    context={
                        'node_type': 'CRMScoreAgent',
                        'entity_type': entity_type
                    }
                )
            
            # Check cache first
            cached_score = self.cache_manager.get_cached_scoring_result(
                entity['id'],
                entity_type
            )
            
            if cached_score:
                logger.info(f"Using cached score for {entity_type} {entity['id']}")
                return cached_score
            
            score = 0
            components = ScoreComponents()
            
            if entity_type == 'company':
                score, components = self.score_company(entity)
            elif entity_type == 'contact':
                score, components = self.score_contact(entity)
            
            if not isinstance(score, (int, float)):
                raise ProcessingError(
                    "Score calculation returned invalid type",
                    context={
                        'node_type': 'CRMScoreAgent',
                        'entity_type': entity_type,
                        'score_type': type(score).__name__
                    }
                )
            
            result = ScoreResult(
                crm_score=score,
                industry_score=0,  # Will be updated by IndustryScoreAgent
                total_score=score,  # Will be updated by MergeScoreAgent
                components=components,
                entity_id=entity.get('id', ''),
                entity_type=entity_type
            )
            
            # Cache the result
            self.cache_manager.cache_scoring_result(
                entity['id'],
                entity_type,
                result
            )
            
            return result
            
        except PydanticValidationError as e:
            error_context = handle_error(
                e,
                context={
                    'node_type': 'CRMScoreAgent',
                    'entity_type': entity_type,
                    'validation_errors': str(e.errors())
                }
            )
            raise ValidationError(
                "Failed to validate entity data",
                context=error_context
            )
        except Exception as e:
            error_context = handle_error(
                e,
                context={
                    'node_type': 'CRMScoreAgent',
                    'entity_type': entity_type
                }
            )
            raise ProcessingError(
                f"Failed to process entity: {str(e)}",
                context=error_context
            )
    
    def clear_cache(self) -> None:
        """Clear all caches for this node"""
        self.cache_manager.clear_cache('scoring')
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for this node"""
        return self.cache_manager.get_cache_stats()

class IndustryScoreAgent(PythonNode):
    name = "IndustryScoreAgent"
    description = """
    Scores entities based on industry-specific signals:
    - Funding rounds
    - IPO mentions
    - Mergers and acquisitions
    - Industry growth indicators
    """
    
    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description,
            inputs=["entity"],
            outputs=["score"]
        )
    
    INDUSTRY_KEYWORDS = {
        'funding': ['series', 'round', 'investment', 'capital'],
        'ipo': ['ipo', 'public', 'listing'],
        'merger': ['acquisition', 'merger', 'buyout'],
        'growth': ['expansion', 'growth', 'scale']
    }
    
    WEIGHTS = {
        'funding': 0.4,
        'ipo': 0.3,
        'merger': 0.2,
        'growth': 0.1
    }
    
    def score_industry(self, research_notes: str) -> float:
        score = 0
        components = []
        weights = {}
        
        if not research_notes:
            return score, ScoreComponents()
        
        # Check for industry keywords
        for keyword_type, keywords in self.INDUSTRY_KEYWORDS.items():
            weight = self.WEIGHTS[keyword_type]
            if any(keyword in research_notes.lower() for keyword in keywords):
                score += weight
                components.append(keyword_type)
                weights[keyword_type] = weight
        
        return score, ScoreComponents(signals=components, weights=weights)
    
    def run(self, entity: Dict[str, Any]) -> ScoreResult:
        try:
            if not entity.get('id'):
                raise ValidationError(
                    "Entity ID is required",
                    context={
                        'node_type': 'IndustryScoreAgent',
                        'entity_type': entity.get('entity_type', '')
                    }
                )
            
            score = 0
            components = ScoreComponents()
            
            if entity.get('research_notes'):
                score, components = self.score_industry(entity['research_notes'])
            
            return ScoreResult(
                crm_score=0,  # Will be updated by CRMScoreAgent
                industry_score=score,
                total_score=score,  # Will be updated by MergeScoreAgent
                components=components,
                entity_id=entity.get('id', ''),
                entity_type=entity.get('entity_type', '')
            )
            
        except Exception as e:
            error_context = handle_error(
                e,
                context={
                    'node_type': 'IndustryScoreAgent',
                    'entity_type': entity.get('entity_type', '')
                }
            )
            raise ProcessingError(
                f"Failed to process industry score: {str(e)}",
                context=error_context
            )

class MergeScoreAgent(PythonNode):
    name = "MergeScoreAgent"
    description = """
    Combines CRM and Industry scores with weighted averages:
    - CRM Score: 60% weight
    - Industry Score: 40% weight
    """
    
    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description,
            inputs=["crm_score", "industry_score"],
            outputs=["final_score"]
        )
    
    CRM_WEIGHT = 0.6
    INDUSTRY_WEIGHT = 0.4
    
    def run(self, crm_score: ScoreResult, industry_score: ScoreResult) -> ScoreResult:
        try:
            if not isinstance(crm_score, ScoreResult) or not isinstance(industry_score, ScoreResult):
                raise ValidationError(
                    "Input must be ScoreResult objects",
                    context={
                        'node_type': 'MergeScoreAgent',
                        'crm_type': type(crm_score).__name__,
                        'industry_type': type(industry_score).__name__
                    }
                )
            
            if crm_score.entity_id != industry_score.entity_id:
                raise ValidationError(
                    "Entity IDs do not match",
                    context={
                        'node_type': 'MergeScoreAgent',
                        'crm_id': crm_score.entity_id,
                        'industry_id': industry_score.entity_id
                    }
                )
            
            if crm_score.entity_type != industry_score.entity_type:
                raise ValidationError(
                    "Entity types do not match",
                    context={
                        'node_type': 'MergeScoreAgent',
                        'crm_type': crm_score.entity_type,
                        'industry_type': industry_score.entity_type
                    }
                )
            
            total_score = (crm_score.crm_score * self.CRM_WEIGHT) + \
                         (industry_score.industry_score * self.INDUSTRY_WEIGHT)
            
            if not (0 <= total_score <= 1):
                raise ProcessingError(
                    "Total score out of bounds",
                    context={
                        'node_type': 'MergeScoreAgent',
                        'score': total_score
                    }
                )
            
            return ScoreResult(
                crm_score=crm_score.crm_score,
                industry_score=industry_score.industry_score,
                total_score=total_score,
                components=ScoreComponents(
                    signals=crm_score.components.signals + industry_score.components.signals,
                    weights={
                        **crm_score.components.weights,
                        **industry_score.components.weights
                    }
                ),
                entity_id=crm_score.entity_id,
                entity_type=crm_score.entity_type
            )
            
        except PydanticValidationError as e:
            error_context = handle_error(
                e,
                context={
                    'node_type': 'MergeScoreAgent',
                    'validation_errors': str(e.errors())
                }
            )
            raise ValidationError(
                "Failed to validate score data",
                context=error_context
            )
        except Exception as e:
            error_context = handle_error(
                e,
                context={
                    'node_type': 'MergeScoreAgent',
                    'entity_id': crm_score.entity_id if hasattr(crm_score, 'entity_id') else 'unknown'
                }
            )
            raise ProcessingError(
                f"Failed to merge scores: {str(e)}",
                context=error_context
            )
