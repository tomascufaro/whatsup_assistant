import json
import logging
import sys
import uuid
import contextvars


# Context variable to propagate request_id across async tasks
request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)


class JsonFormatter(logging.Formatter):
    """Formatter that emits JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        data = {
            "level": record.levelname,
            "msg": record.getMessage(),
            "logger": record.name,
            "time": self.formatTime(record, self.datefmt),
        }
        # Merge extra fields attached via `extra=`
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


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logger to emit JSON to stdout."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        root.addHandler(handler)


def new_request_id() -> str:
    """Generate a new request ID."""
    return str(uuid.uuid4())


def set_request_id(request_id: str | None) -> None:
    """Set request ID in contextvar for downstream access."""
    request_id_var.set(request_id)


def get_request_id() -> str | None:
    """Get current request ID from contextvar."""
    return request_id_var.get()
