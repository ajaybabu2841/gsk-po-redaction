import os
import pyodbc
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
AZURE_SQL_CONN = os.getenv("AZURE_SQL_CONN")

if not AZURE_SQL_CONN:
    raise ValueError("❌ AZURE_SQL_CONN not found in .env file")

# =======================
# Correct SQL for Azure SQL
# =======================
SCHEMA_SQL = """
SET NOCOUNT ON;

-- Hospital Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Hospital' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.Hospital (
        HospitalID UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWID(),
        Name NVARCHAR(255) NOT NULL,
        Address NVARCHAR(500) NULL,
        City NVARCHAR(100) NULL,
        State NVARCHAR(100) NULL,
        GSTIN NVARCHAR(50) NULL,
        Phone NVARCHAR(50) NULL,
        HospitalEmail NVARCHAR(255) NULL,
        CreatedAt DATETIME2(3) NOT NULL DEFAULT SYSUTCDATETIME()
    );
END;

-- Ingestion Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Ingestion' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.Ingestion (
        IngestionID UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWID(),
        SenderEmailID NVARCHAR(255) NULL,
        CreatedAt DATETIME2(3) NOT NULL DEFAULT SYSUTCDATETIME(),
        Body NVARCHAR(MAX) NULL,
        Subject NVARCHAR(500) NULL,
        HospitalID UNIQUEIDENTIFIER NULL,
        Status NVARCHAR(50) NOT NULL DEFAULT 'New',
        CONSTRAINT CK_Ingestion_Status CHECK (Status IN ('New','In Progress','Completed','Failed')),
        CONSTRAINT FK_Ingestion_Hospital FOREIGN KEY (HospitalID) REFERENCES dbo.Hospital(HospitalID)
    );
END;

-- FileUpload Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'FileUpload' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.FileUpload (
        FileID UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWID(),
        IngestionID UNIQUEIDENTIFIER NULL,
        FileName NVARCHAR(500) NOT NULL,
        BlobURL NVARCHAR(MAX) NULL,
        ReceivedAt DATETIME2(3) NOT NULL DEFAULT SYSUTCDATETIME(),
        KYCVerified BIT NULL,
        CONSTRAINT FK_FileUpload_Ingestion FOREIGN KEY (IngestionID) REFERENCES dbo.Ingestion(IngestionID)
    ); 


-- MaskedFile Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'MaskedFile' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.MaskedFile (
        MaskedFileID UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWID(),
        FileID UNIQUEIDENTIFIER NOT NULL,
        MaskedFileName NVARCHAR(500) NULL,
        MaskedFileURL NVARCHAR(MAX) NULL,
        AccuracyPercent DECIMAL(5,2) NULL,
        ProcessedAt DATETIME2(3) NULL,
        CONSTRAINT FK_MaskedFile_File FOREIGN KEY (FileID) REFERENCES dbo.FileUpload(FileID)
    );
    CREATE INDEX IX_MaskedFile_FileID ON dbo.MaskedFile(FileID);
END;

-- Product Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Product' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.Product (
        ProductID UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWID(),
        ProductName NVARCHAR(500) NOT NULL,
        GMMCode NVARCHAR(100) NULL,
        HSNCode NVARCHAR(50) NULL,
        MRP DECIMAL(18,4) NULL,
        DateCreated DATETIME2(3) NOT NULL DEFAULT SYSUTCDATETIME(),
        DateModified DATETIME2(3) NULL,
        ValidTill DATE NULL
    );
END;

-- POHeader Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'POHeader' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.POHeader (
        POID UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWID(),
        IngestionID UNIQUEIDENTIFIER NULL,
        FileID UNIQUEIDENTIFIER NULL,
        PONumber NVARCHAR(200) NULL,
        HospitalID UNIQUEIDENTIFIER NULL,
        PODate DATE NULL,
        AWDName NVARCHAR(255) NULL,
        VendorGSTIN NVARCHAR(50) NULL,
        VendorCode NVARCHAR(100) NULL,
        POApprovalDate DATE NULL,
        RCNumber NVARCHAR(200) NULL,
        RCValidityDate DATE NULL,
        CONSTRAINT FK_POHeader_Ingestion FOREIGN KEY (IngestionID) REFERENCES dbo.Ingestion(IngestionID),
        CONSTRAINT FK_POHeader_File FOREIGN KEY (FileID) REFERENCES dbo.FileUpload(FileID),
        CONSTRAINT FK_POHeader_Hospital FOREIGN KEY (HospitalID) REFERENCES dbo.Hospital(HospitalID)
    );
    CREATE INDEX IX_POHeader_IngestionID ON dbo.POHeader(IngestionID);
    CREATE INDEX IX_POHeader_FileID ON dbo.POHeader(FileID);
    CREATE INDEX IX_POHeader_HospitalID ON dbo.POHeader(HospitalID);
END;

-- POItem Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'POItem' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.POItem (
        POItemID UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWID(),
        POID UNIQUEIDENTIFIER NOT NULL,
        ProductID UNIQUEIDENTIFIER NULL,
        UnitOfMeasure NVARCHAR(50) NULL,
        HSNCode NVARCHAR(50) NULL,
        Quantity INT NULL,
        GSKQuantity INT NULL,
        Price DECIMAL(18,6) NULL,
        RCRate DECIMAL(18,6) NULL,
        ItemCodeFromPO NVARCHAR(200) NULL,
        Marked BIT NULL,
        CONSTRAINT FK_POItem_POHeader FOREIGN KEY (POID) REFERENCES dbo.POHeader(POID),
        CONSTRAINT FK_POItem_Product FOREIGN KEY (ProductID) REFERENCES dbo.Product(ProductID)
    );
    CREATE INDEX IX_POItem_POID ON dbo.POItem(POID);
    CREATE INDEX IX_POItem_ProductID ON dbo.POItem(ProductID);
END;

-- Invoice Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Invoice' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.Invoice (
        InvoiceID UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWID(),
        IngestionID UNIQUEIDENTIFIER NULL,
        FileID UNIQUEIDENTIFIER NULL,
        InvoiceNumber NVARCHAR(200) NULL,
        POID UNIQUEIDENTIFIER NULL,
        HospitalID UNIQUEIDENTIFIER NULL,
        Quantity INT NULL,
        Price DECIMAL(18,6) NULL,
        Date DATE NULL,
        CONSTRAINT FK_Invoice_Ingestion FOREIGN KEY (IngestionID) REFERENCES dbo.Ingestion(IngestionID),
        CONSTRAINT FK_Invoice_File FOREIGN KEY (FileID) REFERENCES dbo.FileUpload(FileID),
        CONSTRAINT FK_Invoice_PO FOREIGN KEY (POID) REFERENCES dbo.POHeader(POID),
        CONSTRAINT FK_Invoice_Hospital FOREIGN KEY (HospitalID) REFERENCES dbo.Hospital(HospitalID)
    );
    CREATE INDEX IX_Invoice_IngestionID ON dbo.Invoice(IngestionID);
    CREATE INDEX IX_Invoice_FileID ON dbo.Invoice(FileID);
    CREATE INDEX IX_Invoice_POID ON dbo.Invoice(POID);
    CREATE INDEX IX_Invoice_HospitalID ON dbo.Invoice(HospitalID);
END;
"""

def create_schema():
    with pyodbc.connect(AZURE_SQL_CONN) as conn:
        cursor = conn.cursor()
        print(" Connected to Azure SQL Database")
        cursor.execute(SCHEMA_SQL)
        conn.commit()
        print("Schema created successfully in Azure SQL Database")

if __name__ == "__main__":
    create_schema()