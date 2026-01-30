from decimal import Decimal
from typing import Optional,List, Dict, Any, Literal
from pydantic import BaseModel, Field, EmailStr
from datetime import date

class PoClassifyModel(BaseModel):
    Type: Literal["Bad Quality","OverCrowded","Header & Row Items are multiline", "Row Items are multiline but not Header", "Rows items are Misaligned to the Header"]
    Confidence : float

class MedicineList(BaseModel):
    MedicineListName: List[str]


class POItemModel(BaseModel):
    ProductDescription: str = Field(..., description="Full item name and description as in the PO. You will always have a name but description is optional")
    ExtendedProductName: Optional[str] = Field(...,description=
        "A longer or more detailed version of the main product name, if present in the PO. "
        "This usually appears on the line immediately below the product name and contains "
        "the same base product with additional details such as full dosage form, strength, "
        "or expanded wording. Do NOT repeat the main product name here if it is the same.\n\n"
        "Example:\n"
        "ProductName: 'ACITROM 1 MG TAB'\n"
        "ExtendedProductName: 'ACITROM 1 MG TABLET'"
    )
    UnitOfMeasure: Optional[str] = Field(None, description="Unit of Measurement as in the PO")
    HSNCode: Optional[str] = Field(None, description="HSN / Material code as in the PO")
    Quantity: Optional[int] = Field(None, description="Quantity ordered as in the PO")
    Price: Optional[float] = Field(None, description="Unit price as in the PO")
    RCRate: Optional[float] = Field(None, description="Rate Contract rate as in the PO")
    ItemCodeFromPO: Optional[str] = Field(None, description="Item / Material code as in the PO")
    Marked: int = 1

class POItemList(BaseModel):
    items : list[POItemModel]

class POTableEvaluation(BaseModel):
    table_index: int
    page_number: int
    grid: Any
    markdown: str
    is_po: bool
    reason: str = Field(description="Why the table is classified as PO or not")
    med_col_idx: Optional[int] = None
    header_rows: Optional[List[int]] = None
    
class POTableEvaluationResult(BaseModel):
    tables: List[POTableEvaluation]

class POHeader(BaseModel):
    PONumber: Optional[str] = Field(
        None, 
        description="Purchase Order number/reference"
    )
    PODate: Optional[date] = Field(
        None, 
        description="Date when PO was issued/created (NOT approval date)"
    )
    AWDName: Optional[str] = Field(
        None, 
        description="Vendor/Supplier/AWD name (the company fulfilling the order)"
    )
    VendorGSTIN: Optional[str] = Field(
        None, 
        description="Vendor's GST Identification Number (15 characters)"
    )
    VendorCode: Optional[str] = Field(
        None, 
        description="Vendor code/ID assigned by the hospital"
    )
    POApprovalDate: Optional[date] = Field(
        None, 
        description="Date when PO was approved (can be different or same from issue date)"
    )
    RCNumber: Optional[str] = Field(
        None, 
        description="Rate Contract number/reference"
    )
    RCValidityDate: Optional[date] = Field(
        None, 
        description="Rate Contract validity/expiry date"
    )
    HospitalName: Optional[str] = Field(
        None, 
        description="Name of the hospital/buyer organization not the pharmacy details"
    )
    HospitalId:Optional[str] = Field(
        None,
        description="ID of the hospital/buyer organization"
    )


class POItem(BaseModel):
    ProductName: Optional[str] = Field(
        None,
        description="Name of the product mentioned in the PO"
    )

    Product_Code: Optional[str] = Field(
        None,
        description="Product / material code mentioned in the PO"
    )

    PO_UOM: Optional[str] = Field(
        None,
        description="Unit of Measurement mentioned in the PO"
    )

    PO_Qty: Optional[int] = Field(
        None,
        description="Quantity mentioned in the PO"
    )

    PO_Qty_GSK_Pack: Optional[int] = Field(
        None,
        description="Quantity converted into GSK pack size"
    )

    ProductUnitRate: Optional[float] = Field(
        None,
        description="Unit rate of the product mentioned in the PO"
    )

    RC_Rate: Optional[float] = Field(
        None,
        description="Rate Contract rate applicable to the product"
    )
    GMM_Code: Optional[str] = Field(
        None,
        description="GMM code of the product if available"
    )
    RC_Rate: Optional[float] = Field(
        None,
        description="Rate Contract rate applicable to the product"
    )

class ProcessPDFResponse(BaseModel):
    original_file_name: str
    # local_input_pdf_path: str
    # redacted_pdf_path: str
    # predicted_csv_path: str
    header_data: dict
    medicine_column: str
    # NEW FIELDS
    table_columns: List[str]
    table_rows: List[Dict[str, Any]]

class BlobProcessRequest(BaseModel):
    storage_account: str
    container_name: str
    blob_file_name: str
    file_id: str | None = None
    ingestion_id: str | None = None

class ManualRedactionResponse(BaseModel):
    status: Literal["MANUAL_REQUIRED"]
    file_name: str
    message: str
    reason: str


class HospitalCreate(BaseModel):
    HospitalName: str

    City: Optional[str] = None
    State: Optional[str] = None
    HospitalEmail: Optional[EmailStr] = None

    RCNo: Optional[int] = None
    RcCreatorName: Optional[str] = None
    PriceApprovalfrPeriod: Optional[date] = None
    PriceApprovaltoPeriod: Optional[date] = None
    AtHo: Optional[str] = None
    RCExtension: Optional[date] = None

    class Config:
        extra = "forbid"

class HospitalUpdate(BaseModel):
    HospitalEmail: Optional[EmailStr] = None
    RCExtension: Optional[date] = None

    class Config:
        extra = "forbid" 
 
class ProductInsert(BaseModel):
    ProductName: str
    Product_Code: Optional[str] = None
    PO_UOM: Optional[str] = None
    PO_Qty: Optional[int] = None
    PO_Qty_GSK_Pack: Optional[int] = None
    ProductUnitRate: Optional[float] = None
    RC_Rate: Optional[float] = None
    GMM_Code: Optional[str] = None

class ManualPOHeaderRequest(BaseModel):
    ingestion_id: str
    file_id: str
    po_id: Optional[str] = None

    po_number:Optional[str] = None
    po_date: Optional[date] = None
    hospital_id: Optional[str] = None
    hospital_name: Optional[str] = None

    vendor_gstin: Optional[str] = None
    vendor_code: Optional[str] = None
    awd_name: Optional[str] = None

    po_approval_date: Optional[date] = None
    rc_number: Optional[str] = None
    rc_validity_date: Optional[date] = None

class ManualPOItem(BaseModel):
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    unit_of_measure: Optional[str] = None
    hsn_code: Optional[str] = None
    quantity: Optional[int] = None
    gsk_quantity: Optional[int] = None
    price: Optional[Decimal] = None
    rc_rate: Optional[Decimal] = None
    item_code_from_po: Optional[str] = None
    marked: Optional[bool] = None


class ManualPOItemRequest(BaseModel):
    po_id: str
    items: List[ManualPOItem]