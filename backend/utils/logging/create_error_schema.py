import os
import pyodbc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
AZURE_SQL_CONN = os.getenv("AZURE_SQL_CONN")

if not AZURE_SQL_CONN:
    raise ValueError("❌ AZURE_SQL_CONN not found in .env file")

ERROR_TABLE_SQL = """
SET NOCOUNT ON;

IF NOT EXISTS (
    SELECT * FROM sys.tables
    WHERE name = 'ErrorDump'
        AND schema_id = SCHEMA_ID('dbo')
)
BEGIN
    CREATE TABLE dbo.ErrorDump (
    ErrorID BIGINT IDENTITY(1,1) PRIMARY KEY,
    RequestID UNIQUEIDENTIFIER NULL,
    FileName NVARCHAR(500) NULL,
    Stage NVARCHAR(200) NOT NULL,            -- ex: OCR, HeaderExtraction, LLM_Call, Redaction
    ErrorCategory NVARCHAR(200) NULL,        -- ex: MissingHeader, OCRFailure, JSONParseError
    ErrorMessage NVARCHAR(MAX) NOT NULL,     -- human readable message
    StackTrace NVARCHAR(MAX) NULL,           -- full error trace
    Metadata NVARCHAR(MAX) NULL,             -- JSON (table_count, pdf_pages, etc)
    CreatedAt DATETIME2(3) NOT NULL DEFAULT SYSUTCDATETIME(),
    Processed BIT NOT NULL DEFAULT 0         -- to mark if DS team reviewed it
);

CREATE INDEX IX_ErrorDump_RequestID ON dbo.ErrorDump(RequestID);
CREATE INDEX IX_ErrorDump_Stage ON dbo.ErrorDump(Stage);
CREATE INDEX IX_ErrorDump_CreatedAt ON dbo.ErrorDump(CreatedAt);
END;
"""

# ============================================
# Function to create schema
# ============================================
def create_error_schema():
    print(" Connecting to Azure SQL Database...")

    with pyodbc.connect(AZURE_SQL_CONN) as conn:
        cursor = conn.cursor()

        print(" Connected successfully")
        print(" Creating Error table schema...")

        cursor.execute(ERROR_TABLE_SQL)
        conn.commit()

        print(" Error table created or already exists: dbo.ErrorDump")


# ============================================
# Run script
# ============================================
if __name__ == "__main__":
    create_error_schema()