from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter
import os
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the keyword research functionality
from keyword_research import router as keyword_router, get_keyword_ideas_for_langflow

# Create main app
app = FastAPI(title="SEO Agent API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the keyword research router
app.include_router(keyword_router)

# Serve static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Root endpoint serves the frontend
@app.get("/", response_class=HTMLResponse)
async def read_root():
    return FileResponse(static_dir / "index.html")

# Test page for keyword research
@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """Serve the keyword research test page"""
    test_file = Path(__file__).parent / "test_page.html"
    if test_file.exists():
        return FileResponse(test_file)
    else:
        return HTMLResponse("<h1>Test page not found</h1>", status_code=404)

# Langflow integration endpoint
@app.post("/api/langflow/keyword-research")
async def langflow_keyword_research(keywords: list[str], location_id: int = 1022378, language_id: int = 1000):
    """
    Endpoint for Langflow integration
    """
    try:
        logger.info(f"Langflow request: {keywords}, location: {location_id}, language: {language_id}")
        results = get_keyword_ideas_for_langflow(
            keywords=keywords,
            location_id=location_id,
            language_id=language_id
        )
        return {"status": "success", "data": results}
    except Exception as e:
        logger.error(f"Error in Langflow endpoint: {str(e)}")
        return {"status": "error", "message": str(e)}

# Debug endpoint to list all routes
@app.get("/routes")
async def list_routes():
    """List all available API routes"""
    return [{"path": route.path, "name": getattr(route, "name", ""), "methods": getattr(route, "methods", [])} for route in app.routes]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
