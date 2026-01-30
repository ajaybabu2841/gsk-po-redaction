import os
from io import BytesIO
from azure.storage.blob import BlobServiceClient
from utils.logging.logger import get_logger

logger = get_logger(__name__)

def download_blob_as_bytes(
    storage_account: str,
    container_name: str,
    blob_file_name: str
) -> BytesIO:
    """
    Downloads a blob directly into memory as BytesIO.
    No filesystem usage.
    """

    logger.info(
        "Downloading blob as bytes",
        extra={
            "storage_account": storage_account,
            "container_name": container_name,
            "blob_file_name": blob_file_name
        }
    )

    blob_service_client = BlobServiceClient.from_connection_string(
        os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    )

    blob_client = blob_service_client.get_blob_client(
        container=container_name,
        blob=blob_file_name
    )

    stream = blob_client.download_blob()
    pdf_bytes = stream.readall()

    logger.info(
        "Blob downloaded successfully",
        extra={"byte_size": len(pdf_bytes)}
    )

    return BytesIO(pdf_bytes)
