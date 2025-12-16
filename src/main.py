"""
Main entry point for the WhatsApp Assistant application.
Handles incoming webhooks from WhatsApp (Twilio/Meta).
"""

from fastapi import FastAPI, Request
from fastapi.responses import Response
import os
from dotenv import load_dotenv

from services.whatsapp import WhatsAppService
from agent.core import Agent

load_dotenv()

app = FastAPI(title="WhatsApp Assistant")

whatsapp_service = WhatsAppService()
agent = Agent()


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """Handle incoming WhatsApp messages via webhook."""
    data = await request.json()
    
    # Process incoming message
    message = whatsapp_service.parse_incoming_message(data)
    
    if message:
        # Get AI response
        response_text = await agent.process_message(message)
        
        # Send response back via WhatsApp
        await whatsapp_service.send_message(
            to=message["from"],
            body=response_text
        )
    
    return Response(status_code=200)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

