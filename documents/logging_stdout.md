Conversation Tracing via Structured Stdout Logging

Purpose
- Trace each conversation turn end-to-end (webhook → agent → tools) without adding new infra; emit JSON logs to stdout for Modal/local collection.

What to Log
- Correlation: request_id (UUID per webhook), chat_id (WhatsApp number), message_sid (Twilio SID).
- Stages: inbound webhook, agent invoke start/end, each tool call start/end, final response.
- Timing: duration_ms per stage.
- Context: history_len, tool name, response_preview/user_preview (truncated), iterations if available.
- Outcomes: success/error, error message/trace.

Minimal Setup (stdlib, JSON to stdout)
```python
# logging_setup.py
import json, logging, sys, uuid

class JsonFormatter(logging.Formatter):
    def format(self, record):
        data = {
            "level": record.levelname,
            "msg": record.getMessage(),
            "logger": record.name,
            "time": self.formatTime(record, self.datefmt),
        }
        # Merge extra fields that were attached via `extra=`
        skip = {
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process",
        }
        for key, value in record.__dict__.items():
            if key not in skip:
                data[key] = value
        return json.dumps(data, ensure_ascii=False)

def configure_logging(level=logging.INFO):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        root.addHandler(handler)

def new_request_id():
    return str(uuid.uuid4())
```

Webhook (`src/main.py`) usage
```python
from logging_setup import configure_logging, new_request_id
import logging, time

configure_logging()
log = logging.getLogger("webhook")

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    req_id = new_request_id()
    start = time.time()
    form_data = await request.form()
    body = form_data.get("Body", "")
    from_number = form_data.get("From", "")
    message_sid = form_data.get("MessageSid", "")
    chat_id = from_number or None

    log.info("inbound_message", extra={
        "stage": "inbound_message",
        "request_id": req_id, "chat_id": chat_id, "message_sid": message_sid,
        "body_preview": body[:200],
    })

    response_text = await agent.process_message({"body": body}, chat_id=chat_id, request_id=req_id)

    log.info("webhook_done", extra={
        "stage": "webhook_done",
        "request_id": req_id, "chat_id": chat_id, "message_sid": message_sid,
        "duration_ms": int((time.time()-start)*1000),
    })
    ...
```

Agent (`src/agent/core.py`) logging
```python
import logging, time
log = logging.getLogger("agent")

async def process_message(..., request_id=None):
    start = time.time()
    log.info("agent_invoke_start", extra={
        "stage": "agent_invoke_start",
        "request_id": request_id, "chat_id": chat_id,
        "user_preview": user_message[:200],
        "history_len": len(context_messages),
    })
    result = await self.agent_executor.ainvoke({...})
    response = result["messages"][-1].content
    log.info("agent_invoke_end", extra={
        "stage": "agent_invoke_end",
        "request_id": request_id, "chat_id": chat_id,
        "duration_ms": int((time.time()-start)*1000),
        "response_preview": response[:200],
    })
    ...
```

Tools (wrap `_run`)
```python
import logging, time
log = logging.getLogger("tool")

def _run(self, *args, **kwargs):
    start = time.time()
    try:
        res = ...  # existing logic
        log.info("tool_ok", extra={
            "stage": "tool_ok",
            "request_id": kwargs.get("request_id"),
            "tool": self.name,
            "duration_ms": int((time.time()-start)*1000),
        })
        return res
    except Exception as e:
        log.error("tool_error", extra={
            "stage": "tool_error",
            "request_id": kwargs.get("request_id"),
            "tool": self.name,
            "duration_ms": int((time.time()-start)*1000),
            "error": str(e),
        })
        raise
```

Propagation
- Pass request_id through `process_message` and into tool calls (as kwarg or embedded in tool input) so all logs share the same correlation key. LangChain may not forward arbitrary kwargs to tools, so include `request_id` in the agent input/state that tools can read.

Where Logs Go
- Local/dev: stdout in your terminal (e.g., uvicorn output).
- Modal: stdout is captured and viewable in Modal logs. No file sink by default; add another handler if you need file/remote retention.

Operational Notes
- Truncate bodies/previews to avoid PII leakage; keep a stable schema (`request_id`, `chat_id`, `stage`, `duration_ms`) for easy grepping/filtering.
- If later adding OpenTelemetry, you can keep this schema and either bridge logs into spans or add OTEL alongside stdout.
