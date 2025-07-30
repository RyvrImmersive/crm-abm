try:
    from astrapy import DataAPIClient
except ImportError:
    # Fallback for older astrapy versions
    from astrapy.db import AstraDB as DataAPIClient
    
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class AstraService:
    """Service class for AstraDB operations"""
    
    def __init__(self, token: str, endpoint: str, collection_name: str = "company_data"):
        """
        Initialize AstraDB service
        
        Args:
            token: AstraDB application token
            endpoint: AstraDB API endpoint URL
            collection_name: Name of the collection to use
        """
        self.token = token
        self.endpoint = endpoint
        self.collection_name = collection_name
        
        try:
            # Initialize the client (compatible with older astrapy versions)
            try:
                # New astrapy version (1.0+)
                self.client = DataAPIClient(token)
                self.db = self.client.get_database_by_api_endpoint(endpoint)
                self.collection = self.db["company"]
                collection_names = self.db.list_collection_names()
            except (AttributeError, TypeError):
                # Older astrapy version (0.7.x)
                from astrapy.db import AstraDB
                self.db = AstraDB(
                    token=token,
                    api_endpoint=endpoint
                )
                self.collection = self.db.collection("company")
                collection_names = [collection_name]  # Assume collection exists
            
            logger.info(f"Connected to AstraDB: {collection_names}")
            
        except Exception as e:
            logger.error(f"Failed to connect to AstraDB: {str(e)}")
            raise
    
    def get_company_data(self, company_key: str, freshness_days: int = 360) -> Optional[Dict[str, Any]]:
        """
        Get company data from AstraDB if it exists and is fresh
        
        Args:
            company_key: Company identifier (e.g., "Apple - apple.com")
            freshness_days: Consider data stale after this many days
            
        Returns:
            Company data if found and fresh, None otherwise
        """
        try:
            # Calculate freshness threshold
            threshold_date = datetime.now() - timedelta(days=freshness_days)
            # Try multiple search strategies (compatible with older AstraPy)
            search_queries = [
                # Exact match on company_name in metadata
                {"metadata.company_name": company_key},
                # Try with different case variations
                {"metadata.company_name": company_key.title()},
                {"metadata.company_name": company_key.lower()},
                {"metadata.company_name": company_key.upper()},
                # Search by domain if present
                {"metadata.domain_name": company_key.split(' - ')[-1] if ' - ' in company_key else company_key}
            ]
            
            # Add company name only variations (for cases like "tesla - tesla.com" -> "Tesla")
            if ' - ' in company_key:
                company_name_only = company_key.split(' - ')[0].strip()
                search_queries.extend([
                    {"metadata.company_name": company_name_only},
                    {"metadata.company_name": company_name_only.title()},
                    {"metadata.company_name": company_name_only.lower()},
                    {"metadata.company_name": company_name_only.upper()}
                ])
            
            for i, query in enumerate(search_queries):
                try:
                    logger.info(f"Trying search strategy {i+1} for: {company_key}")
                    
                    # Find documents matching the query (older astrapy version)
                    try:
                        result = self.collection.find(filter=query)
                        logger.info(f"Find result type: {type(result)}, content: {result}")
                        
                        # Handle different response formats from older astrapy
                        documents = []
                        if isinstance(result, dict):
                            # Check if it's a response with data field
                            if 'data' in result and 'documents' in result['data']:
                                documents = result['data']['documents']
                            elif 'documents' in result:
                                documents = result['documents']
                            elif '_id' in result:  # Single document
                                documents = [result]
                        elif isinstance(result, list):
                            documents = result
                        
                        logger.info(f"Processed documents: {len(documents)} found")
                        
                    except Exception as find_error:
                        logger.error(f"Find error: {find_error}")
                        documents = []
                    
                    if documents:
                        # Select the best document from multiple matches
                        best_document = self._select_best_document(documents, company_key)
                        
                        # Check data freshness
                        if self._is_data_fresh(best_document, threshold_date):
                            logger.info(f"Found fresh data for {company_key}")
                            return best_document
                        else:
                            logger.info(f"Found stale data for {company_key}")
                            return None
                    
                except Exception as search_error:
                    logger.warning(f"Search strategy {i+1} failed: {str(search_error)}")
                    continue
            
            logger.info(f"No data found for {company_key}")
            return None
            
        except Exception as e:
            logger.error(f"Error querying AstraDB: {str(e)}")
            return None
    
    def _is_data_fresh(self, document: Dict[str, Any], threshold_date: datetime) -> bool:
        """
        Check if document data is fresh based on timestamp
        
        Args:
            document: Document from AstraDB
            threshold_date: Threshold datetime for freshness
            
        Returns:
            True if data is fresh, False otherwise
        """
        try:
            metadata = document.get("metadata", {})
            timestamp_str = metadata.get("timestamp")
            if not timestamp_str:
                logger.info("No timestamp found in document metadata - considering data fresh")
                # If no timestamp, assume data is fresh (could be legacy data)
                return True
            
            # Parse timestamp
            document_date = self._parse_timestamp(timestamp_str)
            if not document_date:
                return False
            
            is_fresh = document_date > threshold_date
            logger.info(f"Data freshness check: {document_date} > {threshold_date} = {is_fresh}")
            
            return is_fresh
            
        except Exception as e:
            logger.error(f"Error checking data freshness: {str(e)}")
            return False
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """
        Parse timestamp string with multiple format support
        
        Args:
            timestamp_str: Timestamp string to parse
            
        Returns:
            Parsed datetime object or None if parsing fails
        """
        timestamp_formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ", 
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S"
        ]
        
        for fmt in timestamp_formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        # Try ISO format parsing
        try:
            if timestamp_str.endswith('Z'):
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                return datetime.fromisoformat(timestamp_str)
        except Exception as e:
            logger.error(f"Failed to parse timestamp '{timestamp_str}': {e}")
            return None
    
    def _select_best_document(self, documents: List[Dict], company_key: str) -> Dict:
        """
        Select the best document from multiple matches based on:
        1. Exact company_name match
        2. Most recent timestamp
        3. Richest data (most populated fields)
        
        Args:
            documents: List of matching documents
            company_key: The search key used
            
        Returns:
            Best matching document
        """
        if len(documents) == 1:
            return documents[0]
        
        logger.info(f"Selecting best from {len(documents)} documents for key: {company_key}")
        
        # Score each document
        scored_docs = []
        for doc in documents:
            score = 0
            metadata = doc.get('metadata', {})
            
            # 1. Exact company name match (highest priority)
            stored_name = metadata.get('company_name', '').lower()
            if stored_name == company_key.lower():
                score += 100
                logger.info(f"Exact match bonus for: {stored_name}")
            
            # 2. Recency score (up to 50 points)
            timestamp_str = metadata.get('timestamp', '')
            if timestamp_str:
                try:
                    doc_time = self._parse_timestamp(timestamp_str)
                    if doc_time:
                        hours_old = (datetime.now() - doc_time).total_seconds() / 3600
                        # More recent = higher score (max 50 points for data < 1 hour old)
                        recency_score = max(0, 50 - hours_old)
                        score += recency_score
                        logger.info(f"Recency score: {recency_score:.1f} (age: {hours_old:.1f}h)")
                except:
                    pass
            
            # 3. Data richness score (up to 30 points)
            richness_score = 0
            
            # Check for rich data structures
            financial_data = metadata.get('financial_data', {})
            if financial_data and isinstance(financial_data, dict):
                # Count non-empty financial fields
                financial_fields = sum(1 for v in financial_data.values() 
                                     if v and v != 'Not found' and v != '$0')
                richness_score += min(10, financial_fields)
            
            hiring_data = metadata.get('hiring_data', {})
            if hiring_data and isinstance(hiring_data, dict):
                hiring_fields = sum(1 for v in hiring_data.values() 
                                  if v and v != 'Not found')
                richness_score += min(5, hiring_fields)
            
            sources = metadata.get('sources', [])
            if sources and isinstance(sources, list):
                richness_score += min(15, len(sources) * 3)
            
            score += richness_score
            logger.info(f"Richness score: {richness_score}")
            
            scored_docs.append((score, doc))
            logger.info(f"Total score: {score} for doc {doc.get('_id', 'unknown')}")
        
        # Sort by score (highest first) and return best
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        best_doc = scored_docs[0][1]
        best_score = scored_docs[0][0]
        
        logger.info(f"Selected best document with score: {best_score}")
        return best_doc
    
    def store_company_data(self, company_key: str, research_data: Dict[str, Any]) -> bool:
        """
        Store company research data in AstraDB
        
        Args:
            company_key: Company identifier
            research_data: Research data to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import uuid
            
            # Prepare document
            document = {
                "_id": str(uuid.uuid4()),
                "$vectorize": company_key,
                "metadata": {
                    **research_data,
                    "company_name": company_key,
                    "timestamp": datetime.now().isoformat(),
                    "data_source": "langflow_api"
                }
            }
            
            # Insert document (compatible with older astrapy)
            try:
                result = self.collection.insert_one(document)
                success = result.inserted_id if hasattr(result, 'inserted_id') else result
            except AttributeError:
                # Older astrapy version
                result = self.collection.insert_one(document)
                success = result
            
            if success:
                logger.info(f"Successfully stored data for {company_key}")
                return True
            else:
                logger.error(f"Failed to store data for {company_key}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing company data: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics
        
        Returns:
            Dictionary with collection stats
        """
        try:
            # Get estimated document count (older astrapy version)
            try:
                # Try to get a sample of documents to estimate count
                sample_docs = self.collection.find(filter={})
                if isinstance(sample_docs, list):
                    count_result = f"~{len(sample_docs)}" if len(sample_docs) < 100 else "100+"
                else:
                    count_result = "Available"
            except Exception as e:
                logger.error(f"Stats error: {e}")
                count_result = "Unknown"
            
            return {
                "document_count": count_result,
                "collection_name": self.collection_name,
                "status": "connected"
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {
                "document_count": "Error",
                "collection_name": self.collection_name,
                "status": "error"
            }
    
    def search_similar_companies(self, company_name: str, limit: int = 10) -> list:
        """
        Search for similar companies using vector search
        
        Args:
            company_name: Company name to find similar companies for
            limit: Maximum number of results to return
            
        Returns:
            List of similar companies
        """
        try:
            # Use vector search to find similar companies
            cursor = self.collection.find(
                {},
                sort={"$vectorize": company_name},
                limit=limit
            )
            
            results = []
            for doc in cursor:
                metadata = doc.get("metadata", {})
                results.append({
                    "company_name": metadata.get("company_name", "Unknown"),
                    "industry": metadata.get("industry", "Unknown"),
                    "revenue": metadata.get("revenue", "Unknown"),
                    "similarity_score": doc.get("$similarity", 0)
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar companies: {str(e)}")
            return []
    
    def delete_company_data(self, company_key: str) -> bool:
        """
        Delete company data from AstraDB
        
        Args:
            company_key: Company identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.collection.delete_many({"metadata.company_name": company_key})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted {result.deleted_count} documents for {company_key}")
                return True
            else:
                logger.warning(f"No documents found to delete for {company_key}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting company data: {str(e)}")
            return False
