import logging
import sys
from typing import Any

# Custom Filter to drop "body" or "payload" fields if they ever leak into logs
class PrivacyFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage().lower()
        # If a log attempts to print the raw draft, we kill it.
        forbidden_terms = ["draft_content", "user_prompt", "sk-", "payload:"]
        if any(term in msg for term in forbidden_terms):
            record.msg = "[REDACTED BY LIGHT PROTOCOL]"
            record.args = ()
            return True
        return True

def setup_logging():
    logger = logging.getLogger("uvicorn.access")
    # Reset handlers
    logger.handlers = []
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(levelname)s - [NEXUS] - %(message)s"
    ))
    
    # Attach Privacy Filter
    handler.addFilter(PrivacyFilter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)