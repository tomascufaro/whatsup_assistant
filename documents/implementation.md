# Implementation Plan: Native Tool Calling

Goal: enable the WhatsApp agent to trigger tools natively via model tool-calling (store client info, send email) by updating the Modal/vLLM endpoint and client.

Scope (MVP)
- 1:1 chats only.
- Tools: `store_client`, `send_email` (can be used for meeting notifications).
- Model must support tool calling; update Modal app/client to pass tool schemas and handle tool_call responses.
- Use OpenAI-style tool calling JSON format for wire protocol.

Architecture / Modules
- `modal_llm_app.py`: expose tool-calling endpoint (pass tool schemas to vLLM, return model responses including tool_calls in OpenAI format).
- `src/agent/prompts.py`: refine system prompt (light touch; tools handled via schemas).
- `src/agent/tool_schemas.py` (new): OpenAI-style tool definitions (JSON schemas only).
  - Definitions: JSON schema for each tool (name, description, parameters with type/required fields).
  - Format: OpenAI function calling format (`{"type": "function", "function": {...}}`).
- `src/tools/` (existing): reuse/extend existing modules for implementations.
  - `src/tools/database.py`: extend with simple `store_client(data)` wrapper function (not LangChain tool).
  - `src/tools/email.py`: extend with simple `send_email(data)` wrapper function (not LangChain tool).
  - These are plain Python functions that return result strings (or error dicts).
- `src/agent/core.py`: client side orchestration.
  - Send messages + tool schemas to Modal endpoint.
  - Handle responses: text or tool_calls; execute tool; feed tool result back to model if needed; produce user-facing reply.
- `src/agent/memory.py`: unchanged (context assembly).

Tool definitions (schemas) - OpenAI format
- `store_client` params: name (string, required), email (string, required), phone (string, optional), notes (string, optional).
- `send_email` params: to (string, optional - defaults to env EMAIL_TO_DEFAULT), subject (string, required), body (string, required).

Wire format (OpenAI-style)
- Request: `{"messages": [...], "tools": [{"type": "function", "function": {...}}], ...}`
- Response with tool_call: `{"choices": [{"message": {"role": "assistant", "content": null, "tool_calls": [...]}}]}`
- Tool message: `{"role": "tool", "content": "...", "tool_call_id": "..."}`
- Use standard OpenAI field names: `tools`, `tool_choice`, `tool_calls`, `tool_call_id`.

Server changes (Modal / vLLM)
- Ensure the model supports tool calling (e.g., Qwen2.5 with function calling enabled in vLLM).
- Update endpoint handler to accept `tools` in the request body and pass through to vLLM.
- Return raw model response including `tool_calls` in OpenAI format.
- If using streaming, handle tool messages; for simplicity, start non-streaming.

Client flow (`core.py`)
1) Build messages: system + memory + user.
2) Load tool schemas from `tool_schemas.py`.
3) Call Modal endpoint with messages + tool schemas.
4) If response is plain text: return to user.
5) If response includes `tool_calls`:
   - For each call (MVP: assume one): parse tool name/arguments.
   - Execute local implementation from `src/tools/` modules.
   - Handle errors: tool functions return `{"error": true, "message": "..."}` on failure, or success string.
   - For v1 (simplified): always return fixed confirmations to the user (no second LLM call).
   - If later re-querying: append tool result as tool message (`role: "tool"`, `tool_call_id`, `content`) and call Modal again.
6) Send final reply to user; log tool usage.

Tools implementation (wrapper functions in `src/tools/`)
- `store_client(data: dict) -> str | dict`:
  - Append to `data/clients.csv` (create if missing, headers name,email,phone,notes,created_at).
  - Minimal validation (require name/email).
  - Return success string or `{"error": true, "message": "..."}` on failure.
- `send_email(data: dict) -> str | dict`:
  - Thin wrapper around existing email helper/SMTP (reuse `src/tools/email.py` infrastructure).
  - Validate `to` (or use default from env), subject/body non-empty.
  - Return success string or `{"error": true, "message": "..."}` on failure.
- Both return short strings summarizing the result for the model (or error dicts that `core.py` can format).

Error handling
- Tool functions return `{"error": true, "message": "..."}` on validation/execution failures.
- `core.py` intercepts errors and can either:
  - Send error directly to user (simple path).
  - Or feed error to model for user-friendly message (if re-querying).
- Define explicit error format at plan level: `{"error": true, "message": "descriptive error"}`.

Config
- CSV path: `data/clients.csv` (env override optional).
- Email config: use envs `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM`, `EMAIL_TO`. Default `to` to `EMAIL_TO` if missing in the tool call.
- Flag: `ENABLE_TOOL_CALLING` (default on once ready).

Testing
- Unit: tool schemas present and valid OpenAI format; tool implementations validate inputs; CSV append; email stub called.
- Integration: mock Modal response with tool_call -> execute tool -> verify tool result format -> (if re-query) second call returns final text; plain text path unchanged.
- Add test: verify `core.py` correctly parses tool_call, calls right function, appends tool message with correct `role`/`tool_call_id`/`content`, builds second-model-call payload correctly.

Rollout steps
- Update `modal_llm_app.py` to accept/forward `tools` and return `tool_calls` in OpenAI format.
- Add `src/agent/tool_schemas.py` with OpenAI-style schemas.
- Extend `src/tools/database.py` and `src/tools/email.py` with simple wrapper functions for native tool calling.
- Update `core.py` client to send tools and handle tool_call responses (simplified flow: fixed confirmations for v1, optional re-query for email).
- Adjust system prompt if needed (minimal).
- Smoke test locally with mocked tool_call responses before hitting Modal.
