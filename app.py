from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import uvicorn
import os
import sys
from typing import List, Dict, Any
from datetime import datetime, timedelta

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import services
from services.property_service import property_service
from services.email_service import email_service
from services.recommendations_service import recommendations_service
from services.diagnostics_service import diagnostics_service
from src.services.genie_service import genie_service

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Lakehouse Inn Voice of Customer",
    description="A Voice of the Customer application for Lakehouse Inn that uses GenAI to continuously scan and interpret guest feedback across 120 hotel properties",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def read_root():
    """Serve the main index.html file"""
    return FileResponse("frontend/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Lakehouse Inn Voice of Customer"}

# API Routes for the three screens

@app.get("/api/diagnostics/kpis")
async def get_diagnostics_kpis():
    """Get real-time diagnostics KPIs for all properties"""
    try:
        return property_service.get_diagnostics_kpis()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/diagnostics/flagged-properties")
async def get_flagged_properties():
    """Get list of properties flagged for issues"""
    try:
        flagged_properties = property_service.get_flagged_properties()
        return {"flagged_properties": flagged_properties}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/diagnostics/kickoff-workspace")
async def kickoff_anomaly_workspace():
    """Kick off anomaly detection workspace"""
    try:
        return diagnostics_service.kickoff_anomaly_workspace()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/diagnostics/scan-progress")
async def get_scan_progress():
    """Get current scanning progress"""
    try:
        return diagnostics_service.get_scan_progress()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/diagnostics/scan-results")
async def get_scan_results():
    """Get detailed scan results"""
    try:
        results = diagnostics_service.get_scan_results()
        return {"scan_results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/kpis")
async def get_dashboard_kpis():
    """Get property health dashboard KPIs"""
    try:
        return {
            "average_rating": 4.6,
            "response_rate": 87,
            "avg_response_time_minutes": 12,
            "satisfaction_trends": [
                {"date": "2024-01-01", "satisfaction": 94.2},
                {"date": "2024-01-02", "satisfaction": 94.8},
                {"date": "2024-01-03", "satisfaction": 95.1},
                {"date": "2024-01-04", "satisfaction": 95.2}
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dashboard/genie-query")
async def genie_query(query: dict):
    """Process Genie AI query against gold table"""
    try:
        user_query = query.get("query", "")
        
        # Use Genie service for natural language queries
        result = genie_service.continue_conversation(user_query)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/properties")
async def get_properties():
    """Get list of all properties"""
    try:
        properties = property_service.get_all_properties()
        return {"properties": properties}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/properties/{property_id}/details")
async def get_property_details(property_id: str):
    """Get detailed analysis for a specific property"""
    try:
        property_data = property_service.get_property_details(property_id)
        if not property_data:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Generate recommendations for this property
        recommendations = recommendations_service.generate_recommendations(property_data)
        
        # Add recommendations to the response
        property_data["recommendations"] = recommendations
        
        return property_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/properties/{property_id}/generate-email")
async def generate_property_email(property_id: str):
    """Generate email communication for property issues"""
    try:
        # Get property data
        property_data = property_service.get_property_details(property_id)
        if not property_data:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Generate email using the email service
        email_result = email_service.generate_property_email(property_data)
        
        return email_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
