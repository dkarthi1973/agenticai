# mock_data.py

# ServiceNow Ticket Examples
MOCK_TICKETS = [
    {
        "ticket_id": "INC0012345",
        "priority": "High",
        "category": "Infrastructure",
        "subcategory": "Middleware",
        "description": "Install Apache HTTP Server 2.4.x on production web server",
        "ci_name": "web-server-prod-01",
        "environment": "production",
        "requested_by": "john.doe@company.com"
    },
    {
        "ticket_id": "INC0012346",
        "priority": "Medium",
        "category": "Infrastructure",
        "subcategory": "Application Server",
        "description": "Upgrade Tomcat from 9.0.x to 10.1.x on staging environment",
        "ci_name": "app-server-staging-02",
        "environment": "staging",
        "requested_by": "jane.smith@company.com"
    }
]

# Ansible Playbook Examples
MOCK_PLAYBOOKS = {
    "apache_install.yml": """
---
- name: Install Apache HTTP Server
  hosts: "{{ target_host }}"
  become: yes
  tasks:
    - name: Install Apache
      yum:
        name: httpd
        state: present
    - name: Start Apache service
      service:
        name: httpd
        state: started
        enabled: yes
    - name: Configure firewall
      firewalld:
        service: http
        state: enabled
        permanent: yes
""",
    "tomcat_upgrade.yml": """
---
- name: Upgrade Tomcat
  hosts: "{{ target_host }}"
  become: yes
  tasks:
    - name: Stop Tomcat service
      service:
        name: tomcat
        state: stopped
    - name: Download new Tomcat version
      get_url:
        url: "https://archive.apache.org/dist/tomcat/tomcat-10/v10.1.15/bin/apache-tomcat-10.1.15.tar.gz"
        dest: /tmp/tomcat.tar.gz
    - name: Extract Tomcat
      unarchive:
        src: /tmp/tomcat.tar.gz
        dest: /opt/
        remote_src: yes
    - name: Start Tomcat service
      service:
        name: tomcat
        state: started
"""
}