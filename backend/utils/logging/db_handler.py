# import logging
# import json
# import pyodbc
# import os
# from datetime import datetime
# from db.db_connection import get_connection

# class DBLogHandler(logging.Handler):
#     def __init__(self):
#         super().__init__()

#         # conn_str = os.getenv("AZURE_SQL_CONN")
#         # if not conn_str:
#         #     raise ValueError("❌ AZURE_SQL_CONN missing in environment variables")

#         # self.conn = get_connection()
#         # self.conn.autocommit = True

#     def emit(self, record):
#         try:
#             cursor = self.conn.cursor()

#             raw_log = record.getMessage()
#             parsed = json.loads(raw_log)

#             timestamp = parsed.get("timestamp")
#             request_id = parsed.get("request_id")
#             message = parsed.get("message")

#             cursor.execute(
#                 """
#                 INSERT INTO AppLogs (Timestamp, RequestId, LogLevel, Message, RawLog)
#                 VALUES (?, ?, ?, ?, ?)
#                 """,
#                 (
#                     timestamp,
#                     request_id,
#                     record.levelname,
#                     message,
#                     raw_log  # store raw JSON string
#                 )
#             )

#         except Exception as e:
#             print("DB logging failed:", e)

import logging
import json
import os
import pyodbc
from db.db_connection import get_connection

class DBLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.conn = None  # Lazy connection

    def _ensure_connection(self):
        """Ensure SQL connection is alive; reconnect if needed."""
        if self.conn is None:
            try:
                self.conn = get_connection()
            except Exception as e:
                print(" DB connection failed, logs will skip:", e)
                self.conn = None

    def emit(self, record):
        try:
            # Ensure connection is available
            self._ensure_connection()
            if self.conn is None:
                return  # Skip DB logging gracefully

            cursor = self.conn.cursor()

            raw_log = record.getMessage()
            parsed = json.loads(raw_log)

            timestamp = parsed.get("timestamp")
            request_id = parsed.get("request_id")
            message = parsed.get("message")

            cursor.execute(
                """
                INSERT INTO AppLogs (Timestamp, RequestId, LogLevel, Message, RawLog)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    request_id,
                    record.levelname,
                    message,
                    raw_log,
                )
            )

        except Exception as e:
            print(" DB logging failed:", e)
            self.conn = None  # Force reconnect next time
