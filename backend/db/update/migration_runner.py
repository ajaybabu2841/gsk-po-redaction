import os
import pyodbc
from dotenv import load_dotenv
# from .db_insert_operations import get_connection
from db.db_connection import get_connection


load_dotenv()
AZURE_SQL_CONN = os.getenv("AZURE_SQL_CONN")
MIGRATIONS_FOLDER = "migrations"


def ensure_migration_table(cursor):
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = '_Migrations')
    BEGIN
        CREATE TABLE _Migrations (
            id INT IDENTITY(1,1) PRIMARY KEY,
            filename NVARCHAR(255) NOT NULL,
            applied_at DATETIME2 DEFAULT SYSUTCDATETIME()
        );
    END
    """)
    print(" Migration tracking table ready.")

def get_applied_migrations(cursor):
    cursor.execute("SELECT filename FROM _Migrations")
    return {row[0] for row in cursor.fetchall()}

def apply_migration(cursor, filename):
    with open(os.path.join(MIGRATIONS_FOLDER, filename), "r", encoding="utf-8") as f:
        sql = f.read()
    print(f" Applying migration: {filename}")
    for statement in sql.split(";"):
        stmt = statement.strip()
        if stmt:
            cursor.execute(stmt)
    cursor.execute("INSERT INTO _Migrations (filename) VALUES (?)", (filename,))
    print(f" Migration applied: {filename}")

def run_migrations():
    with get_connection() as conn:
        cursor = conn.cursor()
        ensure_migration_table(cursor)
        applied = get_applied_migrations(cursor)
        all_files = sorted(f for f in os.listdir(MIGRATIONS_FOLDER) if f.endswith(".sql"))

        for filename in all_files:
            if filename not in applied:
                apply_migration(cursor, filename)
                conn.commit()
            else:
                print(f"Skipping already applied: {filename}")

        print(" All migrations up to date.")

if __name__ == "__main__":
    run_migrations()
