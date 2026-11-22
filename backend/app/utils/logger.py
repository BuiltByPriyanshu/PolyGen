import logging
import sys
from app.config import settings


class SecretRedactingFilter(logging.Filter):
    """Masks sensitive API keys from server logs so credentials never leak."""

    def filter(self, record: logging.LogRecord) -> bool:
        secret = settings.ai_provider_api_key
        if secret and len(secret) > 4:
            msg = record.getMessage()
            if secret in msg:
                record.msg = msg.replace(secret, "***REDACTED***")
                record.args = ()
        return True


def get_logger(name: str = "polygen.backend") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
        handler.addFilter(SecretRedactingFilter())
        logger.addHandler(handler)
    return logger


logger = get_logger()