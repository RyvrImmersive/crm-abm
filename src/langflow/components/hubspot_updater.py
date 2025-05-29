"""
HubSpot updater component for updating entity scores in HubSpot
"""
from typing import Dict, Any, List, Optional
from ..node.types import PythonNode
from hubspot import HubSpot
import logging
from datetime import datetime
from ..agents.scoring import CRMScoreAgent
import time

logger = logging.getLogger(__name__)

class HubspotUpdaterNode(PythonNode):
    """Node that updates HubSpot entities with scores"""
    
    def __init__(self, 
                 access_token: str,
                 batch_size: int = 25,
                 max_entities: int = 100):
        super().__init__(
            name="HubspotUpdaterNode",
            description="""
            Pulls entities from HubSpot, scores them, and updates HubSpot with the scores.
            Can be scheduled to run periodically.
            """,
            inputs=["trigger"],
            outputs=["results"]
        )
        self.access_token = access_token
        self.batch_size = batch_size
        self.max_entities = max_entities
        self.scoring_agent = CRMScoreAgent()
        self._init_client()
    
    def _init_client(self):
        """Initialize the HubSpot client"""
        try:
            self.hubspot = HubSpot(access_token=self.access_token)
            logger.info(f"HubspotUpdaterNode initialized with batch size {self.batch_size}")
        except Exception as e:
            logger.error(f"Failed to initialize HubSpot client: {str(e)}")
            raise
    
    def fetch_companies(self, limit: int = None) -> List[Dict[str, Any]]:
        """Fetch companies from HubSpot"""
        try:
            if limit is None:
                limit = self.max_entities
                
            companies = []
            after = None
            page_size = min(self.batch_size, limit)
            
            while len(companies) < limit:
                # Fetch a batch of companies
                company_batch = self.hubspot.crm.companies.basic_api.get_page(
                    limit=page_size,
                    after=after,
                    properties=["name", "domain", "industry", "description", "hubspot_score"]
                )
                
                # Add companies to the list
                companies.extend(company_batch.results)
                
                # Check if there are more companies to fetch
                if not company_batch.paging or not company_batch.paging.next.after:
                    break
                
                # Set the after cursor for the next batch
                after = company_batch.paging.next.after
                
                # If we've reached the limit, stop fetching
                if len(companies) >= limit:
                    break
            
            logger.info(f"Fetched {len(companies)} companies from HubSpot")
            return companies
        except Exception as e:
            logger.error(f"Error fetching companies from HubSpot: {str(e)}")
            return []
    
    def fetch_contacts(self, limit: int = None) -> List[Dict[str, Any]]:
        """Fetch contacts from HubSpot"""
        try:
            if limit is None:
                limit = self.max_entities
                
            contacts = []
            after = None
            page_size = min(self.batch_size, limit)
            
            while len(contacts) < limit:
                # Fetch a batch of contacts
                contact_batch = self.hubspot.crm.contacts.basic_api.get_page(
                    limit=page_size,
                    after=after,
                    properties=["firstname", "lastname", "email", "jobtitle", "hubspot_score"]
                )
                
                # Add contacts to the list
                contacts.extend(contact_batch.results)
                
                # Check if there are more contacts to fetch
                if not contact_batch.paging or not contact_batch.paging.next.after:
                    break
                
                # Set the after cursor for the next batch
                after = contact_batch.paging.next.after
                
                # If we've reached the limit, stop fetching
                if len(contacts) >= limit:
                    break
            
            logger.info(f"Fetched {len(contacts)} contacts from HubSpot")
            return contacts
        except Exception as e:
            logger.error(f"Error fetching contacts from HubSpot: {str(e)}")
            return []
    
    def update_company_score(self, company_id: str, score: float) -> bool:
        """Update a company's score in HubSpot"""
        try:
            # Convert score to integer percentage (0-100)
            score_int = int(score * 100)
            
            # Create properties to update
            properties = {
                "hubspot_score": str(score_int),
                "abm_score": str(score_int),
                "score_updated_at": datetime.now().isoformat()
            }
            
            # Update the company
            self.hubspot.crm.companies.basic_api.update(
                company_id,
                properties=properties
            )
            
            logger.info(f"Updated company {company_id} with score {score_int}")
            return True
        except Exception as e:
            logger.error(f"Error updating company {company_id} score: {str(e)}")
            return False
    
    def update_contact_score(self, contact_id: str, score: float) -> bool:
        """Update a contact's score in HubSpot"""
        try:
            # Convert score to integer percentage (0-100)
            score_int = int(score * 100)
            
            # Create properties to update
            properties = {
                "hubspot_score": str(score_int),
                "abm_score": str(score_int),
                "score_updated_at": datetime.now().isoformat()
            }
            
            # Update the contact
            self.hubspot.crm.contacts.basic_api.update(
                contact_id,
                properties=properties
            )
            
            logger.info(f"Updated contact {contact_id} with score {score_int}")
            return True
        except Exception as e:
            logger.error(f"Error updating contact {contact_id} score: {str(e)}")
            return False
    
    def process_companies(self, limit: int = None) -> Dict[str, Any]:
        """Process companies: fetch, score, and update"""
        start_time = time.time()
        
        # Fetch companies
        companies = self.fetch_companies(limit)
        
        # Process results
        processed = 0
        updated = 0
        errors = 0
        
        for company in companies:
            try:
                # Convert HubSpot company to dictionary format expected by scoring agent
                company_dict = {
                    "id": company.id,
                    "type": "company",
                    "properties": company.properties
                }
                
                # Score the company
                score_result = self.scoring_agent.run(entity=company_dict)
                
                # Extract the score
                if "crm_score" in score_result:
                    score = score_result["crm_score"]
                    
                    # Update the company in HubSpot
                    if self.update_company_score(company.id, score):
                        updated += 1
                    else:
                        errors += 1
                else:
                    logger.warning(f"No score found for company {company.id}")
                    errors += 1
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Error processing company {company.id}: {str(e)}")
                errors += 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            "entity_type": "company",
            "processed": processed,
            "updated": updated,
            "errors": errors,
            "duration_seconds": duration
        }
    
    def process_contacts(self, limit: int = None) -> Dict[str, Any]:
        """Process contacts: fetch, score, and update"""
        start_time = time.time()
        
        # Fetch contacts
        contacts = self.fetch_contacts(limit)
        
        # Process results
        processed = 0
        updated = 0
        errors = 0
        
        for contact in contacts:
            try:
                # Convert HubSpot contact to dictionary format expected by scoring agent
                contact_dict = {
                    "id": contact.id,
                    "type": "contact",
                    "properties": contact.properties
                }
                
                # Score the contact
                score_result = self.scoring_agent.run(entity=contact_dict)
                
                # Extract the score
                if "crm_score" in score_result:
                    score = score_result["crm_score"]
                    
                    # Update the contact in HubSpot
                    if self.update_contact_score(contact.id, score):
                        updated += 1
                    else:
                        errors += 1
                else:
                    logger.warning(f"No score found for contact {contact.id}")
                    errors += 1
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Error processing contact {contact.id}: {str(e)}")
                errors += 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            "entity_type": "contact",
            "processed": processed,
            "updated": updated,
            "errors": errors,
            "duration_seconds": duration
        }
    
    def run(self, trigger: Any = None) -> Dict[str, Any]:
        """Run the updater node"""
        try:
            logger.info("Starting HubSpot updater run")
            
            # Process companies and contacts
            company_results = self.process_companies()
            contact_results = self.process_contacts()
            
            # Combine results
            results = {
                "timestamp": datetime.now().isoformat(),
                "companies": company_results,
                "contacts": contact_results,
                "total_processed": company_results["processed"] + contact_results["processed"],
                "total_updated": company_results["updated"] + contact_results["updated"],
                "total_errors": company_results["errors"] + contact_results["errors"],
                "status": "success"
            }
            
            logger.info(f"HubSpot updater run completed: {results['total_updated']} entities updated")
            return results
            
        except Exception as e:
            logger.error(f"Error in HubSpot updater run: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }
