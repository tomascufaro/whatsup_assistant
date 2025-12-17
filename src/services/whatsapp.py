"""
WhatsApp service for handling outbound messages via Twilio.
Note: Inbound messages are handled directly in main.py via TwiML.
"""

import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()


class WhatsAppService:
    """Service for sending WhatsApp messages via Twilio REST API."""

    def __init__(self):
        self.twilio_client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        self.twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
    
    async def send_message(self, to: str, body: str) -> bool:
        """Send a WhatsApp message via Twilio REST API (for proactive messages)."""
        try:
            message = self.twilio_client.messages.create(
                body=body,
                from_=f"whatsapp:{self.twilio_number}",
                to=to if to.startswith("whatsapp:") else f"whatsapp:{to}"
            )
            return bool(message.sid)
        except Exception as e:
            print(f"Error sending message: {e}")
            return False

