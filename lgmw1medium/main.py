# main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn
import sqlite3
import json
import logging
from workflow import MiddlewareInstallationWorkflow
from database import IncidentDB

# Initialize database and logging
db = IncidentDB()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Multi-Agent Middleware Installation System",
    description="API for processing middleware installation tickets",
    version="1.0.0"
)

workflow = MiddlewareInstallationWorkflow(db=db)

class TicketRequest(BaseModel):
    ticket_data: Dict[str, Any]

@app.post("/process-ticket")
async def process_ticket(request: TicketRequest, background_tasks: BackgroundTasks):
    """Process ticket with async option"""
    try:
        ticket_id = request.ticket_data.get("ticket_id", "")
        
        if not ticket_id:
            raise HTTPException(status_code=400, detail="Ticket ID is required")
            
        if db.get_incident(ticket_id):
            raise HTTPException(status_code=400, detail=f"Ticket {ticket_id} already exists")
        
        # Start async processing
        background_tasks.add_task(process_ticket_async, request.ticket_data)
        
        return {
            "status": "processing_started",
            "ticket_id": ticket_id,
            "message": "Ticket is being processed asynchronously"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting processing: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def process_ticket_async(ticket_data: Dict[str, Any]):
    """Background task for processing ticket"""
    try:
        result = workflow.process_ticket(ticket_data)
        logger.info(f"Successfully processed ticket {ticket_data['ticket_id']}")
    except Exception as e:
        logger.error(f"Failed to process ticket {ticket_data['ticket_id']}: {str(e)}")
        db.update_incident(ticket_data["ticket_id"], {
            "status": "failed",
            "error": str(e)
        })

@app.get("/incident/{ticket_id}")
async def get_incident(ticket_id: str):
    """Get incident details with status"""
    try:
        incident = db.get_incident(ticket_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        # Convert JSON strings to objects
        incident["classification"] = json.loads(incident.get("classification", "{}"))
        incident["execution_result"] = json.loads(incident.get("execution_result", "{}"))
        incident["validation_report"] = json.loads(incident.get("validation_report", "{}"))
        incident["messages"] = json.loads(incident.get("messages", "[]"))
        
        return incident
    except Exception as e:
        logger.error(f"Error getting incident: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving incident")

@app.get("/ticket-status/{ticket_id}")
async def get_ticket_status(ticket_id: str):
    """Simplified status check endpoint"""
    incident = db.get_incident(ticket_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    return {
        "ticket_id": ticket_id,
        "status": incident.get("status", "unknown"),
        "last_update": incident.get("updated_at")
    }


@app.get("/all-incidents")
async def get_all_incidents(
    limit: int = Query(default=100, gt=0, le=1000),
    skip: int = Query(default=0, ge=0)
):
    """Get paginated list of all incidents"""
    try:
        incidents = db.get_all_incidents(limit=limit, skip=skip)
        return incidents
    except ValueError as e:
        logger.error(f"Database error getting all incidents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error getting all incidents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@app.get("/health")
async def health_check():
    """Health check with DB verification"""
    try:
        db.get_incident("healthcheck")  # Test DB connection
        return {
            "status": "healthy",
            "service": "multi-agent-middleware-system",
            "database": "connected"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": "uvicorn.logging.DefaultFormatter",
                    "fmt": "%(levelprefix)s %(asctime)s - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                },
            },
            "loggers": {
                "uvicorn": {"handlers": ["default"], "level": "INFO"},
                "uvicorn.error": {"level": "INFO"},
                "uvicorn.access": {
                    "handlers": ["default"],
                    "level": "INFO",
                    "propagate": False,
                },
            },
        }
    )