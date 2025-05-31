from typing import Dict, Any, Optional, List
from ..node.base import Node
from ..node.types import PythonNode
from hubspot import HubSpot
from ..utils.cache import CacheManager
import logging
from pydantic import Field, ValidationError as PydanticValidationError
from datetime import datetime
import json

class ValidationError(Exception):
    """Custom validation error class for HubspotFeedNode"""
    pass

logger = logging.getLogger(__name__)

class HubspotFeedNode(PythonNode):
    """Node that handles HubSpot webhook data and generates prompts"""
    
    def __init__(self, 
                 entity_type: str, 
                 access_token: Optional[str] = None,
                 fallback_prompt: str = "Generate a CRM record based on this data: {data}"):
        super().__init__(
            name="HubspotFeedNode",
            description="""
            Generates prompts for CRM entities from HubSpot data.
            If data is incomplete, fetches additional data from HubSpot API.
            Uses caching to optimize repeated requests.
            """,
            inputs=["entity"],
            outputs=["prompt"]
        )
        # Initialize basic properties
        self.entity_type = entity_type
        self.access_token = access_token
        self.fallback_prompt = fallback_prompt
        self.cache_manager = CacheManager()
        
        # Validate inputs
        if not access_token:
            logger.error("HubSpot access token is required")
            raise ValidationError("HubSpot access token is required")
            
        if not entity_type or entity_type not in ['company', 'contact', 'deal']:
            logger.error(f"Invalid entity type: {entity_type}")
            raise ValidationError(f"Invalid entity type: {entity_type}")
        
        # Initialize HubSpot client (only once)
        try:
            self.hubspot = HubSpot(access_token=access_token)
            logger.info(f"HubspotFeedNode initialized for entity type: {entity_type}")
        except Exception as e:
            logger.error(f"Failed to initialize HubSpot client: {str(e)}")
            raise
    
    def generate_prompt(self, entity_data: Dict[str, Any]) -> str:
        """Generate a prompt based on the entity type and data"""
        try:
            base_prompt = self.fallback_prompt
            
            if not isinstance(entity_data, dict):
                raise ValidationError(
                    "Entity data must be a dictionary",
                    context={
                        'node_type': 'HubspotFeedNode',
                        'entity_type': self.entity_type,
                        'data_type': type(entity_data).__name__
                    }
                )
            
            # Check cache first
            cached_data = self.cache_manager.get_cached_hubspot_data(
                entity_data['id'],
                self.entity_type
            )
            
            if cached_data:
                logger.info(f"Using cached HubSpot data for {self.entity_type} {entity_data['id']}")
                entity_data.update(cached_data)
            else:
                # If data is incomplete, fetch additional data from HubSpot
                if self.entity_type == "company":
                    required_keys = ['name', 'industry']
                    if not all(key in entity_data for key in required_keys):
                        try:
                            company = self.hubspot.crm.companies.basic_api.get_by_id(entity_data['id'])
                            entity_data.update(company.to_dict())
                            # Cache the fresh data
                            self.cache_manager.cache_hubspot_data(
                                entity_data['id'],
                                self.entity_type,
                                company.to_dict()
                            )
                        except Exception as e:
                            # Log the error
                            logger.error(f"Failed to fetch company data from HubSpot: {str(e)}")
                            
                            # Create error context
                            error_context = {
                                'node_type': 'HubspotFeedNode',
                                'entity_type': self.entity_type,
                                'company_id': entity_data.get('id', 'unknown'),
                                'error_type': e.__class__.__name__,
                                'timestamp': datetime.now().isoformat()
                            }
                            
                            # Use fallback data
                            logger.warning(f"Using fallback data for company {entity_data.get('id', 'unknown')}")
                            entity_data['name'] = entity_data.get('name', 'Unknown Company')
                            entity_data['industry'] = entity_data.get('industry', 'Unknown Industry')
                elif self.entity_type == "contact":
                    required_keys = ['firstname', 'lastname']
                    if not all(key in entity_data for key in required_keys):
                        try:
                            contact = self.hubspot.crm.contacts.basic_api.get_by_id(entity_data['id'])
                            entity_data.update(contact.to_dict())
                            # Cache the fresh data
                            self.cache_manager.cache_hubspot_data(
                                entity_data['id'],
                                self.entity_type,
                                contact.to_dict()
                            )
                        except Exception as e:
                            # Log the error
                            logger.error(f"Failed to fetch contact data from HubSpot: {str(e)}")
                            
                            # Create error context
                            error_context = {
                                'node_type': 'HubspotFeedNode',
                                'entity_type': self.entity_type,
                                'contact_id': entity_data.get('id', 'unknown'),
                                'error_type': e.__class__.__name__,
                                'timestamp': datetime.now().isoformat()
                            }
                            
                            # Use fallback data
                            logger.warning(f"Using fallback data for contact {entity_data.get('id', 'unknown')}")
                            entity_data['firstname'] = entity_data.get('firstname', 'Unknown')
                            entity_data['lastname'] = entity_data.get('lastname', 'Contact')
                elif self.entity_type == "deal":
                    required_keys = ['dealname', 'amount']
                    if not all(key in entity_data for key in required_keys):
                        try:
                            deal = self.hubspot.crm.deals.basic_api.get_by_id(entity_data['id'])
                            entity_data.update(deal.to_dict())
                            # Cache the fresh data
                            self.cache_manager.cache_hubspot_data(
                                entity_data['id'],
                                self.entity_type,
                                deal.to_dict()
                            )
                        except Exception as e:
                            # Log the error
                            logger.error(f"Failed to fetch deal data from HubSpot: {str(e)}")
                            
                            # Create error context
                            error_context = {
                                'node_type': 'HubspotFeedNode',
                                'entity_type': self.entity_type,
                                'deal_id': entity_data.get('id', 'unknown'),
                                'error_type': e.__class__.__name__,
                                'timestamp': datetime.now().isoformat()
                            }
                            
                            # Use fallback data
                            logger.warning(f"Using fallback data for deal {entity_data.get('id', 'unknown')}")
                            entity_data['dealname'] = entity_data.get('dealname', 'Unknown Deal')
                            entity_data['amount'] = entity_data.get('amount', '0')
            
            # Check for cached prompt
            cached_prompt = self.cache_manager.get_cached_prompt(
                entity_data['id'],
                self.entity_type
            )
            
            if cached_prompt:
                logger.info(f"Using cached prompt for {self.entity_type} {entity_data['id']}")
                return cached_prompt
            
            # Generate and cache new prompt
            prompt = base_prompt.format(data=json.dumps(entity_data, indent=2))
            self.cache_manager.cache_prompt(
                entity_data['id'],
                self.entity_type,
                prompt
            )
            
            return prompt
            
        except KeyError as e:
            # Log the error
            logger.error(f"Missing required field: {str(e)}")
            
            # Create error context
            error_context = {
                'node_type': 'HubspotFeedNode',
                'entity_type': self.entity_type,
                'missing_key': str(e),
                'error_type': 'KeyError',
                'timestamp': datetime.now().isoformat()
            }
            
            # Return a fallback prompt
            return f"Error processing entity data: Missing required field {str(e)}. Available data: {json.dumps(entity_data)}"
            
        except Exception as e:
            # Log the error
            logger.error(f"Failed to generate prompt: {str(e)}")
            
            # Create error context
            error_context = {
                'node_type': 'HubspotFeedNode',
                'entity_type': self.entity_type,
                'error_type': e.__class__.__name__,
                'timestamp': datetime.now().isoformat()
            }
            
            # Return a fallback prompt
            return f"Error processing entity: {entity_data.get('id', 'unknown')}. Error: {str(e)}"
            
    
    def run(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Generate prompt for the given entity"""
        try:
            prompt = self.generate_prompt(entity)
            return {"prompt": prompt}
        except Exception as e:
            # Log the error
            logger.error(f"Error generating prompt: {str(e)}")
            
            # Create simple error context
            error_context = {
                'node_type': 'HubspotFeedNode',
                'entity_type': self.entity_type,
                'error_type': e.__class__.__name__,
                'timestamp': datetime.now().isoformat()
            }
            
            # Return error response
            return {
                "status": "error",
                "message": f"Error generating prompt: {str(e)}",
                "error_context": error_context,
                "prompt": f"Error processing entity: {entity.get('id', 'unknown')}"
            }
    
    def clear_cache(self) -> None:
        """Clear all caches for this node"""
        self.cache_manager.clear_cache('hubspot')
        self.cache_manager.clear_cache('prompt')
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for this node"""
        return self.cache_manager.get_cache_stats()
