# streamlit_app.py
import streamlit as st
import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
TIMEOUT = 120  # seconds
POLL_INTERVAL = 5  # seconds

st.set_page_config(page_title="Middleware Installation System", layout="wide")
st.title("🤖 Multi-Agent Middleware Installation System")

# Mock Data
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
    ticket_id = st.text_input("Ticket ID*", value=mock_ticket["ticket_id"], 
                            help="Unique incident ticket ID (e.g. INC0012345)")
    priority = st.selectbox("Priority*", ["Low", "Medium", "High", "Critical"], 
                          index=2, help="Select the priority level")
    category = st.text_input("Category*", value=mock_ticket["category"],
                           help="Ticket category (e.g. Infrastructure)")
    subcategory = st.text_input("Subcategory*", value=mock_ticket["subcategory"],
                              help="Ticket subcategory (e.g. Middleware)")
    description = st.text_area("Description*", value=mock_ticket["description"],
                             help="Detailed description of the request")
    ci_name = st.text_input("CI Name*", value=mock_ticket["ci_name"],
                          help="Configuration item name (e.g. web-server-prod-01)")
    environment = st.selectbox("Environment*", ["dev", "staging", "production"], 
                             index=2, help="Target environment")
    requested_by = st.text_input("Requested By*", value=mock_ticket["requested_by"],
                               help="Requester's email address")

    st.markdown("*Required fields")

with col2:
    st.subheader("🚀 Agent Execution")
    
    if st.button("Process Ticket", type="primary", key="process_ticket"):
        if not ticket_id:
            st.error("Ticket ID is required!")
            st.stop()
            
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
        
        # Start processing
        with st.spinner("Starting ticket processing..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/process-ticket",
                    json={"ticket_data": ticket_data},
                    timeout=5
                )
                
                if response.status_code == 200:
                    st.success("✅ Processing started successfully!")
                    start_response = response.json()
                    
                    # Poll for status updates
                    status_placeholder = st.empty()
                    progress_bar = st.progress(0)
                    status_details = st.empty()
                    
                    for i in range(int(TIMEOUT/POLL_INTERVAL)):
                        status_response = requests.get(
                            f"{BACKEND_URL}/ticket-status/{ticket_id}",
                            timeout=5
                        )
                        
                        if status_response.status_code == 200:
                            status = status_response.json()
                            progress = min(95, (i+1)*5)  # Cap progress at 95%
                            progress_bar.progress(progress)
                            
                            if status["status"] == "completed":
                                progress_bar.progress(100)
                                status_placeholder.success("✅ Processing completed!")
                                # Get full results
                                incident = requests.get(
                                    f"{BACKEND_URL}/incident/{ticket_id}",
                                    timeout=5
                                ).json()
                                
                                # Display results
                                st.subheader("📊 Execution Flow")
                                for msg in incident.get("messages", []):
                                    st.write(f"- {msg}")
                                
                                st.success(f"🎉 Final status: {incident.get('status')}")
                                break
                            elif status["status"] == "failed":
                                progress_bar.progress(100)
                                status_placeholder.error("❌ Processing failed")
                                st.error(incident.get("error", "Unknown error"))
                                break
                            else:
                                status_placeholder.info(f"🔄 Processing... ({status['status']})")
                                status_details.text(f"Last update: {status['last_update']}")
                        
                        time.sleep(POLL_INTERVAL)
                    else:
                        progress_bar.progress(100)
                        status_placeholder.warning("⚠️ Processing is taking longer than expected")
                
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.Timeout:
                st.error("Request timed out. Please check the backend service.")
            except Exception as e:
                st.error(f"Connection error: {str(e)}")

# Agent Status Dashboard
st.subheader("🤖 Agent Status Dashboard")

try:
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
            status_icon = "🟢" if agent["status"] == "Ready" else "🟡" if agent["status"] == "Processing" else "🔴"
            st.metric(
                label=f"{agent['icon']} {agent['name']}", 
                value=f"{status_icon} {agent['status']}"
            )
except Exception as e:
    st.error(f"Error loading agent status: {str(e)}")

# Status Check Section
with st.expander("🔍 Check Incident Status"):
    check_id = st.text_input("Enter Ticket ID to check status", key="check_ticket_id")
    if st.button("Check Status", key="check_status"):
        if not check_id:
            st.warning("Please enter a Ticket ID")
        else:
            try:
                response = requests.get(
                    f"{BACKEND_URL}/incident/{check_id}",
                    timeout=5
                )
                if response.status_code == 200:
                    incident = response.json()
                    st.success(f"Found incident {check_id}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Status", incident.get("status", "unknown"))
                        st.metric("Priority", incident.get("priority", "unknown"))
                    with col2:
                        st.metric("Environment", incident.get("environment", "unknown"))
                        st.metric("Last Updated", incident.get("updated_at", "unknown"))
                    
                    st.json(incident)
                elif response.status_code == 404:
                    st.info(f"Incident {check_id} not found")
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Connection error: {str(e)}")

st.subheader("📂 All Tickets in System")

# Add filters/controls
col1, col2, col3 = st.columns(3)
with col1:
    filter_status = st.selectbox("Filter by Status", 
                               ["All", "received", "processing", "completed", "failed"])
with col2:
    filter_priority = st.selectbox("Filter by Priority",
                                 ["All", "Low", "Medium", "High", "Critical"])
with col3:
    limit_tickets = st.slider("Max tickets to show", 5, 100, 20)

if st.button("Refresh Ticket List", key="refresh_tickets"):
    st.rerun()

try:
    # Get all incidents from backend
    response = requests.get(
        f"{BACKEND_URL}/all-incidents",
        timeout=5
    )
    
    if response.status_code == 200:
        all_tickets = response.json()
        
        # Apply filters
        if filter_status != "All":
            all_tickets = [t for t in all_tickets if t.get("status") == filter_status]
        if filter_priority != "All":
            all_tickets = [t for t in all_tickets if t.get("priority") == filter_priority]
        
        # Limit number of tickets
        all_tickets = all_tickets[:limit_tickets]
        
        if not all_tickets:
            st.info("No tickets match the current filters")
        else:
            # Display as expandable cards
            for ticket in all_tickets:
                with st.expander(f"📌 {ticket['ticket_id']} - {ticket['status'].title()}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Priority", ticket.get("priority", "unknown"))
                        st.metric("Environment", ticket.get("environment", "unknown"))
                    with col2:
                        st.metric("Status", ticket.get("status", "unknown"))
                        st.metric("Last Updated", ticket.get("updated_at", "unknown"))
                    
                    st.text(f"Description: {ticket.get('description', '')}")
                    
                    if st.button(f"View Details", key=f"view_{ticket['ticket_id']}"):
                        st.json(ticket)
    else:
        st.error(f"Error fetching tickets: {response.status_code} - {response.text}")
except Exception as e:
    st.error(f"Failed to load tickets: {str(e)}")



# Add some styling
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
    }
    .stTextInput>div>div>input {
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)