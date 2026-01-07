import logging
import sys
from typing import Any
from app.core.config import settings

def setup_logging():
    # Configure Root Logger to catch ALL system logs
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Reset handlers
    root_logger.handlers = []
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(levelname)s - [NEXUS] - %(message)s"
    ))
    
    # Attach Privacy Filter
    handler.addFilter(PrivacyFilter())
    root_logger.addHandler(handler)
    
    # Ensure Uvicorn uses our secure handler
    logging.getLogger("uvicorn").handlers = [handler]
    logging.getLogger("uvicorn.access").handlers = [handler]

# Custom Filter to drop "body" or "payload" fields if they ever leak into logs
class PrivacyFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if settings.DEBUG_PROMPTS:
            return True

        msg = record.getMessage().lower()
        # If a log attempts to print the raw draft, we kill it.
        forbidden_terms = ["draft_content", "user_prompt", "sk-", "payload:", "bearer"]
        if any(term in msg for term in forbidden_terms):
            record.msg = "[REDACTED BY LIGHT PROTOCOL]"
            record.args = ()
            return True
        return True