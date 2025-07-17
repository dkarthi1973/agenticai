Multi-Agent Middleware Installation System
Overview

This system automates the processing of ServiceNow tickets for middleware installation/upgrade tasks using a multi-agent workflow. The system consists of several specialized agents that handle different stages of the ticket processing pipeline.
Key Components
Agents

    Ticket Receiver - Validates and structures incoming ServiceNow tickets

    Ticket Classifier - Uses LLM to classify tickets and determine required actions

    Ticket Executor - Executes Ansible playbooks for middleware operations

    Ticket Validator - Validates the execution results

    Ticket Updater - Updates the ServiceNow ticket with results

Main Files

    main.py: FastAPI application serving as the system's entry point

    workflow.py: Orchestrates the multi-agent workflow

    agent_state.py: Defines the shared state structure for agents

    streamlit_app.py: Provides a web interface for testing the system

Installation

    Clone the repository(go to sub folder try simple and then try another one same as simple with log and db integration)

    Install dependencies:
    bash

    pip install fastapi uvicorn langgraph streamlit requests pydantic langchain_ollama

    Ensure Ollama is running with required models (llama3, mistral)

Usage
API Endpoints

    POST /process-ticket: Process a ServiceNow ticket

    GET /health: Health check endpoint

Streamlit UI

Run the web interface:
bash

streamlit run streamlit_app.py

Sample Ticket Data

Example tickets are provided in mock_data.py:
python

{
    "ticket_id": "INC0012345",
    "priority": "High",
    "category": "Infrastructure",
    "subcategory": "Middleware",
    "description": "Install Apache HTTP Server 2.4.x on production web server",
    "ci_name": "web-server-prod-01",
    "environment": "production",
    "requested_by": "john.doe@company.com"
}

Workflow

    Receive and validate ticket

    Classify ticket (determine middleware type, action, playbook)

    Execute appropriate Ansible playbook

    Validate installation/upgrade results

    Update ServiceNow ticket with results

Configuration

    Modify mock_data.py to add more sample tickets or playbooks

    Adjust LLM parameters in ticket_classifier.py and ticket_validator.py

License

[MIT License] - Free for use and modification
