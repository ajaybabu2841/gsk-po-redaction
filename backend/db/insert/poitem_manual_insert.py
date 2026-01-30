import uuid
from db.db_connection import get_connection

COLUMN_MAP = {
    "product_id": "ProductID",
    "product_name": "ProductName",
    "unit_of_measure": "UnitOfMeasure",
    "hsn_code": "HSNCode",
    "quantity": "Quantity",
    "gsk_quantity": "GSKQuantity",
    "price": "Price",
    "rc_rate": "RCRate",
    "item_code_from_po": "ItemCodeFromPO",
    "marked": "Marked",
}

def insert_po_items_manual(po_id: str, items: list):
    conn = get_connection()
    cursor = conn.cursor()

    for item in items:
        po_item_id = str(uuid.uuid4())
        data = item.model_dump(exclude_unset=True)

        columns = ["POItemID", "POID"]
        placeholders = ["?", "?"]
        values = [po_item_id, po_id]

        for api_field, db_column in COLUMN_MAP.items():
            if api_field in data:
                columns.append(db_column)
                placeholders.append("?")
                values.append(data[api_field])

        sql = f"""
            INSERT INTO dbo.POItem
            ({", ".join(columns)}, CreatedAt)
            VALUES ({", ".join(placeholders)}, SYSUTCDATETIME())
        """

        cursor.execute(sql, values)

    conn.commit()
    conn.close()
    print(f" Manual POItems inserted for POID: {po_id}")