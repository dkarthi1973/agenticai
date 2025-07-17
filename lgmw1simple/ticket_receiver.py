from pydantic import BaseModel
from typing import Dict, Any
import json

class ServiceNowTicket(BaseModel):
    ticket_id: str
    priority: str
    category: str
    subcategory: str
    description: str
    ci_name: str
    environment: str
    requested_by: str
    
class TicketReceiver:
    def receive_ticket(self, raw_ticket: Dict[str, Any]) -> ServiceNowTicket:
        """Validate and structure incoming ticket"""
        try:
            if not raw_ticket:
                raise ValueError("No ticket data provided")
                
            print(f"Raw ticket data: {raw_ticket}")  # Debug logging
            ticket = ServiceNowTicket(**raw_ticket)
            print(f"Validated ticket: {ticket}")
            return ticket
        except Exception as e:
            print(f"Ticket validation failed: {e}")
            raise ValueError(f"Invalid ticket data: {str(e)}")