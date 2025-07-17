# ticket_executor.py
import subprocess
import json
from typing import Dict, Any
from ticket_receiver import ServiceNowTicket  # Add this import

class TicketExecutor:
    def __init__(self):
        self.name = "ticket_executor"
        self.playbook_path = "./playbooks/"
    
    def execute_playbook(self, ticket: ServiceNowTicket, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Execute appropriate Ansible playbook"""
        try:
            playbook_name = classification["playbook_required"]
            if playbook_name not in ["apache_install.yml", "tomcat_upgrade.yml"]:
                raise ValueError(f"Invalid playbook: {playbook_name}")
                
            playbook_path = f"{self.playbook_path}{playbook_name}"
            execution_result = self._mock_ansible_execution(playbook_path, ticket)
            
            print(f"⚙️ Executing playbook {playbook_name} for ticket {ticket.ticket_id}")
            return execution_result
        except Exception as e:
            print(f"Execution error: {str(e)}")
            raise ValueError(f"Playbook execution failed: {str(e)}")
    
    def _mock_ansible_execution(self, playbook_path: str, ticket: ServiceNowTicket) -> Dict[str, Any]:
        """Mock Ansible playbook execution"""
        return {
            "status": "success",
            "playbook": playbook_path,
            "target_host": ticket.ci_name,
            "execution_time": "15min",
            "tasks_completed": 5,
            "tasks_failed": 0,
            "logs": "Mock execution completed successfully"
        }