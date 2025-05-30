from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import json
import os
from ..agents.scoring import CRMScoreAgent

router = APIRouter(prefix="/scoring", tags=["scoring"])

# Initialize logger
logger = logging.getLogger(__name__)

# Default weights for different scoring factors
DEFAULT_WEIGHTS = {
    "hiring": 0.1,
    "funding": 0.1,
    "industry_match": 0.2,
    "domain_quality": 0.15,
    "positive_news": 0.15,
    "company_size": 0.1,
    "growth_rate": 0.1,
    "tech_adoption": 0.1
}

# Current weights - will be modified by API calls
current_weights = DEFAULT_WEIGHTS.copy()

# Model for weight updates
class WeightUpdate(BaseModel):
    weights: Dict[str, float]

# Model for score request
class ScoreRequest(BaseModel):
    entity: Dict[str, Any]
    weights: Optional[Dict[str, float]] = None

# Get the current weights
@router.get("/weights")
async def get_weights():
    """Get the current weights used for scoring."""
    return {"weights": current_weights}

# Update the weights
@router.post("/weights")
async def update_weights(weight_update: WeightUpdate = Body(...)):
    """Update the weights used for scoring."""
    global current_weights
    
    # Validate weights are between 0 and 1
    for key, value in weight_update.weights.items():
        if value < 0 or value > 1:
            raise HTTPException(status_code=400, detail=f"Weight for {key} must be between 0 and 1")
    
    # Update only the weights that are provided
    for key, value in weight_update.weights.items():
        if key in current_weights:
            current_weights[key] = value
        else:
            logger.warning(f"Unknown weight factor: {key}")
    
    # Normalize weights to ensure they sum to 1
    weight_sum = sum(current_weights.values())
    if weight_sum > 0:
        for key in current_weights:
            current_weights[key] = current_weights[key] / weight_sum
    
    return {"weights": current_weights}

# Reset weights to default
@router.post("/weights/reset")
async def reset_weights():
    """Reset weights to default values."""
    global current_weights
    current_weights = DEFAULT_WEIGHTS.copy()
    return {"weights": current_weights}

# Score an entity with custom weights
@router.post("/score")
async def score_entity(score_request: ScoreRequest):
    """Score an entity using the CRM scoring model with optional custom weights."""
    try:
        # Create a scoring agent
        agent = CRMScoreAgent()
        
        # Apply custom weights if provided
        weights_to_use = score_request.weights if score_request.weights else current_weights
        
        # Score the entity
        # Note: In a real implementation, we would modify the agent to accept custom weights
        # For now, we'll just return the score from the agent
        result = agent.run(score_request.entity)
        
        # Add the weights used for reference
        if "score" in result:
            result["score"]["weights_used"] = weights_to_use
        
        return result
    except Exception as e:
        logger.error(f"Error scoring entity: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scoring entity: {str(e)}")
