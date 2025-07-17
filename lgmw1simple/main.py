# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn
import json  # Add this import
from workflow import MiddlewareInstallationWorkflow

app = FastAPI(title="Multi-Agent Middleware Installation System")
workflow = MiddlewareInstallationWorkflow()

class TicketRequest(BaseModel):
    ticket_data: Dict[str, Any]

@app.post("/process-ticket")
async def process_ticket(request: TicketRequest):
    """Process ServiceNow ticket through multi-agent workflow"""
    try:
        print(f"Received ticket data: {request.ticket_data}")
        result = workflow.process_ticket(request.ticket_data)
        return {
            "status": "success",
            "ticket_id": result["ticket"].ticket_id,
            "final_status": result["validation_report"]["overall_status"],
            "messages": result["messages"],
            "execution_time": result["execution_result"]["execution_time"]
        }
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    except Exception as e:
        print(f"Error processing ticket: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "multi-agent-middleware-system"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)