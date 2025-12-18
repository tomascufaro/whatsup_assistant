"""
Main entry point for the WhatsApp Assistant application.
Handles incoming webhooks from WhatsApp (Twilio).
"""

from fastapi import FastAPI, Request
from fastapi.responses import Response
import os
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse
import logging
import time

from agent.core import Agent
from logging_setup import configure_logging, new_request_id

load_dotenv()
configure_logging()

log = logging.getLogger("webhook")

app = FastAPI(title="WhatsApp Assistant")

agent = Agent()


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """Handle incoming WhatsApp messages via Twilio webhook."""
    try:
        req_id = new_request_id()
        start = time.time()

        # Parse Twilio form data
        form_data = await request.form()

        body = form_data.get("Body", "")
        from_number = form_data.get("From", "")
        message_sid = form_data.get("MessageSid", "")
        chat_id = from_number if from_number else None

        log.info("inbound_message", extra={
            "stage": "inbound_message",
            "request_id": req_id,
            "chat_id": chat_id,
            "message_sid": message_sid,
            "body_preview": body[:200],
        })

        if not body:
            log.warning("empty_message_body", extra={
                "stage": "inbound_message",
                "request_id": req_id,
                "chat_id": chat_id,
                "message_sid": message_sid,
            })
            return Response(content="", media_type="text/xml", status_code=200)

        # Get AI response from Modal
        response_text = await agent.process_message({"body": body}, chat_id=chat_id, request_id=req_id)
        log.info("agent_response_ready", extra={
            "stage": "agent_response_ready",
            "request_id": req_id,
            "chat_id": chat_id,
            "message_sid": message_sid,
            "response_preview": response_text[:200],
        })

        # Build TwiML response
        twiml_response = MessagingResponse()
        twiml_response.message(response_text)

        twiml_str = str(twiml_response)
        log.info("webhook_done", extra={
            "stage": "webhook_done",
            "request_id": req_id,
            "chat_id": chat_id,
            "message_sid": message_sid,
            "duration_ms": int((time.time() - start) * 1000),
        })

        return Response(content=twiml_str, media_type="text/xml", status_code=200)

    except Exception as e:
        log.error("webhook_error", extra={
            "stage": "webhook_error",
            "error": str(e),
        })
        import traceback
        traceback.print_exc()
        return Response(content="", media_type="text/xml", status_code=200)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
