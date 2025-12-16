"""
Email handling tool (Gmail integration).
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
import base64
from email.mime.text import MIMEText


SCOPES = ['https://www.googleapis.com/auth/gmail.send', 
          'https://www.googleapis.com/auth/gmail.readonly']


class EmailInput(BaseModel):
    """Input schema for email operations."""
    action: str = Field(description="Action: 'send' or 'read'")
    to: Optional[str] = Field(default=None, description="Recipient email (for send)")
    subject: Optional[str] = Field(default=None, description="Email subject (for send)")
    body: Optional[str] = Field(default=None, description="Email body (for send)")
    query: Optional[str] = Field(default=None, description="Search query (for read)")


class EmailTool(BaseTool):
    """Tool for sending and reading emails via Gmail."""
    
    name = "gmail"
    description = "Send emails or read emails from Gmail. Use 'send' to send an email, 'read' to search for emails."
    args_schema = EmailInput
    
    def __init__(self):
        super().__init__()
        self.service = self._get_gmail_service()
    
    def _get_gmail_service(self):
        """Get authenticated Gmail service."""
        creds = None
        
        if os.path.exists('gmail_token.pickle'):
            with open('gmail_token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('gmail_token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        return build('gmail', 'v1', credentials=creds)
    
    def _run(self, action: str, to: Optional[str] = None,
             subject: Optional[str] = None, body: Optional[str] = None,
             query: Optional[str] = None) -> str:
        """Execute email operation."""
        try:
            if action == "send":
                message = MIMEText(body)
                message['to'] = to
                message['subject'] = subject
                
                raw_message = base64.urlsafe_b64encode(
                    message.as_bytes()).decode()
                
                send_message = {'raw': raw_message}
                result = self.service.users().messages().send(
                    userId='me', body=send_message).execute()
                
                return f"Email sent successfully. Message ID: {result['id']}"
            
            elif action == "read":
                results = self.service.users().messages().list(
                    userId='me', q=query, maxResults=5).execute()
                messages = results.get('messages', [])
                return f"Found {len(messages)} emails matching query"
            
            else:
                return f"Unknown action: {action}"
        
        except Exception as e:
            return f"Error: {str(e)}"

