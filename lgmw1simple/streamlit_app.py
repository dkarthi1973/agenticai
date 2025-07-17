# streamlit_app.py
import streamlit as st
import requests
import json
from datetime import datetime

st.title("🤖 Multi-Agent Middleware Installation System")

# Mock ServiceNow ticket data
mock_ticket = {
    "ticket_id": "INC0012345",
    "priority": "High",
    "category": "Infrastructure",
    "subcategory": "Middleware",
    "description": "Install Apache HTTP Server 2.4.x on production web server",
    "ci_name": "web-server-prod-01",
    "environment": "production",
    "requested_by": "john.doe@company.com"
}

# UI Layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 ServiceNow Ticket")
    
    # Editable ticket form
    ticket_id = st.text_input("Ticket ID", value=mock_ticket["ticket_id"])
    priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"], 
                           index=2)
    category = st.text_input("Category", value=mock_ticket["category"])
    subcategory = st.text_input("Subcategory", value=mock_ticket["subcategory"])
    description = st.text_area("Description", value=mock_ticket["description"])
    ci_name = st.text_input("CI Name", value=mock_ticket["ci_name"])
    environment = st.selectbox("Environment", ["dev", "staging", "production"], 
                              index=2)
    requested_by = st.text_input("Requested By", value=mock_ticket["requested_by"])

with col2:
    st.subheader("🚀 Agent Execution")
    
    if st.button("Process Ticket", type="primary"):
        # Prepare ticket data
        ticket_data = {
            "ticket_id": ticket_id,
            "priority": priority,
            "category": category,
            "subcategory": subcategory,
            "description": description,
            "ci_name": ci_name,
            "environment": environment,
            "requested_by": requested_by
        }
        
        # Show processing status
        with st.spinner("Processing ticket through multi-agent system..."):
            try:
                # Call FastAPI endpoint
                response = requests.post(
                    "http://localhost:8000/process-ticket",
                    json={"ticket_data": ticket_data},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Display results
                    st.success(f"✅ Ticket {result['ticket_id']} processed successfully!")
                    
                    # Show execution flow
                    st.subheader("📊 Execution Flow")
                    for i, message in enumerate(result["messages"], 1):
                        st.write(f"{i}. {message}")
                    
                    # Show final status
                    if result["final_status"] == "success":
                        st.success(f"🎉 Middleware installation completed in {result['execution_time']}")
                    else:
                        st.error("❌ Middleware installation failed")
                        
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
                    
            except Exception as e:
                st.error(f"Connection error: {str(e)}")

# Agent Status Dashboard
st.subheader("🤖 Agent Status Dashboard")

agents = [
    {"name": "Ticket Receiver", "status": "Ready", "icon": "📥"},
    {"name": "Ticket Classifier", "status": "Ready", "icon": "🔍"},
    {"name": "Ticket Executor", "status": "Ready", "icon": "⚙️"},
    {"name": "Ticket Validator", "status": "Ready", "icon": "✅"},
    {"name": "Ticket Updater", "status": "Ready", "icon": "📝"}
]

cols = st.columns(len(agents))
for i, agent in enumerate(agents):
    with cols[i]:
        st.metric(
            label=f"{agent['icon']} {agent['name']}", 
            value=agent['status']
        )