# workflow.py
from langgraph.graph import StateGraph, END
from typing import Dict, Any  # Add this import
from agent_state import AgentState
from ticket_receiver import TicketReceiver, ServiceNowTicket
from ticket_classifier import TicketClassifier
from ticket_executor import TicketExecutor
from ticket_validator import TicketValidator
from ticket_updater import TicketUpdater

class MiddlewareInstallationWorkflow:
    def __init__(self):
        self.ticket_receiver = TicketReceiver()
        self.ticket_classifier = TicketClassifier()
        self.ticket_executor = TicketExecutor()
        self.ticket_validator = TicketValidator()
        self.ticket_updater = TicketUpdater()
        
        # Create the workflow graph
        self.workflow = StateGraph(AgentState)
        self._build_workflow()
    
    def _build_workflow(self):
        """Build the multi-agent workflow"""
        
        # Add nodes
        self.workflow.add_node("receive", self._receive_node)
        self.workflow.add_node("classify", self._classify_node)
        self.workflow.add_node("execute", self._execute_node)
        self.workflow.add_node("validate", self._validate_node)
        self.workflow.add_node("update", self._update_node)
        
        # Add edges
        self.workflow.add_edge("receive", "classify")
        self.workflow.add_edge("classify", "execute")
        self.workflow.add_edge("execute", "validate")
        self.workflow.add_edge("validate", "update")
        self.workflow.add_edge("update", END)
        
        # Set entry point
        self.workflow.set_entry_point("receive")
    
    def _receive_node(self, state: AgentState) -> AgentState:
        """Ticket receiver node"""
        state["current_agent"] = "ticket_receiver"
        state["messages"].append("Ticket received and validated")
        return state
    
    def _classify_node(self, state: AgentState) -> AgentState:
        """Ticket classifier node"""
        state["current_agent"] = "ticket_classifier"
        classification = self.ticket_classifier.classify_ticket(state["ticket"])
        state["classification"] = classification
        state["messages"].append(f"Ticket classified: {classification['middleware_type']} {classification['action']}")
        return state
    
    def _execute_node(self, state: AgentState) -> AgentState:
        """Ticket executor node"""
        state["current_agent"] = "ticket_executor"
        execution_result = self.ticket_executor.execute_playbook(
            state["ticket"], 
            state["classification"]
        )
        state["execution_result"] = execution_result
        state["messages"].append(f"Playbook executed: {execution_result['status']}")
        return state
    
    def _validate_node(self, state: AgentState) -> AgentState:
        """Ticket validator node"""
        state["current_agent"] = "ticket_validator"
        validation_report = self.ticket_validator.validate_execution(
            state["ticket"], 
            state["execution_result"]
        )
        state["validation_report"] = validation_report
        state["messages"].append(f"Validation completed: {validation_report['overall_status']}")
        return state
    
    def _update_node(self, state: AgentState) -> AgentState:
        """Ticket updater node"""
        state["current_agent"] = "ticket_updater"
        update_response = self.ticket_updater.update_ticket(
            state["ticket"], 
            state["validation_report"]
        )
        state["update_response"] = update_response
        state["messages"].append("ServiceNow ticket updated")
        return state
    
    def process_ticket(self, ticket_data: Dict[str, Any]) -> AgentState:
        """Process a ticket through the entire workflow"""
        try:
            if not ticket_data:
                raise ValueError("Empty ticket data received")
                
            print(f"Processing ticket: {ticket_data}")  # Debug logging
            
            # Initialize state
            initial_state = AgentState(
                ticket=self.ticket_receiver.receive_ticket(ticket_data),
                classification={},
                execution_result={},
                validation_report={},
                update_response={},
                messages=[],
                current_agent="",
                errors=[]
            )
            
            # Compile and run workflow
            app = self.workflow.compile()
            result = app.invoke(initial_state)

            return result
        except Exception as e:
            print(f"Workflow error: {str(e)}")
            raise