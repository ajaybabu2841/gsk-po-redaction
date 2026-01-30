# # backend/utils/logging/error_handler.py

# import traceback
# import json
# import pyodbc
# import os
# from datetime import datetime
# from functools import wraps
# from utils.logging.request_context import request_id_ctx
# from dotenv import load_dotenv

# load_dotenv()

# AZURE_SQL_CONN = os.getenv("AZURE_SQL_CONN")


# def log_error_to_db(stage, error_category, error_message, metadata=None, file_name=None):
#     try:
#         # Convert everything to safe string types
#         request_id_raw = request_id_ctx.get()
#         request_id = str(request_id_raw) if request_id_raw else None
        
#         file_name = str(file_name) if file_name else None
#         stage = str(stage) if stage else ""
#         error_category = str(error_category) if error_category else ""
#         error_message = str(error_message) if error_message else ""

#         stacktrace = traceback.format_exc()
#         stacktrace = str(stacktrace) if stacktrace else ""

#         metadata_json = json.dumps(metadata or {}, ensure_ascii=False)

#         conn = pyodbc.connect(AZURE_SQL_CONN)
#         cursor = conn.cursor()

#         cursor.execute("""
#             INSERT INTO ErrorDump (
#                 RequestID, FileName, Stage, ErrorCategory,
#                 ErrorMessage, StackTrace, Metadata
#             )
#             VALUES (?, ?, ?, ?, ?, ?, ?)
#         """,
#         (
#             request_id,
#             file_name,
#             stage,
#             error_category,
#             error_message,
#             stacktrace,
#             metadata_json
#         ))

#         conn.commit()
#         conn.close()

#     except Exception as db_exc:
#         print(" FAILED TO WRITE ERROR TO DATABASE")
#         print("Reason:", db_exc)



# # ---------------------------------------------
# # Decorator for automatic error logging
# # ---------------------------------------------
# def log_errors(stage):
#     """
#     Automatically logs all unexpected errors inside decorated functions.
#     """
#     def decorator(func):
#         @wraps(func)
#         def wrapper(*args, **kwargs):
#             try:
#                 return func(*args, **kwargs)

#             except Exception as e:
#                 # Extract useful metadata
#                 metadata = {
#                     "args": str(args),
#                     "kwargs": str(kwargs)
#                 }

#                 file_name = (
#                     kwargs.get("file_path")
#                     or kwargs.get("pdf_path")
#                     or kwargs.get("filename")
#                     or None
#                 )

#                 log_error_to_db(
#                     stage=stage,
#                     error_category="SystemError",
#                     error_message=str(e),
#                     metadata=metadata,
#                     file_name=file_name
#                 )

#                 raise   # re-raise so FastAPI/global handler sees it

#         return wrapper
#     return decorator


# # ---------------------------------------------
# # Safe wrapper for LLM calls (common failure area)
# # ---------------------------------------------
# def safe_llm_call(stage):
#     """
#     Wraps LLM calls to ensure errors are logged cleanly.
#     """
#     def decorator(func):
#         @wraps(func)
#         def wrapper(*args, **kwargs):
#             try:
#                 return func(*args, **kwargs)

#             except Exception as e:
#                 log_error_to_db(
#                     stage=stage,
#                     error_category="LLM_CALL_FAILURE",
#                     error_message=str(e),
#                     metadata={"args": str(args), "kwargs": str(kwargs)}
#                 )
#                 raise

#         return wrapper
#     return decorator

import traceback
import pyodbc
import os
from functools import wraps
from dotenv import load_dotenv
from utils.logging.request_context import request_id_ctx

load_dotenv()

AZURE_SQL_CONN = os.getenv("AZURE_SQL_CONN")


# ======================================================
# CORE FAILURE LOGGER (ONLY DB WRITER)
# ======================================================
def log_processing_failure(
    *,
    error: Exception | str,
    category: str,
    stage: str | None = None,
    ingestion_id: str | None = None,
    file_id: str | None = None,
    filename: str | None = None,
):
    try:
        # ✅ SAME PATTERN AS OLD CODE
        request_id_raw = request_id_ctx.get()
        request_id = str(request_id_raw) if request_id_raw else None

        error_message = str(error)

        stacktrace = traceback.format_exc()
        if not stacktrace or stacktrace == "NoneType: None\n":
            stacktrace = "No stacktrace available"

        conn = pyodbc.connect(AZURE_SQL_CONN)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO dbo.ProcessingFailureLog (
                ErrorMessage,
                ErrorCategory,
                IngestionID,
                FileID,
                StackTrace,
                RequestID,
                FileName,
                Stage
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            error_message,
            category,
            ingestion_id,
            file_id,
            stacktrace,
            request_id,
            filename,
            stage
        ))

        conn.commit()
        conn.close()

    except Exception as log_exc:
        # Logging must NEVER break pipeline
        print(" FAILED TO WRITE ProcessingFailureLog")
        print(log_exc)



# ======================================================
# DECORATOR → PIPELINE / SYSTEM ERRORS
# ======================================================
def log_pipeline_errors(stage: str, category: str = "PIPELINE_ERROR"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except Exception as e:
                log_processing_failure(
                    error=e,
                    category=category,
                    stage=stage,
                    ingestion_id=kwargs.get("ingestion_id"),
                    file_id=kwargs.get("file_id"),
                    filename=kwargs.get("filename") or kwargs.get("file_path"),
                )
                raise
        return wrapper
    return decorator



# ======================================================
# EXPLICIT LOGICAL FAILURE (NO EXCEPTION)
# ======================================================
def log_logical_failure(
    *,
    stage: str,
    message: str,
    ingestion_id: str | None = None,
    file_id: str | None = None,
    filename: str | None = None,
):
    log_processing_failure(
        error=message,
        category="LOGICAL_FAILURE",
        stage=stage,
        ingestion_id=ingestion_id,
        file_id=file_id,
        filename=filename,
    )

