import os
import pyodbc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
AZURE_SQL_CONN = os.getenv("AZURE_SQL_CONN")

if not AZURE_SQL_CONN:
    raise ValueError("❌ AZURE_SQL_CONN not found in .env file")

# =======================
# Invoice tables creation SQL
# =======================
INVOICE_SCHEMA_SQL = """
SET NOCOUNT ON;

-- =========================
-- InvoiceHeader Table
-- =========================
IF NOT EXISTS (
    SELECT * FROM sys.tables 
    WHERE name = 'InvoiceHeader' 
      AND schema_id = SCHEMA_ID('dbo')
)
BEGIN
    CREATE TABLE dbo.InvoiceHeader (
        InvoiceHeaderID UNIQUEIDENTIFIER NOT NULL 
            PRIMARY KEY DEFAULT NEWID(),

        IngestionID UNIQUEIDENTIFIER NULL,
        FileID UNIQUEIDENTIFIER NULL,

        PONumber NVARCHAR(200) NULL,
        InvoiceNumber NVARCHAR(200) NULL,

        HospitalName NVARCHAR(255) NULL,
        HospitalID UNIQUEIDENTIFIER NULL,

        AWDName NVARCHAR(255) NULL,
        AWDCERPSCode NVARCHAR(100) NULL,
        InvoiceDate DATE NULL,

        CreatedAt DATETIME2(3) NOT NULL 
            DEFAULT SYSUTCDATETIME(),

        CONSTRAINT FK_InvoiceHeader_Hospital
            FOREIGN KEY (HospitalID)
            REFERENCES dbo.Hospital(HospitalID),

        CONSTRAINT FK_InvoiceHeader_Ingestion
            FOREIGN KEY (IngestionID)
            REFERENCES dbo.Ingestion(IngestionID),

        CONSTRAINT FK_InvoiceHeader_File
            FOREIGN KEY (FileID)
            REFERENCES dbo.FileUpload(FileID)
    );

    CREATE INDEX IX_InvoiceHeader_HospitalID
        ON dbo.InvoiceHeader(HospitalID);

    CREATE INDEX IX_InvoiceHeader_IngestionID
        ON dbo.InvoiceHeader(IngestionID);

    CREATE INDEX IX_InvoiceHeader_FileID
        ON dbo.InvoiceHeader(FileID);
END;

-- =========================
-- InvoiceLineItem Table
-- =========================
IF NOT EXISTS (
    SELECT * FROM sys.tables 
    WHERE name = 'InvoiceLineItem' 
      AND schema_id = SCHEMA_ID('dbo')
)
BEGIN
    CREATE TABLE dbo.InvoiceLineItem (
        InvoiceLineItemID UNIQUEIDENTIFIER NOT NULL 
            PRIMARY KEY DEFAULT NEWID(),

        IngestionID UNIQUEIDENTIFIER NULL,
        FileID UNIQUEIDENTIFIER NULL,

        InvoiceHeaderID UNIQUEIDENTIFIER NOT NULL,

        ProductName NVARCHAR(500) NOT NULL,
        GMMCode NVARCHAR(100) NULL,
        BatchNumber NVARCHAR(100) NULL,

        MRP DECIMAL(18,4) NULL,
        UnitOfMeasurement NVARCHAR(50) NULL,

        InvoiceQty DECIMAL(18,4) NULL,
        InvoiceQtyGSKPack DECIMAL(18,4) NULL,
        ProdUnitRate DECIMAL(18,4) NULL,
        InvoiceValue DECIMAL(18,4) NULL,

        is_gsk BIT NOT NULL DEFAULT 0,

        CONSTRAINT FK_InvoiceLineItem_InvoiceHeader
            FOREIGN KEY (InvoiceHeaderID)
            REFERENCES dbo.InvoiceHeader(InvoiceHeaderID),

        CONSTRAINT FK_InvoiceLineItem_Ingestion
            FOREIGN KEY (IngestionID)
            REFERENCES dbo.Ingestion(IngestionID),

        CONSTRAINT FK_InvoiceLineItem_File
            FOREIGN KEY (FileID)
            REFERENCES dbo.FileUpload(FileID)
    );

    CREATE INDEX IX_InvoiceLineItem_InvoiceHeaderID
        ON dbo.InvoiceLineItem(InvoiceHeaderID);

    CREATE INDEX IX_InvoiceLineItem_IngestionID
        ON dbo.InvoiceLineItem(IngestionID);

    CREATE INDEX IX_InvoiceLineItem_FileID
        ON dbo.InvoiceLineItem(FileID);
END;
"""

def create_invoice_tables():
    with pyodbc.connect(AZURE_SQL_CONN) as conn:
        cursor = conn.cursor()
        print("Connected to Azure SQL Database")
        cursor.execute(INVOICE_SCHEMA_SQL)
        conn.commit()
        print(" InvoiceHeader and InvoiceLineItem tables created successfully")

if __name__ == "__main__":
    create_invoice_tables()
