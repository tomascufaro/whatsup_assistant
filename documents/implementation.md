# Implementation Plan: Native Tool Calling

Goal: enable the WhatsApp agent to trigger tools natively via model tool-calling (store client info, send email) by updating the Modal/vLLM endpoint and client.

Scope (MVP)
- 1:1 chats only.
- Tools: `store_client`, `send_email` (can be used for meeting notifications).
- Model must support tool calling; update Modal app/client to pass tool schemas and handle tool_call responses.

Architecture / Modules
- `modal_llm_app.py` (or similar server): expose tool-calling endpoint (pass tool schemas to vLLM, return model responses including tool_calls).
- `src/agent/prompts.py`: refine system prompt (light touch; tools handled via schemas).
- `src/agent/tools.py` (new): tool definitions (schemas) and implementations.
  - Definitions: JSON schema for each tool (name, description, params).
  - Implementations: `store_client(data)`, `send_email(data)`.
- `src/agent/core.py`: client side orchestration.
  - Send messages + tool schemas to Modal endpoint.
  - Handle responses: text or tool_calls; execute tool; feed tool result back to model if needed; produce user-facing reply.
- `src/agent/memory.py`: unchanged (context assembly).

Tool definitions (schemas)
- `store_client` params: name (string, required), email (string, required), phone (string, optional), notes (string, optional).
- `send_email` params: to (string, required), subject (string, required), body (string, required). Allow default `to` (your email) if missing, optional.

Server changes (Modal / vLLM)
- Ensure the model supports tool calling (e.g., Qwen/LLM with function calling enabled in vLLM).
- Update endpoint handler to accept `tools` in the request body and pass through to vLLM; return raw model response including `tool_calls` and subsequent model text.
- If using streaming, handle tool messages; for simplicity, start non-streaming.

Client flow (`core.py`)
1) Build messages: system + memory + user.
2) Call Modal endpoint with messages + tool schemas.
3) If response is plain text: return to user.
4) If response includes `tool_calls`:
   - For each call (MVP: assume one): parse tool name/arguments.
   - Execute local implementation.
   - Append tool result as a tool message and re-query the model to get the final user-facing reply (or return a fixed confirmation to simplify).
5) Send final reply to user; log tool usage.

Tools implementation (`tools.py`)
- `store_client(data)`: append to `data/clients.csv` (create if missing, headers name,email,phone,notes,created_at). Minimal validation (require name/email).
- `send_email(data)`: thin wrapper around existing email helper/SMTP. Validate `to` (or use default), subject/body non-empty.
- Both return short strings summarizing the result for the model.

Config
- CSV path: `data/clients.csv` (env override optional).
- Email config: reuse existing envs (`EMAIL_FROM`, `EMAIL_TO_DEFAULT`, SMTP creds). Default `to` to your address if missing.
- Flag: `ENABLE_TOOL_CALLING` (default on once ready).

Testing
- Unit: tool schemas present; tool implementations validate inputs; CSV append; email stub called.
- Integration: mock Modal response with tool_call -> execute tool -> second call returns final text; plain text path unchanged.

Rollout steps
- Update `modal_llm_app.py` to accept/forward tools and return tool_calls.
- Add `src/agent/tools.py` with schemas+impls.
- Update `core.py` client to send tools and handle tool_call responses (two-pass flow for tool result).
- Adjust system prompt if needed (minimal).
- Smoke test locally with mocked tool_call responses before hitting Modal.
