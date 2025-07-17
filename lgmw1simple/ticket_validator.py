# ticket_validator.py
from typing import Dict, Any
from langchain_ollama import OllamaLLM  # Updated import
from ticket_receiver import ServiceNowTicket

class TicketValidator:
    def __init__(self):
        self.name = "ticket_validator"
        self.llm = OllamaLLM(
            model="mistral",
            timeout=300,  # Set timeout to 300 seconds
            temperature=0.3
        )
    
    def validate_execution(self, ticket: ServiceNowTicket, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate middleware installation/upgrade"""
        
        validation_checks = {
            "service_status": self._check_service_status(ticket.ci_name),
            "port_connectivity": self._check_port_connectivity(ticket.ci_name),
            "configuration_valid": self._validate_configuration(ticket.ci_name),
            "logs_analysis": self._analyze_logs(execution_result["logs"])
        }
        
        overall_status = "success" if all(validation_checks.values()) else "failed"
        
        validation_report = {
            "ticket_id": ticket.ticket_id,
            "overall_status": overall_status,
            "checks": validation_checks,
            "validation_time": "5min",
            "recommendations": self._generate_recommendations(validation_checks)
        }
        
        print(f"✅ Validation completed for ticket {ticket.ticket_id}: {overall_status}")
        return validation_report
    
    def _check_service_status(self, host: str) -> bool:
        """Mock service status check"""
        return True
    
    def _check_port_connectivity(self, host: str) -> bool:
        """Mock port connectivity check"""
        return True
    
    def _validate_configuration(self, host: str) -> bool:
        """Mock configuration validation"""
        return True
    
    def _analyze_logs(self, logs: str) -> bool:
        """Use LLM to analyze execution logs"""
        analysis_prompt = f"""
        Analyze these execution logs and determine if the installation/upgrade was successful:
        
        Logs: {logs}
        
        Return only 'true' if successful, 'false' if failed.
        """
        
        response = self.llm.invoke(analysis_prompt)  # Updated method call
        return response.strip().lower() == "true"
    
    def _generate_recommendations(self, checks: Dict[str, bool]) -> str:
        """Generate recommendations based on validation results"""
        if all(checks.values()):
            return "All checks passed. System is ready for production use."
        else:
            failed_checks = [check for check, status in checks.items() if not status]
            return f"Failed checks: {', '.join(failed_checks)}. Manual intervention required."