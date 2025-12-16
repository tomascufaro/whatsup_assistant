"""
WhatsApp service for handling incoming and outgoing messages.
Supports both Twilio and Meta WhatsApp Business API.
"""

import os
from typing import Dict, Any, Optional
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()


class WhatsAppService:
    """Service for handling WhatsApp messages via Twilio or Meta API."""
    
    def __init__(self):
        self.use_twilio = bool(os.getenv("TWILIO_ACCOUNT_SID"))
        self.use_meta = bool(os.getenv("META_ACCESS_TOKEN"))
        
        if self.use_twilio:
            self.twilio_client = Client(
                os.getenv("TWILIO_ACCOUNT_SID"),
                os.getenv("TWILIO_AUTH_TOKEN")
            )
            self.twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
        elif self.use_meta:
            self.meta_token = os.getenv("META_ACCESS_TOKEN")
            self.meta_verify_token = os.getenv("META_VERIFY_TOKEN")
    
    def parse_incoming_message(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse incoming webhook data from Twilio or Meta."""
        if self.use_twilio:
            return self._parse_twilio_message(data)
        elif self.use_meta:
            return self._parse_meta_message(data)
        else:
            return None
    
    def _parse_twilio_message(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Twilio webhook format."""
        if "Body" in data and "From" in data:
            return {
                "from": data["From"],
                "to": data.get("To", ""),
                "body": data["Body"],
                "message_id": data.get("MessageSid", ""),
                "provider": "twilio"
            }
        return None
    
    def _parse_meta_message(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Meta WhatsApp Business API webhook format."""
        try:
            entry = data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])
            
            if messages:
                message = messages[0]
                contacts = value.get("contacts", [{}])[0]
                return {
                    "from": message.get("from", ""),
                    "to": value.get("metadata", {}).get("phone_number_id", ""),
                    "body": message.get("text", {}).get("body", ""),
                    "message_id": message.get("id", ""),
                    "name": contacts.get("profile", {}).get("name", ""),
                    "provider": "meta"
                }
        except (KeyError, IndexError):
            pass
        
        return None
    
    async def send_message(self, to: str, body: str) -> bool:
        """Send a WhatsApp message."""
        try:
            if self.use_twilio:
                message = self.twilio_client.messages.create(
                    body=body,
                    from_=f"whatsapp:{self.twilio_number}",
                    to=f"whatsapp:{to}"
                )
                return bool(message.sid)
            
            elif self.use_meta:
                # Meta API implementation would go here
                # This requires the phone_number_id and proper API calls
                import requests
                
                phone_number_id = os.getenv("META_PHONE_NUMBER_ID")
                url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
                
                headers = {
                    "Authorization": f"Bearer {self.meta_token}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "messaging_product": "whatsapp",
                    "to": to,
                    "type": "text",
                    "text": {"body": body}
                }
                
                response = requests.post(url, json=payload, headers=headers)
                return response.status_code == 200
            
            return False
        
        except Exception as e:
            print(f"Error sending message: {e}")
            return False

