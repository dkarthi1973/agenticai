# workflow.py (updated with database fixes)
from langgraph.graph import StateGraph, END
from typing import Dict, Any, Optional
from agent_state import AgentState
from ticket_receiver import TicketReceiver, ServiceNowTicket
from ticket_classifier import TicketClassifier
from ticket_executor import TicketExecutor
from ticket_validator import TicketValidator
from ticket_updater import TicketUpdater
from database import IncidentDB
from logger import WorkflowLogger
import json
from datetime import datetime
import sqlite3

class MiddlewareInstallationWorkflow:
    def __init__(self, db: Optional[IncidentDB] = None, logger: Optional[WorkflowLogger] = None):
        self.ticket_receiver = TicketReceiver()
        self.ticket_classifier = TicketClassifier()
        self.ticket_executor = TicketExecutor()
        self.ticket_validator = TicketValidator()
        self.ticket_updater = TicketUpdater()
        
        # Initialize database and logger with defaults if not provided
        self.db = db if db else IncidentDB()
        self.logger = logger if logger else WorkflowLogger()
        
        # Create the workflow graph
        self.workflow = StateGraph(AgentState)
        self._build_workflow()
    
    def _build_workflow(self):
        """Build the multi-agent workflow graph"""
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
        """Ticket receiver node with logging"""
        try:
            state["current_agent"] = "ticket_receiver"
            state["messages"].append("Ticket received and validated")
            
            # Log to database
            ticket_id = state["ticket"].ticket_id
            self._safe_db_operation(
                self.db.create_incident,
                state["ticket"].dict()
            )
            self._safe_db_operation(
                self.db.log_audit,
                ticket_id,
                "ticket_received",
                "ticket_receiver",
                "Ticket received and validated"
            )
            self.logger.log_incident(
                ticket_id,
                "received",
                state["ticket"].dict()
            )
            
            return state
        except Exception as e:
            self._handle_error(state, "receive", str(e))
            raise
    
    def _classify_node(self, state: AgentState) -> AgentState:
        """Ticket classifier node with logging"""
        try:
            state["current_agent"] = "ticket_classifier"
            classification = self.ticket_classifier.classify_ticket(state["ticket"])
            state["classification"] = classification
            
            # Update database
            ticket_id = state["ticket"].ticket_id
            self._safe_db_operation(
                self.db.update_incident,
                ticket_id,
                {
                    "classification": json.dumps(classification),
                    "status": "classified"
                }
            )
            self._safe_db_operation(
                self.db.log_audit,
                ticket_id,
                "ticket_classified",
                "ticket_classifier",
                json.dumps(classification)
            )
            
            state["messages"].append(
                f"Ticket classified: {classification['middleware_type']} {classification['action']}"
            )
            return state
        except Exception as e:
            self._handle_error(state, "classify", str(e))
            raise
    
    def _execute_node(self, state: AgentState) -> AgentState:
        """Ticket executor node with logging"""
        try:
            state["current_agent"] = "ticket_executor"
            execution_result = self.ticket_executor.execute_playbook(
                state["ticket"], 
                state["classification"]
            )
            state["execution_result"] = execution_result
            
            # Update database
            ticket_id = state["ticket"].ticket_id
            self._safe_db_operation(
                self.db.update_incident,
                ticket_id,
                {
                    "execution_result": json.dumps(execution_result),
                    "status": "executed"
                }
            )
            self._safe_db_operation(
                self.db.log_audit,
                ticket_id,
                "playbook_executed",
                "ticket_executor",
                json.dumps({
                    "playbook": execution_result.get("playbook"),
                    "status": execution_result.get("status")
                })
            )
            
            state["messages"].append(f"Playbook executed: {execution_result['status']}")
            return state
        except Exception as e:
            self._handle_error(state, "execute", str(e))
            raise
    
    def _validate_node(self, state: AgentState) -> AgentState:
        """Ticket validator node with logging"""
        try:
            state["current_agent"] = "ticket_validator"
            validation_report = self.ticket_validator.validate_execution(
                state["ticket"], 
                state["execution_result"]
            )
            state["validation_report"] = validation_report
            
            # Update database
            ticket_id = state["ticket"].ticket_id
            self._safe_db_operation(
                self.db.update_incident,
                ticket_id,
                {
                    "validation_report": json.dumps(validation_report),
                    "status": "validated"
                }
            )
            self._safe_db_operation(
                self.db.log_audit,
                ticket_id,
                "execution_validated",
                "ticket_validator",
                json.dumps({
                    "overall_status": validation_report["overall_status"],
                    "checks": validation_report["checks"]
                })
            )
            
            state["messages"].append(
                f"Validation completed: {validation_report['overall_status']}"
            )
            return state
        except Exception as e:
            self._handle_error(state, "validate", str(e))
            raise
    
    def _update_node(self, state: AgentState) -> AgentState:
        """Ticket updater node with logging"""
        try:
            state["current_agent"] = "ticket_updater"
            update_response = self.ticket_updater.update_ticket(
                state["ticket"], 
                state["validation_report"]
            )
            state["update_response"] = update_response
            
            # Final update
            ticket_id = state["ticket"].ticket_id
            final_status = state["validation_report"]["overall_status"]
            self._safe_db_operation(
                self.db.update_incident,
                ticket_id,
                {
                    "status": final_status,
                    "messages": json.dumps(state["messages"])
                }
            )
            self._safe_db_operation(
                self.db.log_audit,
                ticket_id,
                "ticket_updated",
                "ticket_updater",
                json.dumps({
                    "final_status": final_status,
                    "update_response": update_response
                })
            )
            
            state["messages"].append("ServiceNow ticket updated")
            return state
        except Exception as e:
            self._handle_error(state, "update", str(e))
            raise
    
    def _safe_db_operation(self, operation, *args, **kwargs):
        """Wrapper for database operations with error handling"""
        try:
            return operation(*args, **kwargs)
        except sqlite3.Error as e:
            self.logger.log(
                "ERROR",
                f"Database operation failed: {str(e)}",
                {"operation": operation.__name__}
            )
            raise ValueError(f"Database error: {str(e)}")
    
    def _handle_error(self, state: AgentState, agent: str, error: str):
        """Centralized error handling with logging"""
        ticket_id = state["ticket"].ticket_id if "ticket" in state else "unknown"
        
        error_msg = f"{agent} failed: {error}"
        state.setdefault("errors", []).append(error_msg)
        
        # Log error to database
        try:
            self._safe_db_operation(
                self.db.log_audit,
                ticket_id,
                f"{agent}_error",
                agent,
                error_msg
            )
        except:
            pass  # Prevent recursive errors
            
        self.logger.log(
            "ERROR",
            error_msg,
            {"ticket_id": ticket_id, "agent": agent}
        )
    
    def process_ticket(self, ticket_data: Dict[str, Any]) -> AgentState:
        """Process a ticket through the entire workflow with logging"""
        try:
            if not ticket_data:
                raise ValueError("Empty ticket data received")
                
            self.logger.log(
                "INFO", 
                f"Processing ticket: {ticket_data.get('ticket_id', 'unknown')}",
                {"ticket_data": ticket_data}
            )
            
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
            
            # Log completion
            self.logger.log(
                "INFO",
                f"Ticket {result['ticket'].ticket_id} processed with status: "
                f"{result['validation_report']['overall_status']}",
                {
                    "execution_time": result["execution_result"]["execution_time"],
                    "messages": result["messages"]
                }
            )
            
            return result
        except Exception as e:
            self._handle_error(
                initial_state if 'initial_state' in locals() else {},
                "workflow",
                str(e)
            )
            raise
    
    def get_incident_history(self, ticket_id: str) -> Dict[str, Any]:
        """Get complete incident history from database"""
        try:
            # Get incident details
            incident = self._safe_db_operation(
                self.db.get_incident,
                ticket_id
            )
            if not incident:
                return {"error": "Incident not found"}
            
            # Get audit logs
            with self.db.conn:
                cursor = self.db.conn.cursor()
                cursor.execute(
                    "SELECT * FROM audit_log WHERE ticket_id = ? ORDER BY timestamp DESC",
                    (ticket_id,)
                )
                logs = [dict(row) for row in cursor.fetchall()]
            
            return {
                "incident": incident,
                "audit_logs": logs
            }
        except Exception as e:
            self.logger.log(
                "ERROR",
                f"Failed to get history for {ticket_id}: {str(e)}"
            )
            return {"error": str(e)}