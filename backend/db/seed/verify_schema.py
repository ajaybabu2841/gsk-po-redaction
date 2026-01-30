import os
import pyodbc
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
AZURE_SQL_CONN = os.getenv("AZURE_SQL_CONN")

# Expected tables based on your ERD
EXPECTED_TABLES = [
    "Hospital",
    "Ingestion",
    "FileUpload",
    "MaskedFile",
    "Product",
    "POHeader",
    "POItem",
    "Invoice"
]

def verify_schema():
    """Verify that all expected tables exist and print schema summary."""
    if not AZURE_SQL_CONN:
        raise ValueError(" AZURE_SQL_CONN not set in .env file")

    with pyodbc.connect(AZURE_SQL_CONN) as conn:
        cursor = conn.cursor()

        # Fetch all user tables
        cursor.execute("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_SCHEMA = 'dbo'
        """)
        db_tables = {row[0] for row in cursor.fetchall()}

        print("\nChecking Azure SQL schema...")
        print("--------------------------------------------------------")

        # Compare expected vs actual
        missing_tables = [t for t in EXPECTED_TABLES if t not in db_tables]
        extra_tables = [t for t in db_tables if t not in EXPECTED_TABLES]

        if missing_tables:
            print(f"Missing tables ({len(missing_tables)}): {', '.join(missing_tables)}")
        else:
            print(" All expected tables are present.")

        if extra_tables:
            print(f" Extra tables found ({len(extra_tables)}): {', '.join(extra_tables)}")

        # Get column and row counts for each existing table
        summary = []
        for table in EXPECTED_TABLES:
            if table in db_tables:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = ?
                """, (table,))
                col_count = cursor.fetchone()[0]

                cursor.execute(f"SELECT COUNT(*) FROM dbo.{table}")
                row_count = cursor.fetchone()[0]

                summary.append((table, col_count, row_count))
            else:
                summary.append((table, "-", "-"))

        df = pd.DataFrame(summary, columns=["Table", "Columns", "Rows"])

        print("\n Schema Verification Summary:")
        print(df.to_string(index=False))

        if missing_tables:
            print("\n Schema validation FAILED: Missing tables detected.")
        else:
            print("\n Schema validation PASSED: All tables verified successfully.")

if __name__ == "__main__":
    verify_schema()
