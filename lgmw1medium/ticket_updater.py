# ticket_updater.py
import requests
from typing import Dict, Any
from ticket_receiver import ServiceNowTicket  # Add this import

class TicketUpdater:
    def __init__(self):
        self.name = "ticket_updater"
        self.servicenow_url = "https://mock-servicenow.com/api"
    
    def update_ticket(self, ticket: ServiceNowTicket, validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """Update ServiceNow ticket with execution results"""
        
        update_payload = {
            "ticket_id": ticket.ticket_id,
            "status": "completed" if validation_report["overall_status"] == "success" else "failed",
            "resolution_notes": self._generate_resolution_notes(validation_report),
            "actual_duration": validation_report.get("execution_time", "20min"),
            "validation_results": validation_report["checks"]
        }
        
        # Mock ServiceNow API call
        response = self._mock_servicenow_update(update_payload)
        
        print(f"📝 Ticket {ticket.ticket_id} updated with status: {update_payload['status']}")
        return response
    
    def _mock_servicenow_update(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Mock ServiceNow ticket update"""
        return {
            "status": "success",
            "ticket_id": payload["ticket_id"],
            "updated_at": "2024-12-07T10:30:00Z",
            "response": "Ticket updated successfully"
        }
    
    def _generate_resolution_notes(self, validation_report: Dict[str, Any]) -> str:
        """Generate human-readable resolution notes"""
        if validation_report["overall_status"] == "success":
            return f"Middleware installation/upgrade completed successfully. All validation checks passed. {validation_report['recommendations']}"
        else:
            return f"Middleware installation/upgrade failed. {validation_report['recommendations']}"