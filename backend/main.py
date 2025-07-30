from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
import logging

# Import our existing services
from services.astra_service import AstraService
from services.langflow_service import LangflowService
from services.lookalike_service import LookalikeService
from services.sentiment_service import SentimentService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Company Research API",
    description="Professional API for company research and competitive intelligence",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class CompanyResearchRequest(BaseModel):
    company_name: str
    domain_name: str
    force_refresh: bool = False
    data_freshness_days: int = 360

class LookalikeRequest(BaseModel):
    company_data: Dict[str, Any]

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None

# Service instances
astra_service = None
langflow_service = None
lookalike_service = None
sentiment_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global astra_service, langflow_service, lookalike_service, sentiment_service
    
    try:
        # Get environment variables
        astra_token = os.getenv('ASTRA_DB_TOKEN')
        astra_endpoint = os.getenv('ASTRA_DB_ENDPOINT')
        langflow_api_key = os.getenv('LANGFLOW_API_KEY')
        langflow_flow_url = os.getenv('LANGFLOW_FLOW_URL')
        
        if not all([astra_token, astra_endpoint, langflow_api_key, langflow_flow_url]):
            raise ValueError("Missing required environment variables")
        
        # Initialize services
        astra_service = AstraService(astra_token, astra_endpoint)
        langflow_service = LangflowService(langflow_api_key, langflow_flow_url)
        lookalike_service = LookalikeService()
        sentiment_service = SentimentService()
        
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

def get_services():
    """Dependency to get service instances"""
    return {
        "astra": astra_service,
        "langflow": langflow_service,
        "lookalike": lookalike_service,
        "sentiment": sentiment_service
    }

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Company Research API is running", "status": "healthy"}

@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test database connection
        stats = astra_service.get_collection_stats()
        return ApiResponse(
            success=True,
            data={
                "status": "healthy",
                "database_connected": True,
                "companies_in_db": stats.get('document_count', 0)
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
            message="Health check failed"
        )

@app.post("/api/research", response_model=ApiResponse)
async def research_company(
    request: CompanyResearchRequest,
    services: Dict = Depends(get_services)
):
    """Research a company and return comprehensive data"""
    try:
        astra = services["astra"]
        langflow = services["langflow"]
        
        # Create company key
        company_key = f"{request.company_name.lower().strip()} - {request.domain_name.lower().strip()}"
        
        # Check for existing data first
        if not request.force_refresh:
            existing_data = astra.get_company_data(company_key, request.data_freshness_days)
            if existing_data:
                logger.info(f"Returning cached data for {company_key}")
                return ApiResponse(
                    success=True,
                    data={
                        "company_data": existing_data,
                        "is_cached": True,
                        "is_mock": False
                    }
                )
        
        # Trigger research flow
        flow_response = langflow.trigger_research(
            request.company_name, 
            request.domain_name, 
            use_fallback=True
        )
        
        logger.info(f"Langflow response structure: {flow_response}")
        
        if not flow_response.get('success'):
            raise HTTPException(
                status_code=500, 
                detail=f"Research flow failed: {flow_response.get('error', 'Unknown error')}"
            )
        
        # Handle fallback data
        is_fallback = flow_response.get('fallback', False)
        
        # Safely extract company data with flexible structure handling
        try:
            # Try multiple possible response structures
            response_data = flow_response['response']
            
            # Check if response has nested 'data' field
            if isinstance(response_data, dict) and 'data' in response_data:
                company_data = response_data['data']
            # Check if response has 'outputs' field (common Langflow structure)
            elif isinstance(response_data, dict) and 'outputs' in response_data:
                # Extract from outputs structure
                outputs = response_data['outputs']
                if isinstance(outputs, list) and len(outputs) > 0:
                    company_data = outputs[0].get('outputs', {}).get('message', {})
                else:
                    company_data = outputs
            # Use response data directly if it looks like company data
            elif isinstance(response_data, dict) and ('metadata' in response_data or 'company_name' in response_data):
                company_data = response_data
            else:
                # Fallback: use the entire response
                logger.warning(f"Unknown response structure, using entire response: {response_data}")
                company_data = response_data
                
        except KeyError as e:
            logger.error(f"Missing key in flow_response: {e}. Response: {flow_response}")
            raise HTTPException(
                status_code=500,
                detail=f"Invalid response structure from research flow: missing {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error parsing flow response: {e}. Response: {flow_response}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse research flow response: {str(e)}"
            )
        
        if is_fallback:
            logger.warning(f"Using mock data for {company_key}: {flow_response.get('fallback_reason')}")
        
        # Store data in database
        store_success = astra.store_company_data(company_key, company_data)
        if not store_success:
            logger.warning(f"Failed to store data for {company_key}")
        
        return ApiResponse(
            success=True,
            data={
                "company_data": company_data,
                "is_cached": False,
                "is_mock": is_fallback,
                "fallback_reason": flow_response.get('fallback_reason') if is_fallback else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Research failed for {request.company_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/lookalike", response_model=ApiResponse)
async def find_lookalike_companies(
    request: LookalikeRequest,
    services: Dict = Depends(get_services)
):
    """Find similar companies using AI-powered search"""
    try:
        lookalike = services["lookalike"]
        
        # Find similar companies
        results = lookalike.find_lookalike_companies(request.company_data)
        
        return ApiResponse(
            success=True,
            data=results
        )
        
    except Exception as e:
        logger.error(f"Lookalike search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats(services: Dict = Depends(get_services)):
    """Get platform statistics"""
    try:
        astra = services["astra"]
        stats = astra.get_collection_stats()
        
        return ApiResponse(
            success=True,
            data={
                "companies_in_database": stats.get('document_count', 0),
                "data_freshness_threshold": "360 days"
            }
        )
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sentiment", response_model=ApiResponse)
async def analyze_sentiment(
    sources: List[Dict[str, Any]],
    services: Dict = Depends(get_services)
):
    """Analyze sentiment of news sources"""
    try:
        sentiment = services["sentiment"]
        
        analysis = sentiment.analyze_sources_sentiment(sources)
        
        return ApiResponse(
            success=True,
            data=analysis
        )
        
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
