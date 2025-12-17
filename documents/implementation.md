# Implementation Plan: Twilio → Modal Llama Loop (Clean Rebuild)

## Goal
Route Twilio WhatsApp webhooks directly to the Modal-hosted Llama endpoint and return the model’s reply, keeping everything minimal and testable step by step.

## Scope
- Twilio-only (drop Meta for now).
- One path: webhook receives message → call Modal → reply.
- Start with TwiML responses (no outbound REST send), then add outbound send if needed.

## Environment Variables (required unless noted)
- `MODAL_ENDPOINT_URL` - Your deployed LLM endpoint: `https://tomascufaro--whatsup-llm-generate-endpoint.modal.run`
- `TWILIO_ACCOUNT_SID` (not needed for local testing, required for deployment)
- `TWILIO_AUTH_TOKEN` (not needed for local testing, required for deployment)
- `TWILIO_PHONE_NUMBER` (not needed for local testing, required for deployment)

## Implementation Steps
1) **Webhook parsing (Twilio form data)**
   - In `src/main.py`, read `await request.form()` (not JSON).
   - Extract `Body`, `From`, `To`, `MessageSid`.
   - Minimal validation; log/return 200 even on parse failures.

2) **Model call**
   - `Agent.process_message` uses HTTP POST to Modal endpoint (already implemented in `src/agent/core.py`).
   - Spanish system prompt already configured in `src/agent/prompts.py`.
   - No changes needed for MVP.

3) **Respond via TwiML (simplest loop)**
   - Build `MessagingResponse` with the model text and return as the webhook HTTP response.
   - This avoids a second Twilio REST call while you test the round-trip.

4) **Optional outbound send**
   - Keep `WhatsAppService.send_message` for proactive sends.
   - Gate usage behind a flag so core flow relies only on TwiML during testing.

5) **Logging/observability**
   - Add concise logs for: parse failures, Modal call exceptions, empty responses.
   - Avoid noisy prints; prefer structured `print`/logging for now.

6) **Testing**
   - Local: `uvicorn src.main:app --reload`.
   - Health: `curl http://localhost:8000/health`.
   - Webhook sim: `curl -X POST http://localhost:8000/webhook/whatsapp -d "From=whatsapp:+123&Body=Hola"`.
   - Verify the TwiML response contains the model text.

7) **Deploy & hook up**
   - Deploy FastAPI to Modal: `uv run modal deploy modal_app.py`
   - Get the deployed URL from Modal output
   - Point Twilio WhatsApp sandbox webhook to: `https://your-url/webhook/whatsapp`
   - Send a real WhatsApp message and confirm the round-trip.

## File Touchpoints
- `src/main.py`: switch to form parsing, TwiML response, minimal logging.
- `src/services/whatsapp.py`: simplify to Twilio-only, remove unused Meta code.
- `src/agent/core.py`: ✅ already uses HTTP to call Modal endpoint - no changes needed.
- `src/agent/prompts.py`: ✅ already configured for Spanish - no changes needed.
- `modal_app.py`: deployment config for FastAPI (already exists).
- `modal_llm_app.py`: ✅ Llama endpoint already deployed.

## Current Status
✅ Modal LLM deployed at: `https://tomascufaro--whatsup-llm-generate-endpoint.modal.run` (update after redeploy)
✅ Agent configured to call Modal endpoint with Spanish prompts
✅ UV project setup complete with all dependencies

## Next Moves (suggested order)
1) Update `src/main.py` webhook to use form data and return TwiML with the model reply.
2) Simplify `src/services/whatsapp.py` to Twilio-only (remove Meta code).
3) Create `.env` file with `MODAL_ENDPOINT_URL` for local testing.
4) Local curl test: `curl -X POST http://localhost:8000/webhook/whatsapp -d "From=whatsapp:+123&Body=Hola"`
5) Deploy to Modal: `uv run modal deploy modal_app.py`
6) Configure Twilio sandbox webhook to point to deployed URL.
7) Test with real WhatsApp message.
