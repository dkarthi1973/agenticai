# agent_state.py
from typing import Dict, Any, List
from typing_extensions import TypedDict
from ticket_receiver import ServiceNowTicket  # Add this import

class AgentState(TypedDict):
    ticket: ServiceNowTicket
    classification: Dict[str, Any]
    execution_result: Dict[str, Any]
    validation_report: Dict[str, Any]
    update_response: Dict[str, Any]
    messages: List[str]
    current_agent: str
    errors: List[str]