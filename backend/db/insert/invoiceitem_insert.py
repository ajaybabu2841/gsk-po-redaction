# db/insert/invoiceitem_insert.py
from db.db_connection import get_connection

def insert_invoice_items(invoice_header_id, df, product_col):
    """
    Insert invoice line items into dbo.InvoiceLineItem.
    Returns number of inserted items.
    """
    inserted_count = 0
    print("\n Starting DB insertion for Invoice Line Items...\n")

    for index, row in df.iterrows():
        product_name = row.get(product_col)
        if not product_name:
            continue

        gmm_code = row.get("GMMCode")
        batch_number = row.get("BatchNumber")
        mrp = row.get("MRP")
        uom = row.get("UnitOfMeasurement") or row.get("Unit")
        invoice_qty = row.get("InvoiceQty")
        invoice_qty_gsk = row.get("InvoiceQtyGSKPack")
        prod_unit_rate = row.get("ProdUnitRate")
        invoice_value = row.get("InvoiceValue")
        is_gsk = int(row.get("is_gsk", 0))
        ingestion_id = row.get("IngestionID")
        file_id = row.get("FileID")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO dbo.InvoiceLineItem
            (IngestionID, FileID, InvoiceHeaderID, ProductName, GMMCode, BatchNumber, MRP, UnitOfMeasurement, InvoiceQty, InvoiceQtyGSKPack, ProdUnitRate, InvoiceValue, is_gsk)
            OUTPUT inserted.InvoiceLineItemID
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ingestion_id,
            file_id,
            invoice_header_id,
            product_name,
            gmm_code,
            batch_number,
            mrp,
            uom,
            invoice_qty,
            invoice_qty_gsk,
            prod_unit_rate,
            invoice_value,
            is_gsk
        ))
        invoice_line_item_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        inserted_count += 1
        print(f" Inserted InvoiceLineItem → InvoiceLineItemID = {invoice_line_item_id}")

    print(f"\n Successfully inserted {inserted_count} invoice line items into dbo.InvoiceLineItem.\n")
    return inserted_count
