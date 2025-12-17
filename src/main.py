"""
Main entry point for the WhatsApp Assistant application.
Handles incoming webhooks from WhatsApp (Twilio).
"""

from fastapi import FastAPI, Request
from fastapi.responses import Response
import os
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse

from agent.core import Agent

load_dotenv()

app = FastAPI(title="WhatsApp Assistant")

agent = Agent()


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """Handle incoming WhatsApp messages via Twilio webhook."""
    try:
        # Parse Twilio form data
        form_data = await request.form()

        body = form_data.get("Body", "")
        from_number = form_data.get("From", "")
        message_sid = form_data.get("MessageSid", "")

        print(f"Received message: {body} from {from_number} (SID: {message_sid})")

        if not body:
            print("Warning: Empty message body")
            return Response(content="", media_type="text/xml", status_code=200)

        # Get AI response from Modal
        response_text = await agent.process_message({"body": body})
        print(f"Response text from agent: {response_text}")

        # Build TwiML response
        twiml_response = MessagingResponse()
        twiml_response.message(response_text)

        twiml_str = str(twiml_response)
        print(f"TwiML response: {twiml_str}")

        return Response(content=twiml_str, media_type="text/xml", status_code=200)

    except Exception as e:
        print(f"Error processing webhook: {e}")
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

