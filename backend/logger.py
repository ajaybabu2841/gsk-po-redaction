import logging
import json
import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from opencensus.ext.azure.log_exporter import AzureLogHandler

from utils.logging.request_context import request_id_ctx
from utils.logging.db_handler import DBLogHandler

load_dotenv()

# -------------------------------
# SINGLETON HANDLERS
# -------------------------------
_console_handler = None
_db_handler = None
_ai_handler = None
ENABLE_DB_LOGGING = os.getenv("ENABLE_DB_LOGGING", "false").lower() == "true"



class StructuredLogger(logging.LoggerAdapter):
    def process(self, message, kwargs):
        log_payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id_ctx.get(),
            "message": message,
        }

        # Merge any metadata
        extra = kwargs.pop("extra", {})
        log_payload.update(extra)

        return json.dumps(log_payload), kwargs


def get_logger(name: str) -> StructuredLogger:
    global _console_handler, _db_handler, _ai_handler

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # If logger has handlers already, return a structured wrapper
    if logger.handlers:
        return StructuredLogger(logger, {})

    # ===========================
    # Console Handler (Singleton)
    # ===========================
    if _console_handler is None:
        _console_handler = logging.StreamHandler()
        _console_handler.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(_console_handler)

    # ===========================
    # DB Handler (DISABLED FOR TESTING)
    # ===========================
    if ENABLE_DB_LOGGING:
        if _db_handler is None:
            try:
                _db_handler = DBLogHandler()
            except Exception as e:
                print("⚠ Failed to initialize DBLogHandler:", e)
                _db_handler = None

        if _db_handler:
            logger.addHandler(_db_handler)

    # ==================================
    # Azure Application Insights Handler
    # ==================================
    conn_str = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")

    if conn_str:
        if _ai_handler is None:
            try:
                _ai_handler = AzureLogHandler(connection_string=conn_str)
            except Exception as e:
                print("⚠ Failed to initialize AzureLogHandler:", e)
                _ai_handler = None

        if _ai_handler:
            logger.addHandler(_ai_handler)
    else:
        print("⚠ APPLICATIONINSIGHTS_CONNECTION_STRING not set. Skipping App Insights logging.")

    return StructuredLogger(logger, {})
