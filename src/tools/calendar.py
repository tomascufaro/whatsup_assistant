"""
Google Calendar integration tool.
"""

import os
from typing import Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import pickle


SCOPES = ['https://www.googleapis.com/auth/calendar']


class CalendarInput(BaseModel):
    """Input schema for calendar operations."""
    action: str = Field(description="Action to perform: 'create', 'list', 'get'")
    title: Optional[str] = Field(default=None, description="Event title (for create)")
    start_time: Optional[str] = Field(default=None, description="Start time in ISO format")
    end_time: Optional[str] = Field(default=None, description="End time in ISO format")
    event_id: Optional[str] = Field(default=None, description="Event ID (for get)")


class CalendarTool(BaseTool):
    """Tool for interacting with Google Calendar."""
    
    name = "google_calendar"
    description = "Manage Google Calendar events. Can create, list, or get calendar events."
    args_schema = CalendarInput
    
    def __init__(self):
        super().__init__()
        self.service = self._get_calendar_service()
    
    def _get_calendar_service(self):
        """Get authenticated Google Calendar service."""
        creds = None
        
        # Load existing credentials
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        return build('calendar', 'v3', credentials=creds)
    
    def _run(self, action: str, title: Optional[str] = None, 
             start_time: Optional[str] = None, end_time: Optional[str] = None,
             event_id: Optional[str] = None) -> str:
        """Execute calendar operation."""
        try:
            if action == "create":
                event = {
                    'summary': title,
                    'start': {'dateTime': start_time, 'timeZone': 'UTC'},
                    'end': {'dateTime': end_time, 'timeZone': 'UTC'},
                }
                event = self.service.events().insert(
                    calendarId='primary', body=event).execute()
                return f"Event created: {event.get('htmlLink')}"
            
            elif action == "list":
                events_result = self.service.events().list(
                    calendarId='primary',
                    maxResults=10,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                events = events_result.get('items', [])
                return f"Found {len(events)} upcoming events"
            
            elif action == "get":
                event = self.service.events().get(
                    calendarId='primary', eventId=event_id).execute()
                return f"Event: {event.get('summary')}"
            
            else:
                return f"Unknown action: {action}"
        
        except Exception as e:
            return f"Error: {str(e)}"

