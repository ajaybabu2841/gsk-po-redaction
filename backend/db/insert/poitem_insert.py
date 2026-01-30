# from db.db_connection import get_connection
# from utils.logging.logger import get_logger

# logger = get_logger(__name__)

# # ======================================================
# # 🔹 Insert PO Items (Normalized DF Only)
# # ======================================================
# def insert_po_items(po_id: int, df):
#     """
#     Insert normalized POItem rows into dbo.POItem.

#     Contract:
#     - df MUST be normalized via LLM
#     - df columns MUST exactly match SQL schema
#     - df MUST contain only GSK rows
#     """

#     REQUIRED_COLUMNS = [
#         "ProductDescription",
#         "UnitOfMeasure",
#         "HSNCode",
#         "Quantity",
#         "Price",
#         "RCRate",
#         "ItemCodeFromPO",
#         "Marked"
#     ]

#     # ------------------------------------------------------------------
#     # Validation
#     # ------------------------------------------------------------------
#     missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
#     if missing_cols:
#         raise ValueError(
#             f"Normalized POItem DF missing columns: {missing_cols}"
#         )

#     if df.empty:
#         logger.warning(
#             "No POItem rows to insert",
#             extra={"po_id": po_id}
#         )
#         return 0

#     logger.info(
#         "Starting POItem DB insertion",
#         extra={
#             "po_id": po_id,
#             "row_count": len(df)
#         }
#     )

#     # ------------------------------------------------------------------
#     # Load Product Master (once)
#     # ------------------------------------------------------------------
#     def normalize_product_name(text: str) -> str:
#         return (
#             text.lower()
#                 .replace("-", "")
#                 .replace("(", "")
#                 .replace(")", "")
#                 .replace(",", "")
#                 .replace("  ", " ")
#                 .strip()
#         )

#     conn = get_connection()
#     cursor = conn.cursor()

#     cursor.execute(
#         "SELECT ProductID, ProductDescription FROM dbo.Product"
#     )
#     products = cursor.fetchall()

#     product_map = {
#         normalize_product_name(p.ProductDescription): p.ProductID
#         for p in products
#     }

#     inserted_count = 0

#     # ------------------------------------------------------------------
#     # Insert Rows
#     # ------------------------------------------------------------------
#     for _, row in df.iterrows():

#         product_name = row["ProductDescription"]
#         norm_name = normalize_product_name(product_name)

#         product_id = product_map.get(norm_name)

#         if not product_id:
#             logger.warning(
#                 "Product not found in master table",
#                 extra={"product_name": product_name}
#             )

#         cursor.execute(
#             """
#             INSERT INTO dbo.POItem
#             (
#                 POID,
#                 ProductID,
#                 ProductName,
#                 UnitOfMeasure,
#                 HSNCode,
#                 Quantity,
#                 GSKQuantity,
#                 Price,
#                 RCRate,
#                 ItemCodeFromPO,
#                 Marked,
#                 CreatedAt
#             )
#             OUTPUT inserted.POItemID
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME())
#             """,
#             (
#                 po_id,
#                 product_id,
#                 # product_name,
#                 row["ProductDescription"],
#                 row["UnitOfMeasure"],
#                 row["HSNCode"],
#                 row["Quantity"],
#                 1,  # GSKQuantity (always 1 per row)
#                 row["Price"],
#                 row["RCRate"],
#                 row["ItemCodeFromPO"],
#                 row["Marked"],
#             )
#         )

#         po_item_id = cursor.fetchone()[0]
#         inserted_count += 1

#         logger.info(
#             "Inserted POItem row",
#             extra={
#                 "po_id": po_id,
#                 "po_item_id": po_item_id,
#                 "product_name": product_name
#             }
#         )

#     # ------------------------------------------------------------------
#     # Commit & Cleanup
#     # ------------------------------------------------------------------
#     conn.commit()
#     conn.close()

#     logger.info(
#         "POItem insertion completed successfully",
#         extra={
#             "po_id": po_id,
#             "inserted_count": inserted_count
#         }
#     )

#     return inserted_count


from typing import List
from models.po_models import POItemModel
from db.db_connection import get_connection
from utils.logging.logger import get_logger

logger = get_logger(__name__)

def insert_po_items(po_id: str, items: List[POItemModel]):
    """
    Insert POItem rows into dbo.POItem.

    Contract:
    - items MUST be validated POItemModel objects
    - items MUST contain only GSK rows
    """

    if not items:
        logger.warning(
            "No POItem rows to insert",
            extra={"po_id": po_id}
        )
        return 0

    logger.info(
        "Starting POItem DB insertion",
        extra={
            "po_id": po_id,
            "row_count": len(items)
        }
    )

    # ------------------------------------------------------------------
    # Load Product Master (once)
    # ------------------------------------------------------------------
    def normalize_product_name(text: str) -> str:
        return (
            text.lower()
                .replace("-", "")
                .replace("(", "")
                .replace(")", "")
                .replace(",", "")
                .replace("  ", " ")
                .strip()
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT ProductID, ProductDescription FROM dbo.Product"
    )
    products = cursor.fetchall()

    product_map = {
        normalize_product_name(p.ProductDescription): p.ProductID
        for p in products
    }

    inserted_count = 0

    # ------------------------------------------------------------------
    # Insert Rows
    # ------------------------------------------------------------------
    for item in items:

        norm_name = normalize_product_name(item.ProductDescription)
        product_id = product_map.get(norm_name)

        if not product_id:
            logger.warning(
                "Product not found in master table",
                extra={"product_name": item.ProductDescription}
            )

        cursor.execute(
            """
            INSERT INTO dbo.POItem
            (
                POID,
                ProductID,
                ProductName,
                UnitOfMeasure,
                HSNCode,
                Quantity,
                GSKQuantity,
                Price,
                RCRate,
                ItemCodeFromPO,
                Marked,
                CreatedAt
            )
            OUTPUT inserted.POItemID
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME())
            """,
            (
                po_id,
                product_id,
                item.ProductDescription,
                item.UnitOfMeasure,
                item.HSNCode,
                item.Quantity,
                1,
                item.Price,
                item.RCRate,
                item.ItemCodeFromPO,
                item.Marked,
            )
        )

        cursor.fetchone()
        inserted_count += 1

    conn.commit()
    conn.close()

    logger.info(
        "POItem insertion completed successfully",
        extra={
            "po_id": po_id,
            "inserted_count": inserted_count
        }
    )

    return inserted_count
