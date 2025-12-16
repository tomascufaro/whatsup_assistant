"""
Database tool for reading/writing to CSV file.
"""

import os
import pandas as pd
from typing import Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


CSV_PATH = os.path.join(os.path.dirname(__file__), '../../data/clients.csv')


class DatabaseInput(BaseModel):
    """Input schema for database operations."""
    action: str = Field(description="Action: 'get', 'add', 'update', or 'list'")
    name: Optional[str] = Field(default=None, description="Client name")
    email: Optional[str] = Field(default=None, description="Client email")
    phone: Optional[str] = Field(default=None, description="Client phone")
    notes: Optional[str] = Field(default=None, description="Client notes")


class DatabaseTool(BaseTool):
    """Tool for managing client database (CSV file)."""
    
    name = "client_database"
    description = "Manage client information in the database. Can get, add, update, or list clients."
    args_schema = DatabaseInput
    
    def _ensure_csv_exists(self):
        """Ensure the CSV file exists with proper headers."""
        if not os.path.exists(CSV_PATH):
            os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
            df = pd.DataFrame(columns=['name', 'email', 'phone', 'notes'])
            df.to_csv(CSV_PATH, index=False)
    
    def _run(self, action: str, name: Optional[str] = None,
             email: Optional[str] = None, phone: Optional[str] = None,
             notes: Optional[str] = None) -> str:
        """Execute database operation."""
        try:
            self._ensure_csv_exists()
            df = pd.read_csv(CSV_PATH)
            
            if action == "get":
                if not name:
                    return "Error: name is required for 'get' action"
                client = df[df['name'].str.lower() == name.lower()]
                if client.empty:
                    return f"Client '{name}' not found"
                return client.to_dict('records')[0]
            
            elif action == "add":
                if not name or not email:
                    return "Error: name and email are required for 'add' action"
                
                new_row = {
                    'name': name,
                    'email': email,
                    'phone': phone or '',
                    'notes': notes or ''
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv(CSV_PATH, index=False)
                return f"Client '{name}' added successfully"
            
            elif action == "update":
                if not name:
                    return "Error: name is required for 'update' action"
                
                mask = df['name'].str.lower() == name.lower()
                if not mask.any():
                    return f"Client '{name}' not found"
                
                if email:
                    df.loc[mask, 'email'] = email
                if phone:
                    df.loc[mask, 'phone'] = phone
                if notes:
                    df.loc[mask, 'notes'] = notes
                
                df.to_csv(CSV_PATH, index=False)
                return f"Client '{name}' updated successfully"
            
            elif action == "list":
                if df.empty:
                    return "No clients in database"
                return f"Found {len(df)} clients in database"
            
            else:
                return f"Unknown action: {action}"
        
        except Exception as e:
            return f"Error: {str(e)}"

