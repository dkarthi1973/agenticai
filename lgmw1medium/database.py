# database.py
import sqlite3
from datetime import datetime
from typing import Dict, Any, List
import json
from pathlib import Path
import logging

class IncidentDB:
    def __init__(self, db_path: str = "incidents.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__ + ".IncidentDB")
        self._init_db()
        
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Create incidents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT NOT NULL UNIQUE,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    execution_result TEXT NOT NULL,
                    validation_report TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    messages TEXT NOT NULL,
                    environment TEXT NOT NULL DEFAULT 'production',
                    error TEXT
                )
            """)
            # Create audit log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details TEXT NOT NULL
                )
            """)
            conn.commit()

    def create_incident(self, ticket_data: Dict[str, Any]) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO incidents (
                    ticket_id, priority, status, classification,
                    execution_result, validation_report, created_at,
                    updated_at, messages, environment
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticket_data["ticket_id"],
                ticket_data.get("priority", "medium"),
                "received",
                "{}", 
                "{}", 
                "{}",
                timestamp, 
                timestamp, 
                "[]",
                ticket_data.get("environment", "production")  # Added this missing value
            ))
            conn.commit()
            return cursor.lastrowid

    def update_incident(self, ticket_id: str, updates: Dict[str, Any]):
        """Update incident with proper parameter binding"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # First check if column exists
                cursor.execute("PRAGMA table_info(incidents)")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Only include updates for columns that exist
                valid_updates = {k: v for k, v in updates.items() if k in columns}
                
                if not valid_updates:
                    return
                    
                set_clause = ", ".join(f"{k} = ?" for k in valid_updates.keys())
                values = list(valid_updates.values())
                
                # Add updated_at and ticket_id to values
                values.append(datetime.now().isoformat())
                values.append(ticket_id)
                
                query = f"""
                    UPDATE incidents 
                    SET {set_clause}, updated_at = ?
                    WHERE ticket_id = ?
                """
                cursor.execute(query, values)
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error updating incident: {str(e)}")
            raise

    def log_audit(self, ticket_id: str, action: str, agent: str, details: str):
        """Log audit entry with proper parameter binding"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_log (
                    ticket_id, action, agent, timestamp, details
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                ticket_id, action, agent, 
                datetime.now().isoformat(), details
            ))

    def get_all_incidents(self, limit: int = 100, skip: int = 0) -> list[dict]:
        """Get all incidents from database with pagination"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        ticket_id, priority, status, 
                        created_at, updated_at, environment
                    FROM incidents 
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, skip))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Database error in get_all_incidents: {str(e)}")
            raise ValueError("Error retrieving incidents from database") 
    
    def get_incident(self, ticket_id: str) -> Dict[str, Any]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM incidents WHERE ticket_id = ?
                """, (ticket_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                # Convert SQLite Row to dict and decode JSON fields
                result = dict(row)
                for json_field in ['classification', 'execution_result', 
                                'validation_report', 'messages']:
                    if result.get(json_field):
                        result[json_field] = json.loads(result[json_field])
                return result
        except Exception as e:
            print(f"Database error: {str(e)}")
            return None