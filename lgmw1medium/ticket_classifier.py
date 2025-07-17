# ticket_classifier.py
from langchain_ollama import OllamaLLM
from typing import Dict, Any
import json
import re
from ticket_receiver import ServiceNowTicket

class TicketClassifier:
    def __init__(self):
        self.name = "ticket_classifier"
        self.llm = OllamaLLM(
            model="llama3",
            timeout=300,
            temperature=0.3,
            format="json"
        )
        # Template for consistent JSON output
        self.json_template = """{
            "middleware_type": "apache",
            "action": "install",
            "target_environment": "prod",
            "risk_level": "high",
            "playbook_required": "apache_install.yml",
            "estimated_duration": "30min"
        }"""
    
    def classify_ticket(self, ticket: ServiceNowTicket) -> Dict[str, Any]:
        """Classify ticket with multiple fallback strategies"""
        classification_prompt = f"""
        Analyze this ServiceNow ticket and return ONLY the JSON object with these exact fields:
        {self.json_template}

        Ticket Details:
        - ID: {ticket.ticket_id}
        - Category: {ticket.category}
        - Subcategory: {ticket.subcategory}
        - Description: {ticket.description}
        - CI Name: {ticket.ci_name}
        - Environment: {ticket.environment}

        Rules:
        1. Return ONLY the JSON object
        2. Do not include any explanations
        3. Use double quotes for all strings
        4. Remove all whitespace outside the JSON object
        """
        
        try:
            # First attempt with strict JSON format
            response = self.llm.invoke(classification_prompt)
            print(f"Initial LLM Response: {response}")
            
            # Multiple parsing strategies
            classification = self._parse_response(response)
            self._validate_classification(classification)
            
            print(f"Successful Classification: {classification}")
            return classification
            
        except Exception as e:
            print(f"Classification failed: {str(e)}")
            # Fallback to default values if parsing fails
            return self._get_fallback_classification(ticket)

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Multiple strategies to extract JSON from response"""
        strategies = [
            self._try_direct_json_parse,
            self._try_extract_json_with_regex,
            self._try_fix_json_format
        ]
        
        for strategy in strategies:
            try:
                return strategy(response)
            except:
                continue
                
        raise ValueError("All parsing strategies failed")

    def _try_direct_json_parse(self, response: str) -> Dict[str, Any]:
        """Try parsing response as direct JSON"""
        return json.loads(response.strip())

    def _try_extract_json_with_regex(self, response: str) -> Dict[str, Any]:
        """Extract JSON using regex patterns"""
        json_pattern = r'\{[\s\S]*\}'
        match = re.search(json_pattern, response)
        if not match:
            raise ValueError("No JSON found in response")
        return json.loads(match.group(0))

    def _try_fix_json_format(self, response: str) -> Dict[str, Any]:
        """Attempt to fix common JSON formatting issues"""
        fixed = response.strip()
        fixed = fixed.replace('\n', '').replace('\\', '')
        fixed = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', fixed)  # Remove control chars
        return json.loads(fixed)

    def _validate_classification(self, classification: Dict[str, Any]):
        """Validate classification structure"""
        required_fields = {
            "middleware_type": ["apache", "tomcat"],
            "action": ["install", "upgrade"],
            "target_environment": ["dev", "staging", "prod"],
            "risk_level": ["low", "medium", "high"],
            "playbook_required": ["apache_install.yml", "tomcat_upgrade.yml"],
            "estimated_duration": ["30min"]
        }
        
        for field, allowed in required_fields.items():
            if field not in classification:
                raise ValueError(f"Missing field: {field}")
            if classification[field].lower() not in allowed:
                raise ValueError(f"Invalid {field}: {classification[field]}")

    def _get_fallback_classification(self, ticket: ServiceNowTicket) -> Dict[str, Any]:
        """Provide fallback classification when parsing fails"""
        print("Using fallback classification")
        return {
            "middleware_type": "apache" if "apache" in ticket.description.lower() else "tomcat",
            "action": "install" if "install" in ticket.description.lower() else "upgrade",
            "target_environment": ticket.environment.lower(),
            "risk_level": "high" if ticket.priority.lower() == "high" else "medium",
            "playbook_required": "apache_install.yml" if "apache" in ticket.description.lower() else "tomcat_upgrade.yml",
            "estimated_duration": "30min"
        }