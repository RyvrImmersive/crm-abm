from typing import Dict, Any, Optional, List
from ..node.base import Node
from ..node.types import PythonNode
from hubspot import HubSpot
from ..utils.cache import CacheManager
import logging
from pydantic import Field, ValidationError

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
        self.entity_type = entity_type
        self.access_token = access_token
        self.fallback_prompt = fallback_prompt
        self.cache_manager = CacheManager()
        self.hubspot_client = HubSpot(api_key=access_token) if access_token else None
        
        if not access_token:
            raise ValidationError(
                "HubSpot access token is required",
                context={
                    'node_type': 'HubspotFeedNode',
                    'entity_type': entity_type
                }
            )
            
        if not entity_type or entity_type not in ['company', 'contact', 'deal']:
            raise ValidationError(
                "Invalid entity type",
                context={
                    'node_type': 'HubspotFeedNode',
                    'entity_type': entity_type
                }
            )
            
        self.entity_type = entity_type
        self.access_token = access_token
        self.fallback_prompt = fallback_prompt
        self.hubspot = HubSpot(access_token=access_token)
        self.cache_manager = CacheManager()
    
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
                            error_context = handle_error(
                                e,
                                context={
                                    'node_type': 'HubspotFeedNode',
                                    'entity_type': self.entity_type,
                                    'company_id': entity_data.get('id', 'unknown')
                                }
                            )
                            raise IntegrationError(
                                f"Failed to fetch company data from HubSpot: {str(e)}",
                                context=error_context
                            )
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
                            error_context = handle_error(
                                e,
                                context={
                                    'node_type': 'HubspotFeedNode',
                                    'entity_type': self.entity_type,
                                    'contact_id': entity_data.get('id', 'unknown')
                                }
                            )
                            raise IntegrationError(
                                f"Failed to fetch contact data from HubSpot: {str(e)}",
                                context=error_context
                            )
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
                            error_context = handle_error(
                                e,
                                context={
                                    'node_type': 'HubspotFeedNode',
                                    'entity_type': self.entity_type,
                                    'deal_id': entity_data.get('id', 'unknown')
                                }
                            )
                            raise IntegrationError(
                                f"Failed to fetch deal data from HubSpot: {str(e)}",
                                context=error_context
                            )
            
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
            error_context = handle_error(
                e,
                context={
                    'node_type': 'HubspotFeedNode',
                    'entity_type': self.entity_type,
                    'missing_key': str(e)
                }
            )
            raise ValidationError(
                f"Missing required field: {str(e)}",
                context=error_context
            )
        except Exception as e:
            error_context = handle_error(
                e,
                context={
                    'node_type': 'HubspotFeedNode',
                    'entity_type': self.entity_type
                }
            )
            raise ProcessingError(
                f"Failed to generate prompt: {str(e)}",
                context=error_context
            )
    
    def run(self, entity: Dict[str, Any]) -> str:
        """Generate prompt for the given entity"""
        try:
            return self.generate_prompt(entity)
        except Exception as e:
            error_context = handle_error(
                e,
                context={
                    'node_type': 'HubspotFeedNode',
                    'entity_type': self.entity_type
                }
            )
            raise ProcessingError(
                f"Error generating prompt: {str(e)}",
                context=error_context
            )
    
    def clear_cache(self) -> None:
        """Clear all caches for this node"""
        self.cache_manager.clear_cache('hubspot')
        self.cache_manager.clear_cache('prompt')
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for this node"""
        return self.cache_manager.get_cache_stats()
