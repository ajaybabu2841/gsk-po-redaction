# create_logger_schema.py

import os
import pyodbc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
AZURE_SQL_CONN = os.getenv("AZURE_SQL_CONN")

if not AZURE_SQL_CONN:
    raise ValueError("❌ AZURE_SQL_CONN not found in .env file")


# ============================================
# SQL for ONLY the logging table
# ============================================
LOGGER_TABLE_SQL = """
SET NOCOUNT ON;

IF NOT EXISTS (
    SELECT * FROM sys.tables 
    WHERE name = 'AppLogs' 
      AND schema_id = SCHEMA_ID('dbo')
)
BEGIN
    CREATE TABLE dbo.AppLogs (
        Id BIGINT IDENTITY(1,1) PRIMARY KEY,
        Timestamp DATETIME2(3) NOT NULL,
        RequestId UNIQUEIDENTIFIER NULL,
        LogLevel NVARCHAR(20) NOT NULL,
        Message NVARCHAR(MAX) NOT NULL,
        RawLog NVARCHAR(MAX) NOT NULL,
        CreatedAt DATETIME2(3) NOT NULL DEFAULT SYSUTCDATETIME()
    );

    -- Useful indexes for fast searching
    CREATE INDEX IX_AppLogs_RequestId ON dbo.AppLogs(RequestId);
    CREATE INDEX IX_AppLogs_Timestamp ON dbo.AppLogs(Timestamp);
END;
"""


# ============================================
# Function to create schema
# ============================================
def create_logger_schema():
    print(" Connecting to Azure SQL Database...")

    with pyodbc.connect(AZURE_SQL_CONN) as conn:
        cursor = conn.cursor()

        print(" Connected successfully")
        print("Creating logger table schema...")

        cursor.execute(LOGGER_TABLE_SQL)
        conn.commit()

        print(" Logger table created or already exists: dbo.AppLogs")


# ============================================
# Run script
# ============================================
if __name__ == "__main__":
    create_logger_schema()
